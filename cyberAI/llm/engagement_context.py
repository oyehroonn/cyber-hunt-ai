"""
Structured engagement context for LLM orchestration and RAG prompts.
Target-agnostic: summarizes recon, plans, runner stats, and key file paths.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from cyberAI.config import get_config
from cyberAI.utils.helpers import load_json


def _safe_len(obj: Any) -> int:
    if obj is None:
        return 0
    if isinstance(obj, list):
        return len(obj)
    if isinstance(obj, dict):
        return len(obj)
    return 0


def _read_json(path: Path, max_depth_keys: int = 12) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = load_json(path)
    if not isinstance(data, dict):
        return {"_raw_type": type(data).__name__}
    # Shallow copy with truncated lists for LLM
    out: dict[str, Any] = {}
    for i, (k, v) in enumerate(data.items()):
        if i >= max_depth_keys:
            out["_truncated_keys"] = True
            break
        if k == "endpoints" and isinstance(v, list):
            out[k] = {
                "count": len(v),
                "sample": v[:5],
            }
        elif k == "routes" and isinstance(v, list):
            out[k] = {"count": len(v), "sample": [r.get("url") for r in v[:5] if isinstance(r, dict)]}
        elif k == "findings" and isinstance(v, list):
            out[k] = {"count": len(v), "sample_titles": [f.get("title") for f in v[:8] if isinstance(f, dict)]}
        elif isinstance(v, (list, dict)) and _safe_len(v) > 20:
            out[k] = f"<{type(v).__name__} len={_safe_len(v)}>"
        else:
            out[k] = v
    return out


def build_engagement_context(
    run_id: str,
    phase: str,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build a single JSON-serializable context object for the LLM.
    """
    config = get_config()
    base = (config.target_url or "").rstrip("/")
    out: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "phase": phase,
        "target_url": config.target_url,
        "config": {
            "llm_enabled": config.llm_enabled,
            "llm_orchestration_enabled": config.llm_orchestration_enabled,
            "confirmed_tests_enabled": config.confirmed_tests_enabled,
            "roles_configured": [a.role for a in config.role_accounts],
            "has_webhook_oob": bool(config.webhook_site_uuid),
            "has_auto_register_spec": bool(config.auto_register_spec),
        },
        "pipeline": {
            "phases_order": ["recon", "plan", "test", "verify", "report"],
            "cli_commands": [
                "python -m cyberAI.main recon --target <url> --run-id <id>",
                "python -m cyberAI.main plan --run-id <id>",
                "python -m cyberAI.main test --run-id <id> [--categories confirmed_authz,ssrf_oob,rag,...]",
                "python -m cyberAI.main verify --run-id <id>",
                "python -m cyberAI.main report --run-id <id>",
                "python -m cyberAI.main full --target <url>",
            ],
        },
    }

    intel_path = config.get_output_path("recon", "intelligence", "master_intel.json")
    ep_path = config.get_output_path("recon", "intelligence", "endpoint_inventory.json")
    plans_path = config.get_output_path("planning", "test_plans.json")
    findings_path = config.get_output_path("testing", "findings", "all_findings.json")
    runner_path = config.get_output_path("testing", "runner_state.json")
    verified_path = config.get_output_path("verification", "confirmed", "verified_findings.json")

    out["artifacts"] = {
        "master_intel": str(intel_path),
        "endpoint_inventory": str(ep_path),
        "test_plans": str(plans_path),
        "all_findings": str(findings_path),
        "runner_state": str(runner_path),
        "verified_findings": str(verified_path),
    }

    out["recon_summary"] = _read_json(intel_path)
    inv = load_json(ep_path) if ep_path.is_file() else {}
    if isinstance(inv, dict) and "endpoints" in inv:
        out["endpoint_count"] = len(inv.get("endpoints") or [])
    elif isinstance(inv, list):
        out["endpoint_count"] = len(inv)

    plans = load_json(plans_path) or {}
    if isinstance(plans, dict) and "plans" in plans:
        out["plan_count"] = len(plans.get("plans") or [])

    findings_data = load_json(findings_path) or {}
    if isinstance(findings_data, dict):
        out["findings_count"] = findings_data.get("total") or len(findings_data.get("findings") or [])

    runner = load_json(runner_path) or {}
    if isinstance(runner, dict):
        out["runner_stats"] = runner.get("stats", runner)

    if extra:
        out["phase_extra"] = extra

    return out


def context_to_prompt_chunk(ctx: dict[str, Any], max_chars: int = 12000) -> str:
    """Serialize context for LLM prompts (truncated)."""
    s = json.dumps(ctx, indent=2, default=str, ensure_ascii=False)
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 20] + "\n... [truncated]"


def build_rag_addon_context(run_id: str) -> str:
    """Short string appended to RAG tester prompts (any target)."""
    ctx = build_engagement_context(run_id, phase="testing")
    lines = [
        f"Run: {ctx.get('run_id')}",
        f"Target: {ctx.get('target_url')}",
        f"Endpoints (inventory): {ctx.get('endpoint_count', 'unknown')}",
        f"Roles: {ctx.get('config', {}).get('roles_configured')}",
        f"OOB webhook configured: {ctx.get('config', {}).get('has_webhook_oob')}",
    ]
    return "\n".join(lines)
