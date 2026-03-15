"""
Step 18.5: Mass Assignment Testing - Test for mass assignment vulnerabilities.
"""

from typing import Optional

from cyberAI.config import get_config
from cyberAI.models import Finding, Severity, TestCategory, TestPlan
from cyberAI.utils.http_client import AsyncHTTPClient
from cyberAI.utils.helpers import generate_run_id


class MassAssignmentTester:
    """Tests for mass assignment vulnerabilities."""
    
    EXTRA_KEYS = [
        "role", "isAdmin", "is_admin", "admin", "ownerId", "owner_id",
        "userId", "user_id", "orgId", "org_id", "tenantId", "tenant_id",
        "plan", "credits", "balance", "approved", "verified", "status",
        "permissions", "scope", "featureFlags", "billingStatus",
    ]
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._findings: list[Finding] = []
    
    def get_extra_keys_inventory(self) -> list[str]:
        """Get all candidate extra fields to test."""
        return self.EXTRA_KEYS
    
    async def test_mass_assignment(self, endpoint: str) -> list[Finding]:
        """Add extra keys to create/update requests."""
        findings = []
        client = AsyncHTTPClient()
        
        try:
            for key in self.EXTRA_KEYS:
                test_payload = {"name": "test", key: True}
                
                response, _ = await client.post(endpoint, json_data=test_payload)
                
                if response.status_code in (200, 201):
                    resp_json = response.json() if response.text else {}
                    if key in str(resp_json):
                        findings.append(Finding(
                            title=f"Mass assignment accepted: {key} at {endpoint}",
                            severity=Severity.HIGH if key in ["role", "isAdmin", "admin"] else Severity.MEDIUM,
                            category=TestCategory.MASS_ASSIGNMENT,
                            asset=endpoint,
                            root_cause="Server accepts and persists undeclared fields",
                        ))
                        
        finally:
            await client.close()
        
        self._findings.extend(findings)
        return findings
    
    async def run_test(self, plan: TestPlan) -> list[Finding]:
        if plan.target_endpoint:
            return await self.test_mass_assignment(plan.target_endpoint)
        return []
    
    def get_findings(self) -> list[Finding]:
        return self._findings
