"""
Step 1: Core Discovery - BFS crawling with state capture.
Discovers routes, captures screenshots, DOM snapshots, and actions.
"""

import asyncio
import heapq
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from cyberAI.recon.network_intelligence import NetworkIntelligence
from urllib.parse import urljoin, urlparse

from loguru import logger
from playwright.async_api import BrowserContext, Page, TimeoutError as PlaywrightTimeout

from cyberAI.config import get_config
from cyberAI.models import Action, Route
from cyberAI.utils.browser import (
    dump_dom,
    get_browser_pool,
    get_page_actions,
    take_screenshot,
)
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    generate_run_id,
    load_json,
    safe_filename,
)

try:
    from cyberAI.recon.priority_scorer import score_url_security_relevance, path_template_for_novelty
except ImportError:
    def score_url_security_relevance(url: str) -> float:
        return 0.5
    def path_template_for_novelty(url: str) -> str:
        return url


class CoreDiscovery:
    """
    BFS crawler that discovers all reachable routes in an application.
    Captures screenshots, DOM snapshots, and available actions.
    """
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._visited_urls: set[str] = set()
        self._routes: list[Route] = []
        self._base_domain: str = ""
        self._max_depth = 10
        self._max_pages = 500
        self._page_timeout = 30000
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        return f"{parsed.scheme}://{parsed.netloc}{path}"
    
    def _is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to the target domain."""
        try:
            parsed = urlparse(url)
            base = (self._base_domain or "").lower()
            netloc = (parsed.netloc or "").lower()

            # Treat www.<domain> and <domain> as same-site.
            if base.startswith("www."):
                base_alt = base.removeprefix("www.")
            else:
                base_alt = "www." + base if base else base

            return netloc == base or netloc == base_alt or netloc.endswith("." + base) or netloc.endswith("." + base_alt)
        except Exception:
            return False
    
    def _is_valid_crawl_url(self, url: str) -> bool:
        """Check if URL should be crawled."""
        if not url or not url.startswith(('http://', 'https://')):
            return False
        
        if not self._is_same_domain(url):
            return False
        
        skip_extensions = [
            '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
            '.css', '.js', '.woff', '.woff2', '.ttf', '.eot',
            '.mp3', '.mp4', '.avi', '.mov', '.zip', '.tar', '.gz'
        ]
        lower_url = url.lower()
        if any(lower_url.endswith(ext) for ext in skip_extensions):
            return False
        
        skip_patterns = ['logout', 'signout', 'delete', 'remove', 'destroy']
        if any(p in lower_url for p in skip_patterns):
            return False
        
        return True
    
    def _extract_slug(self, url: str) -> str:
        """Extract a meaningful slug from URL."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        if not path:
            return "home"
        return path.replace('/', '_')
    
    async def _detect_page_state(self, page: Page) -> dict:
        """Detect the current state of the page."""
        state = {
            "has_error": False,
            "is_empty": False,
            "is_loading": False,
            "has_form": False,
            "is_login_page": False,
            "has_toast": False,
            "indicators": [],
        }
        
        try:
            indicators = await page.evaluate('''() => {
                const indicators = [];
                
                // Check for error states
                const errorClasses = ['error', 'alert-danger', 'alert-error', 'error-message'];
                errorClasses.forEach(cls => {
                    if (document.querySelector('.' + cls)) {
                        indicators.push('error_' + cls);
                    }
                });
                
                // Check for empty states
                const emptyClasses = ['empty', 'no-data', 'no-results', 'empty-state'];
                emptyClasses.forEach(cls => {
                    if (document.querySelector('.' + cls)) {
                        indicators.push('empty_' + cls);
                    }
                });
                
                // Check for loading states
                const loadingClasses = ['loading', 'spinner', 'skeleton', 'loader'];
                loadingClasses.forEach(cls => {
                    if (document.querySelector('.' + cls)) {
                        indicators.push('loading_' + cls);
                    }
                });
                
                // Check for login/auth page
                const loginIndicators = ['login', 'signin', 'sign-in', 'auth'];
                loginIndicators.forEach(ind => {
                    if (document.body.innerHTML.toLowerCase().includes(ind)) {
                        indicators.push('auth_' + ind);
                    }
                });
                
                // Check for forms
                if (document.querySelector('form')) {
                    indicators.push('has_form');
                }
                
                // Check for toasts/notifications
                const toastClasses = ['toast', 'notification', 'snackbar', 'alert'];
                toastClasses.forEach(cls => {
                    if (document.querySelector('.' + cls)) {
                        indicators.push('toast_' + cls);
                    }
                });
                
                return indicators;
            }''')
            
            state["indicators"] = indicators
            state["has_error"] = any("error_" in i for i in indicators)
            state["is_empty"] = any("empty_" in i for i in indicators)
            state["is_loading"] = any("loading_" in i for i in indicators)
            state["has_form"] = "has_form" in indicators
            state["is_login_page"] = any("auth_" in i for i in indicators)
            state["has_toast"] = any("toast_" in i for i in indicators)
            
        except Exception as e:
            logger.debug(f"Error detecting page state: {e}")
        
        return state
    
    async def _extract_links(self, page: Page) -> list[str]:
        """Extract all links from the current page."""
        try:
            links = await page.evaluate(r'''() => {
                const links = new Set();
                
                // Regular links
                document.querySelectorAll('a[href]').forEach(a => {
                    const href = a.getAttribute('href');
                    if (href && !href.startsWith('#') && !href.startsWith('javascript:')) {
                        links.add(href);
                    }
                });
                
                // Links in onclick handlers
                document.querySelectorAll('[onclick]').forEach(el => {
                    const onclick = el.getAttribute('onclick');
                    const matches = onclick.match(/(?:location\.href|window\.location)\s*=\s*['"](.*?)['"]/);
                    if (matches) {
                        links.add(matches[1]);
                    }
                });
                
                // Data attributes with URLs
                document.querySelectorAll('[data-href], [data-url], [data-link]').forEach(el => {
                    ['data-href', 'data-url', 'data-link'].forEach(attr => {
                        const val = el.getAttribute(attr);
                        if (val) links.add(val);
                    });
                });
                
                return Array.from(links);
            }''')
            
            absolute_links = []
            current_url = page.url
            
            for link in links:
                if link.startswith(('http://', 'https://')):
                    absolute_links.append(link)
                elif link.startswith('/'):
                    absolute_links.append(urljoin(current_url, link))
                else:
                    absolute_links.append(urljoin(current_url, link))
            
            return list(set(absolute_links))
            
        except Exception as e:
            logger.debug(f"Error extracting links: {e}")
            return []
    
    async def _discover_modals_and_drawers(self, page: Page) -> list[dict]:
        """Discover and open modals, drawers, and dropdown menus."""
        modals_found = []
        
        try:
            triggers = await page.evaluate('''() => {
                const triggers = [];
                
                // Modal triggers
                const modalSelectors = [
                    '[data-toggle="modal"]',
                    '[data-bs-toggle="modal"]',
                    '[data-target^="#"]',
                    '[aria-haspopup="dialog"]',
                    '.modal-trigger',
                    '.open-modal'
                ];
                
                modalSelectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        triggers.push({
                            type: 'modal',
                            selector: sel,
                            text: el.textContent?.trim().substring(0, 50) || ''
                        });
                    });
                });
                
                // Drawer triggers
                const drawerSelectors = [
                    '[data-toggle="drawer"]',
                    '.drawer-trigger',
                    '[aria-controls*="drawer"]',
                    '[aria-controls*="sidebar"]'
                ];
                
                drawerSelectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        triggers.push({
                            type: 'drawer',
                            selector: sel,
                            text: el.textContent?.trim().substring(0, 50) || ''
                        });
                    });
                });
                
                // Dropdown triggers
                const dropdownSelectors = [
                    '[data-toggle="dropdown"]',
                    '[data-bs-toggle="dropdown"]',
                    '.dropdown-toggle',
                    '[aria-haspopup="menu"]'
                ];
                
                dropdownSelectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        triggers.push({
                            type: 'dropdown',
                            selector: sel,
                            text: el.textContent?.trim().substring(0, 50) || ''
                        });
                    });
                });
                
                return triggers;
            }''')
            
            for trigger in triggers[:10]:
                try:
                    element = await page.query_selector(trigger['selector'])
                    if element:
                        await element.click()
                        await asyncio.sleep(0.5)
                        
                        modal_content = await page.evaluate('''() => {
                            const modal = document.querySelector('.modal.show, .modal.active, [role="dialog"]:not([hidden])');
                            if (modal) {
                                return {
                                    html: modal.innerHTML.substring(0, 1000),
                                    hasForm: modal.querySelector('form') !== null
                                };
                            }
                            return null;
                        }''')
                        
                        if modal_content:
                            modals_found.append({
                                "trigger": trigger,
                                "has_form": modal_content.get("hasForm", False),
                            })
                        
                        close_btn = await page.query_selector('.modal .close, .modal .btn-close, [data-dismiss="modal"]')
                        if close_btn:
                            await close_btn.click()
                            await asyncio.sleep(0.3)
                        else:
                            await page.keyboard.press('Escape')
                            await asyncio.sleep(0.3)
                            
                except Exception as e:
                    logger.debug(f"Error with modal trigger: {e}")
                    
        except Exception as e:
            logger.debug(f"Error discovering modals: {e}")
        
        return modals_found
    
    async def _process_page(
        self,
        page: Page,
        url: str,
        depth: int,
        role: Optional[str] = None
    ) -> tuple[Route, list[str]]:
        """
        Process a single page: capture screenshot, DOM, actions, and links.
        
        Args:
            page: Playwright Page object
            url: URL being processed
            depth: Current crawl depth
            role: Role context
            
        Returns:
            Tuple of (Route, list of discovered URLs)
        """
        slug = self._extract_slug(url)
        safe_slug = safe_filename(f"{slug}_{depth}")
        
        try:
            await page.goto(url, timeout=self._page_timeout, wait_until="networkidle")
        except PlaywrightTimeout:
            logger.warning(f"Timeout loading {url}, continuing with partial content")
        except Exception as e:
            logger.warning(f"Error loading {url}: {e}")
            raise
        
        await asyncio.sleep(1)
        
        state = await self._detect_page_state(page)
        
        screenshot_path = await take_screenshot(page, safe_slug)
        dom_path = await dump_dom(page, safe_slug)
        
        raw_actions = await get_page_actions(page)
        actions = [
            Action(
                action_type=a.get("type", "click"),
                selector=a.get("selector", ""),
                text=a.get("text", ""),
                href=a.get("href"),
                form_fields=a.get("fields", []),
            )
            for a in raw_actions
        ]
        
        page_title = await page.title()
        
        modals = await self._discover_modals_and_drawers(page)
        
        links = await self._extract_links(page)
        
        route = Route(
            slug=slug,
            url=url,
            screenshot_path=screenshot_path,
            dom_path=dom_path,
            actions=actions,
            role_context=role,
            page_title=page_title,
            source="crawl",
        )
        
        route.raw_state = state
        route.modals_found = len(modals)
        
        return route, links

    async def _inject_session_into_context(
        self, context: BrowserContext, role: str, start_url: str
    ) -> None:
        """Load session from store and add cookies to context (ASRTS 2.4.5)."""
        try:
            from cyberAI.identity.session_store import SessionStore
            store_path = self.config.get_output_path("sessions", "sessions.json")
            store = SessionStore(store_path)
            engagement_id = self.config.run_id or "default"
            session = store.get(engagement_id, role)
            if not session or not session.get("cookies"):
                return
            parsed = urlparse(start_url)
            domain = parsed.netloc or ""
            cookies_list = [
                {"name": k, "value": v, "domain": domain, "path": "/"}
                for k, v in session["cookies"].items()
            ]
            if cookies_list:
                await context.add_cookies(cookies_list)
                logger.debug(f"Injected session for role {role} ({len(cookies_list)} cookies)")
        except Exception as e:
            logger.debug(f"Session inject: {e}")

    async def _check_and_repair_session(
        self,
        context: BrowserContext,
        page: Page,
        role: str,
        start_url: str,
    ) -> None:
        """Re-check session health; if unhealthy, run repair and re-inject (ASRTS 2.4.5)."""
        try:
            from cyberAI.identity.session_store import SessionStore
            from cyberAI.identity.session_health import SessionHealthChecker, SessionRepairRunner
            from cyberAI.identity.login_sequence import load_login_sequence
            from pathlib import Path
            store_path = self.config.get_output_path("sessions", "sessions.json")
            store = SessionStore(store_path)
            engagement_id = self.config.run_id or "default"
            session = store.get(engagement_id, role)
            if not session or not session.get("cookies"):
                return
            checker = SessionHealthChecker(start_url)
            if await checker.is_healthy(session["cookies"]):
                return
            logger.info(f"Session unhealthy for {role}; attempting repair")
            acc = self.config.get_role_account(role) if getattr(self.config, "get_role_account", None) else None
            credentials = {"username": acc.username, "password": acc.password} if acc else {}
            login_sequence_path = None
            try:
                from cyberAI.governance.loader import load_engagement_config
                engagement = load_engagement_config(self.config.engagement_config_path)
                if engagement and engagement.test_identities:
                    for ti in engagement.test_identities:
                        if ti.role == role and ti.login_sequence_ref:
                            base = Path(self.config.engagement_config_path).parent if getattr(self.config, "engagement_config_path", None) else self.config.output_dir
                            login_sequence_path = (base / ti.login_sequence_ref).resolve()
                            break
            except Exception:
                pass
            if not login_sequence_path or not login_sequence_path.is_file():
                for name in (f"login_{role}.json", "login_sequence.json"):
                    p = self.config.get_output_path("recon", "intelligence", name)
                    if p and p.is_file():
                        login_sequence_path = p
                        break
            repair = SessionRepairRunner(
                store, engagement_id, role,
                login_sequence_path=login_sequence_path,
                credentials=credentials,
            )
            if await repair.run(page):
                await self._inject_session_into_context(context, role, start_url)
        except Exception as e:
            logger.debug(f"Session check/repair: {e}")
    
    async def crawl(
        self,
        start_url: str,
        role: Optional[str] = None,
        max_depth: Optional[int] = None,
        max_pages: Optional[int] = None,
        context: Optional[BrowserContext] = None,
        network_intel: Optional["NetworkIntelligence"] = None,
        seed_urls: Optional[list[str]] = None,
    ) -> list[Route]:
        """
        Perform BFS crawl starting from the given URL.
        
        Args:
            start_url: Starting URL for the crawl
            role: Role context for this crawl
            max_depth: Maximum crawl depth
            max_pages: Maximum pages to crawl
            context: Optional existing browser context (caller owns it; not closed here).
            network_intel: Optional NetworkIntelligence to attach to context to capture requests.
            
        Returns:
            List of discovered Route objects
        """
        if max_depth is not None:
            self._max_depth = max_depth
        if max_pages is not None:
            self._max_pages = max_pages
        
        parsed = urlparse(start_url)
        self._base_domain = parsed.netloc
        
        logger.info(f"Starting crawl from {start_url} (role: {role})")
        
        own_context = False
        if context is None:
            browser_pool = get_browser_pool()
            context = await browser_pool.get_browser_context(role=role)
            own_context = True
        
        if network_intel is not None:
            await network_intel.attach_to_context(context, role)
        
        page = await context.new_page()
        
        # ASRTS 2.4.5: Inject session cookies when crawling as a role
        if role:
            await self._inject_session_into_context(context, role, start_url)
        
        try:
            # ASRTS Phase 2.2: priority queue (heap) so high-value URLs are crawled first
            novelty = None
            try:
                from cyberAI.recon.novelty_index import NoveltyIndex
                novelty_path = self.config.get_output_path("recon", "intelligence", "novelty_index.json")
                novelty = NoveltyIndex(novelty_path)
                novelty.load()
            except ImportError:
                pass

            def _priority(url: str, depth: int, is_novel: bool) -> float:
                rel = score_url_security_relevance(url)
                depth_penalty = 0.05 * depth
                novelty_boost = 0.2 if is_novel else 0.0
                return rel + novelty_boost - depth_penalty

            seq = 0
            start_priority = _priority(start_url, 0, novelty.add_from_canonical("GET", path_template_for_novelty(start_url), []) if novelty else False)
            heap: list[tuple[float, int, str, int]] = [(-start_priority, seq, start_url, 0)]
            seq += 1
            if seed_urls:
                for u in seed_urls:
                    if u and isinstance(u, str) and self._is_valid_crawl_url(u):
                        is_nov = novelty.add_from_canonical("GET", path_template_for_novelty(u), []) if novelty else False
                        p = _priority(u, 0, is_nov)
                        heapq.heappush(heap, (-p, seq, u, 0))
                        seq += 1

            while heap and len(self._routes) < self._max_pages:
                _neg_pri, _s, url, depth = heapq.heappop(heap)
                normalized = self._normalize_url(url)
                if normalized in self._visited_urls:
                    continue
                if depth > self._max_depth:
                    continue
                if not self._is_valid_crawl_url(url):
                    continue
                self._visited_urls.add(normalized)
                logger.info(f"Crawling [{depth}] (pri={-_neg_pri:.2f}): {url}")
                try:
                    route, new_links = await self._process_page(page, url, depth, role)
                    self._routes.append(route)
                    # ASRTS 2.4.5: Health re-check every 20 pages; repair and re-inject if needed
                    if role and len(self._routes) % 20 == 0:
                        await self._check_and_repair_session(context, page, role, start_url)
                    for link in new_links:
                        norm_link = self._normalize_url(link)
                        if norm_link in self._visited_urls:
                            continue
                        if not self._is_valid_crawl_url(link):
                            continue
                        new_depth = depth + 1
                        path_tpl = path_template_for_novelty(link)
                        is_novel = novelty.add_from_canonical("GET", path_tpl, []) if novelty else False
                        pri = _priority(link, new_depth, is_novel)
                        heapq.heappush(heap, (-pri, seq, link, new_depth))
                        seq += 1
                    if novelty is not None:
                        novelty.save()
                    await asyncio.sleep(self.config.request_delay_ms / 1000)
                except Exception as e:
                    logger.warning(f"Error processing {url}: {e}")
                    continue
            logger.info(f"Crawl complete. Discovered {len(self._routes)} routes.")
        finally:
            await page.close()
            if own_context:
                await context.close()
        
        return self._routes
    
    async def crawl_multi_step_forms(self, page: Page, form_route: Route) -> list[Route]:
        """
        Walk through multi-step forms and capture each step.
        
        Args:
            page: Playwright Page object
            form_route: Route containing the form
            
        Returns:
            List of Route objects for each form step
        """
        step_routes = []
        
        try:
            step_count = 0
            max_steps = 10
            
            while step_count < max_steps:
                step_slug = f"{form_route.slug}_step{step_count}"
                
                screenshot_path = await take_screenshot(page, step_slug)
                dom_path = await dump_dom(page, step_slug)
                
                step_route = Route(
                    slug=step_slug,
                    url=page.url,
                    screenshot_path=screenshot_path,
                    dom_path=dom_path,
                    role_context=form_route.role_context,
                    source="form_step",
                )
                step_routes.append(step_route)
                
                next_button = await page.query_selector(
                    'button[type="submit"]:not([disabled]), '
                    '.next-step, .btn-next, [data-action="next"]'
                )
                
                if not next_button:
                    break
                
                button_text = await next_button.text_content()
                if button_text and any(t in button_text.lower() for t in ['submit', 'finish', 'complete']):
                    break
                
                await next_button.click()
                await asyncio.sleep(1)
                
                step_count += 1
                
        except Exception as e:
            logger.debug(f"Error walking form steps: {e}")
        
        return step_routes
    
    def save_routes(self) -> str:
        """
        Save discovered routes to JSON file.
        
        Returns:
            Path to saved file
        """
        output_path = self.config.get_output_path(
            "recon", "intelligence", "routes.json"
        )
        
        data = add_meta_to_output(
            {"routes": [r.model_dump() for r in self._routes]},
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        
        atomic_write_json(output_path, data)
        logger.info(f"Saved {len(self._routes)} routes to {output_path}")
        
        return str(output_path)
    
    def get_routes(self) -> list[Route]:
        """Get discovered routes."""
        return self._routes


async def run_core_discovery(
    target_url: str,
    role: Optional[str] = None,
    run_id: Optional[str] = None,
    context: Optional[BrowserContext] = None,
    network_intel: Optional["NetworkIntelligence"] = None,
    seed_urls: Optional[list[str]] = None,
) -> list[Route]:
    """
    Run core discovery on target URL.
    
    Args:
        target_url: URL to start crawling from
        role: Role context
        run_id: Run ID for this execution
        context: Optional browser context (e.g. with network intel attached); not closed by this function.
        network_intel: Optional NetworkIntelligence to capture requests during crawl.
        
    Returns:
        List of discovered Route objects
    """
    discovery = CoreDiscovery(run_id=run_id)
    routes = await discovery.crawl(
        target_url, role=role, context=context, network_intel=network_intel, seed_urls=seed_urls
    )
    discovery.save_routes()
    return routes


if __name__ == "__main__":
    async def main():
        import sys
        
        url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
        
        discovery = CoreDiscovery()
        routes = await discovery.crawl(url, max_pages=10)
        discovery.save_routes()
        
        print(f"\nDiscovered {len(routes)} routes:")
        for route in routes:
            print(f"  - {route.slug}: {route.url}")
    
    asyncio.run(main())
