"""
Tool 4 — discover_endpoints
Tool 7 — build_endpoint_inventory

discover_endpoints: Active path brute-forcing with built-in wordlist + AI extension.
build_endpoint_inventory: Consolidate and risk-score all discovered endpoints.
"""

from __future__ import annotations

import asyncio
import re
from typing import Optional

import httpx
from loguru import logger

from cyberAI.llm.agent.state import RunState


# ---------------------------------------------------------------------------
# Built-in wordlist (compact subset of raft-medium + API-focused paths)
# ---------------------------------------------------------------------------
_BUILTIN_WORDLIST = [
    # Common API paths
    "api", "api/v1", "api/v2", "api/v3", "rest", "graphql",
    # Auth
    "login", "logout", "register", "auth", "oauth", "token", "refresh",
    "api/login", "api/logout", "api/register", "api/auth", "rest/user/login",
    # Users
    "api/Users", "api/users", "api/user", "api/profile", "api/me", "api/account",
    # Admin
    "admin", "administration", "api/admin", "rest/admin",
    "rest/admin/application-configuration", "rest/admin/application-version",
    # Common resources
    "api/Products", "api/products", "api/Orders", "api/orders",
    "api/Baskets", "api/baskets", "api/Cards", "api/cards",
    "api/Feedbacks", "api/feedbacks", "api/Addresses", "api/addresses",
    "api/Deliveries", "api/deliveries", "api/Recycles", "api/recycles",
    "api/Complaints", "api/complaints", "api/Wallets", "api/wallets",
    "api/SecurityQuestions", "api/SecurityAnswers", "api/Vouchers",
    "api/Challenges", "api/Memories", "api/QuantityItems",
    # Config/health
    "health", "healthz", "status", "metrics", "info", "version",
    "api/health", "api/status", "api/version", "api/config",
    "actuator", "actuator/health", "actuator/info", "actuator/env",
    # Files
    "robots.txt", "sitemap.xml", ".well-known/security.txt",
    # Common paths
    "swagger.json", "api-docs", "openapi.json",
    # Security
    "api/SecurityQuestions", "api/Vouchers/apply", "api/BasketItems",
    "api/BasketItems/{id}", "api/WhoAmI", "rest/user/whoami",
    "rest/basket", "rest/products/search",
    # Debug
    "debug", "trace", "phpinfo.php", ".env", "config.json",
]

_PII_KEYWORDS = {
    "email", "mail", "phone", "mobile", "address", "name", "firstname", "lastname",
    "fullname", "ssn", "birth", "dob", "passport", "license", "credit", "card",
    "password", "secret", "token", "role", "admin", "permission",
}

_EXPORT_KEYWORDS = {"export", "download", "report", "csv", "pdf", "backup", "dump"}
_RATE_LIMIT_HEADERS = {"x-ratelimit-limit", "x-ratelimit-remaining", "retry-after", "x-rate-limit"}

_ID_RE = re.compile(r"\{(?:id|uuid|userId|productId|orderId|basketId)\}", re.IGNORECASE)


def _has_id_param(path: str) -> bool:
    return bool(_ID_RE.search(path)) or re.search(r"/\d+", path) is not None


def _infer_pii(path: str) -> bool:
    p = path.lower()
    return any(k in p for k in _PII_KEYWORDS)


def _infer_export(path: str) -> bool:
    p = path.lower()
    return any(k in p for k in _EXPORT_KEYWORDS)


def _compute_risk_score(ep: dict, probed_status: Optional[int] = None) -> float:
    score = 0.0
    path = ep.get("path", "")

    if _has_id_param(path):
        score += 3.0
    if _infer_pii(path):
        score += 2.0
    if ep.get("auth_required") is False:
        score += 2.0
    if ep.get("accessible_unauthenticated"):
        score += 2.0
    if _infer_export(path):
        score += 1.0
    if ep.get("rate_limited"):
        score -= 1.0
    if probed_status == 403:
        score -= 1.0

    return round(max(0.0, min(10.0, score)), 1)


def _test_priority(score: float) -> str:
    if score >= 7:
        return "critical"
    if score >= 5:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# discover_endpoints
# ---------------------------------------------------------------------------

