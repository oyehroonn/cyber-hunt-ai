"""
Step 2: Network Intelligence - Request interception and endpoint classification.
Captures all network requests, classifies endpoints, and extracts metadata.
"""

import asyncio
import re
from datetime import datetime
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import (
    Endpoint,
    EndpointClassification,
    FieldSchema,
    HttpMethod,
    RequestRecord,
    SensitivityLabel,
)
from cyberAI.utils.browser import get_browser_pool
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    classify_endpoint,
    decode_jwt_payload,
    extract_ids_from_text,
    extract_tenant_identifiers,
    generate_run_id,
    parse_rate_limit_headers,
)


class NetworkIntelligence:
    """
    Intercepts and analyzes network requests during browsing.
    Classifies endpoints and extracts security-relevant metadata.
    """
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._requests: list[RequestRecord] = []
        self._endpoints: dict[str, Endpoint] = {}
        self._extracted_ids: dict[str, list[str]] = {}
        self._tenant_identifiers: dict[str, str] = {}
        self._role_info: dict[str, Any] = {}
        self._feature_flags: dict[str, Any] = {}
        self._rate_limit_info: dict[str, dict] = {}
        self._error_fingerprints: dict[str, list[str]] = {}
    
    def _make_endpoint_key(self, method: str, url: str) -> str:
        """Create a unique key for endpoint deduplication."""
        parsed = urlparse(url)
        path = re.sub(r'/[0-9a-f-]{36}', '/{uuid}', parsed.path)
        path = re.sub(r'/\d+', '/{id}', path)
        return f"{method}:{parsed.netloc}{path}"
    
    def _classify_sensitivity(self, url: str, response_body: Optional[str]) -> SensitivityLabel:
        """Classify the sensitivity level of an endpoint."""
        url_lower = url.lower()
        
        high_patterns = [
            '/admin', '/billing', '/payment', '/credential', '/password',
            '/secret', '/token', '/session', '/user/me', '/profile',
            '/account', '/auth', '/key', '/api-key'
        ]
        if any(p in url_lower for p in high_patterns):
            return SensitivityLabel.HIGH
        
        medium_patterns = [
            '/settings', '/config', '/preferences', '/export', '/import',
            '/upload', '/download', '/invite', '/share', '/audit'
        ]
        if any(p in url_lower for p in medium_patterns):
            return SensitivityLabel.MEDIUM
        
        if response_body:
            sensitive_fields = [
                'email', 'phone', 'address', 'ssn', 'credit_card',
                'password', 'secret', 'token', 'api_key'
            ]
            body_lower = response_body.lower()
            if any(f in body_lower for f in sensitive_fields):
                return SensitivityLabel.MEDIUM
        
        return SensitivityLabel.LOW
    
    def _infer_schema(self, data: Any, prefix: str = "") -> list[FieldSchema]:
        """Infer field schemas from response/request data."""
        schemas = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                field_path = f"{prefix}.{key}" if prefix else key
                
                if value is None:
                    field_type = "null"
                elif isinstance(value, bool):
                    field_type = "boolean"
                elif isinstance(value, int):
                    field_type = "integer"
                elif isinstance(value, float):
                    field_type = "number"
                elif isinstance(value, str):
                    field_type = "string"
                elif isinstance(value, list):
                    field_type = "array"
                elif isinstance(value, dict):
                    field_type = "object"
                    schemas.extend(self._infer_schema(value, field_path))
                    continue
                else:
                    field_type = "unknown"
                
                is_sensitive = any(
                    s in key.lower()
                    for s in ['password', 'secret', 'token', 'key', 'credential', 'ssn', 'credit']
                )
                
                schemas.append(FieldSchema(
                    name=field_path,
                    field_type=field_type,
                    is_sensitive=is_sensitive,
                ))
                
        elif isinstance(data, list) and data:
            if isinstance(data[0], dict):
                schemas.extend(self._infer_schema(data[0], f"{prefix}[]"))
        
        return schemas
    
    def _extract_jwt_info(self, headers: dict) -> Optional[dict]:
        """Extract information from JWT tokens in headers."""
        auth_header = headers.get("Authorization", headers.get("authorization", ""))
        
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = decode_jwt_payload(token)
            if payload:
                return {
                    "roles": payload.get("roles", payload.get("role", [])),
                    "permissions": payload.get("permissions", payload.get("scope", [])),
                    "tenant_id": payload.get("tenant_id", payload.get("org_id")),
                    "user_id": payload.get("sub", payload.get("user_id")),
                    "exp": payload.get("exp"),
                }
        
        return None
    
    def _extract_feature_flags(self, response_json: Optional[dict]) -> dict[str, Any]:
        """Extract feature flags from response data."""
        flags = {}
        
        if not response_json:
            return flags
        
        def extract_flags(data: Any, prefix: str = "") -> None:
            if isinstance(data, dict):
                for key, value in data.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    
                    flag_patterns = ['flag', 'feature', 'enable', 'disable', 'toggle', 'beta', 'experiment']
                    if any(p in key.lower() for p in flag_patterns):
                        if isinstance(value, bool):
                            flags[full_key] = value
                        elif isinstance(value, dict):
                            flags[full_key] = value
                    
                    if isinstance(value, dict):
                        extract_flags(value, full_key)
        
        extract_flags(response_json)
        return flags
    
    def process_request(
        self,
        record: RequestRecord,
        role_context: Optional[str] = None,
    ) -> Endpoint:
        """
        Process a captured request and extract intelligence.
        
        Args:
            record: The captured RequestRecord
            role_context: Role context for this request
            
        Returns:
            Endpoint object for this request
        """
        endpoint_key = self._make_endpoint_key(record.method.value, record.url)
        
        if endpoint_key in self._endpoints:
            endpoint = self._endpoints[endpoint_key]
            if role_context and role_context not in endpoint.role_access:
                endpoint.role_access[role_context] = record.response_status < 400
            return endpoint
        
        classification = EndpointClassification(
            classify_endpoint(record.method.value, record.url)
        )
        
        sensitivity = self._classify_sensitivity(
            record.url, record.response_body
        )
        
        body_schema = []
        if record.body_json:
            body_schema = self._infer_schema(record.body_json)
        
        response_schema = []
        if record.response_json:
            response_schema = self._infer_schema(record.response_json)
        
        parsed = urlparse(record.url)
        params = {}
        for key, values in parse_qs(parsed.query).items():
            params[key] = FieldSchema(
                name=key,
                field_type="string",
                enum_values=values if len(values) > 1 else [],
            )
        
        jwt_info = self._extract_jwt_info(record.headers)
        auth_context = None
        if jwt_info:
            auth_context = "bearer"
            if role_context:
                self._role_info[role_context] = jwt_info
        elif "cookie" in record.headers.get("Cookie", "").lower() or record.cookies:
            auth_context = "session"
        
        rate_info = parse_rate_limit_headers(record.response_headers)
        if rate_info:
            self._rate_limit_info[endpoint_key] = rate_info
        
        ids = extract_ids_from_text(record.url)
        if record.response_body:
            body_ids = extract_ids_from_text(record.response_body)
            for id_type, values in body_ids.items():
                if id_type not in self._extracted_ids:
                    self._extracted_ids[id_type] = []
                self._extracted_ids[id_type].extend(values)
        
        tenant_ids = extract_tenant_identifiers(
            record.headers, record.body, record.url
        )
        self._tenant_identifiers.update(tenant_ids)
        
        if record.response_json:
            flags = self._extract_feature_flags(record.response_json)
            self._feature_flags.update(flags)
        
        if record.response_status >= 400:
            error_fp = f"{record.response_status}:{record.response_body[:100] if record.response_body else ''}"
            if endpoint_key not in self._error_fingerprints:
                self._error_fingerprints[endpoint_key] = []
            self._error_fingerprints[endpoint_key].append(error_fp)
        
        endpoint = Endpoint(
            method=record.method,
            url=record.url,
            path_pattern=self._make_endpoint_key(record.method.value, record.url).split(":", 1)[1],
            params=params,
            headers={k: v for k, v in record.headers.items() if k.lower() not in ['cookie', 'authorization']},
            body_schema=body_schema,
            response_schema=response_schema,
            auth_context=auth_context,
            sensitivity_label=sensitivity,
            classification=classification,
            rate_limited=bool(rate_info),
            rate_limit_info=rate_info,
            role_access={role_context: record.response_status < 400} if role_context else {},
        )
        
        self._endpoints[endpoint_key] = endpoint
        self._requests.append(record)
        
        return endpoint
    
    def process_requests_batch(
        self,
        records: list[RequestRecord],
        role_context: Optional[str] = None,
    ) -> list[Endpoint]:
        """Process a batch of request records."""
        endpoints = []
        for record in records:
            endpoint = self.process_request(record, role_context)
            endpoints.append(endpoint)
        return endpoints
    
    async def attach_to_context(self, context, role: Optional[str] = None) -> None:
        """
        Attach request listener to a browser context.
        
        Args:
            context: Playwright BrowserContext
            role: Role context for requests from this context
        """
        async def on_response(response):
            try:
                request = response.request
                
                content_type = response.headers.get("content-type", "")
                if not any(t in content_type for t in ["json", "text", "html", "xml"]):
                    return
                
                body = None
                body_json = None
                if request.method in ("POST", "PUT", "PATCH"):
                    try:
                        body = request.post_data
                        if body:
                            import json
                            try:
                                body_json = json.loads(body)
                            except:
                                pass
                    except:
                        pass
                
                response_body = None
                response_json = None
                try:
                    response_body = await response.text()
                    if "application/json" in content_type:
                        import json
                        try:
                            response_json = json.loads(response_body)
                        except:
                            pass
                except:
                    pass
                
                record = RequestRecord(
                    method=HttpMethod(request.method),
                    url=request.url,
                    headers=dict(request.headers),
                    body=body,
                    body_json=body_json,
                    response_status=response.status,
                    response_headers=dict(response.headers),
                    response_body=response_body[:50000] if response_body else None,
                    response_json=response_json,
                    timestamp=datetime.utcnow(),
                    role_context=role,
                )
                
                self.process_request(record, role)
                
            except Exception as e:
                logger.debug(f"Error capturing response: {e}")
        
        context.on("response", on_response)
    
    def get_endpoints(self) -> list[Endpoint]:
        """Get all discovered endpoints."""
        return list(self._endpoints.values())
    
    def get_requests(self) -> list[RequestRecord]:
        """Get all captured requests."""
        return self._requests

    def add_requests(
        self,
        records: list[RequestRecord],
        role_context: Optional[str] = None,
    ) -> None:
        """Append request records and update endpoints (e.g. from form mining, API spec)."""
        for r in records:
            self._requests.append(r)
            self.process_request(r, role_context)

    def add_endpoint(self, endpoint: Endpoint) -> None:
        """Register an endpoint (e.g. from API spec) without a request record."""
        key = self._make_endpoint_key(endpoint.method.value, endpoint.url)
        self._endpoints[key] = endpoint

    def get_extracted_ids(self) -> dict[str, list[str]]:
        """Get all extracted IDs."""
        return {k: list(set(v)) for k, v in self._extracted_ids.items()}
    
    def get_tenant_identifiers(self) -> dict[str, str]:
        """Get all tenant identifiers."""
        return self._tenant_identifiers
    
    def get_feature_flags(self) -> dict[str, Any]:
        """Get all extracted feature flags."""
        return self._feature_flags
    
    def get_role_info(self) -> dict[str, Any]:
        """Get role information from JWT tokens."""
        return self._role_info
    
    def save_intelligence(self, warc_writer=None) -> tuple[str, str]:
        """
        Save all captured intelligence to files.
        If warc_writer is provided (ASRTS), writes each request/response to WARC and sets warc_ref.

        Returns:
            Tuple of (requests_path, endpoints_path)
        """
        if warc_writer is not None:
            for i, r in enumerate(self._requests):
                try:
                    req_body = r.body.encode("utf-8", errors="replace") if r.body else None
                    resp_body = r.response_body.encode("utf-8", errors="replace") if isinstance(r.response_body, str) else (r.response_body if r.response_body else None)
                    ref = warc_writer.write_record(
                        method=r.method.value,
                        url=r.url,
                        request_headers=r.headers,
                        request_body=req_body,
                        response_status=r.response_status,
                        response_headers=r.response_headers,
                        response_body=resp_body,
                    )
                    if ref:
                        self._requests[i] = r.model_copy(update={"warc_ref": ref})
                except Exception as e:
                    logger.debug(f"WARC write for request {r.url}: {e}")
        requests_path = self.config.get_output_path(
            "recon", "requests", "all_requests.json"
        )
        requests_data = add_meta_to_output(
            {"requests": [r.model_dump() for r in self._requests]},
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        atomic_write_json(requests_path, requests_data)
        
        endpoints_path = self.config.get_output_path(
            "recon", "intelligence", "endpoints.json"
        )
        endpoints_data = add_meta_to_output(
            {
                "endpoints": [e.model_dump() for e in self._endpoints.values()],
                "extracted_ids": self.get_extracted_ids(),
                "tenant_identifiers": self._tenant_identifiers,
                "feature_flags": self._feature_flags,
                "role_info": self._role_info,
                "rate_limit_info": self._rate_limit_info,
                "error_fingerprints": self._error_fingerprints,
            },
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        atomic_write_json(endpoints_path, endpoints_data)
        
        logger.info(f"Saved {len(self._requests)} requests and {len(self._endpoints)} endpoints")
        
        return str(requests_path), str(endpoints_path)


async def run_network_intelligence(
    browser_pool=None,
    role: Optional[str] = None,
    run_id: Optional[str] = None,
) -> NetworkIntelligence:
    """
    Create and configure network intelligence capture.
    
    Args:
        browser_pool: Optional browser pool to attach to
        role: Role context
        run_id: Run ID
        
    Returns:
        Configured NetworkIntelligence instance
    """
    intel = NetworkIntelligence(run_id=run_id)
    
    if browser_pool:
        context = await browser_pool.get_browser_context(role=role)
        await intel.attach_to_context(context, role)
    
    return intel


if __name__ == "__main__":
    async def main():
        intel = NetworkIntelligence()
        
        record = RequestRecord(
            method=HttpMethod.GET,
            url="https://api.example.com/users/123",
            headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"},
            response_status=200,
            response_json={"id": 123, "name": "Test User", "email": "test@example.com"},
        )
        
        endpoint = intel.process_request(record, role_context="user")
        
        print(f"Endpoint: {endpoint.classification}")
        print(f"Sensitivity: {endpoint.sensitivity_label}")
        print(f"Auth context: {endpoint.auth_context}")
        
        intel.save_intelligence()
    
    asyncio.run(main())
