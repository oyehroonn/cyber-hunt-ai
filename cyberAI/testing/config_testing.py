"""
Step 18.17: Config Testing - Test security configuration weaknesses.
"""

from typing import Optional
from cyberAI.config import get_config
from cyberAI.models import Finding, Severity, TestCategory, TestPlan
from cyberAI.utils.helpers import generate_run_id, load_json


class ConfigTester:
    """Tests security configuration weaknesses."""
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._findings: list[Finding] = []
    
    async def analyze_security_controls(self) -> list[Finding]:
        """Analyze security_controls.json and flag issues."""
        findings = []
        
        controls_path = self.config.get_output_path("recon", "intelligence", "security_controls.json")
        data = load_json(controls_path)
        
        if not data or "report" not in data:
            return findings
        
        report = data["report"]
        
        if report.get("missing_controls"):
            for control in report["missing_controls"]:
                findings.append(Finding(
                    title=f"Missing security control: {control}",
                    severity=Severity.MEDIUM,
                    category=TestCategory.CONFIG,
                    asset="Security Headers",
                    root_cause=f"Missing {control} header or configuration",
                ))
        
        if report.get("weak_controls"):
            for control in report["weak_controls"]:
                findings.append(Finding(
                    title=f"Weak security control: {control}",
                    severity=Severity.LOW,
                    category=TestCategory.CONFIG,
                    asset="Security Headers",
                    root_cause=f"Weak {control} configuration",
                ))
        
        cors_origins = report.get("cors_origins", [])
        if "*" in cors_origins:
            findings.append(Finding(
                title="CORS allows all origins",
                severity=Severity.MEDIUM,
                category=TestCategory.CONFIG,
                asset="CORS Configuration",
                root_cause="Wildcard CORS origin",
            ))
        
        self._findings.extend(findings)
        return findings
    
    async def run_test(self, plan: TestPlan) -> list[Finding]:
        return await self.analyze_security_controls()
    
    def get_findings(self) -> list[Finding]:
        return self._findings
