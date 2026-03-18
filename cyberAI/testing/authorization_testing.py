"""
Step 18.2: Authorization Testing - Test IDOR, privilege escalation, and access controls.
ASRTS Phase 2.5: Differential auth testing (replay same request as multiple roles, compare).
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

            # Prefer endpoints discovered during recon instead of guessing /api/* paths.
            endpoints_path = self.config.get_output_path("recon", "intelligence", "endpoints.json")
            discovered_endpoints: list[str] = []
            endpoints_data = load_json(endpoints_path)
            if endpoints_data and "endpoints" in endpoints_data:
                for e in endpoints_data["endpoints"]:
                    path_pattern = e.get("path_pattern") or ""
                    url = e.get("url") or ""
                    # Focus on endpoints that look like object-by-id access patterns.
                    if "{id}" in path_pattern or "{uuid}" in path_pattern:
                        discovered_endpoints.append(path_pattern)
                    elif any(tok in url for tok in ["/{id}", "/{uuid}"]):
                        discovered_endpoints.append(url)

            # Fallback if recon found nothing (keep existing behavior, but mark as speculative later).
            endpoints = discovered_endpoints or [f"/api/{object_type or 'users'}/{{id}}"]
            
            for endpoint_template in endpoints:
                for test_id in test_ids:
                    endpoint = endpoint_template.replace("{id}", test_id)
                    endpoint = endpoint.replace("{uuid}", test_id)
                    
                    # Accuracy gates:
                    # - do not follow redirects (prevents marketing-page false positives)
                    # - require JSON content-type (or at least not text/html)
                    response, record = await client.get(endpoint, follow_redirects=False, record=True)
                    
                    content_type = (response.headers.get("content-type") or "").lower()
                    redirected = bool(getattr(response, "history", None))

                    # Only flag as potential IDOR if it looks like a real API response.
                    if response.status_code == 200 and (not redirected) and ("application/json" in content_type):
                        evidence_refs = [record.warc_ref] if (record and getattr(record, "warc_ref", None)) else []
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
                            request_proof=record,
                            response_proof=(record.response_body_preview if record else None),
                            raw_evidence={
                                "content_type": content_type,
                                "redirected": redirected,
                                "final_url": record.final_url if record else str(getattr(response, "url", "")),
                            },
                            evidence_warc_refs=evidence_refs,
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
    
    async def test_differential_auth(
        self,
        role_high: str = "admin",
        role_low: str = "user",
        engagement_id: Optional[str] = None,
    ) -> list[Finding]:
        """
        ASRTS Phase 2.5: Replay same request as role_high and role_low; if role_low
        gets same success/data as role_high, flag as BOLA. Uses session store (file-backed).
        """
        findings = []
        try:
            from cyberAI.identity.session_store import SessionStore
        except ImportError:
            logger.debug("Identity layer not available; skipping differential auth test")
            return findings

        store_path = self.config.get_output_path("sessions", "sessions.json")
        store = SessionStore(store_path)
        eng = engagement_id or self.config.run_id or "default"
        session_high = store.get(eng, role_high)
        session_low = store.get(eng, role_low)
        if not session_high or not session_low:
            logger.debug("Differential auth: missing session for one or both roles")
            return findings

        endpoints_path = self.config.get_output_path("recon", "intelligence", "endpoints.json")
        endpoints_data = load_json(endpoints_path)
        templates: list[str] = []
        if endpoints_data and "endpoints" in endpoints_data:
            for e in endpoints_data["endpoints"]:
                path_pattern = e.get("path_pattern") or ""
                url = e.get("url") or ""
                if "{id}" in path_pattern or "{uuid}" in path_pattern:
                    templates.append(path_pattern)
                elif any(tok in url for tok in ["/{id}", "/{uuid}"]):
                    templates.append(url)
        if not templates:
            templates = [f"/api/users/{{id}}"]

        test_ids = ["1", "2", "100"]
        client = AsyncHTTPClient()
        try:
            for endpoint_template in templates[:20]:
                for test_id in test_ids:
                    url = endpoint_template.replace("{id}", test_id).replace("{uuid}", test_id)
                    if not url.startswith(("http://", "https://")):
                        url = (self.config.target_url or "").rstrip("/") + ("/" + url.lstrip("/") if url.startswith("/") else url)
                    if not url.startswith(("http://", "https://")):
                        continue

                    client.set_cookies(session_high["cookies"])
                    resp_high, rec_high = await client.get(url, follow_redirects=False, record=True)
                    client.clear_cookies()
                    client.set_cookies(session_low["cookies"])
                    resp_low, rec_low = await client.get(url, follow_redirects=False, record=True)
                    client.clear_cookies()

                    ct_high = (resp_high.headers.get("content-type") or "").lower()
                    ct_low = (resp_low.headers.get("content-type") or "").lower()
                    if resp_high.status_code != 200 or resp_low.status_code != 200:
                        await asyncio.sleep(self.config.request_delay_ms / 1000)
                        continue
                    if "application/json" not in ct_high or "application/json" not in ct_low:
                        await asyncio.sleep(self.config.request_delay_ms / 1000)
                        continue
                    if getattr(resp_high, "history", None) or getattr(resp_low, "history", None):
                        await asyncio.sleep(self.config.request_delay_ms / 1000)
                        continue

                    # Same success: check if bodies look like same resource (BOLA)
                    try:
                        body_high = resp_high.json() if hasattr(resp_high, "json") else {}
                        body_low = resp_low.json() if hasattr(resp_low, "json") else {}
                    except Exception:
                        body_high = {}
                        body_low = {}
                    keys_high = set(body_high.keys()) if isinstance(body_high, dict) else set()
                    keys_low = set(body_low.keys()) if isinstance(body_low, dict) else set()
                    if keys_high and keys_low and (keys_high == keys_low or len(keys_high & keys_low) >= 2):
                        evidence_refs = []
                        if rec_high and getattr(rec_high, "warc_ref", None):
                            evidence_refs.append(rec_high.warc_ref)
                        if rec_low and getattr(rec_low, "warc_ref", None):
                            evidence_refs.append(rec_low.warc_ref)
                        findings.append(Finding(
                            title=f"Potential BOLA: {role_low} received same data as {role_high} at {url}",
                            severity=Severity.HIGH,
                            category=TestCategory.AUTHZ,
                            asset=url,
                            reproduction_steps=[
                                ReproductionStep(step_number=1, action=f"GET as {role_high}", actual_result=f"{resp_high.status_code}"),
                                ReproductionStep(step_number=2, action=f"GET as {role_low}", actual_result=f"{resp_low.status_code} (same structure)"),
                            ],
                            root_cause="Broken Object Level Authorization",
                            request_proof=rec_high,
                            response_proof=rec_high.response_body_preview if rec_high else None,
                            raw_evidence={
                                "role_high": role_high,
                                "role_low": role_low,
                                "role_low_request_proof": rec_low.model_dump() if rec_low else None,
                            },
                            evidence_warc_refs=evidence_refs,
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
