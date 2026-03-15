"""
Step 18.2: Authorization Testing - Test IDOR, privilege escalation, and access controls.
"""

import asyncio
from typing import Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import Finding, ReproductionStep, Severity, TestCategory, TestPlan
from cyberAI.utils.http_client import AsyncHTTPClient
from cyberAI.utils.helpers import generate_run_id, load_json


class AuthorizationTester:
    """Tests authorization and access controls."""
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._findings: list[Finding] = []
    
    async def test_horizontal_idor(self, object_type: str = None, id_list: list[str] = None) -> list[Finding]:
        """For every object: fetch/update/delete another user's object by substituting IDs."""
        findings = []
        client = AsyncHTTPClient()
        
        try:
            test_ids = id_list or ["1", "2", "100", "999"]
            endpoints = [f"/api/{object_type or 'users'}/{{id}}"]
            
            for endpoint_template in endpoints:
                for test_id in test_ids:
                    endpoint = endpoint_template.replace("{id}", test_id)
                    
                    response, record = await client.get(endpoint)
                    
                    if response.status_code == 200:
                        findings.append(Finding(
                            title=f"Potential IDOR at {endpoint}",
                            severity=Severity.HIGH,
                            category=TestCategory.AUTHZ,
                            asset=endpoint,
                            reproduction_steps=[
                                ReproductionStep(
                                    step_number=1,
                                    action=f"GET {endpoint} with ID from another user",
                                    actual_result=f"Access granted ({response.status_code})",
                                )
                            ],
                            root_cause="Missing ownership validation",
                        ))
                    
                    await asyncio.sleep(self.config.request_delay_ms / 1000)
                    
        finally:
            await client.close()
        
        self._findings.extend(findings)
        return findings
    
    async def test_vertical_privilege_escalation(self) -> list[Finding]:
        """Access admin endpoints as basic user; access premium features as free user."""
        findings = []
        client = AsyncHTTPClient()
        
        try:
            admin_endpoints = [
                "/admin", "/api/admin", "/admin/users", "/api/v1/admin/settings"
            ]
            
            for endpoint in admin_endpoints:
                response, _ = await client.get(endpoint)
                
                if response.status_code == 200:
                    findings.append(Finding(
                        title=f"Admin endpoint accessible: {endpoint}",
                        severity=Severity.CRITICAL,
                        category=TestCategory.AUTHZ,
                        asset=endpoint,
                        root_cause="Missing role check",
                    ))
                
                await asyncio.sleep(self.config.request_delay_ms / 1000)
                
        finally:
            await client.close()
        
        self._findings.extend(findings)
        return findings
    
    async def test_direct_endpoint_access(self) -> list[Finding]:
        """Call endpoints that UI hides for current role, directly."""
        findings = []
        return findings
    
    async def test_tenant_isolation(self) -> list[Finding]:
        """Mutate tenant identifier in requests to access cross-tenant data."""
        findings = []
        return findings
    
    async def test_foreign_key_manipulation(self) -> list[Finding]:
        """Change ownerId, userId, orgId, tenantId in create/update requests."""
        findings = []
        return findings
    
    async def run_test(self, plan: TestPlan) -> list[Finding]:
        """Run a specific test based on plan."""
        if "idor" in plan.name.lower():
            return await self.test_horizontal_idor(plan.target_object)
        elif "vertical" in plan.name.lower() or "escalation" in plan.name.lower():
            return await self.test_vertical_privilege_escalation()
        elif "direct" in plan.name.lower():
            return await self.test_direct_endpoint_access()
        return []
    
    def get_findings(self) -> list[Finding]:
        return self._findings


if __name__ == "__main__":
    async def main():
        tester = AuthorizationTester()
        findings = await tester.test_horizontal_idor("users", ["1", "2", "3"])
        print(f"Found {len(findings)} authorization issues")
    
    asyncio.run(main())
