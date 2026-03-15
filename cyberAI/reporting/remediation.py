"""Step 20.6: Remediation."""
from cyberAI.models import VerifiedFinding

def generate_remediation(finding: VerifiedFinding) -> dict:
    return {"fix": f"Fix {finding.title}", "verification": "Re-test after fix", "priority": finding.severity.value}
