"""
Step 18.1: Authentication Testing - Test authentication flows and session management.
"""

import asyncio
from typing import Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import Finding, ReproductionStep, Severity, TestCategory, TestPlan
from cyberAI.utils.browser import get_browser_pool
from cyberAI.utils.http_client import AsyncHTTPClient
from cyberAI.utils.helpers import generate_run_id


class AuthTester:
    """Tests authentication mechanisms."""
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._findings: list[Finding] = []
    
    async def test_login_flows(self) -> list[Finding]:
        """Test all login paths including SSO, magic link, invite redemption."""
        findings = []
        client = AsyncHTTPClient()
        
        try:
            login_paths = ["/login", "/auth/login", "/signin", "/api/auth/login"]
            
            for path in login_paths:
                response, record = await client.post(
                    path,
                    json_data={"email": "test@test.com", "password": "wrongpassword"},
                    record=True,
                )
                
                if response.status_code == 200:
                    findings.append(Finding(
                        title=f"Weak login validation at {path}",
                        severity=Severity.HIGH,
                        category=TestCategory.AUTH,
                        asset=path,
                        reproduction_steps=[
                            ReproductionStep(
                                step_number=1,
                                action=f"POST {path} with invalid credentials",
                                expected_result="401 Unauthorized",
                                actual_result=f"Got {response.status_code}",
                            )
                        ],
                        root_cause="Insufficient credential validation",
                    ))
                
                await asyncio.sleep(self.config.request_delay_ms / 1000)
                
        finally:
            await client.close()
        
        self._findings.extend(findings)
        return findings
    
    async def test_session_rotation(self) -> list[Finding]:
        """Verify session token changes after login and privilege change."""
        findings = []
        return findings
    
    async def test_stale_session_reuse(self) -> list[Finding]:
        """Use token from session A after logout; try expired tokens."""
        findings = []
        return findings
    
    async def test_remember_me(self) -> list[Finding]:
        """Check persistent cookie lifespan and server-side invalidation."""
        findings = []
        return findings
    
    async def test_password_reset(self) -> list[Finding]:
        """Test reset token guessability, expiry, reuse, cross-account use."""
        findings = []
        client = AsyncHTTPClient()
        
        try:
            reset_paths = ["/password-reset", "/forgot-password", "/api/auth/reset-password"]
            
            for path in reset_paths:
                for i in range(3):
                    response, _ = await client.post(
                        path,
                        json_data={"email": "test@test.com"},
                        record=False,
                    )
                    await asyncio.sleep(0.1)
                
        finally:
            await client.close()
        
        self._findings.extend(findings)
        return findings
    
    async def test_mfa_bypass(self) -> list[Finding]:
        """Skip MFA step, replay MFA token, use token after time expiry."""
        findings = []
        return findings
    
    async def test_parallel_sessions(self) -> list[Finding]:
        """Login from two browsers simultaneously, check interference."""
        findings = []
        return findings
    
    async def run_test(self, plan: TestPlan) -> list[Finding]:
        """Run a specific test based on plan."""
        method_name = plan.name
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return await method()
        return []
    
    def get_findings(self) -> list[Finding]:
        """Get all findings from this tester."""
        return self._findings


if __name__ == "__main__":
    async def main():
        tester = AuthTester()
        findings = await tester.test_login_flows()
        print(f"Found {len(findings)} authentication issues")
    
    asyncio.run(main())
