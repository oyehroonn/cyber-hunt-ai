"""
Tool 14 — replay_request_with_variants
Tool 15 — diff_responses

replay_request_with_variants: Replay a captured request with systematic variations.
diff_responses: Structured diff between two HTTP responses.
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
    "email", "mail", "phone", "address", "name", "firstname", "lastname",
    "fullname", "ssn", "birth", "dob", "passport", "role", "isAdmin",
    "admin", "creditCard", "card", "balance", "wallet",
}


def _body_hash(body: Any) -> str:
    try:
        serialized = json.dumps(body, sort_keys=True)
    except Exception:
        serialized = str(body)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


def _find_pii(body: Any) -> list[str]:
    found = []
    if isinstance(body, dict):
        for k, v in body.items():
            if k.lower() in _PII_KEYS and v:
                found.append(k)
            elif isinstance(v, (dict, list)):
                found.extend(_find_pii(v))
    elif isinstance(body, list):
        for item in body:
            found.extend(_find_pii(item))
    return list(set(found))


def _deep_diff(a: Any, b: Any, path: str = "") -> dict:
    """Recursively diff two JSON-compatible values."""
    changed: dict[str, Any] = {}
    if type(a) != type(b):
        return {path or "root": {"a": a, "b": b}}
    if isinstance(a, dict):
        all_keys = set(a.keys()) | set(b.keys())
        for k in all_keys:
            sub = _deep_diff(a.get(k), b.get(k), path=f"{path}.{k}" if path else k)
            changed.update(sub)
    elif isinstance(a, list):
        for i, (ai, bi) in enumerate(zip(a, b)):
            sub = _deep_diff(ai, bi, path=f"{path}[{i}]")
            changed.update(sub)
    elif a != b:
        changed[path or "root"] = {"a": a, "b": b}
    return changed


async def replay_request_with_variants(
    base_request: dict,
    variants: list[dict],
    run_id: str = "",
    state: Optional[RunState] = None,
    target_url: str = "",
) -> dict:
    """
    Replay a base request with systematic variations and return diffs.

    base_request: {method, url, headers, body, session_name}
    variants: [{field: "path_param", value: "1337", description: "admin ID"}]

    Returns:
    {
      "results": [
        {
          "description": "admin ID in path",
          "request": {...},
          "response": {"status": 200, "body_hash": "...", "pii_fields": [...]},
          "diff_from_base": {"body_changed": true, "new_fields": ["role", "admin_token"]}
        }
      ]
    }
    """
    base_target = target_url.rstrip("/") if target_url else (
        state.get("target", "").rstrip("/") if state else ""
    )

    method = base_request.get("method", "GET").upper()
    url = base_request.get("url", "/")
    req_headers = dict(base_request.get("headers", {}))
    req_body = base_request.get("body")
    session_name = base_request.get("session_name", "")

    # Enrich headers with session JWT
    if session_name and state:
        sess = state.get_sessions().get(session_name, {})
        jwt = sess.get("jwt", "")
        if jwt:
            req_headers["Authorization"] = f"Bearer {jwt}"

    if "Content-Type" not in req_headers and req_body:
        req_headers["Content-Type"] = "application/json"

    results: list[dict] = []

    async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
        # Execute base request first
        try:
            base_resp = await client.request(
                method,
                url if url.startswith("http") else base_target + url,
                headers=req_headers,
                json=req_body if req_body else None,
                follow_redirects=False,
            )
            base_body: Any = {}
            try:
                base_body = base_resp.json()
            except Exception:
                base_body = {"raw": base_resp.text[:500]}
            base_hash = _body_hash(base_body)
        except Exception as e:
            return {"error": f"Base request failed: {e}", "results": []}

        # Execute each variant
        for variant in variants:
            field = variant.get("field", "")
            value = variant.get("value", "")
            description = variant.get("description", f"{field}={value}")
            variant_method = variant.get("method", method)

            # Build variant URL / body / headers
            v_url = url
            v_body = dict(req_body) if isinstance(req_body, dict) else req_body
            v_headers = dict(req_headers)

            # Override session if variant specifies
            if variant.get("session_name") and state:
                sess = state.get_sessions().get(variant["session_name"], {})
                jwt = sess.get("jwt", "")
                if jwt:
                    v_headers["Authorization"] = f"Bearer {jwt}"
                elif variant.get("no_auth"):
                    v_headers.pop("Authorization", None)

            if field == "path_param":
                # Replace last numeric segment or {id} placeholder
                v_url = re.sub(r"/\d+", f"/{value}", v_url, count=1)
                v_url = re.sub(r"\{[^}]+\}", str(value), v_url, count=1)
            elif field == "query_param":
                param_name = variant.get("param_name", "id")
                v_url = f"{v_url}?{param_name}={value}"
            elif field == "header":
                v_headers[variant.get("header_name", field)] = str(value)
            elif field == "body_field" and isinstance(v_body, dict):
                v_body[variant.get("body_key", "id")] = value
            elif field == "no_auth":
                v_headers.pop("Authorization", None)
            elif field == "replace_body":
                v_body = value

            try:
                full_url = v_url if v_url.startswith("http") else base_target + v_url
                resp = await client.request(
                    variant_method,
                    full_url,
                    headers=v_headers,
                    json=v_body if v_body else None,
                    follow_redirects=False,
                )
                try:
                    resp_body = resp.json()
                except Exception:
                    resp_body = {"raw": resp.text[:500]}

                resp_hash = _body_hash(resp_body)
                pii = _find_pii(resp_body)
                diff = diff_responses(
                    {"status": base_resp.status_code, "body": base_body},
                    {"status": resp.status_code, "body": resp_body},
                )

                results.append({
                    "description": description,
                    "request": {
                        "method": variant_method,
                        "url": full_url,
                        "headers": {k: v for k, v in v_headers.items()
                                    if k.lower() != "authorization"},
                    },
                    "response": {
                        "status": resp.status_code,
                        "body_hash": resp_hash,
                        "pii_fields": pii,
                        "body_sample": str(resp_body)[:300],
                    },
                    "diff_from_base": {
                        "body_changed": resp_hash != base_hash,
                        "status_changed": resp.status_code != base_resp.status_code,
                        "verdict": diff.get("verdict", "unknown"),
                        "changed_fields": list(diff.get("changed_fields", {}).keys()),
                    },
                })
            except Exception as e:
                results.append({
                    "description": description,
                    "error": str(e),
                })

    return {
        "base_response": {
            "status": base_resp.status_code,
            "body_hash": base_hash,
        },
        "results": results,
        "variants_tested": len(variants),
    }


def diff_responses(
    response_a: dict,
    response_b: dict,
    context: str = "idor_check",
) -> dict:
    """
    Structured diff between two HTTP responses.

    Returns:
    {
      "status_match": true/false,
      "body_identical": false,
      "changed_fields": {"email": {"a": "...", "b": "..."}},
      "a_specific_values": {"email": "user_a@test"},
      "b_specific_values": {"email": "user_b@test"},
      "pii_in_b_not_in_a": ["user_b_email"],
      "verdict": "idor_confirmed",
      "confidence": 0.95
    }
    """
    status_a = response_a.get("status", 0)
    status_b = response_b.get("status", 0)
    body_a = response_a.get("body", {})
    body_b = response_b.get("body", {})

    hash_a = _body_hash(body_a)
    hash_b = _body_hash(body_b)
    body_identical = hash_a == hash_b

    changed_fields = _deep_diff(body_a, body_b) if not body_identical else {}

    # Find PII specific to each response
    pii_a = set(_find_pii(body_a))
    pii_b = set(_find_pii(body_b))
    pii_in_b_not_a = list(pii_b - pii_a)

    # Extract values of changed fields from each response
    a_vals: dict = {}
    b_vals: dict = {}
    if isinstance(body_a, dict) and isinstance(body_b, dict):
        for field_path, change in changed_fields.items():
            if "." not in field_path and "[" not in field_path:
                if body_a.get(field_path) is not None:
                    a_vals[field_path] = body_a[field_path]
                if body_b.get(field_path) is not None:
                    b_vals[field_path] = body_b[field_path]

    # Verdict determination
    if body_identical and status_a == status_b:
        verdict = "same_data"
        confidence = 0.9
    elif status_b in (401, 403):
        verdict = "access_denied"
        confidence = 1.0
    elif status_b == 500:
        verdict = "error_response"
        confidence = 0.5
    elif status_b == 200 and not body_identical:
        if context == "idor_check" and (changed_fields or pii_in_b_not_a):
            verdict = "idor_confirmed"
            confidence = 0.95 if pii_in_b_not_a else 0.75
        else:
            verdict = "different_response"
            confidence = 0.6
    elif not body_a and not body_b:
        verdict = "empty"
        confidence = 0.3
    else:
        verdict = "inconclusive"
        confidence = 0.4

    return {
        "status_match": status_a == status_b,
        "body_identical": body_identical,
        "changed_fields": changed_fields,
        "a_specific_values": a_vals,
        "b_specific_values": b_vals,
        "pii_in_b_not_in_a": pii_in_b_not_a,
        "verdict": verdict,
        "confidence": confidence,
    }
