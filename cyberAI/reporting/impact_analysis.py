"""Step 20.2: Impact Analysis."""
from cyberAI.models import VerifiedFinding

def analyze_impact(finding: VerifiedFinding) -> dict:
    return {"scope": finding.breadth or "unknown", "impact_types": [i.value for i in finding.impact_types]}
