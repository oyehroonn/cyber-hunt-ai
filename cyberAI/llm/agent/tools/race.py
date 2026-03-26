"""
Tool 12 — test_race_condition

Detect race condition vulnerabilities by sending N identical state-changing
requests simultaneously and checking for multiple successes.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Optional

import httpx
from loguru import logger

from cyberAI.llm.agent.state import RunState


async def test_race_condition(
    endpoint: dict,
    payload: dict,
    num_concurrent: int = 25,
    window_ms: float = 50.0,
    session_name: str = "user_a",
    run_id: str = "",
    state: Optional[RunState] = None,
    target_url: str = "",
) -> dict:
    """
    Creates N HTTP clients, pre-stages requests, releases all simultaneously.
    Monitors for: multiple 200 responses to a state-change that should only
    allow one (e.g., coupon redemption, limited-use tokens, inventory decrement).

    Returns:
    {
      "requests_sent": 25,
      "success_responses": 14,   # should be 1 if no race condition
      "confirmed_race": true,
      "state_after": {"balance": 420.00},
      "finding_id": "F-007"
    }
    """
    base = target_url.rstrip("/") if target_url else (
        state.get("target", "").rstrip("/") if state else ""
    )

    sessions = state.get_sessions() if state else {}
    sess = sessions.get(session_name, {})
    jwt = sess.get("jwt", "")

    path = endpoint.get("path", "/")
    method = (endpoint.get("methods") or ["POST"])[0].upper()

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    # Pre-create all clients to minimize setup time during the race
    clients: list[httpx.AsyncClient] = []
    for _ in range(num_concurrent):
        clients.append(httpx.AsyncClient(base_url=base, timeout=15.0, verify=False))

    responses: list[dict] = []
    start_barrier = asyncio.Event()

    async def fire(client: httpx.AsyncClient, idx: int) -> None:
        # Wait for the release signal (tight window)
        await start_barrier.wait()
        try:
            r = await client.request(method, path, json=payload, headers=headers)
            responses.append({
                "idx": idx,
                "status": r.status_code,
                "body": r.text[:500] if r.content else "",
            })
        except Exception as e:
            responses.append({"idx": idx, "status": -1, "error": str(e)})

    # Launch all tasks but hold at barrier
    tasks = [asyncio.create_task(fire(c, i)) for i, c in enumerate(clients)]

    # Release all simultaneously within window_ms
    await asyncio.sleep(0.01)  # tiny warm-up
    start_barrier.set()

    # Wait for all to complete
    await asyncio.gather(*tasks, return_exceptions=True)

    # Clean up clients
    for c in clients:
        await c.aclose()

    # Analyze
    success_count = sum(1 for r in responses if r.get("status") in (200, 201))
    error_count = sum(1 for r in responses if r.get("status") == -1)

    # A race condition exists if more than 1 request succeeded on a
    # state-changing operation that should be atomic/idempotent
    confirmed_race = success_count > 1 and method in ("POST", "PUT", "PATCH", "DELETE")

    # Try to get state after
    state_after: dict = {}
    if jwt:
        try:
            async with httpx.AsyncClient(base_url=base, timeout=10.0, verify=False) as verify_client:
                r_check = await verify_client.get(
                    path.split("?")[0],
                    headers={"Authorization": f"Bearer {jwt}", "Accept": "application/json"},
                )
                if r_check.status_code == 200 and r_check.content:
                    try:
                        state_after = r_check.json()
                    except Exception:
                        pass
        except Exception:
            pass

    finding_id = ""
    if confirmed_race and state:
        fdata = {
            "type": "RACE_CONDITION",
            "subtype": "concurrent_state_change",
            "title": f"Race Condition on {method} {path} — {success_count}/{num_concurrent} concurrent requests succeeded",
            "endpoint": path,
            "method": method,
            "severity": "high",
            "cvss_score": 7.5,
            "cvss_vector": "CVSS:3.1/AV:N/AC:H/PR:L/UI:N/S:U/C:H/I:H/A:N",
            "owasp_category": "A04:2021 Insecure Design",
            "cwe_id": "CWE-362",
            "status": "confirmed",
            "reproduction_count": 1,
            "evidence": {
                "requests_sent": num_concurrent,
                "success_responses": success_count,
                "response_statuses": [r["status"] for r in responses],
                "payload": payload,
                "state_after": state_after,
                "window_ms": window_ms,
            },
            "remediation": (
                f"Implement optimistic locking or database-level atomic transactions for {method} {path}. "
                "Use SELECT FOR UPDATE or equivalent to prevent concurrent state modification."
            ),
            "run_id": run_id,
            "target": base,
        }
        finding_id = state.add_finding(fdata)
        state.write_log("test", "WARNING", "test_race_condition",
                        f"CONFIRMED race on {path}: {success_count}/{num_concurrent} succeeded")
        logger.warning(f"test_race_condition: CONFIRMED on {path} ({success_count}/{num_concurrent})")

    return {
        "requests_sent": num_concurrent,
        "success_responses": success_count,
        "error_responses": error_count,
        "confirmed_race": confirmed_race,
        "state_after": state_after,
        "finding_id": finding_id,
        "response_distribution": {str(r.get("status")): 0 for r in responses},
    }
