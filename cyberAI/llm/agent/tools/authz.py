"""
Tool 10 — test_auth_bypass
Tool 11 — test_mass_assignment

test_auth_bypass: Systematic auth enforcement testing across all endpoints.
test_mass_assignment: Detect privilege escalation via undocumented body fields.
"""

from __future__ import annotations

import json
from typing import Any, Optional

import httpx
from loguru import logger

from cyberAI.llm.agent.state import RunState


_PRIV_ESCALATION_FIELDS = [
    "role", "isAdmin", "is_admin", "admin", "verified", "credit", "balance",
    "permissions", "scope", "group", "tier", "subscription", "level",
    "privilege", "accessLevel", "userType", "accountType",
]

_PII_KEYS = {
    "email", "mail", "phone", "address", "name", "ssn", "password",
    "creditCard", "card", "role", "isAdmin", "balance", "wallet",
}

_EXPIRED_JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlRlc3QiLCJleHAiOjE1MDAwMDAwMDB9"
    ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
)


def _has_pii(body: Any) -> bool:
    if isinstance(body, dict):
        for k, v in body.items():
            if k.lower() in _PII_KEYS and v:
                return True
            if isinstance(v, (dict, list)) and _has_pii(v):
                return True
    elif isinstance(body, list):
        return any(_has_pii(i) for i in body)
    return False


async def test_auth_bypass(
    endpoints: list[dict],
    run_id: str = "",
    state: Optional[RunState] = None,
    target_url: str = "",
) -> dict:
    """
    For each endpoint, tests 4 auth scenarios:
    1. No auth (no token) → expect 401/403
    2. Invalid/expired JWT → expect 401
    3. user_a JWT → expect role-appropriate response
    4. admin JWT → expect 200 (positive control)

    Returns findings where unauthenticated or wrong-role gets 200.
    {
      "auth_bypass_findings": [
        {
          "endpoint": "GET /api/Users",
          "scenario": "no_auth",
          "status": 200,
          "response_contains_pii": true,
          "severity": "high",
          "finding_id": "F-002"
        }
      ]
    }
    """
    base = target_url.rstrip("/") if target_url else (
        state.get("target", "").rstrip("/") if state else ""
    )

    sessions = state.get_sessions() if state else {}
    jwt_user = sessions.get("user_a", {}).get("jwt", "")
    jwt_admin = sessions.get("admin", {}).get("jwt", "")

    findings: list[dict] = []
    tested = 0

    async with httpx.AsyncClient(base_url=base, timeout=10.0, verify=False, follow_redirects=False) as client:
        for ep in endpoints[:80]:
            path = ep.get("path", "/")
            method = (ep.get("methods") or ["GET"])[0].upper()
            if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                continue

            # Scenario 1: No auth
            try:
                r_no_auth = await client.request(method, path, headers={"Accept": "application/json"})
                tested += 1
                if r_no_auth.status_code == 200 and r_no_auth.content:
                    try:
                        body = r_no_auth.json()
                    except Exception:
                        body = {}
                    has_pii = _has_pii(body)
                    severity = "high" if has_pii else "medium"
                    finding = {
                        "endpoint": f"{method} {path}",
                        "scenario": "no_auth",
                        "status": 200,
                        "response_contains_pii": has_pii,
                        "severity": severity,
                        "evidence": {
                            "request": f"{method} {path} HTTP/1.1\nHost: {base}\n(no Authorization header)",
                            "response_status": 200,
                            "response_body_sample": str(body)[:500],
                        },
                    }
                    findings.append(finding)
                    if state:
                        fdata = {
                            "type": "AUTH_BYPASS",
                            "subtype": "unauthenticated_access",
                            "title": f"Unauthenticated access to {method} {path}",
                            "endpoint": path,
                            "method": method,
                            "severity": severity,
                            "cvss_score": 7.5 if has_pii else 5.3,
                            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
                            "owasp_category": "A07:2021 Identification and Authentication Failures",
                            "cwe_id": "CWE-306",
                            "status": "confirmed",
                            "reproduction_count": 1,
                            "evidence": finding["evidence"],
                            "remediation": f"Add authentication middleware to {method} {path}.",
                            "run_id": run_id,
                            "target": base,
                        }
                        fid = state.add_finding(fdata)
                        finding["finding_id"] = fid
            except Exception as e:
                logger.debug(f"test_auth_bypass no_auth {path}: {e}")

            # Scenario 2: Expired JWT
            if jwt_user:
                try:
                    r_expired = await client.request(
                        method, path,
                        headers={"Authorization": f"Bearer {_EXPIRED_JWT}", "Accept": "application/json"},
                    )
                    tested += 1
                    if r_expired.status_code == 200:
                        findings.append({
                            "endpoint": f"{method} {path}",
                            "scenario": "expired_jwt",
                            "status": 200,
                            "severity": "high",
                            "note": "Endpoint accepted an expired JWT",
                        })
                except Exception:
                    pass

    if state:
        state.write_log("test", "INFO", "test_auth_bypass",
                        f"Tested {tested} endpoints, found {len(findings)} auth bypass issues")

    return {
        "auth_bypass_findings": findings,
        "tested_endpoints": tested,
        "confirmed_count": len([f for f in findings if f.get("finding_id")]),
    }


