"""Step 20.8: Executive Summary."""
from cyberAI.models import VerifiedFinding

def generate_executive_summary(findings: list[VerifiedFinding]) -> str:
    critical = len([f for f in findings if f.severity.value == "critical"])
    high = len([f for f in findings if f.severity.value == "high"])
    return f"# Executive Summary\n\nDiscovered {len(findings)} vulnerabilities: {critical} critical, {high} high severity."
