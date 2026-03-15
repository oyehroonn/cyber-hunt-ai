"""Step 20.4: Evidence Pack."""
from cyberAI.models import VerifiedFinding

def generate_evidence_pack(finding: VerifiedFinding) -> dict:
    return {"screenshots": [], "requests": finding.request_proof, "state_diff": {"before": finding.before_state, "after": finding.after_state}}
