"""Step 19.10: Control Bypass."""
from cyberAI.models import Finding

class ControlBypassConfirmer:
    async def confirm_control_bypass(self, finding: Finding) -> dict:
        return {"bypass_confirmed": False, "control_type": None, "abuse_path": None}
