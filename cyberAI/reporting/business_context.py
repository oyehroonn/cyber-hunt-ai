"""Step 20.3: Business Context."""
from cyberAI.models import VerifiedFinding

def translate_to_business_context(finding: VerifiedFinding) -> str:
    return f"This vulnerability could allow attackers to {finding.confirmed_impact or 'compromise the system'}."
