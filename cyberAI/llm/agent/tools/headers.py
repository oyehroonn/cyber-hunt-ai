"""
Tool 5 — analyze_security_headers

Analyze HTTP security headers across target endpoints.
Identifies missing, weak, or misconfigured headers and produces findings.
"""

from __future__ import annotations

from typing import Optional

import httpx
from loguru import logger

from cyberAI.llm.agent.state import RunState


_REQUIRED_HEADERS = {
    "Content-Security-Policy": "Prevents XSS by restricting content sources",
    "Strict-Transport-Security": "Enforces HTTPS (HSTS)",
    "X-Content-Type-Options": "Prevents MIME-type sniffing",
    "X-Frame-Options": "Prevents clickjacking",
    "Referrer-Policy": "Controls referrer information leakage",
    "Permissions-Policy": "Restricts browser feature access",
}

_CORS_HEADER = "Access-Control-Allow-Origin"
_CORS_CREDS_HEADER = "Access-Control-Allow-Credentials"
_SERVER_HEADER = "Server"
_POWERED_BY_HEADER = "X-Powered-By"
_COOKIE_ATTRS = {"secure", "httponly", "samesite"}


def _check_cors(headers: dict) -> Optional[dict]:
    origin = headers.get(_CORS_HEADER, "")
    creds = headers.get(_CORS_CREDS_HEADER, "").lower()
    if origin == "*":
        return {"type": "CORS_WILDCARD", "severity": "medium", "detail": "Access-Control-Allow-Origin: *"}
    if origin and creds == "true":
        return {"type": "CORS_CREDENTIALED", "severity": "high",
                "detail": f"CORS with credentials from {origin}"}
    return None


def _analyze_cookies(set_cookie_headers: list[str]) -> list[dict]:
    issues = []
    for raw in set_cookie_headers:
        parts = [p.strip().lower() for p in raw.split(";")]
        name = raw.split("=")[0].strip()
        secure = any(p == "secure" for p in parts)
        httponly = any(p == "httponly" for p in parts)
        samesite = next((p.split("=")[1].strip() if "=" in p else "missing"
                         for p in parts if "samesite" in p), "missing")
        if not secure or not httponly or samesite == "missing":
            issues.append({
                "name": name,
                "secure": secure,
                "httponly": httponly,
                "samesite": samesite,
            })
    return issues


async def analyze_security_headers(
    target_url: str,
    sample_endpoints: Optional[list[str]] = None,
    run_id: str = "",
    state: Optional[RunState] = None,
) -> dict:
    """
    Fetch target + sample endpoints and analyze security headers.

    Returns:
    {
      "missing_headers": [...],
      "weak_headers": {...},
      "cookies_insecure": [...],
      "tls_issues": [],
      "server_disclosure": "Server: Express",
      "findings": [{"type": "CORS_WILDCARD", "severity": "medium", "endpoint": "/api/Users"}]
    }
    """
    base = target_url.rstrip("/")
    endpoints_to_check = [base + "/"] + [base + ep for ep in (sample_endpoints or [])[:20]]

    missing_headers: set[str] = set()
    weak_headers: dict[str, str] = {}
    cookies_insecure: list[dict] = []
    server_disclosure: Optional[str] = None
    findings: list[dict] = []
    tls_issues: list[str] = []

    # Check TLS
    if base.startswith("http://"):
        tls_issues.append("Target uses HTTP (not HTTPS) — traffic is unencrypted")

    async with httpx.AsyncClient(timeout=15.0, verify=False, follow_redirects=True) as client:
        for url in endpoints_to_check[:10]:
            try:
                r = await client.get(url, headers={"Accept": "application/json, text/html"})
                headers = {k.lower(): v for k, v in r.headers.items()}

                # Check required headers
                for header, desc in _REQUIRED_HEADERS.items():
                    if header.lower() not in headers:
                        missing_headers.add(header)

                # Check X-Frame-Options
                xfo = headers.get("x-frame-options", "")
                if xfo and xfo.upper() == "SAMEORIGIN":
                    weak_headers["X-Frame-Options"] = "SAMEORIGIN (not DENY)"

                # CORS check
                cors_issue = _check_cors({k.lower(): v for k, v in r.headers.items()})
                # Re-check with original case
                cors_issue = _check_cors(dict(r.headers))
                if cors_issue:
                    issue = {**cors_issue, "endpoint": url.replace(base, "")}
                    findings.append(issue)
                    weak_headers["CORS"] = cors_issue["detail"]

                # Cookies
                raw_cookies = r.headers.get_list("set-cookie") if hasattr(r.headers, "get_list") else []
                if not raw_cookies:
                    sc = r.headers.get("set-cookie", "")
                    raw_cookies = [sc] if sc else []
                cookies_insecure.extend(_analyze_cookies(raw_cookies))

                # Server disclosure
                server = r.headers.get("Server") or r.headers.get("server")
                if server and server_disclosure is None:
                    server_disclosure = f"Server: {server}"

                powered = r.headers.get("X-Powered-By") or r.headers.get("x-powered-by")
                if powered:
                    weak_headers["X-Powered-By"] = powered

            except Exception as e:
                logger.debug(f"analyze_security_headers: {url} error: {e}")

    # Generate findings for missing critical headers
    for header in ["Content-Security-Policy", "Strict-Transport-Security"]:
        if header in missing_headers:
            findings.append({
                "type": f"MISSING_{header.upper().replace('-', '_')}",
                "severity": "medium",
                "endpoint": "/",
                "detail": f"Header {header} is not set",
            })

    if state:
        state.write_log("recon", "INFO", "analyze_security_headers",
                        f"Missing: {len(missing_headers)} headers, {len(findings)} findings")

    return {
        "missing_headers": sorted(missing_headers),
        "weak_headers": weak_headers,
        "cookies_insecure": cookies_insecure[:20],
        "tls_issues": tls_issues,
        "server_disclosure": server_disclosure,
        "findings": findings,
        "endpoints_checked": len(endpoints_to_check[:10]),
    }
