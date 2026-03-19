"""
Playwright browser pool manager for CyberAI platform.
Handles browser lifecycle, request interception, and page operations.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
from uuid import uuid4

from fake_useragent import UserAgent
from loguru import logger
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Request,
    Response,
    async_playwright,
)

from cyberAI.config import get_config
from cyberAI.models import HttpMethod, RequestRecord
from cyberAI.utils.helpers import atomic_write_text, safe_filename
from cyberAI.utils.proxy_manager import get_proxy_manager

try:
    from cyberAI.governance.scope import get_scope_validator
except ImportError:
    get_scope_validator = None


class RequestInterceptor:
    """Captures and stores intercepted network requests."""
    
    def __init__(self):
        self.records: list[RequestRecord] = []
        self._lock = asyncio.Lock()
    
    async def add_record(self, record: RequestRecord) -> None:
        """Add a request record."""
        async with self._lock:
            self.records.append(record)
    
    def get_records(self) -> list[RequestRecord]:
        """Get all captured records."""
        return self.records.copy()
    
    def clear(self) -> None:
        """Clear all records."""
        self.records.clear()


class BrowserPool:
    """
    Manages a pool of Playwright browser instances.
    Handles browser lifecycle, context creation, and request interception.
    """
    
    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._contexts: list[BrowserContext] = []
        self._ua = UserAgent()
        self._lock = asyncio.Lock()
        self._request_queue: list[RequestRecord] = []
        self._request_callbacks: list[Callable[[RequestRecord], None]] = []
        self._console_errors: list[dict] = []
        self._network_failures: list[dict] = []
    
    async def initialize(self) -> None:
        """Initialize the browser pool."""
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            config = get_config()
            self._browser = await self._playwright.chromium.launch(
                headless=config.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ]
            )
            logger.info("Browser pool initialized")
    
    async def close(self) -> None:
        """Close all browser resources."""
        for context in self._contexts:
            try:
                await context.close()
            except Exception:
                pass
        self._contexts.clear()
        
        if self._browser:
            await self._browser.close()
            self._browser = None
        
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        
        logger.info("Browser pool closed")
    
    def _get_user_agent(self) -> str:
        """Get a random user agent."""
        config = get_config()
        if config.user_agent_rotation:
            try:
                return self._ua.random
            except Exception:
                pass
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    async def get_browser_context(
        self,
        role: Optional[str] = None,
        proxy: Optional[str] = None,
        headless: Optional[bool] = None,
        intercept_requests: bool = True,
        storage_state: Optional[dict] = None,
    ) -> BrowserContext:
        """
        Create a new browser context.
        
        Args:
            role: Role context for this session
            proxy: Proxy server in host:port format
            headless: Override headless setting
            intercept_requests: Whether to intercept network requests
            storage_state: Optional storage state to restore
            
        Returns:
            Configured BrowserContext
        """
        await self.initialize()
        
        config = get_config()
        
        context_options: dict[str, Any] = {
            "user_agent": self._get_user_agent(),
            "viewport": {"width": 1920, "height": 1080},
            "ignore_https_errors": True,
            "java_script_enabled": True,
        }
        
        if proxy:
            context_options["proxy"] = {"server": f"http://{proxy}"}
        elif config.proxy_enabled:
            proxy_manager = get_proxy_manager()
            next_proxy = await proxy_manager.get_next_proxy()
            if next_proxy:
                context_options["proxy"] = {"server": f"http://{next_proxy}"}
        
        if storage_state:
            context_options["storage_state"] = storage_state
        
        context = await self._browser.new_context(**context_options)
        context._role = role
        context._interceptor = RequestInterceptor() if intercept_requests else None

        # ASRTS: abort out-of-scope requests before they are sent
        if get_scope_validator is not None:
            validator = get_scope_validator()
            if validator is not None:
                async def scope_route(route):
                    req = route.request
                    allowed, reason = validator.is_in_scope(req.url, req.method)
                    if not allowed:
                        logger.debug(f"Browser scope abort: {req.url} reason={reason}")
                        await route.abort()
                    else:
                        await route.continue_()
                await context.route("**/*", scope_route)
        
        if intercept_requests:
            context.on("request", lambda req: asyncio.create_task(self._on_request(context, req)))
            context.on("response", lambda resp: asyncio.create_task(self._on_response(context, resp)))
        
        context.on("console", lambda msg: self._on_console(msg))
        context.on("pageerror", lambda err: self._on_page_error(err))
        
        async with self._lock:
            self._contexts.append(context)
        
        logger.debug(f"Created browser context for role: {role}")
        return context
    
    async def _on_request(self, context: BrowserContext, request: Request) -> None:
        """Handle intercepted request."""
        pass
    
    async def _on_response(self, context: BrowserContext, response: Response) -> None:
        """Handle intercepted response and create request record."""
        try:
            request = response.request
            
            headers = dict(request.headers)
            response_headers = dict(response.headers)
            
            body = None
            body_json = None
            if request.method in ("POST", "PUT", "PATCH"):
                try:
                    body = request.post_data
                    if body:
                        import json
                        try:
                            body_json = json.loads(body)
                        except json.JSONDecodeError:
                            pass
                except Exception:
                    pass
            
            response_body = None
            response_json = None
            content_type = response_headers.get("content-type", "")
            if "application/json" in content_type or "text/" in content_type:
                try:
                    response_body = await response.text()
                    if "application/json" in content_type:
                        import json
                        try:
                            response_json = json.loads(response_body)
                        except json.JSONDecodeError:
                            pass
                except Exception:
                    pass
            
            cookies = {}
            try:
                page_cookies = await context.cookies()
                cookies = {c["name"]: c["value"] for c in page_cookies}
            except Exception:
                pass
            
            record = RequestRecord(
                method=HttpMethod(request.method),
                url=request.url,
                headers=headers,
                cookies=cookies,
                body=body,
                body_json=body_json,
                response_status=response.status,
                response_headers=response_headers,
                response_body=response_body[:50000] if response_body else None,
                response_json=response_json,
                timestamp=datetime.utcnow(),
                role_context=getattr(context, "_role", None),
            )
            
            if hasattr(context, "_interceptor") and context._interceptor:
                await context._interceptor.add_record(record)
            
            async with self._lock:
                self._request_queue.append(record)
                for callback in self._request_callbacks:
                    try:
                        callback(record)
                    except Exception:
                        pass
                        
        except Exception as e:
            logger.debug(f"Error capturing response: {e}")
    
    def _on_console(self, msg) -> None:
        """Handle console messages."""
        if msg.type in ("error", "warning"):
            self._console_errors.append({
                "type": msg.type,
                "text": msg.text,
                "timestamp": datetime.utcnow().isoformat(),
            })
    
    def _on_page_error(self, error) -> None:
        """Handle page errors."""
        self._network_failures.append({
            "error": str(error),
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def add_request_callback(self, callback: Callable[[RequestRecord], None]) -> None:
        """Add a callback for captured requests."""
        self._request_callbacks.append(callback)
    
    def get_request_queue(self) -> list[RequestRecord]:
        """Get all captured requests."""
        return self._request_queue.copy()
    
    def get_context_requests(self, context: BrowserContext) -> list[RequestRecord]:
        """Get requests captured for a specific context."""
        if hasattr(context, "_interceptor") and context._interceptor:
            return context._interceptor.get_records()
        return []
    
    def get_console_errors(self) -> list[dict]:
        """Get captured console errors."""
        return self._console_errors.copy()
    
    def get_network_failures(self) -> list[dict]:
        """Get captured network failures."""
        return self._network_failures.copy()


async def take_screenshot(page: Page, name: str, full_page: bool = True) -> str:
    """
    Take a screenshot of a page.
    
    Args:
        page: Playwright Page object
        name: Screenshot name (without extension)
        full_page: Whether to capture full page
        
    Returns:
        Path to saved screenshot
    """
    config = get_config()
    safe_name = safe_filename(name)
    path = config.get_output_path("recon", "screenshots", f"{safe_name}.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    
    await page.screenshot(path=str(path), full_page=full_page)
    logger.debug(f"Screenshot saved: {path}")
    return str(path)


async def dump_dom(page: Page, name: str) -> str:
    """
    Save the full DOM content of a page.
    
    Args:
        page: Playwright Page object
        name: Snapshot name (without extension)
        
    Returns:
        Path to saved DOM snapshot
    """
    config = get_config()
    safe_name = safe_filename(name)
    path = config.get_output_path("recon", "dom_snapshots", f"{safe_name}.html")
    path.parent.mkdir(parents=True, exist_ok=True)
    
    content = await page.content()
    atomic_write_text(path, content)
    logger.debug(f"DOM snapshot saved: {path}")
    return str(path)


async def get_page_actions(page: Page) -> list[dict]:
    """
    Extract all interactive elements from a page.
    
    Args:
        page: Playwright Page object
        
    Returns:
        List of action dictionaries
    """
    actions = await page.evaluate('''() => {
        const actions = [];
        
        // Buttons
        document.querySelectorAll('button, [role="button"], input[type="submit"], input[type="button"]').forEach(el => {
            actions.push({
                type: 'click',
                selector: el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.className ? '.' + el.className.split(' ').join('.') : ''),
                text: el.textContent?.trim() || el.value || '',
                visible: el.offsetParent !== null
            });
        });
        
        // Links
        document.querySelectorAll('a[href]').forEach(el => {
            actions.push({
                type: 'navigate',
                selector: 'a',
                text: el.textContent?.trim() || '',
                href: el.href,
                visible: el.offsetParent !== null
            });
        });
        
        // Forms
        document.querySelectorAll('form').forEach(form => {
            const fields = [];
            form.querySelectorAll('input, textarea, select').forEach(input => {
                fields.push(input.name || input.id || input.type);
            });
            actions.push({
                type: 'submit',
                selector: 'form' + (form.id ? '#' + form.id : ''),
                action: form.action,
                method: form.method,
                fields: fields
            });
        });
        
        // Clickable elements with onclick
        document.querySelectorAll('[onclick]').forEach(el => {
            if (!el.matches('button, a, input')) {
                actions.push({
                    type: 'click',
                    selector: el.tagName.toLowerCase(),
                    text: el.textContent?.trim().substring(0, 100) || '',
                    visible: el.offsetParent !== null
                });
            }
        });
        
        return actions;
    }''')
    
    return actions


async def wait_for_network_idle(page: Page, timeout: int = 5000) -> None:
    """Wait for network to be idle."""
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception as e:
        logger.debug(f"Network idle wait timed out or failed: {e}")


async def execute_js(page: Page, script: str) -> Any:
    """Execute JavaScript in page context."""
    return await page.evaluate(script)


async def get_local_storage(page: Page) -> dict:
    """Get all localStorage items."""
    return await page.evaluate('''() => {
        const items = {};
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            items[key] = localStorage.getItem(key);
        }
        return items;
    }''')


async def get_session_storage(page: Page) -> dict:
    """Get all sessionStorage items."""
    return await page.evaluate('''() => {
        const items = {};
        for (let i = 0; i < sessionStorage.length; i++) {
            const key = sessionStorage.key(i);
            items[key] = sessionStorage.getItem(key);
        }
        return items;
    }''')


async def get_cookies(context: BrowserContext) -> list[dict]:
    """Get all cookies from context."""
    return await context.cookies()


async def set_cookies(context: BrowserContext, cookies: list[dict]) -> None:
    """Set cookies in context."""
    await context.add_cookies(cookies)


@asynccontextmanager
async def browser_session(
    role: Optional[str] = None,
    proxy: Optional[str] = None,
):
    """
    Context manager for a browser session.
    
    Args:
        role: Role context for this session
        proxy: Proxy server to use
        
    Yields:
        Tuple of (BrowserContext, Page)
    """
    pool = get_browser_pool()
    context = await pool.get_browser_context(role=role, proxy=proxy)
    page = await context.new_page()
    
    try:
        yield context, page
    finally:
        await page.close()
        await context.close()


_browser_pool: Optional[BrowserPool] = None


def get_browser_pool() -> BrowserPool:
    """Get the global browser pool instance."""
    global _browser_pool
    if _browser_pool is None:
        _browser_pool = BrowserPool()
    return _browser_pool


async def cleanup_browser_pool() -> None:
    """Clean up the global browser pool."""
    global _browser_pool
    if _browser_pool:
        await _browser_pool.close()
        _browser_pool = None


if __name__ == "__main__":
    async def main():
        pool = BrowserPool()
        await pool.initialize()
        
        context = await pool.get_browser_context(role="test")
        page = await context.new_page()
        
        await page.goto("https://example.com")
        print(f"Page title: {await page.title()}")
        
        screenshot_path = await take_screenshot(page, "example_test")
        print(f"Screenshot: {screenshot_path}")
        
        dom_path = await dump_dom(page, "example_test")
        print(f"DOM: {dom_path}")
        
        actions = await get_page_actions(page)
        print(f"Actions found: {len(actions)}")
        
        requests = pool.get_context_requests(context)
        print(f"Requests captured: {len(requests)}")
        
        await page.close()
        await context.close()
        await pool.close()
    
    asyncio.run(main())
