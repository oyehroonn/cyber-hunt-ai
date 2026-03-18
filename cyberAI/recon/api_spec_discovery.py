"""
ASRTS §3.3: API spec discovery (OpenAPI/Swagger).
Fetch /openapi.json, /swagger.json, /api-docs; parse; extract endpoints and params; add to intelligence.
"""

import json
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import Endpoint, EndpointClassification, FieldSchema, HttpMethod, SensitivityLabel
from cyberAI.recon.network_intelligence import NetworkIntelligence
from cyberAI.utils.helpers import add_meta_to_output, atomic_write_json

COMMON_SPEC_PATHS = [
    "/openapi.json",
    "/openapi.yaml",
    "/swagger.json",
    "/swagger.yaml",
    "/api-docs",
    "/v1/api-docs",
    "/v2/api-docs",
    "/v3/api-docs",
    "/swagger/v1/api-docs",
    "/api/openapi.json",
    "/api/swagger.json",
]

METHOD_MAP = {
    "get": HttpMethod.GET,
    "post": HttpMethod.POST,
    "put": HttpMethod.PUT,
    "patch": HttpMethod.PATCH,
    "delete": HttpMethod.DELETE,
    "head": HttpMethod.HEAD,
    "options": HttpMethod.OPTIONS,
}


def _param_to_schema(param: dict) -> FieldSchema:
    """Convert OpenAPI/Swagger parameter to FieldSchema."""
    name = param.get("name", "")
    loc = param.get("in", "query")
    schema = param.get("schema") or param
    t = schema.get("type", "string")
    return FieldSchema(
        name=name,
        field_type=t,
        required=param.get("required", False),
        enum_values=schema.get("enum", []),
    )


def _classify_path(path: str) -> EndpointClassification:
    """Heuristic classification from path."""
    p = path.lower()
    if "admin" in p or "delete" in p:
        return EndpointClassification.ADMIN
    if "auth" in p or "login" in p or "token" in p:
        return EndpointClassification.AUTH
    if "user" in p or "profile" in p:
        return EndpointClassification.READ
    if "create" in p or "post" in p or "add" in p:
        return EndpointClassification.CREATE
    if "update" in p or "patch" in p or "edit" in p:
        return EndpointClassification.UPDATE
    if "billing" in p or "payment" in p:
        return EndpointClassification.BILLING
    return EndpointClassification.OTHER


def _sensitivity_from_path(path: str) -> SensitivityLabel:
    p = path.lower()
    if any(x in p for x in ["admin", "credential", "password", "secret", "token", "key"]):
        return SensitivityLabel.HIGH
    if any(x in p for x in ["user", "profile", "settings", "export", "billing"]):
        return SensitivityLabel.MEDIUM
    return SensitivityLabel.LOW


def _parse_openapi_spec(spec: dict, base_url: str) -> list[Endpoint]:
    """Parse OpenAPI 3.x or Swagger 2.x spec into Endpoint list."""
    endpoints = []
    openapi_version = spec.get("openapi") or spec.get("swagger")
    if not openapi_version:
        return endpoints

    servers = spec.get("servers")
    if servers and servers[0].get("url"):
        base_url = servers[0]["url"].rstrip("/")
    else:
        host = spec.get("host", "")
        base_path = spec.get("basePath", "")
        scheme = spec.get("schemes", ["https"])[0]
        if host:
            base_url = f"{scheme}://{host}{base_path}".rstrip("/")

    paths = spec.get("paths") or {}
    for path_template, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method in ["get", "post", "put", "patch", "delete", "head", "options"]:
            op = path_item.get(method)
            if not op:
                continue
            http_method = METHOD_MAP.get(method, HttpMethod.GET)
            url = urljoin(base_url + "/", path_template.lstrip("/"))
            params_list = op.get("parameters") or path_item.get("parameters") or []
            params = {}
            for p in params_list:
                if isinstance(p, dict):
                    fs = _param_to_schema(p)
                    params[fs.name] = fs
            endpoint = Endpoint(
                method=http_method,
                url=url,
                path_pattern=path_template,
                params=params,
                body_schema=[],  # could parse requestBody
                source="api_spec",
                classification=_classify_path(path_template),
                sensitivity_label=_sensitivity_from_path(path_template),
            )
            endpoints.append(endpoint)
    return endpoints


async def run_api_spec_discovery(
    base_url: str,
    run_id: Optional[str] = None,
    network_intel: Optional[NetworkIntelligence] = None,
    client: Optional[Any] = None,
) -> list[Endpoint]:
    """
    Fetch common OpenAPI/Swagger paths; parse; add endpoints to network_intel.
    Returns list of discovered endpoints from specs.
    """
    config = get_config()
    run_id = run_id or getattr(config, "run_id", "") or ""
    base_url = base_url.rstrip("/")
    all_endpoints: list[Endpoint] = []

    if client is None:
        try:
            from cyberAI.utils.http_client import AsyncHTTPClient
            client = AsyncHTTPClient()
        except ImportError:
            logger.warning("API spec discovery: AsyncHTTPClient not available")
            return all_endpoints

    for path in COMMON_SPEC_PATHS:
        url = urljoin(base_url + "/", path.lstrip("/"))
        try:
            if not hasattr(client, "get"):
                continue
            resp, _ = await client.get(url, record=False)
            if resp is None:
                continue
            if getattr(resp, "status_code", 0) != 200:
                continue
            text = getattr(resp, "text", None)
            if not text:
                continue
            if path.endswith(".yaml"):
                try:
                    import yaml
                    spec = yaml.safe_load(text)
                except Exception:
                    continue
            else:
                try:
                    spec = json.loads(text)
                except json.JSONDecodeError:
                    continue
            endpoints = _parse_openapi_spec(spec, base_url)
            for ep in endpoints:
                network_intel.add_endpoint(ep) if network_intel else None
                all_endpoints.append(ep)
            if endpoints:
                logger.info(f"API spec: loaded {len(endpoints)} endpoints from {url}")
                break
        except Exception as e:
            logger.debug(f"API spec fetch {url}: {e}")

    out_path = config.get_output_path("recon", "intelligence", "api_spec_endpoints.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(
        out_path,
        add_meta_to_output(
            {"endpoints": [e.model_dump() for e in all_endpoints], "count": len(all_endpoints)},
            target_url=base_url,
            phase="recon",
            run_id=run_id,
        ),
    )
    return all_endpoints
