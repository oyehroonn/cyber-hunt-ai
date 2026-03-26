"""
Tool 1 — crawl_target
Tool 2 — analyze_js_bundles

crawl_target: Deep web crawl using Playwright headless Chromium.
analyze_js_bundles: Extract hidden endpoints from JS bundles via regex + LinkFinder patterns.
"""

from __future__ import annotations

import asyncio
import re
import urllib.parse
from typing import Optional

import httpx
from loguru import logger

from cyberAI.llm.agent.state import RunState


# ---------------------------------------------------------------------------
# URL normalization
# ---------------------------------------------------------------------------

_ID_PATTERN = re.compile(r"/\d{1,10}(?=/|$)")
_UUID_PATTERN = re.compile(r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)


def _normalize_path(path: str) -> str:
    """Replace numeric IDs and UUIDs with placeholders."""
    path = _ID_PATTERN.sub("/{id}", path)
    path = _UUID_PATTERN.sub("/{uuid}", path)
    return path


def _is_api_url(url: str, base: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    base_parsed = urllib.parse.urlparse(base)
    return parsed.netloc == base_parsed.netloc or not parsed.netloc


def _extract_routes_from_requests(requests: list[dict], base: str) -> list[str]:
    routes = set()
    for req in requests:
        url = req.get("url", "")
        method = req.get("method", "GET")
        if not url or not _is_api_url(url, base):
            continue
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        if not path or path in ("/", ""):
            continue
        norm = _normalize_path(path)
        routes.add(f"{method} {norm}")
    return sorted(routes)


# ---------------------------------------------------------------------------
# crawl_target
# ---------------------------------------------------------------------------

async def crawl_target(
    target_url: str,
    session_name: Optional[str] = None,
    max_pages: int = 200,
    follow_js_redirects: bool = True,
    capture_network: bool = True,
    run_id: str = "",
    state: Optional[RunState] = None,
) -> dict:
    """
    Deep crawl using Playwright. Captures all XHR/fetch API calls.

    Returns:
    {
      "pages_crawled": 47,
      "routes_discovered": ["GET /api/Users", ...],
      "forms_found": [...],
      "js_bundles": ["https://target/main.js", ...],
      "cookies_set": {},
      "errors": []
    }
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("crawl_target: playwright not installed")
        return _crawl_fallback(target_url, session_name, state)

    base = target_url.rstrip("/")
    routes: set[str] = set()
    js_bundles: set[str] = set()
    forms_found: list[dict] = []
    errors: list[str] = []
    pages_crawled = 0
    visited: set[str] = set()
    to_visit = [base + "/", base + "/#/"]
    cookies_set: dict = {}

    # Get JWT for session if available
    jwt: Optional[str] = None
    if session_name and state:
        session_data = state.get_sessions().get(session_name, {})
        jwt = session_data.get("jwt")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent="Mozilla/5.0 (compatible; CyberHuntAI/2.0)",
                ignore_https_errors=True,
            )

            # Inject JWT as cookie/header if session provided
            if jwt:
                parsed = urllib.parse.urlparse(base)
                await ctx.add_cookies([{
                    "name": "token",
                    "value": jwt,
                    "domain": parsed.netloc,
                    "path": "/",
                }])

            # Intercept all network requests
            captured_requests: list[dict] = []

            page = await ctx.new_page()
            if jwt:
                await page.set_extra_http_headers({"Authorization": f"Bearer {jwt}"})

            async def on_request(req):
                if any(ext in req.url for ext in (".png", ".jpg", ".gif", ".ico", ".woff", ".css")):
                    return
                captured_requests.append({"url": req.url, "method": req.method})
                if req.url.endswith(".js") and _is_api_url(req.url, base):
                    js_bundles.add(req.url)

            page.on("request", on_request)

            while to_visit and pages_crawled < max_pages:
                url = to_visit.pop(0)
                if url in visited:
                    continue
                visited.add(url)
                try:
                    resp = await page.goto(url, wait_until="networkidle", timeout=15000)
                    pages_crawled += 1

                    # Extract links
                    hrefs = await page.evaluate("""
                        () => Array.from(document.querySelectorAll('a[href]'))
                             .map(a => a.href)
                             .filter(h => h.startsWith('http') || h.startsWith('/'))
                    """)
                    for href in hrefs:
                        full = href if href.startswith("http") else base + href
                        if _is_api_url(full, base) and full not in visited:
                            to_visit.append(full)

                    # Extract forms
                    page_forms = await page.evaluate("""
                        () => Array.from(document.querySelectorAll('form')).map(f => ({
                            action: f.action,
                            method: f.method || 'GET',
                            fields: Array.from(f.querySelectorAll('input,select,textarea'))
                                        .map(i => i.name || i.id || i.type).filter(Boolean)
                        }))
                    """)
                    forms_found.extend(page_forms)

                    # Get lazy-loaded resource URLs
                    resources = await page.evaluate("""
                        () => performance.getEntriesByType('resource')
                              .map(r => ({url: r.name, type: r.initiatorType}))
                    """)
                    for res in resources:
                        rurl = res.get("url", "")
                        if rurl.endswith(".js") and _is_api_url(rurl, base):
                            js_bundles.add(rurl)

                except Exception as e:
                    errors.append(f"crawl {url}: {str(e)[:200]}")

            # Post-crawl: collect all network-intercepted routes
            for req in captured_requests:
                url_str = req.get("url", "")
                if not _is_api_url(url_str, base):
                    continue
                parsed = urllib.parse.urlparse(url_str)
                path = _normalize_path(parsed.path)
                if path and path not in ("/", ""):
                    routes.add(f"{req['method']} {path}")

            # Collect current cookies
            all_cookies = await ctx.cookies()
            cookies_set = {c["name"]: c["value"][:20] + "..." for c in all_cookies if c.get("value")}

            await browser.close()

    except Exception as e:
        errors.append(f"playwright error: {str(e)[:300]}")
        logger.warning(f"crawl_target: playwright failed: {e}")

    routes_list = sorted(routes)

    # Write endpoints to state
    if state:
        for route in routes_list:
            parts = route.split(" ", 1)
            if len(parts) == 2:
                method, path = parts
                state.add_endpoint({
                    "path": path,
                    "methods": [method],
                    "discovery_source": "crawl",
                    "session": session_name or "unauthenticated",
                })
        state.write_log("recon", "INFO", "crawl_target",
                        f"Crawled {pages_crawled} pages, found {len(routes_list)} routes, "
                        f"{len(js_bundles)} JS bundles")

    return {
        "pages_crawled": pages_crawled,
        "routes_discovered": routes_list,
        "forms_found": forms_found[:50],
        "js_bundles": list(js_bundles),
        "cookies_set": cookies_set,
        "errors": errors[:10],
    }


def _crawl_fallback(target_url: str, session_name: Optional[str], state: Optional[RunState]) -> dict:
    """Minimal fallback when Playwright is not available."""
    logger.info("crawl_target: using httpx fallback (no Playwright)")
    return {
        "pages_crawled": 0,
        "routes_discovered": [],
        "forms_found": [],
        "js_bundles": [],
        "cookies_set": {},
        "errors": ["playwright not installed; install with: pip install playwright && playwright install chromium"],
    }


# ---------------------------------------------------------------------------
# analyze_js_bundles
# ---------------------------------------------------------------------------

# Regex patterns for endpoint extraction
_ENDPOINT_PATTERNS = [
    re.compile(r'["\']/(api|rest|graphql|admin|internal|v\d)[^"\']{0,150}["\']'),
    re.compile(r'["\']["\']/(api|rest)[^"\']{0,100}["\']'),
    re.compile(r'(?:path|route|url|endpoint)\s*[:=]\s*["\']([^"\']{3,100})["\']'),
    re.compile(r'this\.\w+\s*\+\s*["\']/(api|rest)[^"\']{0,80}["\']'),
]

_ROUTE_PATTERN = re.compile(r'"(?:path|route)"\s*:\s*"([^"]+)"')
_SECRET_PATTERN = re.compile(r'(?:password|secret|key|token|auth|apikey|api_key)[=:\s]+["\']([^"\']{8,80})["\']', re.IGNORECASE)
_ROLE_PATTERN = re.compile(r'role[s]?\s*[=:]\s*[\[{]?\s*["\'](\w+)["\']', re.IGNORECASE)
_SOURCEMAP_PATTERN = re.compile(r'//# sourceMappingURL=', re.IGNORECASE)


async def analyze_js_bundles(
    bundle_urls: list[str],
    target_origin: str,
    run_id: str = "",
    state: Optional[RunState] = None,
) -> dict:
    """
    Download JS bundles and extract hidden endpoints via regex analysis.

    Returns:
    {
      "new_endpoints": [...],
      "hidden_routes": [...],
      "role_constants": [...],
      "potential_secrets": [...],
      "graphql_schema_hints": [...],
      "source_maps_exposed": bool
    }
    """
    base = target_origin.rstrip("/")
    new_endpoints: set[str] = set()
    hidden_routes: set[str] = set()
    role_constants: set[str] = set()
    potential_secrets: list[str] = []
    graphql_hints: list[str] = []
    source_maps_exposed = False

    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        for bundle_url in bundle_urls[:20]:  # cap at 20 bundles
            # Resolve relative URLs
            if bundle_url.startswith("/"):
                bundle_url = base + bundle_url

            try:
                r = await client.get(bundle_url)
                if r.status_code != 200:
                    continue
                content = r.text
            except Exception as e:
                logger.debug(f"analyze_js: failed to fetch {bundle_url}: {e}")
                continue

            # Source map detection
            if _SOURCEMAP_PATTERN.search(content):
                source_maps_exposed = True

            # Endpoint extraction
            for pattern in _ENDPOINT_PATTERNS:
                for m in pattern.finditer(content):
                    raw = m.group(0).strip("'\"")
                    # Clean up
                    raw = raw.lstrip('"\'').rstrip('"\'')
                    if raw.startswith("/") and len(raw) > 2:
                        norm = _normalize_path(raw.split("?")[0])
                        new_endpoints.add(norm)

            # Route patterns from Angular/React routers
            for m in _ROUTE_PATTERN.finditer(content):
                path = m.group(1)
                if path.startswith("/") or path.startswith("#/"):
                    path = path.lstrip("#")
                    hidden_routes.add(path)

            # Role constants
            for m in _ROLE_PATTERN.finditer(content):
                role = m.group(1)
                if len(role) < 30:
                    role_constants.add(role)

            # Potential secrets (flagged but not logged in full)
            for m in _SECRET_PATTERN.finditer(content):
                val = m.group(1)
                if len(val) > 8 and val not in ("undefined", "null", "true", "false", "string"):
                    masked = val[:4] + "..." + val[-2:]
                    potential_secrets.append(masked)

            # GraphQL hints
            gql_matches = re.findall(r'(query\s+\w+|mutation\s+\w+|subscription\s+\w+)\s*\{', content)
            graphql_hints.extend(gql_matches[:10])

            logger.debug(f"analyze_js: {bundle_url} → {len(new_endpoints)} endpoints found")

    endpoints_list = sorted(new_endpoints)
    routes_list = sorted(hidden_routes)

    # Write to state
    if state:
        for ep in endpoints_list:
            state.add_endpoint({
                "path": ep,
                "methods": ["GET"],
                "discovery_source": "js_analysis",
            })
        state.write_log("recon", "INFO", "analyze_js_bundles",
                        f"Analyzed {len(bundle_urls)} bundles: "
                        f"{len(endpoints_list)} endpoints, {len(routes_list)} routes found")

    return {
        "new_endpoints": endpoints_list,
        "hidden_routes": routes_list,
        "role_constants": sorted(role_constants),
        "potential_secrets": list(set(potential_secrets))[:20],
        "graphql_schema_hints": list(set(graphql_hints))[:20],
        "source_maps_exposed": source_maps_exposed,
        "bundles_analyzed": len(bundle_urls),
    }
