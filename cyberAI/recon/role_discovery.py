"""
Step 4: Role Discovery - Multi-role crawling and comparison.
Repeats crawl for each configured role and compares access patterns.
"""

import asyncio
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import Endpoint, RoleDiff, Route
from cyberAI.recon.core_discovery import CoreDiscovery
from cyberAI.recon.network_intelligence import NetworkIntelligence
from cyberAI.utils.browser import get_browser_pool
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    generate_run_id,
)


class RoleDiscovery:
    """
    Discovers and compares application behavior across different user roles.
    """
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._role_routes: dict[str, list[Route]] = {}
        self._role_endpoints: dict[str, list[Endpoint]] = {}
        self._role_diffs: list[RoleDiff] = []
        self._permission_hints: dict[str, dict[str, bool]] = {}
    
    async def _login_as_role(self, page, role: str) -> bool:
        """
        Attempt to login as a specific role using configured credentials.
        
        Args:
            page: Playwright Page object
            role: Role to login as
            
        Returns:
            True if login successful
        """
        account = self.config.get_role_account(role)
        if not account:
            logger.warning(f"No credentials configured for role: {role}")
            return False
        
        try:
            login_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[name="username"]',
                'input[id*="email"]',
                'input[id*="username"]',
            ]
            
            for selector in login_selectors:
                element = await page.query_selector(selector)
                if element:
                    await element.fill(account.username)
                    break
            
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id*="password"]',
            ]
            
            for selector in password_selectors:
                element = await page.query_selector(selector)
                if element:
                    await element.fill(account.password)
                    break
            
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                'button:has-text("Log in")',
            ]
            
            for selector in submit_selectors:
                element = await page.query_selector(selector)
                if element:
                    await element.click()
                    break
            
            await asyncio.sleep(3)
            
            success_indicators = [
                '/dashboard',
                '/home',
                '/app',
                'logout',
                'profile',
            ]
            
            current_url = page.url.lower()
            for indicator in success_indicators:
                if indicator in current_url:
                    logger.info(f"Login successful for role: {role}")
                    return True
            
            login_indicators = ['login', 'signin', 'sign-in']
            if any(ind in current_url for ind in login_indicators):
                logger.warning(f"Login may have failed for role: {role}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Login failed for role {role}: {e}")
            return False
    
    async def discover_role(
        self,
        role: str,
        start_url: str,
    ) -> tuple[list[Route], list[Endpoint]]:
        """
        Run discovery for a specific role.
        
        Args:
            role: Role to discover
            start_url: Starting URL
            
        Returns:
            Tuple of (routes, endpoints)
        """
        logger.info(f"Starting discovery for role: {role}")
        
        discovery = CoreDiscovery(run_id=self.run_id)
        intel = NetworkIntelligence(run_id=self.run_id)
        
        browser_pool = get_browser_pool()
        context = await browser_pool.get_browser_context(role=role)
        page = await context.new_page()
        
        try:
            await intel.attach_to_context(context, role)
            
            await page.goto(start_url)
            await asyncio.sleep(1)
            
            if self.config.get_role_account(role):
                login_url = None
                login_paths = ['/login', '/signin', '/auth/login', '/auth/signin']
                for path in login_paths:
                    test_url = f"{start_url.rstrip('/')}{path}"
                    try:
                        response = await page.goto(test_url, wait_until="domcontentloaded", timeout=5000)
                        if response and response.status < 400:
                            login_url = test_url
                            break
                    except:
                        continue
                
                if login_url:
                    await page.goto(login_url)
                    await asyncio.sleep(1)
                    await self._login_as_role(page, role)
            
            await page.close()
            
            routes = await discovery.crawl(start_url, role=role)
            
            role_routes_path = self.config.get_output_path(
                "recon", "intelligence", f"routes_{role}.json"
            )
            atomic_write_json(role_routes_path, add_meta_to_output(
                {"routes": [r.model_dump() for r in routes], "role": role},
                target_url=self.config.target_url,
                phase="recon",
                run_id=self.run_id,
            ))
            
            endpoints = intel.get_endpoints()
            
            role_endpoints_path = self.config.get_output_path(
                "recon", "intelligence", f"endpoints_{role}.json"
            )
            atomic_write_json(role_endpoints_path, add_meta_to_output(
                {"endpoints": [e.model_dump() for e in endpoints], "role": role},
                target_url=self.config.target_url,
                phase="recon",
                run_id=self.run_id,
            ))
            
            self._role_routes[role] = routes
            self._role_endpoints[role] = endpoints
            
            return routes, endpoints
            
        finally:
            await context.close()
    
    async def discover_all_roles(self, start_url: str) -> None:
        """
        Discover all configured roles.
        
        Args:
            start_url: Starting URL for crawls
        """
        roles = [acc.role for acc in self.config.role_accounts]
        
        if not roles:
            roles = ['guest']
        
        for role in roles:
            await self.discover_role(role, start_url)
    
    def compare_roles(self) -> list[RoleDiff]:
        """
        Compare discovered routes and endpoints across roles.
        
        Returns:
            List of RoleDiff objects
        """
        all_endpoint_keys = set()
        for endpoints in self._role_endpoints.values():
            for ep in endpoints:
                key = f"{ep.method}:{ep.url}"
                all_endpoint_keys.add(key)
        
        endpoint_to_id: dict[str, str] = {}
        for endpoints in self._role_endpoints.values():
            for ep in endpoints:
                key = f"{ep.method}:{ep.url}"
                endpoint_to_id[key] = ep.id
        
        for ep_key in all_endpoint_keys:
            roles_with_access = []
            roles_without_access = []
            field_differences: dict[str, dict[str, list[str]]] = {}
            
            reference_fields: Optional[set[str]] = None
            
            for role, endpoints in self._role_endpoints.items():
                ep_found = None
                for ep in endpoints:
                    if f"{ep.method}:{ep.url}" == ep_key:
                        ep_found = ep
                        break
                
                if ep_found:
                    roles_with_access.append(role)
                    
                    current_fields = {f.name for f in ep_found.response_schema}
                    
                    if reference_fields is None:
                        reference_fields = current_fields
                    else:
                        extra_fields = current_fields - reference_fields
                        missing_fields = reference_fields - current_fields
                        
                        if extra_fields or missing_fields:
                            field_differences[role] = {
                                "extra_fields": list(extra_fields),
                                "missing_fields": list(missing_fields),
                            }
                else:
                    roles_without_access.append(role)
            
            button_differences: dict[str, list[str]] = {}
            
            if len(roles_with_access) > 0 or len(roles_without_access) > 0:
                diff = RoleDiff(
                    endpoint_id=endpoint_to_id.get(ep_key, ""),
                    endpoint_url=ep_key.split(":", 1)[1] if ":" in ep_key else ep_key,
                    roles_with_access=roles_with_access,
                    roles_without_access=roles_without_access,
                    field_differences=field_differences,
                    button_differences=button_differences,
                )
                self._role_diffs.append(diff)
                
                for role in roles_with_access:
                    if role not in self._permission_hints:
                        self._permission_hints[role] = {}
                    self._permission_hints[role][ep_key] = True
                
                for role in roles_without_access:
                    if role not in self._permission_hints:
                        self._permission_hints[role] = {}
                    self._permission_hints[role][ep_key] = False
        
        return self._role_diffs
    
    def get_permission_hints(self) -> dict[str, dict[str, bool]]:
        """Get permission hints from role comparison."""
        return self._permission_hints
    
    def save_role_diff(self) -> str:
        """
        Save role comparison results.
        
        Returns:
            Path to saved file
        """
        if not self._role_diffs:
            self.compare_roles()
        
        output_path = self.config.get_output_path(
            "recon", "intelligence", "role_diff.json"
        )
        
        data = add_meta_to_output(
            {
                "role_diffs": [d.model_dump() for d in self._role_diffs],
                "permission_hints": self._permission_hints,
                "roles_discovered": list(self._role_routes.keys()),
            },
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        
        atomic_write_json(output_path, data)
        logger.info(f"Saved role diff with {len(self._role_diffs)} endpoint comparisons")
        
        return str(output_path)


async def run_role_discovery(
    start_url: str,
    run_id: Optional[str] = None,
) -> RoleDiscovery:
    """
    Run role discovery process.
    
    Args:
        start_url: Starting URL
        run_id: Run ID
        
    Returns:
        RoleDiscovery instance with results
    """
    discovery = RoleDiscovery(run_id=run_id)
    await discovery.discover_all_roles(start_url)
    discovery.save_role_diff()
    return discovery


if __name__ == "__main__":
    async def main():
        import sys
        
        url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
        
        discovery = RoleDiscovery()
        await discovery.discover_all_roles(url)
        diffs = discovery.compare_roles()
        discovery.save_role_diff()
        
        print(f"Discovered {len(discovery._role_routes)} roles")
        print(f"Found {len(diffs)} endpoint differences")
    
    asyncio.run(main())
