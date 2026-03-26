"""
Tool 17 — store_finding

Write a finding (with all evidence) to the structured state and optionally
to the RAG knowledge base for future retrieval.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from cyberAI.llm.agent.state import RunState


_VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}
_VALID_STATUSES = {"confirmed", "false_positive"}


def store_finding(
    finding_type: str,
    severity: str,
    title: str,
    endpoint: str,
    method: str,
    evidence: dict,
    cvss_score: float,
    owasp_category: str,
    cwe_id: str,
    remediation: str,
    run_id: str = "",
    state: Optional[RunState] = None,
    target_url: str = "",
    subtype: str = "",
    cvss_vector: str = "",
    reproduction_steps: Optional[list[str]] = None,
    reproduction_count: int = 1,
) -> str:
    """
    Validate and write a finding to state storage.
    Returns the finding_id (e.g., "F-007").

    Schema enforcement:
    - severity must be: critical, high, medium, low, info
    - status is always set to "confirmed" (only confirmed findings are stored via this tool)
    - Never allows "needs_more_data" as a final status
    """
    # Validate
    severity = severity.lower()
    if severity not in _VALID_SEVERITIES:
        severity = "medium"
        logger.warning(f"store_finding: invalid severity, defaulting to medium")

    base = target_url.rstrip("/") if target_url else (
        state.get("target", "").rstrip("/") if state else ""
    )

    finding_data = {
        "type": finding_type.upper(),
        "subtype": subtype or "",
        "title": title,
        "endpoint": endpoint,
        "method": method.upper(),
        "severity": severity,
        "cvss_score": float(cvss_score),
        "cvss_vector": cvss_vector or _default_cvss_vector(severity),
        "owasp_category": owasp_category,
        "cwe_id": cwe_id,
        "status": "confirmed",  # Only confirmed findings go through store_finding
        "reproduction_count": reproduction_count,
        "evidence": evidence,
        "reproduction_steps": reproduction_steps or [],
        "remediation": remediation,
        "run_id": run_id,
        "target": base,
    }

    finding_id = "F-000"
    if state:
        finding_id = state.add_finding(finding_data)
        state.write_log("test", "INFO", "store_finding",
                        f"Stored {finding_type} finding {finding_id}: {title[:60]} ({severity})")

        # Also write to RAG knowledge base if available
        try:
            _write_to_rag(finding_data, state)
        except Exception as e:
            logger.debug(f"store_finding: RAG write failed (non-fatal): {e}")

    logger.info(f"store_finding: {finding_id} — {finding_type} {severity} on {method} {endpoint}")
    return finding_id


def _default_cvss_vector(severity: str) -> str:
    vectors = {
        "critical": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
        "high": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N",
        "medium": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:L/A:N",
        "low": "CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:N/A:N",
        "info": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
    }
    return vectors.get(severity, vectors["medium"])


def _write_to_rag(finding: dict, state: RunState) -> None:
    """Write finding to ChromaDB RAG knowledge base."""
    try:
        from cyberAI.llm.llm_client import write_finding_to_chroma
        write_finding_to_chroma(finding)
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"_write_to_rag: {e}")
