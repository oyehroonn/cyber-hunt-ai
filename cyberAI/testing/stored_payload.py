"""
Step 18.8: Stored Payload Testing - Test for stored XSS and injection.
"""

from typing import Optional
from cyberAI.config import get_config
from cyberAI.models import Finding, Severity, TestCategory, TestPlan
from cyberAI.utils.http_client import AsyncHTTPClient
from cyberAI.utils.helpers import generate_run_id


class StoredPayloadTester:
    """Tests for stored XSS and injection vulnerabilities."""
    
    PAYLOADS = {
        "xss": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
            "<svg onload=alert(1)>",
        ],
        "template": [
            "{{7*7}}",
            "${7*7}",
            "#{7*7}",
            "<%= 7*7 %>",
        ],
        "markdown": [
            "[click](javascript:alert(1))",
            "![img](x\" onerror=\"alert(1))",
        ],
        "csv": [
            "=CMD|'/C calc'!A0",
            "@SUM(1+1)*cmd|' /C calc'!A0",
        ],
    }
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._findings: list[Finding] = []
        self._seeded_payloads: dict[str, str] = {}
    
    async def seed_payloads_all_fields(self) -> dict[str, str]:
        """Insert test payloads into user-controlled fields."""
        return self._seeded_payloads
    
    async def scan_render_surfaces(self, payload_ids: list[str]) -> list[Finding]:
        """Revisit render surfaces to check for payload execution."""
        return []
    
    async def run_test(self, plan: TestPlan) -> list[Finding]:
        return []
    
    def get_findings(self) -> list[Finding]:
        return self._findings
