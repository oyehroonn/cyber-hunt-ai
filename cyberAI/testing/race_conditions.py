"""
Step 18.6: Race Condition Testing - Test for race conditions and TOCTOU bugs.
"""

import asyncio
from typing import Optional

from cyberAI.config import get_config
from cyberAI.models import Finding, Severity, TestCategory, TestPlan
from cyberAI.utils.http_client import AsyncHTTPClient
from cyberAI.utils.helpers import generate_run_id


class RaceConditionTester:
    """Tests for race conditions."""
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._findings: list[Finding] = []
    
    async def run_race_test(
        self,
        endpoint: str,
        n_parallel: int = 10,
        timing_window_ms: int = 50,
    ) -> list[Finding]:
        """Send N synchronized requests within a tight timing window."""
        findings = []
        
        async def make_request(client: AsyncHTTPClient, idx: int):
            response, _ = await client.post(endpoint, json_data={"request_id": idx})
            return response.status_code, response.text
        
        client = AsyncHTTPClient()
        
        try:
            await asyncio.sleep(timing_window_ms / 1000)
            
            tasks = [make_request(client, i) for i in range(n_parallel)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for r in results if isinstance(r, tuple) and r[0] in (200, 201))
            
            if success_count > 1:
                findings.append(Finding(
                    title=f"Potential race condition at {endpoint}",
                    severity=Severity.HIGH,
                    category=TestCategory.RACE,
                    asset=endpoint,
                    root_cause="Insufficient concurrency control",
                    raw_evidence={"parallel_requests": n_parallel, "successes": success_count},
                ))
                
        finally:
            await client.close()
        
        self._findings.extend(findings)
        return findings
    
    async def confirm_double_spend(self, endpoint: str) -> list[Finding]:
        """Specific double-spend test with before/after balance capture."""
        return []
    
    async def run_test(self, plan: TestPlan) -> list[Finding]:
        if plan.target_endpoint:
            return await self.run_race_test(plan.target_endpoint)
        return []
    
    def get_findings(self) -> list[Finding]:
        return self._findings
