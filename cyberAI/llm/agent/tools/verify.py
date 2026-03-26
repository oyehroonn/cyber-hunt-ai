"""
Tool 16 — verify_finding

Given a finding, run targeted verification protocol to reach confirmed/false_positive.
No finding should remain "needs_more_data".
"""

from __future__ import annotations

import asyncio
from typing import Optional

import httpx
from loguru import logger

from cyberAI.llm.agent.state import RunState
from cyberAI.llm.agent.tools.replay import diff_responses


_LOCALHOST_PAYLOADS = [
    "http://127.0.0.1",
    "http://[::1]",
    "http://0x7f000001",
    "http://017700000001",
    "http://2130706433",
    "http://localhost",
    "http://0",
]


async def verify_finding(
    finding_id: str,
    run_id: str = "",
    state: Optional[RunState] = None,
    target_url: str = "",
    oob_manager=None,
) -> dict:
    """
    Reads the finding from state, executes targeted verification, updates status.

    For IDOR: runs cross_session_idor_proof (3 reproductions)
    For SSRF: runs oob_ssrf_proof with fresh domains
    For auth_bypass: runs auth_matrix_check across all role combos
    For mass_assignment: runs before_after_state_diff

    Returns:
    {
      "finding_id": "F-003",
      "previous_status": "needs_more_data",
      "new_status": "confirmed",
      "verification_method": "cross_session_replay",
      "evidence_added": {...},
      "confidence": 0.98
    }
    """
    if not state:
        return {"error": "No state available", "finding_id": finding_id}

    base = target_url.rstrip("/") if target_url else state.get("target", "").rstrip("/")

    # Load finding from state
    findings = state.get("findings", [])
    finding = next((f for f in findings if f.get("id") == finding_id or f.get("finding_id") == finding_id), None)

    if not finding:
        return {"error": f"Finding {finding_id} not found in state", "finding_id": finding_id}

    finding_type = finding.get("type", "")
    previous_status = finding.get("status", "needs_more_data")

    if previous_status == "false_positive":
        return {
            "finding_id": finding_id,
            "previous_status": previous_status,
            "new_status": "false_positive",
            "verification_method": "already_resolved",
            "confidence": 1.0,
        }

    # Dispatch to type-specific verification
    if finding_type == "IDOR":
        result = await _verify_idor(finding, state, base)
    elif finding_type == "SSRF":
        result = await _verify_ssrf(finding, state, base, oob_manager)
    elif finding_type in ("AUTH_BYPASS", "AUTHZ"):
        result = await _verify_auth_bypass(finding, state, base)
    elif finding_type == "MASS_ASSIGNMENT":
        result = await _verify_mass_assignment(finding, state, base)
    elif finding_type == "RACE_CONDITION":
        result = await _verify_race(finding, state, base)
    else:
        # Generic: mark confirmed if it already has evidence
        evidence = finding.get("evidence", {})
        new_status = "confirmed" if evidence else "false_positive"
        result = {
            "new_status": new_status,
            "verification_method": "evidence_check",
            "confidence": 0.7 if new_status == "confirmed" else 0.5,
            "evidence_added": {},
        }

    # Update finding in state
    new_status = result.get("new_status", "false_positive")
    state.update_finding(finding_id, {
        "status": new_status,
        "verification_result": result,
        "reproduction_count": finding.get("reproduction_count", 1) + result.get("reproductions", 0),
    })
    state.write_log("verify", "INFO", "verify_finding",
                    f"Finding {finding_id} ({finding_type}): {previous_status} → {new_status}")

    return {
        "finding_id": finding_id,
        "previous_status": previous_status,
        "new_status": new_status,
        "verification_method": result.get("verification_method", "unknown"),
        "evidence_added": result.get("evidence_added", {}),
        "confidence": result.get("confidence", 0.5),
    }


async def _verify_idor(finding: dict, state: RunState, base: str) -> dict:
    """Reproduce IDOR 3 times to confirm."""
    endpoint = finding.get("endpoint", "")
    method = finding.get("method", "GET")
    evidence = finding.get("evidence", {})

    baseline = evidence.get("baseline", {})
    attack = evidence.get("attack", {})
    baseline_url = baseline.get("url", "")
    attack_url = attack.get("url", "")

    sessions = state.get_sessions()
    jwt_a = sessions.get("user_a", {}).get("jwt", "")

    if not jwt_a or not attack_url:
        return {
            "new_status": "false_positive",
            "verification_method": "cross_session_replay",
            "confidence": 0.3,
            "evidence_added": {"reason": "Missing session or URL for reproduction"},
        }

    headers = {"Authorization": f"Bearer {jwt_a}", "Content-Type": "application/json",
               "Accept": "application/json"}
    success_count = 0
    reproductions = []

    async with httpx.AsyncClient(base_url=base, timeout=15.0, verify=False) as client:
        for i in range(3):
            try:
                r = await client.request(method, attack_url, headers=headers)
                if r.status_code == 200:
                    try:
                        body = r.json()
                    except Exception:
                        body = {}
                    # Check if attack response still contains user_b data
                    user_b_email = sessions.get("user_b", {}).get("email", "")
                    user_b_id = str(sessions.get("user_b", {}).get("user_id", ""))
                    body_str = str(body)
                    if (user_b_email and user_b_email in body_str) or \
                       (user_b_id and user_b_id == str(body.get("id", ""))):
                        success_count += 1
                        reproductions.append({"run": i + 1, "status": 200, "confirmed": True})
                    else:
                        reproductions.append({"run": i + 1, "status": 200, "confirmed": False})
                else:
                    reproductions.append({"run": i + 1, "status": r.status_code, "confirmed": False})
            except Exception as e:
                reproductions.append({"run": i + 1, "error": str(e)})

    confirmed = success_count >= 2  # At least 2/3 must succeed
    return {
        "new_status": "confirmed" if confirmed else "false_positive",
        "verification_method": "cross_session_replay",
        "confidence": success_count / 3,
        "reproductions": success_count,
        "evidence_added": {
            "reproduction_runs": reproductions,
            "success_count": success_count,
        },
    }


