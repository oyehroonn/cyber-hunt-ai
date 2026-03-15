"""Step 20.1: Finding Record - Generate detailed finding write-ups."""
from cyberAI.models import VerifiedFinding

def generate_finding_record(finding: VerifiedFinding) -> str:
    return f"# {finding.title}\n\n**Severity:** {finding.severity.value}\n**Asset:** {finding.asset}"
