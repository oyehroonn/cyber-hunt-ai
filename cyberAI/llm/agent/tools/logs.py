"""
Tool 18 — get_phase_logs

Query the SQLite log store for logs from any completed phase.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from cyberAI.llm.agent.state import RunState


def get_phase_logs(
    run_id: str,
    phase: Optional[str] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
    last_n: int = 100,
    state: Optional[RunState] = None,
) -> dict:
    """
    Query the SQLite log store for logs from any completed phase.

    Parameters:
    - phase: "recon", "plan", "test", "verify", "report", or None for all
    - level: "ERROR", "WARNING", "INFO", or None for all
    - search: keyword filter on message text
    - last_n: return only the last N matching lines

    Returns:
    {
      "total_log_lines": 4829,
      "errors": [{"timestamp": "...", "module": "recon.spider", "message": "..."}],
      "warnings": [...],
      "summary": {
        "phases_run": ["recon", "plan"],
        "error_count": 2,
        "warning_count": 7,
        "key_events": [...]
      }
    }
    """
    if not state:
        return {
            "error": "No state available",
            "total_log_lines": 0,
            "errors": [],
            "warnings": [],
        }

    logs = state.query_logs(
        phase=phase,
        level=level,
        search=search,
        last_n=last_n,
    )

    errors = [l for l in logs if l.get("level", "").upper() == "ERROR"]
    warnings = [l for l in logs if l.get("level", "").upper() == "WARNING"]

    # Build phase summary from state
    phase_summaries = state.get("phase_summaries", {})
    phases_run = list(phase_summaries.keys())

    # Key events: look for important log messages
    key_events = []
    for log in logs:
        msg = log.get("message", "")
        if any(kw in msg.lower() for kw in (
            "found", "discovered", "confirmed", "crawled", "analyzed",
            "registered", "endpoints", "bundles", "schema"
        )):
            key_events.append(msg[:120])

    return {
        "total_log_lines": len(logs),
        "logs": logs[:last_n],
        "errors": errors[:50],
        "warnings": warnings[:50],
        "summary": {
            "phases_run": phases_run,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "key_events": key_events[:20],
        },
    }