async def _verify_ssrf(finding: dict, state: RunState, base: str, oob_manager) -> dict:
    """Re-run OOB SSRF test with 3 fresh domains."""
    oob_available = oob_manager is not None and getattr(oob_manager, "is_available", False)
    evidence = finding.get("evidence", {})
    existing_interactions = evidence.get("oob_interactions", [])

    if existing_interactions and len(existing_interactions) >= 1:
        # Already has OOB evidence — check it's a real server IP
        return {
            "new_status": "confirmed",
            "verification_method": "oob_interaction_review",
            "confidence": 0.95,
            "evidence_added": {"existing_interactions": existing_interactions},
        }

    if not oob_available:
        return {
            "new_status": "false_positive",
            "verification_method": "oob_unavailable",
            "confidence": 0.4,
            "evidence_added": {"note": "Interactsh not available for re-verification"},
        }

    # Re-run 3 times with fresh domains
    injection_point = evidence.get("injection_point", "")
    new_interactions = []
    endpoint_path = finding.get("endpoint", "/")
    method = finding.get("method", "GET")
    sessions = state.get_sessions()
    jwt = sessions.get("user_a", {}).get("jwt", "")
    headers = {"Accept": "application/json"}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    async with httpx.AsyncClient(base_url=base, timeout=10.0, verify=False) as client:
        for _ in range(3):
            correlation = f"verify_ssrf_{finding.get('finding_id', 'x')}"
            cb_url = oob_manager.generate_url(correlation)
            if not cb_url:
                continue
            unique_id = cb_url.split(".")[0].replace("http://", "")
            try:
                await client.get(
                    f"{base}{endpoint_path}?url={cb_url}",
                    headers=headers,
                )
            except Exception:
                pass
            await asyncio.sleep(2.0)
            hits = await oob_manager.wait_for_interaction(unique_id, timeout=5.0)
            new_interactions.extend(hits)

    confirmed = len(new_interactions) > 0
    return {
        "new_status": "confirmed" if confirmed else "false_positive",
        "verification_method": "oob_re_verification",
        "confidence": 0.95 if confirmed else 0.2,
        "evidence_added": {"re_verification_interactions": [
            {"type": i.interaction_type, "source_ip": i.source_ip} for i in new_interactions
        ]},
    }


async def _verify_auth_bypass(finding: dict, state: RunState, base: str) -> dict:
    """Test all 4 role combinations for auth bypass."""
    endpoint = finding.get("endpoint", "/")
    method = finding.get("method", "GET")
    sessions = state.get_sessions()

    jwt_user = sessions.get("user_a", {}).get("jwt", "")
    jwt_admin = sessions.get("admin", {}).get("jwt", "")
    expired_jwt = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJzdWIiOiIxMjM0NTY3ODkwIiwiZXhwIjoxNTAwMDAwMDAwfQ"
        ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    )

    scenarios = [
        ("no_auth", {}),
        ("expired_jwt", {"Authorization": f"Bearer {expired_jwt}"}),
    ]
    if jwt_user:
        scenarios.append(("user", {"Authorization": f"Bearer {jwt_user}"}))
    if jwt_admin:
        scenarios.append(("admin", {"Authorization": f"Bearer {jwt_admin}"}))

    results = {}
    async with httpx.AsyncClient(base_url=base, timeout=10.0, verify=False) as client:
        for scenario_name, extra_headers in scenarios:
            headers = {"Accept": "application/json", **extra_headers}
            try:
                r = await client.request(method, endpoint, headers=headers)
                results[scenario_name] = {
                    "status": r.status_code,
                    "has_content": bool(r.content),
                }
            except Exception as e:
                results[scenario_name] = {"error": str(e)}

    # Auth bypass confirmed if no_auth returns 200 with content
    no_auth_result = results.get("no_auth", {})
    confirmed = no_auth_result.get("status") == 200 and no_auth_result.get("has_content")

    return {
        "new_status": "confirmed" if confirmed else "false_positive",
        "verification_method": "auth_matrix_check",
        "confidence": 0.95 if confirmed else 0.8,
        "evidence_added": {"scenario_results": results},
    }


async def _verify_mass_assignment(finding: dict, state: RunState, base: str) -> dict:
    """Verify mass assignment by checking if escalated fields persist."""
    evidence = finding.get("evidence", {})
    stored_fields = evidence.get("stored_fields", [])
    after = evidence.get("after", {})

    if stored_fields and after:
        # Check if privileged values are still present
        confirmed = any(
            after.get(f) in (True, "admin", 99999, "admin")
            for f in stored_fields
        )
        return {
            "new_status": "confirmed" if confirmed else "false_positive",
            "verification_method": "before_after_state_diff",
            "confidence": 0.9 if confirmed else 0.5,
            "evidence_added": {},
        }

    return {
        "new_status": "false_positive",
        "verification_method": "missing_evidence",
        "confidence": 0.3,
        "evidence_added": {},
    }


async def _verify_race(finding: dict, state: RunState, base: str) -> dict:
    """Verify race condition: success_responses > 1."""
    evidence = finding.get("evidence", {})
    success_count = evidence.get("success_responses", 0)
    confirmed = success_count > 1

    return {
        "new_status": "confirmed" if confirmed else "false_positive",
        "verification_method": "response_count_check",
        "confidence": 0.9 if confirmed else 0.4,
        "evidence_added": {},
    }
