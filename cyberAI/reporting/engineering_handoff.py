"""Step 20.9: Engineering Handoff."""
from cyberAI.models import VerifiedFinding

def generate_engineering_handoff(findings: list[VerifiedFinding]) -> str:
    lines = ["# Engineering Handoff\n"]
    for f in findings:
        lines.append(f"## {f.title}\n**Asset:** {f.asset}\n")
    return "\n".join(lines)
