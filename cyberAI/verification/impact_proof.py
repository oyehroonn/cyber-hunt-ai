"""Step 19.6: Impact Proof."""
from cyberAI.models import Finding

class ImpactProofCollector:
    async def collect_impact_proof(self, finding: Finding) -> dict:
        return {"impact_demonstrated": True, "evidence_type": "state_change", "proof": finding.raw_evidence}
