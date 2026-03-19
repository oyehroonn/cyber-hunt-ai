"""
Async HTTP client with proxy rotation, UA rotation, and request recording.
"""

import asyncio
import json
import hashlib
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import httpx
from fake_useragent import UserAgent
from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import HttpMethod, RequestRecord
from cyberAI.utils.helpers import parse_rate_limit_headers
from cyberAI.utils.proxy_manager import get_proxy_manager

try:
    from cyberAI.governance.scope import get_scope_validator
    from cyberAI.governance.rate_limiter import get_global_rate_limiter
    from urllib.parse import urlparse
except ImportError:
    get_scope_validator = None
    get_global_rate_limiter = None


class AsyncHTTPClient:
    """
    Async HTTP client wrapper with proxy rotation, UA rotation, and request recording.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        use_proxy: Optional[bool] = None,
        rotate_ua: Optional[bool] = None,
    ):
        """
        Initialize the HTTP client.
        
        Args:
            base_url: Base URL for relative requests
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            use_proxy: Override proxy setting
            rotate_ua: Override UA rotation setting
        """
        config = get_config()
        self.base_url = base_url or config.target_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_proxy = use_proxy if use_proxy is not None else config.proxy_enabled
        self.rotate_ua = rotate_ua if rotate_ua is not None else config.user_agent_rotation
        
        self._ua = UserAgent()
        self._client: Optional[httpx.AsyncClient] = None
        self._cookies: dict[str, str] = {}
        self._default_headers: dict[str, str] = {}
        self._request_delay_ms = config.request_delay_ms
        self._last_request_time = 0.0
        self._request_history: list[RequestRecord] = []
        self._lock = asyncio.Lock()
    
    def _get_user_agent(self) -> str:
        """Get a user agent string."""
        if self.rotate_ua:
            try:
                return self._ua.random
            except Exception:
                pass
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the httpx client."""
        if self._client is None:
            proxy = None
            if self.use_proxy:
                proxy_manager = get_proxy_manager()
                proxy_str = await proxy_manager.get_next_proxy()
                if proxy_str:
                    proxy = f"http://{proxy_str}"
            
            client_kw: dict[str, Any] = {
                "timeout": httpx.Timeout(self.timeout),
                "follow_redirects": True,
                "limits": httpx.Limits(max_connections=100, max_keepalive_connections=20),
                # Disable SSL verification to match browser's ignore_https_errors=True
                # This prevents SSL cert errors when testing against self-signed/expired certs
                "verify": False,
            }
            if proxy:
                client_kw["proxy"] = proxy
            self._client = httpx.AsyncClient(**client_kw)
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def set_default_headers(self, headers: dict[str, str]) -> None:
        """Set default headers for all requests."""
        self._default_headers.update(headers)
    
    def set_auth_token(self, token: str, header_name: str = "Authorization", prefix: str = "Bearer ") -> None:
        """Set an authentication token."""
        self._default_headers[header_name] = f"{prefix}{token}"
    
    def set_cookies(self, cookies: dict[str, str]) -> None:
        """Set cookies for all requests."""
        self._cookies.update(cookies)
    
    def clear_cookies(self) -> None:
        """Clear all cookies."""
        self._cookies.clear()
    
    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        if self._request_delay_ms > 0:
            now = asyncio.get_event_loop().time() * 1000
            elapsed = now - self._last_request_time
            if elapsed < self._request_delay_ms:
                await asyncio.sleep((self._request_delay_ms - elapsed) / 1000)
            self._last_request_time = asyncio.get_event_loop().time() * 1000
    
    def _build_headers(self, extra_headers: Optional[dict] = None) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "User-Agent": self._get_user_agent(),
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        headers.update(self._default_headers)
        if extra_headers:
            headers.update(extra_headers)
        return headers
    
    async def request(
        self,
        method: str,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        json_data: Optional[dict] = None,
        data: Optional[dict] = None,
        content: Optional[bytes] = None,
        role_context: Optional[str] = None,
        state_context: Optional[str] = None,
        record: bool = True,
        follow_redirects: Optional[bool] = None,
    ) -> tuple[httpx.Response, Optional[RequestRecord]]:
        """
        Make an HTTP request.
        
        Args:
            method: HTTP method
            url: URL (absolute or relative to base_url)
            params: Query parameters
            headers: Additional headers
            json_data: JSON body data
            data: Form data
            content: Raw content bytes
            role_context: Role context for recording
            state_context: State context for recording
            record: Whether to record the request
            
        Returns:
            Tuple of (response, request_record)
        """
        await self._apply_rate_limit()
        
        if not url.startswith(("http://", "https://")):
            url = urljoin(self.base_url, url)
        
        # ASRTS: scope check before any request
        if get_scope_validator is not None:
            validator = get_scope_validator()
            if validator is not None:
                allowed, reason = validator.is_in_scope(url, method.upper())
                if not allowed:
                    logger.warning(f"Scope check denied request: {url} reason={reason}")
                    # Return a synthetic "blocked" response so callers don't get None
                    class BlockedResponse:
                        def __init__(self, u: str):
                            self.status_code = 403
                            self.url = u
                            self.headers = {}
                            self.history = []
                            self.cookies = {}
                        def json(self): return {}
                        @property
                        def text(self): return ""
                        @property
                        def content_type(self): return "application/octet-stream"
                    return BlockedResponse(url), None
        
        # ASRTS: per-host rate limit when engagement config is loaded
        if get_global_rate_limiter is not None and urlparse is not None:
            limiter = get_global_rate_limiter()
            if limiter is not None:
                try:
                    parsed = urlparse(url)
                    await limiter.acquire(parsed.netloc or "unknown")
                except Exception as e:
                    logger.debug(f"Rate limiter acquire: {e}")
        
        request_headers = self._build_headers(headers)
        
        client = await self._get_client()
        
        start_time = datetime.utcnow()
        response = None
        
        for attempt in range(self.max_retries):
            try:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    headers=request_headers,
                    json=json_data,
                    data=data,
                    content=content,
                    cookies=self._cookies,
                    follow_redirects=follow_redirects if follow_redirects is not None else True,
                )
                break
            except httpx.TimeoutException:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Request timeout, retrying ({attempt + 1}/{self.max_retries})")
                await asyncio.sleep(1 * (attempt + 1))
            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"HTTP error: {e}, retrying ({attempt + 1}/{self.max_retries})")
                await asyncio.sleep(1 * (attempt + 1))
        
        request_record = None
        if record and response:
            request_record = await self.record_request(
                method=method,
                url=url,
                headers=request_headers,
                body=json.dumps(json_data) if json_data else (str(data) if data else None),
                body_json=json_data,
                response=response,
                role_context=role_context,
                state_context=state_context,
                start_time=start_time,
            )
        
        return response, request_record
    
    async def get(self, url: str, **kwargs) -> tuple[httpx.Response, Optional[RequestRecord]]:
        """Make a GET request."""
        return await self.request("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> tuple[httpx.Response, Optional[RequestRecord]]:
        """Make a POST request."""
        return await self.request("POST", url, **kwargs)
    
    async def put(self, url: str, **kwargs) -> tuple[httpx.Response, Optional[RequestRecord]]:
        """Make a PUT request."""
        return await self.request("PUT", url, **kwargs)
    
    async def patch(self, url: str, **kwargs) -> tuple[httpx.Response, Optional[RequestRecord]]:
        """Make a PATCH request."""
        return await self.request("PATCH", url, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> tuple[httpx.Response, Optional[RequestRecord]]:
        """Make a DELETE request."""
        return await self.request("DELETE", url, **kwargs)
    
    async def record_request(
        self,
        method: str,
        url: str,
        headers: dict,
        body: Optional[str],
        body_json: Optional[dict],
        response: httpx.Response,
        role_context: Optional[str] = None,
        state_context: Optional[str] = None,
        start_time: Optional[datetime] = None,
    ) -> RequestRecord:
        """
        Create a request record from request/response data.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            body: Request body string
            body_json: Request body as JSON
            response: httpx Response object
            role_context: Role context
            state_context: State context
            start_time: Request start time
            
        Returns:
            RequestRecord object
        """
        response_body = None
        response_json = None
        content_type = response.headers.get("content-type", "")
        body_preview = None
        body_hash = None
        redirect_chain: list[dict[str, Any]] = []

        try:
            for h in response.history:
                redirect_chain.append(
                    {
                        "status_code": getattr(h, "status_code", None),
                        "url": str(getattr(h, "url", "")),
                        "location": h.headers.get("location"),
                    }
                )
        except Exception:
            pass
        
        try:
            if "application/json" in content_type:
                response_json = response.json()
                response_body = response.text
            elif "text/" in content_type:
                response_body = response.text
        except Exception:
            try:
                response_body = response.text[:50000]
            except Exception:
                pass

        try:
            if response_body:
                body_preview = response_body[:2000]
                body_hash = hashlib.sha256(response_body.encode("utf-8", errors="ignore")).hexdigest()
        except Exception:
            pass
        
        duration_ms = None
        if start_time:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        record = RequestRecord(
            method=HttpMethod(method.upper()),
            url=url,
            final_url=str(getattr(response, "url", url)) if response is not None else url,
            redirect_chain=redirect_chain,
            headers=headers,
            cookies=dict(response.cookies),
            body=body,
            body_json=body_json,
            response_status=response.status_code,
            response_content_type=content_type,
            response_headers=dict(response.headers),
            response_body=response_body,
            response_json=response_json,
            response_body_hash=body_hash,
            response_body_preview=body_preview,
            timestamp=start_time or datetime.utcnow(),
            role_context=role_context,
            state_context=state_context,
            duration_ms=duration_ms,
        )
        
        async with self._lock:
            self._request_history.append(record)
        
        return record
    
    async def replay_request(
        self,
        record: RequestRecord,
        modifications: Optional[dict] = None,
        role_context: Optional[str] = None,
    ) -> tuple[httpx.Response, RequestRecord]:
        """
        Replay a recorded request with optional modifications.
        
        Args:
            record: RequestRecord to replay
            modifications: Dict of modifications to apply
                - headers: dict to merge
                - params: dict to merge
                - body_json: dict to replace body
                - url: str to replace URL
            role_context: New role context
            
        Returns:
            Tuple of (response, new_request_record)
        """
        modifications = modifications or {}
        
        url = modifications.get("url", record.url)
        headers = {**record.headers, **modifications.get("headers", {})}
        body_json = modifications.get("body_json", record.body_json)
        
        return await self.request(
            method=record.method.value,
            url=url,
            headers=headers,
            json_data=body_json,
            role_context=role_context or record.role_context,
            state_context=record.state_context,
        )
    
    def get_request_history(self) -> list[RequestRecord]:
        """Get all recorded requests."""
        return self._request_history.copy()
    
    def clear_history(self) -> None:
        """Clear request history."""
        self._request_history.clear()
    
    def get_rate_limit_info(self, response: httpx.Response) -> Optional[dict]:
        """Extract rate limit information from response headers."""
        return parse_rate_limit_headers(dict(response.headers))


class HTTPClientPool:
    """
    Pool of HTTP clients for parallel requests.
    """
    
    def __init__(self, pool_size: int = 10):
        self.pool_size = pool_size
        self._clients: list[AsyncHTTPClient] = []
        self._client_index = 0
        self._lock = asyncio.Lock()
    
    async def get_client(self) -> AsyncHTTPClient:
        """Get a client from the pool."""
        async with self._lock:
            if len(self._clients) < self.pool_size:
                client = AsyncHTTPClient()
                self._clients.append(client)
                return client
            
            client = self._clients[self._client_index % len(self._clients)]
            self._client_index += 1
            return client
    
    async def close_all(self) -> None:
        """Close all clients in the pool."""
        for client in self._clients:
            await client.close()
        self._clients.clear()


_http_client: Optional[AsyncHTTPClient] = None


def get_http_client() -> AsyncHTTPClient:
    """Get the global HTTP client instance."""
    global _http_client
    if _http_client is None:
        _http_client = AsyncHTTPClient()
    return _http_client


async def cleanup_http_client() -> None:
    """Clean up the global HTTP client."""
    global _http_client
    if _http_client:
        await _http_client.close()
        _http_client = None


if __name__ == "__main__":
    async def main():
        client = AsyncHTTPClient(base_url="https://httpbin.org")
        
        print("Testing GET request...")
        response, record = await client.get("/get", params={"test": "value"})
        print(f"Status: {response.status_code}")
        print(f"Record URL: {record.url if record else 'N/A'}")
        
        print("\nTesting POST request...")
        response, record = await client.post(
            "/post",
            json_data={"key": "value"},
        )
        print(f"Status: {response.status_code}")
        
        print("\nTesting replay...")
        if record:
            response2, record2 = await client.replay_request(
                record,
                modifications={"body_json": {"key": "modified_value"}}
            )
            print(f"Replay status: {response2.status_code}")
        
        print(f"\nTotal requests recorded: {len(client.get_request_history())}")
        
        await client.close()
    
    asyncio.run(main())