async def discover_endpoints(
    target_url: str,
    wordlist: str = "builtin",
    concurrent_requests: int = 30,
    session_name: Optional[str] = None,
    ai_extend: bool = True,
    run_id: str = "",
    state: Optional[RunState] = None,
) -> dict:
    """
    Active path brute-forcing.

    Returns:
    {
      "new_paths_found": [...],
      "interesting_status_codes": {"/admin": 200, "/metrics": 401},
      "total_probed": 4729
    }
    """
    base = target_url.rstrip("/")

    # Get JWT
    jwt: Optional[str] = None
    if session_name and state:
        sess = state.get_sessions().get(session_name, {})
        jwt = sess.get("jwt")

    headers: dict = {"Accept": "application/json"}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    paths_to_probe = list(_BUILTIN_WORDLIST)

    # Extend based on already-known paths
    if state:
        existing = state.get_endpoints()
        known_segments = set()
        for ep in existing:
            parts = ep.get("path", "").split("/")
            for part in parts:
                if part and not part.startswith("{"):
                    known_segments.add(part)
        # Add variants of known segments
        for seg in list(known_segments)[:30]:
            for suffix in ["", "s", "/search", "/export", "/admin", "/me", "/count"]:
                paths_to_probe.append(f"api/{seg}{suffix}")

    # Deduplicate
    paths_to_probe = list(dict.fromkeys(paths_to_probe))

    new_paths: list[str] = []
    interesting: dict[str, int] = {}
    sem = asyncio.Semaphore(concurrent_requests)

    async def probe(path: str) -> None:
        url = f"{base}/{path.lstrip('/')}"
        async with sem:
            try:
                async with httpx.AsyncClient(timeout=8.0, verify=False, follow_redirects=False) as client:
                    r = await client.get(url, headers=headers)
                    status = r.status_code
                    if status in (200, 201, 301, 302, 401, 403):
                        norm_path = "/" + path.lstrip("/")
                        interesting[norm_path] = status
                        if status in (200, 201):
                            new_paths.append(norm_path)
                            if state:
                                state.add_endpoint({
                                    "path": norm_path,
                                    "methods": ["GET"],
                                    "discovery_source": "brute_force",
                                    "status_code": status,
                                    "auth_required": False if status in (200, 201) else True,
                                })
            except Exception:
                pass

    tasks = [probe(p) for p in paths_to_probe]
    await asyncio.gather(*tasks)

    if state:
        state.write_log("recon", "INFO", "discover_endpoints",
                        f"Probed {len(paths_to_probe)} paths, found {len(new_paths)} new endpoints")

    return {
        "new_paths_found": sorted(set(new_paths)),
        "interesting_status_codes": interesting,
        "total_probed": len(paths_to_probe),
    }


# ---------------------------------------------------------------------------
# build_endpoint_inventory
# ---------------------------------------------------------------------------

async def build_endpoint_inventory(
    run_id: str = "",
    state: Optional[RunState] = None,
    target_url: str = "",
) -> dict:
    """
    Consolidate all endpoints from state, deduplicate, enrich with risk scores.

    Returns:
    {
      "total_endpoints": 156,
      "endpoint_inventory": [...],
      "high_priority_count": 23
    }
    """
    if not state:
        return {"total_endpoints": 0, "endpoint_inventory": [], "high_priority_count": 0}

    raw_endpoints = state.get_endpoints()

    # Deduplicate by path (merge methods from duplicates)
    path_map: dict[str, dict] = {}
    for ep in raw_endpoints:
        path = ep.get("path", "")
        if not path:
            continue
        if path not in path_map:
            path_map[path] = {
                "path": path,
                "methods": list(ep.get("methods", ["GET"])),
                "auth_required": ep.get("auth_required"),
                "accessible_unauthenticated": ep.get("accessible_unauthenticated", False),
                "discovery_sources": [ep.get("discovery_source", "unknown")],
                "params": ep.get("params", []),
                "rate_limited": False,
                "status_code": ep.get("status_code"),
            }
        else:
            # Merge
            existing = path_map[path]
            for m in ep.get("methods", []):
                if m not in existing["methods"]:
                    existing["methods"].append(m)
            src = ep.get("discovery_source", "unknown")
            if src not in existing["discovery_sources"]:
                existing["discovery_sources"].append(src)

    # Enrich and score
    inventory = []
    base = target_url.rstrip("/") if target_url else ""

    async with httpx.AsyncClient(timeout=8.0, verify=False, follow_redirects=False) as client:
        for path, ep in path_map.items():
            # Quick probe to check auth requirement
            if base and ep.get("auth_required") is None:
                try:
                    r = await client.get(base + path, headers={"Accept": "application/json"})
                    ep["status_code"] = r.status_code
                    ep["auth_required"] = r.status_code in (401, 403)
                    ep["accessible_unauthenticated"] = r.status_code in (200, 201)
                    # Check rate limit headers
                    ep["rate_limited"] = any(
                        h.lower() in _RATE_LIMIT_HEADERS
                        for h in r.headers.keys()
                    )
                    # Infer PII from response body sample
                    if r.status_code == 200 and r.content:
                        try:
                            body_text = r.text[:2000].lower()
                            ep["response_has_pii"] = any(k in body_text for k in _PII_KEYWORDS)
                        except Exception:
                            pass
                except Exception:
                    pass

            score = _compute_risk_score(ep, ep.get("status_code"))
            ep["risk_score"] = score
            ep["test_priority"] = _test_priority(score)
            ep["has_id_param"] = _has_id_param(path)
            ep["inferred_roles"] = []
            if ep.get("auth_required"):
                ep["inferred_roles"] = ["user"]
            if any(kw in path.lower() for kw in ("admin", "internal", "config", "debug")):
                ep["inferred_roles"].append("admin")

            inventory.append(ep)

    # Sort by risk score descending
    inventory.sort(key=lambda x: x["risk_score"], reverse=True)

    high_priority = [e for e in inventory if e["risk_score"] >= 7]

    if state:
        state.write_log("recon", "INFO", "build_endpoint_inventory",
                        f"Inventory: {len(inventory)} endpoints, {len(high_priority)} high-priority")

    return {
        "total_endpoints": len(inventory),
        "endpoint_inventory": inventory,
        "high_priority_count": len(high_priority),
        "critical_count": len([e for e in inventory if e["test_priority"] == "critical"]),
    }
