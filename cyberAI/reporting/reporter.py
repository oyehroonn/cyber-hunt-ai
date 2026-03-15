"""
Step 20: Report Generator - Orchestrates report generation.
Creates executive summaries, engineering handoffs, and detailed findings.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from jinja2 import Environment, FileSystemLoader
from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import (
    PatternCluster,
    RemediationItem,
    Report,
    VerifiedFinding,
)
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    atomic_write_text,
    generate_run_id,
    load_json,
)


class ReportGenerator:
    """
    Generates comprehensive security assessment reports.
    """
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._findings: list[VerifiedFinding] = []
        self._report: Optional[Report] = None
        
        template_dir = Path(__file__).parent / "templates"
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=False,
        )
    
    def load_verified_findings(self) -> list[VerifiedFinding]:
        """Load verified findings."""
        findings_path = self.config.get_output_path(
            "verification", "confirmed", "verified_findings.json"
        )
        data = load_json(findings_path)
        
        if data and "verified_findings" in data:
            self._findings = [VerifiedFinding(**f) for f in data["verified_findings"]]
        
        return self._findings
    
    def _cluster_by_pattern(self) -> list[PatternCluster]:
        """Group findings by common root cause."""
        clusters: dict[str, PatternCluster] = {}
        
        for finding in self._findings:
            root_cause = finding.root_cause or finding.category.value
            
            if root_cause not in clusters:
                clusters[root_cause] = PatternCluster(
                    pattern_name=root_cause,
                    root_cause=root_cause,
                    recommended_fix=f"Address {root_cause} across affected endpoints",
                    fix_complexity="medium",
                )
            
            clusters[root_cause].finding_ids.append(finding.id)
            clusters[root_cause].affected_endpoints.append(finding.asset)
        
        return list(clusters.values())
    
    def _generate_remediation_queue(self) -> list[RemediationItem]:
        """Generate prioritized remediation items."""
        items = []
        
        sorted_findings = sorted(
            self._findings,
            key=lambda f: (
                {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(f.severity.value, 5),
                -f.reliability_score,
            )
        )
        
        for i, finding in enumerate(sorted_findings):
            items.append(RemediationItem(
                finding_id=finding.id,
                priority=i + 1,
                fix_description=f"Fix {finding.title}",
                verification_steps=[s.action for s in finding.reproduction_steps[:3]],
                estimated_effort="hours" if finding.severity.value in ("low", "info") else "days",
            ))
        
        return items
    
    def _generate_severity_breakdown(self) -> dict[str, int]:
        """Generate severity breakdown."""
        breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for finding in self._findings:
            sev = finding.severity.value
            if sev in breakdown:
                breakdown[sev] += 1
        
        return breakdown
    
    def generate_report(self) -> Report:
        """Generate the complete report."""
        if not self._findings:
            self.load_verified_findings()
        
        pattern_clusters = self._cluster_by_pattern()
        remediation_queue = self._generate_remediation_queue()
        severity_breakdown = self._generate_severity_breakdown()
        
        executive_summary = self._render_executive_summary()
        engineering_pack = self._render_engineering_handoff()
        
        self._report = Report(
            target_url=self.config.target_url,
            run_id=self.run_id,
            findings=self._findings,
            executive_summary=executive_summary,
            engineering_pack=engineering_pack,
            pattern_clusters=pattern_clusters,
            remediation_queue=remediation_queue,
            total_endpoints_tested=0,
            total_tests_run=0,
            severity_breakdown=severity_breakdown,
        )
        
        return self._report
    
    def _render_executive_summary(self) -> str:
        """Render executive summary from template."""
        try:
            template = self._jinja_env.get_template("executive_summary.md.j2")
            return template.render(
                findings=self._findings,
                severity_breakdown=self._generate_severity_breakdown(),
                target_url=self.config.target_url,
                generated_at=datetime.utcnow().isoformat(),
            )
        except Exception as e:
            logger.warning(f"Template rendering failed: {e}")
            return self._generate_executive_summary_fallback()
    
    def _generate_executive_summary_fallback(self) -> str:
        """Generate executive summary without template."""
        breakdown = self._generate_severity_breakdown()
        
        lines = [
            "# Executive Summary",
            "",
            f"**Target:** {self.config.target_url}",
            f"**Assessment Date:** {datetime.utcnow().strftime('%Y-%m-%d')}",
            "",
            "## Key Findings",
            "",
            f"- **Critical:** {breakdown['critical']}",
            f"- **High:** {breakdown['high']}",
            f"- **Medium:** {breakdown['medium']}",
            f"- **Low:** {breakdown['low']}",
            f"- **Informational:** {breakdown['info']}",
            "",
            "## Top Risks",
            "",
        ]
        
        critical_high = [f for f in self._findings if f.severity.value in ("critical", "high")]
        for finding in critical_high[:5]:
            lines.append(f"- **{finding.title}** ({finding.severity.value}): {finding.asset}")
        
        return "\n".join(lines)
    
    def _render_engineering_handoff(self) -> str:
        """Render engineering handoff from template."""
        try:
            template = self._jinja_env.get_template("engineering_handoff.md.j2")
            return template.render(
                findings=self._findings,
                target_url=self.config.target_url,
            )
        except Exception as e:
            logger.warning(f"Template rendering failed: {e}")
            return self._generate_engineering_handoff_fallback()
    
    def _generate_engineering_handoff_fallback(self) -> str:
        """Generate engineering handoff without template."""
        lines = [
            "# Engineering Handoff",
            "",
            "## Findings to Address",
            "",
        ]
        
        for finding in self._findings:
            lines.append(f"### {finding.title}")
            lines.append(f"**Severity:** {finding.severity.value}")
            lines.append(f"**Asset:** {finding.asset}")
            lines.append("")
            
            if finding.reproduction_steps:
                lines.append("**Steps to Reproduce:**")
                for step in finding.reproduction_steps:
                    lines.append(f"{step.step_number}. {step.action}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def save_all_outputs(self) -> dict[str, str]:
        """Save all report outputs."""
        if not self._report:
            self.generate_report()
        
        outputs = {}
        
        exec_summary_path = self.config.get_output_path(
            "reports", "markdown", "executive_summary.md"
        )
        atomic_write_text(exec_summary_path, self._report.executive_summary)
        outputs["executive_summary_md"] = str(exec_summary_path)
        
        eng_handoff_path = self.config.get_output_path(
            "reports", "markdown", "engineering_handoff.md"
        )
        atomic_write_text(eng_handoff_path, self._report.engineering_pack)
        outputs["engineering_handoff_md"] = str(eng_handoff_path)
        
        for finding in self._findings:
            finding_path = self.config.get_output_path(
                "reports", "markdown", "findings", f"finding_{finding.id[:8]}.md"
            )
            finding_path.parent.mkdir(parents=True, exist_ok=True)
            finding_md = self._render_finding(finding)
            atomic_write_text(finding_path, finding_md)
        
        all_findings_path = self.config.get_output_path("reports", "json", "all_findings.json")
        atomic_write_json(all_findings_path, add_meta_to_output(
            {"findings": [f.model_dump() for f in self._findings]},
            target_url=self.config.target_url, phase="reporting", run_id=self.run_id
        ))
        outputs["all_findings_json"] = str(all_findings_path)
        
        severity_path = self.config.get_output_path("reports", "json", "severity_breakdown.json")
        atomic_write_json(severity_path, self._report.severity_breakdown)
        outputs["severity_breakdown_json"] = str(severity_path)
        
        findings_data = []
        for f in self._findings:
            findings_data.append({
                "id": f.id,
                "title": f.title,
                "severity": f.severity.value,
                "affected_asset": f.asset,
                "affected_roles": ",".join(f.affected_roles),
                "preconditions": ",".join(f.preconditions),
                "reliability_score": f.reliability_score,
                "impact_type": ",".join([i.value for i in f.impact_types]),
                "confirmed": f.status.value if hasattr(f, 'status') else "unknown",
            })
        
        df = pd.DataFrame(findings_data)
        csv_path = self.config.get_output_path("reports", "csv", "findings.csv")
        df.to_csv(csv_path, index=False)
        outputs["findings_csv"] = str(csv_path)
        
        txt_summary_path = self.config.get_output_path("reports", "txt", "executive_summary.txt")
        txt_content = self._report.executive_summary.replace("**", "").replace("#", "").replace("*", "")
        atomic_write_text(txt_summary_path, txt_content)
        outputs["executive_summary_txt"] = str(txt_summary_path)
        
        remediation_path = self.config.get_output_path("reports", "txt", "remediation_queue.txt")
        remediation_lines = ["Remediation Queue\n" + "=" * 50 + "\n"]
        for item in self._report.remediation_queue:
            remediation_lines.append(f"{item.priority}. {item.fix_description}")
        atomic_write_text(remediation_path, "\n".join(remediation_lines))
        outputs["remediation_queue_txt"] = str(remediation_path)
        
        logger.info(f"Generated {len(outputs)} report files")
        
        return outputs
    
    def _render_finding(self, finding: VerifiedFinding) -> str:
        """Render a single finding to markdown."""
        try:
            template = self._jinja_env.get_template("finding.md.j2")
            return template.render(finding=finding)
        except Exception:
            lines = [
                f"# {finding.title}",
                "",
                f"**Severity:** {finding.severity.value}",
                f"**Asset:** {finding.asset}",
                f"**Category:** {finding.category.value}",
                "",
                "## Reproduction Steps",
                "",
            ]
            for step in finding.reproduction_steps:
                lines.append(f"{step.step_number}. {step.action}")
            
            return "\n".join(lines)


async def run_report_generation(run_id: Optional[str] = None) -> ReportGenerator:
    """Run report generation."""
    generator = ReportGenerator(run_id=run_id)
    generator.load_verified_findings()
    generator.generate_report()
    generator.save_all_outputs()
    return generator


if __name__ == "__main__":
    async def main():
        generator = ReportGenerator()
        generator.load_verified_findings()
        generator.generate_report()
        outputs = generator.save_all_outputs()
        
        print("Generated reports:")
        for name, path in outputs.items():
            print(f"  {name}: {path}")
    
    asyncio.run(main())
