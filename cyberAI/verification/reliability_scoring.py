"""Step 19.11: Reliability Scoring."""
from cyberAI.models import Finding

class ReliabilityScorer:
    async def score_reliability(self, finding: Finding) -> float:
        score = 50.0
        if finding.reproduction_steps:
            score += 20
        if finding.request_proof:
            score += 20
        if finding.before_state and finding.after_state:
            score += 10
        return min(score, 100.0)
