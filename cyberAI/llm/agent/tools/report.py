"""
Tool 19 — write_report

Generate the final report from all stored findings, evidence, and phase logs.
Produces markdown, JSON, and CSV outputs.
"""

from __future__ import annotations

import csv
import io
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from cyberAI.llm.agent.state import RunState


_OWASP_REFS = {
    "IDOR": "OWASP WSTG-ATHZ-04, API1:2023 Broken Object Level Authorization",
    "SSRF": "OWASP A10:2021 Server-Side Request Forgery, CWE-918",
    "AUTH_BYPASS": "OWASP A07:2021 Identification and Authentication Failures",
    "MASS_ASSIGNMENT": "OWASP API6:2023 Unrestricted Access to Sensitive Business Flows",
    "RACE_CONDITION": "OWASP A04:2021 Insecure Design, CWE-362",
    "SQLI": "OWASP A03:2021 Injection, CWE-89",
}


async def write_report(
    run_id: str,
    formats: Optional[list[str]] = None,
    include_raw_evidence: bool = True,
    executive_summary: bool = True,
    state: Optional[RunState] = None,
    target_url: str = "",
    output_dir: str = "outputs",
) -> dict:
    """
    Reads all findings, evidence, session data, endpoint inventory, and phase logs.
    Generates executive summary, technical findings, appendices.

    Returns: {"reports_written": ["output/run_id_report.md", "output/run_id_findings.json"]}
    """
    formats = formats or ["markdown", "json", "csv"]

    base = target_url.rstrip("/") if target_url else (
        state.get("target", "").rstrip("/") if state else "Unknown Target"
    )

    if not state:
        return {"error": "No state available", "reports_written": []}

    findings = state.get_findings()
    confirmed = [f for f in findings if f.get("status") == "confirmed"]
    false_positives = [f for f in findings if f.get("status") == "false_positive"]
    endpoints = state.get_endpoints()
    sessions = state.get_sessions()

    # Severity counts
    sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in confirmed:
        sev = f.get("severity", "info").lower()
        sev_counts[sev] = sev_counts.get(sev, 0) + 1

    # Overall risk score
    risk_score = sum(
        f.get("cvss_score", 0) * {"critical": 1.0, "high": 0.7, "medium": 0.4, "low": 0.2, "info": 0.1}.get(
            f.get("severity", "info"), 0.1)
        for f in confirmed
    )

    timestamp = datetime.utcnow().isoformat() + "Z"
    reports_written: list[str] = []

    # Ensure output directory exists
    report_dir = Path(output_dir) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    # ----- MARKDOWN -----
    if "markdown" in formats:
        md = _build_markdown(
            run_id=run_id,
            target=base,
            timestamp=timestamp,
            confirmed=confirmed,
            false_positives=false_positives,
            endpoints=endpoints,
            sessions=sessions,
            sev_counts=sev_counts,
            risk_score=risk_score,
            include_raw_evidence=include_raw_evidence,
            state=state,
        )
        md_path = report_dir / "markdown" / f"{run_id}_report.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md, encoding="utf-8")
        reports_written.append(str(md_path))
        logger.info(f"write_report: markdown written to {md_path}")

    # ----- JSON -----
    if "json" in formats:
        report_data = {
            "run_id": run_id,
            "target": base,
            "timestamp": timestamp,
            "severity_counts": sev_counts,
            "risk_score": round(risk_score, 1),
            "confirmed_findings": confirmed,
            "false_positives": false_positives,
            "endpoint_count": len(endpoints),
            "sessions_used": list(sessions.keys()),
        }
        json_path = report_dir / "json" / f"{run_id}_findings.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
        reports_written.append(str(json_path))

    # ----- CSV -----
    if "csv" in formats:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "finding_id", "type", "severity", "cvss_score", "title",
            "endpoint", "method", "owasp_category", "cwe_id", "status",
        ])
        writer.writeheader()
        for f in confirmed:
            writer.writerow({
                "finding_id": f.get("finding_id", ""),
                "type": f.get("type", ""),
                "severity": f.get("severity", ""),
                "cvss_score": f.get("cvss_score", ""),
                "title": f.get("title", ""),
                "endpoint": f.get("endpoint", ""),
                "method": f.get("method", ""),
                "owasp_category": f.get("owasp_category", ""),
                "cwe_id": f.get("cwe_id", ""),
                "status": f.get("status", ""),
            })
        csv_path = report_dir / "csv" / f"{run_id}_findings.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_text(output.getvalue(), encoding="utf-8")
        reports_written.append(str(csv_path))

    if state:
        state.write_log("report", "INFO", "write_report",
                        f"Report written: {len(confirmed)} confirmed findings, {len(reports_written)} files")

    return {
        "reports_written": reports_written,
        "confirmed_findings": len(confirmed),
        "severity_counts": sev_counts,
        "risk_score": round(risk_score, 1),
    }


