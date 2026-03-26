"""
Tool 3 — fetch_api_schema

Discover and download API schema: OpenAPI/Swagger, GraphQL introspection, WADL.
Probes all common schema paths.
"""

from __future__ import annotations

from typing import Optional

import httpx
from loguru import logger

from cyberAI.llm.agent.state import RunState


_SCHEMA_PROBE_PATHS = [
    "/swagger.json",
    "/swagger.yaml",
    "/api-docs",
    "/api-docs.json",
    "/api-docs/swagger.json",
    "/openapi.json",
    "/openapi.yaml",
    "/v1/api-docs",
    "/api/v1/swagger.json",
    "/api/swagger.json",
    "/api/openapi.json",
    "/.well-known/openapi",
    "/docs/openapi.json",
    "/swagger/v1/swagger.json",
]

_GRAPHQL_PATHS = [
    "/graphql",
    "/__graphql",
    "/graphql/schema",
    "/api/graphql",
    "/v1/graphql",
    "/graphiql",
]

_GRAPHQL_INTROSPECTION = """
{
  __schema {
    types {
      name
      kind
      fields {
        name
        type { name kind }
      }
    }
    queryType { name }
    mutationType { name }
    subscriptionType { name }
  }
}
"""


def _parse_openapi(schema: dict) -> list[dict]:
    """Extract endpoint list from OpenAPI/Swagger schema."""
    endpoints = []
    paths = schema.get("paths", {})
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, spec in methods.items():
            if method.upper() in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"):
                params = []
                for p in spec.get("parameters", []):
                    if isinstance(p, dict):
                        params.append({"name": p.get("name"), "in": p.get("in"), "required": p.get("required", False)})
                endpoints.append({
                    "path": path,
                    "method": method.upper(),
                    "params": params,
                    "summary": spec.get("summary", ""),
                    "tags": spec.get("tags", []),
                })
    return endpoints


def _parse_graphql_types(schema_data: dict) -> tuple[list[str], list[str]]:
    """Extract type names and mutation names from GraphQL introspection."""
    types = []
    mutations = []
    schema = schema_data.get("data", {}).get("__schema", {})
    for t in schema.get("types", []):
        name = t.get("name", "")
        if name and not name.startswith("__"):
            types.append(name)
    mutation_type = schema.get("mutationType")
    if mutation_type:
        mutations_name = mutation_type.get("name", "Mutation")
        for t in schema.get("types", []):
            if t.get("name") == mutations_name:
                for f in t.get("fields") or []:
                    mutations.append(f.get("name", ""))
    return types, mutations


async def fetch_api_schema(
    target_url: str,
    session_name: Optional[str] = None,
    run_id: str = "",
    state: Optional[RunState] = None,
) -> dict:
    """
    Probe all common schema paths.

    Returns:
    {
      "schema_type": "openapi_v3",
      "schema_url": "/api-docs",
      "endpoints_parsed": 156,
      "schemas": [...],
      "graphql_types": [...],
      "graphql_mutations": [...]
    }
    """
    base = target_url.rstrip("/")

    # Get JWT for session
    jwt: Optional[str] = None
    if session_name and state:
        sess = state.get_sessions().get(session_name, {})
        jwt = sess.get("jwt")

    headers: dict = {"Accept": "application/json", "Content-Type": "application/json"}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    async with httpx.AsyncClient(timeout=20.0, verify=False, follow_redirects=True) as client:
        # Try OpenAPI/Swagger
        for path in _SCHEMA_PROBE_PATHS:
            try:
                r = await client.get(base + path, headers=headers)
                if r.status_code == 200 and r.content:
                    try:
                        schema = r.json()
                    except Exception:
                        continue

                    if not isinstance(schema, dict):
                        continue

                    schema_version = "unknown"
                    if "openapi" in schema:
                        schema_version = f"openapi_v{schema['openapi'][:1]}"
                    elif "swagger" in schema:
                        schema_version = f"swagger_v{schema.get('swagger', '2')[:1]}"
                    else:
                        continue

                    endpoints = _parse_openapi(schema)
                    logger.info(f"fetch_api_schema: found {schema_version} at {path} ({len(endpoints)} endpoints)")

                    # Write endpoints to state
                    if state:
                        for ep in endpoints:
                            state.add_endpoint({
                                "path": ep["path"],
                                "methods": [ep["method"]],
                                "params": ep["params"],
                                "discovery_source": "schema",
                            })

                    return {
                        "schema_type": schema_version,
                        "schema_url": path,
                        "endpoints_parsed": len(endpoints),
                        "schemas": endpoints[:200],
                        "graphql_types": [],
                        "graphql_mutations": [],
                        "info": schema.get("info", {}),
                    }
            except Exception as e:
                logger.debug(f"fetch_api_schema: {path} failed: {e}")

        # Try GraphQL introspection
        for path in _GRAPHQL_PATHS:
            try:
                r = await client.post(
                    base + path,
                    json={"query": _GRAPHQL_INTROSPECTION},
                    headers=headers,
                )
                if r.status_code == 200 and r.content:
                    try:
                        data = r.json()
                    except Exception:
                        continue
                    if "data" in data and "__schema" in data.get("data", {}):
                        types, mutations = _parse_graphql_types(data)
                        logger.info(f"fetch_api_schema: GraphQL introspection at {path} ({len(types)} types)")
                        if state:
                            state.add_endpoint({
                                "path": path,
                                "methods": ["POST"],
                                "discovery_source": "graphql_introspection",
                            })
                        return {
                            "schema_type": "graphql",
                            "schema_url": path,
                            "endpoints_parsed": len(mutations),
                            "schemas": [],
                            "graphql_types": types[:100],
                            "graphql_mutations": mutations[:50],
                        }
            except Exception as e:
                logger.debug(f"fetch_api_schema: graphql {path} failed: {e}")

    logger.info("fetch_api_schema: no schema found at any probe path")
    return {
        "schema_type": "none",
        "schema_url": None,
        "endpoints_parsed": 0,
        "schemas": [],
        "graphql_types": [],
        "graphql_mutations": [],
    }
