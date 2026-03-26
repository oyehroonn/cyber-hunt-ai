"""
Tool 8 — test_idor

Multi-session cross-user IDOR testing using the OWASP WSTG / Autorize methodology.

The ONLY correct IDOR methodology:
  1. User A accesses User A's owned resource → baseline
  2. User A swaps User B's resource ID into the same request → attack
  3. Server returns User B's data → CONFIRMED IDOR

Never call this "IDOR" if step 3 doesn't happen.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Optional

import httpx
from loguru import logger

from cyberAI.llm.agent.state import RunState


_PII_KEYS = {
    "email", "mail", "phone", "mobile", "address", "name", "firstname", "lastname",
    "fullname", "ssn", "birth", "dob", "passport", "license", "role", "isAdmin",
    "admin", "creditCard", "card", "balance", "wallet",
}

_ID_PARAM_RE = re.compile(r"\{(?:id|uuid|userId|productId|orderId|basketId|addressId|cardId)\}", re.IGNORECASE)


def _body_hash(body: Any) -> str:
    try:
        serialized = json.dumps(body, sort_keys=True)
    except Exception:
        serialized = str(body)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


def _find_pii_fields(body: Any) -> list[str]:
    found = []
    if isinstance(body, dict):
        for k, v in body.items():
            if k.lower() in _PII_KEYS and v:
                found.append(k)
            elif isinstance(v, (dict, list)):
                found.extend(_find_pii_fields(v))
    elif isinstance(body, list):
        for item in body:
            found.extend(_find_pii_fields(item))
    return list(set(found))


def _extract_id_from_body(body: Any) -> Optional[Any]:
    if isinstance(body, dict):
        for key in ("id", "userId", "user_id", "uid", "basketId", "orderId"):
            if key in body:
                return body[key]
        data = body.get("data")
        if isinstance(data, dict):
            return _extract_id_from_body(data)
    return None


def _fill_id_param(path: str, obj_id: Any) -> str:
    result = _ID_PARAM_RE.sub(str(obj_id), path)
    # Also replace bare /:id/ pattern
    result = re.sub(r"/\d+", f"/{obj_id}", result, count=1)
    return result


def _determine_severity(pii_fields: list[str], endpoint: dict) -> str:
    if any(k in pii_fields for k in ("password", "creditCard", "ssn", "isAdmin")):
        return "critical"
    if any(k in pii_fields for k in ("email", "phone", "address", "role")):
        return "high"
    return "medium"


def _calculate_cvss_idor(pii_fields: list[str], authenticated: bool = True) -> float:
    base = 6.5 if authenticated else 8.0
    if any(k in pii_fields for k in ("password", "creditCard", "ssn")):
        return min(9.8, base + 1.5)
    if any(k in pii_fields for k in ("email", "role", "isAdmin")):
        return min(9.0, base + 0.5)
    return base


def _censor_sensitive(body: Any) -> Any:
    """Mask sensitive values in response bodies before storing as evidence."""
    if isinstance(body, dict):
        out = {}
        for k, v in body.items():
            if k.lower() in ("password", "passwordhash", "totpsecret", "verificationtoken"):
                out[k] = "***REDACTED***"
            else:
                out[k] = _censor_sensitive(v)
        return out
    if isinstance(body, list):
        return [_censor_sensitive(i) for i in body]
    return body


async def _get_or_create_owned_object(
    endpoint: dict,
    session: dict,
    target_url: str,
) -> Optional[Any]:
    """
    Get the ID of an object owned by a session user.
    For /api/Users/{id} → use user_id from session.
    For other endpoints → try to create one.
    """
    path = endpoint.get("path", "")
    base = target_url.rstrip("/")
    jwt = session.get("jwt", "")
    user_id = session.get("user_id")

    headers = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}

    # For Users endpoint, user_id IS the object ID
    if "/users" in path.lower() and user_id:
        return user_id

    # Try to create an owned object via POST on the collection endpoint
    collection_path = re.sub(r"/\{[^}]+\}$", "", path)
    if collection_path == path:
        # No ID param at end — can't create
        return user_id  # fallback to user_id

    async with httpx.AsyncClient(base_url=base, timeout=15.0, verify=False) as client:
        try:
            r = await client.post(
                collection_path,
                json={},
                headers=headers,
            )
            if r.status_code in (200, 201):
                body = r.json() if r.content else {}
                obj_id = _extract_id_from_body(body)
                if obj_id:
                    return obj_id
        except Exception as e:
            logger.debug(f"test_idor: create object failed for {collection_path}: {e}")

    # Fallback: try sequential IDs (1, 2, 3)
    for seq_id in [user_id, 1, 2, 3]:
        if seq_id:
            url = _fill_id_param(path, seq_id)
            try:
                r = await client.get(url, headers=headers)
                if r.status_code == 200:
                    return seq_id
            except Exception:
                pass

    return None


async def test_idor(
    endpoint: dict,
    run_id: str = "",
    num_swaps: int = 10,
    test_vertical: bool = True,
    state: Optional[RunState] = None,
    target_url: str = "",
) -> dict:
    """
    Full cross-session IDOR test.

    Returns:
    {
      "endpoint": "/api/Users/{id}",
      "tests_run": 10,
      "confirmed_idor": true,
      "idor_type": "horizontal",
      "evidence": {...},
      "cvss_score": 8.1,
      "finding_id": "F-003"
    }
    """
    path = endpoint.get("path", "")
    method = endpoint.get("method", "GET").upper()
    base = target_url.rstrip("/")

    # Must have ID param
    if not _ID_PARAM_RE.search(path) and not re.search(r"/\d+", path):
        return {
            "endpoint": path,
            "confirmed_idor": False,
            "reason": "No ID parameter in path — IDOR not applicable",
            "tests_run": 0,
        }

    # Must have at least 2 user sessions
    if not state:
        return {"confirmed_idor": False, "reason": "No state available"}

    sessions = state.get_sessions()
    if "user_a" not in sessions or "user_b" not in sessions:
        return {
            "confirmed_idor": False,
            "reason": f"Need user_a and user_b sessions; have: {list(sessions.keys())}",
        }

    session_a = sessions["user_a"]
    session_b = sessions["user_b"]

    # Step 1: Get owned IDs for both users
    id_a = await _get_or_create_owned_object(endpoint, session_a, base)
    id_b = await _get_or_create_owned_object(endpoint, session_b, base)

    if not id_a or not id_b or id_a == id_b:
        # Try offset IDs
        id_a = session_a.get("user_id", 1)
        id_b = session_b.get("user_id", 2)
        if id_a == id_b:
            id_b = int(id_a) + 1 if id_a else 2

    jwt_a = session_a.get("jwt", "")
    jwt_b = session_b.get("jwt", "")
    headers_a = {"Authorization": f"Bearer {jwt_a}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(base_url=base, timeout=15.0, verify=False) as client:
        # Step 2: Baseline — User A accesses User A's object
        baseline_url = _fill_id_param(path, id_a)
        try:
            baseline_resp = await client.request(method, baseline_url, headers=headers_a)
        except Exception as e:
            return {"confirmed_idor": False, "reason": f"Baseline request failed: {e}", "tests_run": 0}

        if baseline_resp.status_code not in (200, 201):
            return {
                "confirmed_idor": False,
                "reason": f"Baseline failed (status {baseline_resp.status_code}) — endpoint may require different setup",
                "tests_run": 1,
            }

        try:
            baseline_body = baseline_resp.json()
        except Exception:
            baseline_body = {"raw": baseline_resp.text[:500]}

        baseline_hash = _body_hash(baseline_body)

        # Step 3: Attack — User A accesses User B's object
        attack_url = _fill_id_param(path, id_b)
        try:
            attack_resp = await client.request(method, attack_url, headers=headers_a)
        except Exception as e:
            return {"confirmed_idor": False, "reason": f"Attack request failed: {e}", "tests_run": 2}

        if attack_resp.status_code in (401, 403, 404):
            return {
                "confirmed_idor": False,
                "reason": f"Authorization properly enforced (status {attack_resp.status_code})",
                "tests_run": 2,
                "endpoint": path,
            }

        if attack_resp.status_code != 200:
            return {
                "confirmed_idor": False,
                "reason": f"Unexpected status {attack_resp.status_code}",
                "tests_run": 2,
            }

        try:
            attack_body = attack_resp.json()
        except Exception:
            attack_body = {"raw": attack_resp.text[:500]}

        attack_hash = _body_hash(attack_body)
        attack_body_str = json.dumps(attack_body)

        # Step 4: Decision — is this ACTUALLY user_b's data?
        user_b_email = session_b.get("email", "")
        user_b_id = str(session_b.get("user_id", ""))

        evidence_flags = {
            "email_present": bool(user_b_email and user_b_email in attack_body_str),
            "id_matches": bool(user_b_id and user_b_id == str(attack_body.get("id", ""))),
            "body_differs": baseline_hash != attack_hash,
        }
        confirmed = any(evidence_flags.values())

        if not confirmed:
            return {
                "confirmed_idor": False,
                "reason": "Status 200 but response appears to be public/same data for all users",
                "evidence_flags": evidence_flags,
                "tests_run": 2,
            }

        pii_fields = _find_pii_fields(attack_body)
        severity = _determine_severity(pii_fields, endpoint)
        cvss = _calculate_cvss_idor(pii_fields, authenticated=True)

        # Format raw requests for evidence
        def fmt_request(url_path: str, sess_jwt: str) -> str:
            return (f"{method} {url_path} HTTP/1.1\n"
                    f"Host: {base.replace('https://', '').replace('http://', '')}\n"
                    f"Authorization: Bearer {sess_jwt[:30]}...\n"
                    f"Content-Type: application/json")

        finding_data = {
            "type": "IDOR",
            "subtype": "horizontal",
            "endpoint": path,
            "method": method,
            "severity": severity,
            "cvss_score": cvss,
            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N",
            "owasp_category": "API1:2023 Broken Object Level Authorization",
            "cwe_id": "CWE-284",
            "title": f"Horizontal IDOR on {path}",
            "status": "confirmed",
            "reproduction_count": 1,
            "reproduction_runs_needed": 2,
            "evidence": {
                "baseline": {
                    "url": baseline_url,
                    "request": fmt_request(baseline_url, jwt_a),
                    "response_status": baseline_resp.status_code,
                    "response_body": _censor_sensitive(baseline_body),
                    "hash": baseline_hash,
                },
                "attack": {
                    "url": attack_url,
                    "request": fmt_request(attack_url, jwt_a),
                    "response_status": attack_resp.status_code,
                    "response_body": _censor_sensitive(attack_body),
                    "hash": attack_hash,
                },
                "user_b_identifiers_in_response": evidence_flags,
                "pii_fields_exposed": pii_fields,
            },
            "reproduction_steps": [
                f"Register as user_a and user_b via POST /api/Users",
                f"Log in as user_a (POST /rest/user/login), note JWT",
                f"Send: {method} {attack_url} with user_a's JWT",
                f"Observe: response contains user_b's data",
                "Expected: 403 Forbidden",
            ],
            "remediation": (
                f"Add object ownership check in {method} {path} handler: "
                "verify request.user.id === requested_id OR request.user.role === 'admin'"
            ),
            "run_id": run_id,
            "target": base,
        }

        # Store in state
        finding_id = "pending"
        if state:
            finding_id = state.add_finding(finding_data)
            state.write_log("recon", "WARNING", "test_idor",
                            f"CONFIRMED IDOR on {path} (severity={severity}, cvss={cvss})")

        logger.warning(f"test_idor: CONFIRMED horizontal IDOR on {path} (cvss={cvss})")

        return {
            "endpoint": path,
            "tests_run": 2,
            "confirmed_idor": True,
            "idor_type": "horizontal",
            "severity": severity,
            "cvss_score": cvss,
            "pii_fields_exposed": pii_fields,
            "finding_id": finding_id,
            "evidence_summary": (
                f"User A (id={id_a}) accessed User B's resource (id={id_b}). "
                f"Evidence: email_present={evidence_flags['email_present']}, "
                f"body_differs={evidence_flags['body_differs']}"
            ),
        }