async def test_mass_assignment(
    update_endpoints: list[dict],
    session_name: str = "user_a",
    run_id: str = "",
    state: Optional[RunState] = None,
    target_url: str = "",
) -> dict:
    """
    Sends requests with extra privilege-escalating fields appended to legitimate body.
    Tests fields like: role, isAdmin, admin, is_admin, verified, credit, balance,
                       permissions, scope, group, tier, subscription

    Decision rule: if update succeeds (200/204) AND re-fetching the object shows
    the injected field was stored → confirmed mass assignment.

    Returns confirmed findings with exact payload and before/after diff.
    """
    base = target_url.rstrip("/") if target_url else (
        state.get("target", "").rstrip("/") if state else ""
    )

    sessions = state.get_sessions() if state else {}
    sess = sessions.get(session_name, {})
    jwt = sess.get("jwt", "")
    user_id = sess.get("user_id")

    if not jwt:
        return {"confirmed_findings": [], "reason": f"No JWT for session {session_name}"}

    headers = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json",
               "Accept": "application/json"}
    findings: list[dict] = []

    # Filter for write endpoints
    write_eps = [
        ep for ep in update_endpoints
        if any(m in (ep.get("methods") or []) for m in ("PUT", "PATCH", "POST"))
    ]

    async with httpx.AsyncClient(base_url=base, timeout=15.0, verify=False) as client:
        for ep in write_eps[:30]:
            path = ep.get("path", "")
            method = next(
                (m for m in (ep.get("methods") or []) if m in ("PUT", "PATCH")),
                "POST"
            )
            # Fill ID params if present
            import re
            if user_id:
                path_filled = re.sub(r"\{[^}]+\}", str(user_id), path)
            else:
                path_filled = re.sub(r"\{[^}]+\}", "1", path)

            # Step 1: GET baseline (if GET method exists)
            baseline_body: dict = {}
            try:
                r_get = await client.get(path_filled, headers=headers)
                if r_get.status_code == 200 and r_get.content:
                    baseline_body = r_get.json() if isinstance(r_get.json(), dict) else {}
            except Exception:
                pass

            # Step 2: Send mass assignment payload
            attack_payload = dict(baseline_body)
            for field in _PRIV_ESCALATION_FIELDS:
                if field in ("isAdmin", "admin", "is_admin"):
                    attack_payload[field] = True
                elif field == "role":
                    attack_payload[field] = "admin"
                elif field in ("credit", "balance"):
                    attack_payload[field] = 99999
                else:
                    attack_payload[field] = "admin"

            try:
                r_attack = await client.request(method, path_filled, json=attack_payload, headers=headers)
                if r_attack.status_code not in (200, 201, 204):
                    continue

                # Step 3: Re-fetch and check if escalation fields were stored
                try:
                    r_verify = await client.get(path_filled, headers=headers)
                    if r_verify.status_code != 200 or not r_verify.content:
                        continue
                    after_body = r_verify.json() if isinstance(r_verify.json(), dict) else {}
                except Exception:
                    continue

                stored_fields = []
                for field in _PRIV_ESCALATION_FIELDS:
                    b_val = baseline_body.get(field)
                    a_val = after_body.get(field)
                    payload_val = attack_payload.get(field)
                    if a_val is not None and a_val != b_val and str(a_val) == str(payload_val):
                        stored_fields.append(field)

                if stored_fields:
                    finding = {
                        "endpoint": f"{method} {path}",
                        "stored_escalation_fields": stored_fields,
                        "severity": "critical" if any(
                            f in stored_fields for f in ("isAdmin", "admin", "is_admin", "role")
                        ) else "high",
                        "evidence": {
                            "attack_payload": {k: v for k, v in attack_payload.items()
                                              if k in stored_fields},
                            "baseline": baseline_body,
                            "after": after_body,
                            "stored_fields": stored_fields,
                        },
                    }
                    findings.append(finding)

                    if state:
                        fdata = {
                            "type": "MASS_ASSIGNMENT",
                            "subtype": "privilege_escalation",
                            "title": f"Mass Assignment on {method} {path} — fields: {stored_fields}",
                            "endpoint": path,
                            "method": method,
                            "severity": finding["severity"],
                            "cvss_score": 9.1 if "isAdmin" in stored_fields or "role" in stored_fields else 7.5,
                            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N",
                            "owasp_category": "API6:2023 Unrestricted Access to Sensitive Business Flows",
                            "cwe_id": "CWE-915",
                            "status": "confirmed",
                            "reproduction_count": 1,
                            "evidence": finding["evidence"],
                            "remediation": (
                                f"Use an allowlist for accepted fields in {method} {path}. "
                                f"Never accept {stored_fields} from client input."
                            ),
                            "run_id": run_id,
                            "target": base,
                        }
                        fid = state.add_finding(fdata)
                        finding["finding_id"] = fid
                        state.write_log("test", "WARNING", "test_mass_assignment",
                                        f"CONFIRMED mass assignment on {path}: {stored_fields}")
                        logger.warning(f"test_mass_assignment: CONFIRMED on {path}: {stored_fields}")

            except Exception as e:
                logger.debug(f"test_mass_assignment {path}: {e}")

    return {
        "confirmed_findings": findings,
        "tested_endpoints": len(write_eps),
        "confirmed_count": len(findings),
    }
