"""Step 20.7: Priority Ranking."""
from cyberAI.models import VerifiedFinding

def rank_by_priority(findings: list[VerifiedFinding]) -> list[VerifiedFinding]:
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    return sorted(findings, key=lambda f: (severity_order.get(f.severity.value, 5), -f.reliability_score))
