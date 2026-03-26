"""
Build a single Markdown file aggregating recon/plan/test/verify/report/agent artifacts for a run_id.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from cyberAI.config import get_config
from cyberAI.utils.helpers import load_json


def _safe_load(path: Path) -> Optional[dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        data = load_json(path)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _meta_matches(data: Optional[dict], run_id: str) -> bool:
    if not data:
        return False
    m = data.get("_meta") or {}
    return str(m.get("run_id", "")) == run_id


def _count_endpoints(master: dict) -> Optional[int]:
    inv = master.get("endpoints")
    if isinstance(inv, list):
        return len(inv)
    ep = load_json(Path(get_config().get_output_path("recon", "intelligence", "endpoint_inventory.json")))
    if isinstance(ep, dict) and isinstance(ep.get("endpoints"), list):
        return len(ep["endpoints"])
    return None


def build_consolidated_markdown(run_id: str) -> str:
    cfg = get_config()
    out_dir = cfg.output_dir

    lines: list[str] = []
    lines.append(f"# Consolidated security assessment report\n")
    lines.append(f"**Run ID:** `{run_id}`  \n")
    lines.append(f"**Generated:** {datetime.utcnow().isoformat()} UTC  \n")
    lines.append("\n---\n")

    # Verified findings (canonical for this run)
    vf_path = out_dir / "verification" / "confirmed" / "verified_findings.json"
    vf = _safe_load(vf_path)
    findings: list[Any] = []
    if vf and _meta_matches(vf, run_id):
        meta = vf.get("_meta") or {}
        target = meta.get("target_url") or "(see findings assets)"
        lines.append("## Engagement metadata\n\n")
        lines.append(f"- **Target (from verification _meta):** {target}\n")
        lines.append(f"- **Verified at:** {meta.get('generated_at', '')}\n")
        findings = list(vf.get("verified_findings") or [])
        lines.append(f"- **Verified findings count:** {len(findings)}\n\n")

        lines.append("## Findings summary (table)\n\n")
        lines.append("| # | Severity | Category | Title | Asset |\n")
        lines.append("|---|----------|----------|-------|-------|\n")
        for i, f in enumerate(findings, 1):
            sev = f.get("severity", "")
            cat = f.get("category", "")
            title = (f.get("title") or "")[:120].replace("|", "\\|")
            asset = (f.get("asset") or "")[:100].replace("|", "\\|")
            lines.append(f"| {i} | {sev} | {cat} | {title} | {asset} |\n")
        lines.append("\n")
    else:
        lines.append("## Verified findings\n\n*(No `verified_findings.json` for this run_id, or meta mismatch.)*\n\n")

    # Severity breakdown (reports/json)
    sb = _safe_load(out_dir / "reports" / "json" / "severity_breakdown.json")
    if sb:
        lines.append("## Severity breakdown (reports/json/severity_breakdown.json)\n\n")
        lines.append("```json\n" + json.dumps(sb, indent=2) + "\n```\n\n")

    # Recon
    mi = _safe_load(out_dir / "recon" / "intelligence" / "master_intel.json")
    if mi and _meta_matches(mi, run_id):
        lines.append("## Reconnaissance\n\n")
        n_routes = len(mi.get("routes") or [])
        n_ep = _count_endpoints(mi)
        ss = mi.get("sensitive_surfaces") or []
        lines.append(f"- **Routes (sample count):** {n_routes}\n")
        if n_ep is not None:
            lines.append(f"- **Endpoints (inventory / master):** {n_ep}\n")
        lines.append(f"- **Sensitive surfaces count:** {len(ss)}\n\n")
    else:
        lines.append("## Reconnaissance\n\n*(master_intel.json missing or different run_id.)*\n\n")

    # Planning
    tp = _safe_load(out_dir / "planning" / "test_plans.json")
    if tp and _meta_matches(tp, run_id):
        plans = tp.get("plans") or []
        lines.append("## Planning\n\n")
        lines.append(f"- **Test plans generated:** {len(plans)}\n\n")
    else:
        lines.append("## Planning\n\n*(test_plans.json missing or run_id mismatch.)*\n\n")

    # Testing / runner
    tf = _safe_load(out_dir / "testing" / "findings" / "all_findings.json")
    rs = _safe_load(out_dir / "testing" / "runner_state.json")
    lines.append("## Testing phase\n\n")
    if tf and _meta_matches(tf, run_id):
        lines.append(f"- **all_findings.json:** run_id matches; findings: {len(tf.get('findings') or [])}\n")
    else:
        lines.append("- **all_findings.json:** older run or mismatch — see **Appendix A** for canonical verified JSON.\n")
    if rs:
        lines.append(f"- **runner_state.json stats:** `{json.dumps(rs.get('stats', {}))}`\n")
    lines.append("\n")

    # Agent memory
    agent_dir = out_dir / "llm" / "agent_memory"
    tr = agent_dir / f"transcript_{run_id}.jsonl"
    sc = agent_dir / f"scratch_{run_id}.jsonl"
    lines.append("## Agent loop (if used)\n\n")
    if tr.is_file():
        tail = tr.read_text(encoding="utf-8", errors="replace")
        if len(tail) > 120000:
            tail = tail[:120000] + "\n\n... [transcript truncated for file size]\n"
        lines.append("### Transcript (`transcript_{run_id}.jsonl`)\n\n")
        lines.append("```\n" + tail + "\n```\n\n")
    else:
        lines.append("*No agent transcript file found for this run_id.*\n\n")
    if sc.is_file():
        lines.append("### Memory scratchpad\n\n```\n" + sc.read_text(encoding="utf-8", errors="replace")[:50000] + "\n```\n\n")

    # Logs index
    log_dir = out_dir / "logs"
    lines.append("## Log files for this run\n\n")
    if log_dir.is_dir():
        matched = sorted(log_dir.glob(f"*{run_id}*"))
        if matched:
            for p in matched:
                lines.append(f"- `{p.relative_to(out_dir)}` ({p.stat().st_size} bytes)\n")
        else:
            lines.append("*(No log files matched this run_id.)*\n")
    else:
        lines.append("*(No logs directory.)*\n")
    lines.append("\n")

    # Appendix: full verified JSON
    if vf and _meta_matches(vf, run_id) and findings:
        lines.append("## Appendix A — Full verified findings (JSON)\n\n")
        lines.append("```json\n")
        lines.append(json.dumps(vf, indent=2, default=str)[:500000])
        lines.append("\n```\n")

    lines.append("\n---\n*End of consolidated report.*\n")
    return "".join(lines)


def write_consolidated_report(run_id: str) -> Path:
    """Write `outputs/reports/markdown/CONSOLIDATED_ASSESSMENT_{run_id}.md`."""
    cfg = get_config()
    md = build_consolidated_markdown(run_id)
    path = cfg.get_output_path("reports", "markdown", f"CONSOLIDATED_ASSESSMENT_{run_id}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md, encoding="utf-8")
    return path


if __name__ == "__main__":
    import sys

    from cyberAI.config import Config

    Config.load()
    rid = sys.argv[1] if len(sys.argv) > 1 else ""
    if not rid:
        print("Usage: python -m cyberAI.reporting.consolidate_run_report <run_id>", file=sys.stderr)
        sys.exit(1)
    p = write_consolidated_report(rid)
    print(p)
