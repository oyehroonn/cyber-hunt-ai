"""
Step 5: Account State Discovery - State-based access pattern analysis.
Discovers differences in application behavior across various account states.
"""

import asyncio
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import Endpoint, Route, StateDiff
from cyberAI.recon.core_discovery import CoreDiscovery
from cyberAI.recon.network_intelligence import NetworkIntelligence
from cyberAI.utils.browser import get_browser_pool
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    generate_run_id,
)


class AccountStateDiscovery:
    """
    Discovers application behavior differences across account states.
    States: unverified, verified, trial, paid, suspended, active, draft, published, etc.
    """
    
    COMMON_STATES = [
        "unverified",
        "verified", 
        "trial",
        "paid",
        "free",
        "premium",
        "suspended",
        "active",
        "inactive",
        "draft",
        "published",
        "pending",
        "approved",
        "rejected",
        "empty",
        "populated",
    ]
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._state_routes: dict[str, list[Route]] = {}
        self._state_endpoints: dict[str, list[Endpoint]] = {}
        self._state_diffs: list[StateDiff] = {}
        self._detected_states: set[str] = set()
    
    async def _detect_current_state(self, page) -> list[str]:
        """
        Detect the current account state from page content.
        
        Args:
            page: Playwright Page object
            
        Returns:
            List of detected state indicators
        """
        try:
            indicators = await page.evaluate('''() => {
                const indicators = [];
                const bodyText = document.body.innerText.toLowerCase();
                const html = document.body.innerHTML.toLowerCase();
                
                // State keywords to look for
                const stateKeywords = {
                    'unverified': ['verify your email', 'verification required', 'confirm your email'],
                    'verified': ['email verified', 'account verified'],
                    'trial': ['trial', 'days remaining', 'trial expires', 'free trial'],
                    'paid': ['premium', 'pro plan', 'subscription active'],
                    'free': ['free plan', 'upgrade to', 'free tier'],
                    'suspended': ['suspended', 'account disabled', 'access denied'],
                    'active': ['active', 'subscription active'],
                    'pending': ['pending', 'awaiting approval', 'under review'],
                    'draft': ['draft', 'unpublished'],
                    'published': ['published', 'live'],
                    'empty': ['no items', 'get started', 'create your first', 'empty'],
                };
                
                for (const [state, keywords] of Object.entries(stateKeywords)) {
                    for (const keyword of keywords) {
                        if (bodyText.includes(keyword) || html.includes(keyword)) {
                            indicators.push(state);
                            break;
                        }
                    }
                }
                
                // Check for state-related CSS classes
                const stateClasses = ['trial', 'premium', 'free', 'suspended', 'verified', 'unverified'];
                stateClasses.forEach(cls => {
                    if (document.querySelector('.' + cls) || document.querySelector('[class*="' + cls + '"]')) {
                        indicators.push(cls);
                    }
                });
                
                // Check for data attributes
                const elements = document.querySelectorAll('[data-state], [data-status], [data-plan]');
                elements.forEach(el => {
                    const state = el.getAttribute('data-state') || el.getAttribute('data-status') || el.getAttribute('data-plan');
                    if (state) indicators.push(state.toLowerCase());
                });
                
                return [...new Set(indicators)];
            }''')
            
            return indicators
            
        except Exception as e:
            logger.debug(f"Error detecting state: {e}")
            return []
    
    async def _trigger_state_change(self, page, target_state: str) -> bool:
        """
        Attempt to trigger a state change.
        
        Args:
            page: Playwright Page object
            target_state: Target state to achieve
            
        Returns:
            True if state change was triggered
        """
        state_triggers = {
            "verified": [
                '//a[contains(text(), "Verify")]',
                '//button[contains(text(), "Verify")]',
                '//*[@data-action="verify"]',
            ],
            "published": [
                '//button[contains(text(), "Publish")]',
                '//button[contains(text(), "Go Live")]',
                '//*[@data-action="publish"]',
            ],
            "active": [
                '//button[contains(text(), "Activate")]',
                '//button[contains(text(), "Enable")]',
            ],
            "draft": [
                '//button[contains(text(), "Save as Draft")]',
                '//button[contains(text(), "Unpublish")]',
            ],
        }
        
        triggers = state_triggers.get(target_state, [])
        
        for xpath in triggers:
            try:
                element = await page.query_selector(f'xpath={xpath}')
                if element:
                    await element.click()
                    await asyncio.sleep(2)
                    return True
            except Exception:
                continue
        
        return False
    
    async def discover_state(
        self,
        state: str,
        start_url: str,
        role: Optional[str] = None,
    ) -> tuple[list[Route], list[Endpoint]]:
        """
        Run discovery for a specific account state.
        
        Args:
            state: State to discover
            start_url: Starting URL
            role: Optional role context
            
        Returns:
            Tuple of (routes, endpoints)
        """
        logger.info(f"Starting discovery for state: {state}")
        
        discovery = CoreDiscovery(run_id=self.run_id)
        intel = NetworkIntelligence(run_id=self.run_id)
        
        browser_pool = get_browser_pool()
        context = await browser_pool.get_browser_context(role=role)
        
        try:
            await intel.attach_to_context(context, role)
            
            routes = await discovery.crawl(start_url, role=role, max_pages=50)
            
            self._state_routes[state] = routes
            self._state_endpoints[state] = intel.get_endpoints()
            
            return routes, intel.get_endpoints()
            
        finally:
            await context.close()
    
    async def discover_states_for_role(
        self,
        start_url: str,
        role: str,
        states: Optional[list[str]] = None,
    ) -> None:
        """
        Discover multiple states for a single role.
        
        Args:
            start_url: Starting URL
            role: Role to test
            states: Optional list of states to test
        """
        if states is None:
            states = self.COMMON_STATES
        
        browser_pool = get_browser_pool()
        context = await browser_pool.get_browser_context(role=role)
        page = await context.new_page()
        
        try:
            await page.goto(start_url)
            await asyncio.sleep(2)
            
            detected = await self._detect_current_state(page)
            self._detected_states.update(detected)
            logger.info(f"Detected states: {detected}")
            
        finally:
            await page.close()
            await context.close()
        
        for state in states[:5]:
            try:
                await self.discover_state(state, start_url, role)
            except Exception as e:
                logger.warning(f"Failed to discover state {state}: {e}")
    
    def compare_states(self) -> dict[str, StateDiff]:
        """
        Compare discovered behavior across states.
        
        Returns:
            Dictionary of state to StateDiff mappings
        """
        for state, endpoints in self._state_endpoints.items():
            available_endpoints = [f"{e.method}:{e.url}" for e in endpoints]
            
            available_actions = []
            for route in self._state_routes.get(state, []):
                for action in route.actions:
                    available_actions.append(action.text or action.selector)
            
            transitions = []
            
            visible_elements = []
            for route in self._state_routes.get(state, []):
                visible_elements.append(route.page_title or route.slug)
            
            diff = StateDiff(
                state=state,
                available_actions=available_actions[:50],
                available_endpoints=available_endpoints,
                visible_ui_elements=visible_elements[:50],
                transitions_allowed=transitions,
            )
            
            self._state_diffs[state] = diff
        
        return self._state_diffs
    
    def save_state_diff(self) -> str:
        """
        Save state comparison results.
        
        Returns:
            Path to saved file
        """
        if not self._state_diffs:
            self.compare_states()
        
        output_path = self.config.get_output_path(
            "recon", "intelligence", "state_diff.json"
        )
        
        data = add_meta_to_output(
            {
                "state_diffs": {k: v.model_dump() for k, v in self._state_diffs.items()},
                "detected_states": list(self._detected_states),
                "states_analyzed": list(self._state_routes.keys()),
            },
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        
        atomic_write_json(output_path, data)
        logger.info(f"Saved state diff with {len(self._state_diffs)} states analyzed")
        
        return str(output_path)


async def run_account_state_discovery(
    start_url: str,
    role: Optional[str] = None,
    run_id: Optional[str] = None,
) -> AccountStateDiscovery:
    """
    Run account state discovery.
    
    Args:
        start_url: Starting URL
        role: Optional role context
        run_id: Run ID
        
    Returns:
        AccountStateDiscovery instance with results
    """
    discovery = AccountStateDiscovery(run_id=run_id)
    await discovery.discover_states_for_role(start_url, role or "user")
    discovery.save_state_diff()
    return discovery


if __name__ == "__main__":
    async def main():
        import sys
        
        url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
        
        discovery = AccountStateDiscovery()
        await discovery.discover_states_for_role(url, "user", states=["active", "empty"])
        discovery.compare_states()
        discovery.save_state_diff()
        
        print(f"Discovered states: {discovery._detected_states}")
        print(f"Analyzed {len(discovery._state_diffs)} state variations")
    
    asyncio.run(main())