def _build_markdown(
    run_id: str,
    target: str,
    timestamp: str,
    confirmed: list,
    false_positives: list,
    endpoints: list,
    sessions: dict,
    sev_counts: dict,
    risk_score: float,
    include_raw_evidence: bool,
    state: RunState,
) -> str:
    lines = []

    # Title
    lines.append(f"# CyberHunt AI — Security Assessment Report")
    lines.append(f"")
    lines.append(f"**Target:** {target}")
    lines.append(f"**Run ID:** {run_id}")
    lines.append(f"**Date:** {timestamp[:10]}")
    lines.append(f"**Generated by:** CyberHunt AI v2")
    lines.append("")

    # Executive Summary
    lines.append("---")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    for sev in ("critical", "high", "medium", "low", "info"):
        if sev_counts.get(sev, 0) > 0:
            lines.append(f"| {sev.capitalize()} | {sev_counts[sev]} |")
    lines.append("")
    lines.append(f"**Overall Risk Score:** {round(risk_score, 1)}")
    lines.append("")

    # Top 3 critical
    top_critical = [f for f in confirmed if f.get("severity") in ("critical", "high")][:3]
    if top_critical:
        lines.append("**Top Findings:**")
        for f in top_critical:
            lines.append(f"- **{f.get('severity', '').upper()}** [{f.get('type')}] {f.get('title', '')}")
        lines.append("")

    # Recommended actions
    lines.append("**Recommended Immediate Actions:**")
    action_map = {
        "IDOR": "Implement object ownership checks — verify request.user.id === requested_id",
        "SSRF": "Whitelist allowed URL schemes/hosts, block RFC 1918 addresses",
        "AUTH_BYPASS": "Add authentication middleware to all non-public endpoints",
        "MASS_ASSIGNMENT": "Use field allowlists in PUT/PATCH handlers",
        "SQLI": "Replace string concatenation with parameterized queries",
    }
    seen_types = set()
    for f in confirmed:
        t = f.get("type", "")
        if t not in seen_types and t in action_map:
            lines.append(f"- {action_map[t]}")
            seen_types.add(t)
    lines.append("")

    # Methodology
    lines.append("---")
    lines.append("")
    lines.append("## 2. Methodology")
    lines.append("")
    lines.append(f"- **Endpoints Discovered:** {len(endpoints)}")
    lines.append(f"- **Sessions Used:** {', '.join(sessions.keys()) or 'none'}")
    lines.append(f"- **Findings Investigated:** {len(confirmed) + len(false_positives)}")
    lines.append(f"- **Confirmed Findings:** {len(confirmed)}")
    lines.append(f"- **False Positives Cleared:** {len(false_positives)}")
    lines.append("")
    lines.append("**Tools Used:** auth_register_and_login, crawl_target, analyze_js_bundles, "
                 "fetch_api_schema, discover_endpoints, build_endpoint_inventory, "
                 "analyze_security_headers, test_idor, test_ssrf_oob, test_auth_bypass, "
                 "test_mass_assignment, test_race_condition, test_sqli_blind, "
                 "replay_request_with_variants, diff_responses, verify_finding, "
                 "store_finding, get_phase_logs, write_report, error_retry")
    lines.append("")

    # Technical Findings
    lines.append("---")
    lines.append("")
    lines.append("## 3. Technical Findings")
    lines.append("")

    if not confirmed:
        lines.append("*No confirmed findings for this assessment.*")
        lines.append("")
    else:
        for i, f in enumerate(confirmed, 1):
            fid = f.get("id") or f.get("finding_id") or f"F-{i:03d}"
            severity = f.get("severity", "medium").capitalize()
            ftype = f.get("type", "")
            lines.append(f"### Finding {fid}: {f.get('title', ftype)}")
            lines.append("")
            lines.append(f"**Severity:** {severity} | **CVSS Score:** {f.get('cvss_score', 'N/A')}")
            lines.append(f"**OWASP Category:** {f.get('owasp_category', _OWASP_REFS.get(ftype, 'N/A'))}")
            lines.append(f"**CWE:** {f.get('cwe_id', 'N/A')}")
            lines.append(f"**Endpoint:** `{f.get('method', 'GET')} {f.get('endpoint', '/')}`")
            lines.append(f"**Status:** Confirmed ({f.get('reproduction_count', 1)} reproduction(s))")
            lines.append("")

            lines.append("**Description:**")
            lines.append(f"This {ftype} vulnerability was confirmed on `{f.get('endpoint', '/')}`. "
                         f"See evidence below for full reproduction details.")
            lines.append("")

            # Reproduction steps
            rep_steps = f.get("reproduction_steps", [])
            if rep_steps:
                lines.append("**Reproduction Steps:**")
                for j, step in enumerate(rep_steps, 1):
                    lines.append(f"{j}. {step}")
                lines.append("")

            # Evidence
            if include_raw_evidence and f.get("evidence"):
                evidence = f["evidence"]
                lines.append("**Evidence:**")
                baseline = evidence.get("baseline", {})
                attack = evidence.get("attack", {})
                if baseline.get("request"):
                    lines.append("*Baseline Request:*")
                    lines.append("```http")
                    lines.append(baseline["request"])
                    lines.append("```")
                if attack.get("request"):
                    lines.append("*Attack Request:*")
                    lines.append("```http")
                    lines.append(attack["request"])
                    lines.append("```")
                oob = evidence.get("oob_interactions", [])
                if oob:
                    lines.append(f"*OOB Interactions:* {len(oob)} callback(s) received from target server")
                lines.append("")

            # Remediation
            lines.append(f"**Remediation:**")
            lines.append(f.get("remediation", "See OWASP guidelines."))
            lines.append("")
            lines.append("---")
            lines.append("")

    # Endpoint Inventory Appendix
    lines.append("## 4. Endpoint Inventory")
    lines.append("")
    if endpoints:
        lines.append("| Endpoint | Methods | Risk Score | Priority |")
        lines.append("|----------|---------|------------|----------|")
        for ep in sorted(endpoints, key=lambda x: x.get("risk_score", 0), reverse=True)[:50]:
            methods = ", ".join(ep.get("methods", ["GET"]))
            lines.append(f"| `{ep.get('path', '/')}` | {methods} | "
                         f"{ep.get('risk_score', 'N/A')} | {ep.get('test_priority', 'low')} |")
    lines.append("")

    # False Positives Appendix
    if false_positives:
        lines.append("## 5. Investigated and Cleared (False Positives)")
        lines.append("")
        for f in false_positives:
            lines.append(f"- **{f.get('type', 'Unknown')}** on `{f.get('endpoint', '/')}`: {f.get('title', 'N/A')}")
        lines.append("")

    # Errors and Limitations
    lines.append("## 6. Errors and Limitations")
    lines.append("")
    errors = state.query_logs(level="ERROR", last_n=20)
    if errors:
        lines.append("The following errors occurred during the assessment:")
        for err in errors[:10]:
            lines.append(f"- [{err.get('phase', '?')}] {err.get('message', '')[:120]}")
    else:
        lines.append("No critical errors encountered during the assessment.")
    lines.append("")

    return "\n".join(lines)
