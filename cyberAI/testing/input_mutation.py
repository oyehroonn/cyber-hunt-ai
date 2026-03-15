"""
Step 18.4: Input Mutation Testing - Test input validation with fuzzing.
"""

import asyncio
from typing import Any, Optional

from cyberAI.config import get_config
from cyberAI.models import Finding, Severity, TestCategory, TestPlan
from cyberAI.utils.http_client import AsyncHTTPClient
from cyberAI.utils.helpers import generate_run_id


class InputMutationTester:
    """Tests input validation with various payloads."""
    
    MUTATION_PAYLOADS = {
        "string": [
            "A" * 65536,
            None,
            True,
            [],
            {},
            "test\x00null",
            "test\r\nHeader: Injected",
            "%s" * 100,
            "test'\"<>",
            "тест",
            "\u202e\u0041\u0042\u0043",
        ],
        "integer": [
            2147483647,
            -2147483648,
            -1,
            0,
            0.5,
            "123",
            [],
            9999999999999999999,
        ],
        "email": [
            "test@test.com\r\nBcc:attacker@x.com",
            "<script>alert(1)</script>@example.com",
            "test@test",
            "a" * 100 + "@example.com",
        ],
        "url": [
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "file:///etc/passwd",
            "http://169.254.169.254/latest/meta-data/",
            "http://localhost:6379/",
            "http://127.0.0.1:22/",
        ],
    }
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._findings: list[Finding] = []
    
    def get_mutation_payloads(self, field_type: str) -> list[Any]:
        """Return payloads for a given field type."""
        return self.MUTATION_PAYLOADS.get(field_type, self.MUTATION_PAYLOADS["string"])
    
    async def mutate_endpoint(self, endpoint: str, role: str = None) -> list[Finding]:
        """Systematically test all fields of an endpoint with payloads."""
        findings = []
        client = AsyncHTTPClient()
        
        try:
            for field_type, payloads in self.MUTATION_PAYLOADS.items():
                for payload in payloads[:5]:
                    response, _ = await client.post(
                        endpoint,
                        json_data={"test_field": payload},
                        record=False,
                    )
                    
                    if response.status_code == 500:
                        findings.append(Finding(
                            title=f"Server error with {field_type} payload at {endpoint}",
                            severity=Severity.MEDIUM,
                            category=TestCategory.INPUT,
                            asset=endpoint,
                            root_cause="Insufficient input validation",
                        ))
                    
                    await asyncio.sleep(self.config.request_delay_ms / 1000)
                    
        finally:
            await client.close()
        
        self._findings.extend(findings)
        return findings
    
    async def run_test(self, plan: TestPlan) -> list[Finding]:
        if plan.target_endpoint:
            return await self.mutate_endpoint(plan.target_endpoint)
        return []
    
    def get_findings(self) -> list[Finding]:
        return self._findings
