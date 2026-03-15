"""
Step 15: Comparison Engine - Cross-role and cross-state comparison.
Runs actions across all role/state combinations and analyzes differences.
"""

import asyncio
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import ComparisonResult, Endpoint, RequestRecord
from cyberAI.utils.http_client import AsyncHTTPClient
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    generate_run_id,
)


class ComparisonEngine:
    """
    Compares application behavior across roles and states.
    """
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._comparison_results: list[ComparisonResult] = []
        self._role_tokens: dict[str, str] = {}
        self._state_tokens: dict[str, str] = {}
    
    def set_role_token(self, role: str, token: str) -> None:
        """Set authentication token for a role."""
        self._role_tokens[role] = token
    
    def set_state_token(self, state: str, token: str) -> None:
        """Set authentication token for a state."""
        self._state_tokens[state] = token
    
    async def _execute_action(
        self,
        client: AsyncHTTPClient,
        endpoint: Endpoint,
        context_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Execute an action and capture results.
        
        Args:
            client: HTTP client
            endpoint: Endpoint to test
            context_token: Optional auth token
            
        Returns:
            Dict of execution results
        """
        headers = {}
        if context_token:
            headers["Authorization"] = f"Bearer {context_token}"
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            response, record = await client.request(
                method=endpoint.method.value,
                url=endpoint.url,
                headers=headers,
                record=True,
            )
            
            end_time = asyncio.get_event_loop().time()
            duration_ms = (end_time - start_time) * 1000
            
            result = {
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "response_size": len(response.text) if response.text else 0,
                "fields": [],
                "error": None,
            }
            
            if response.status_code < 400:
                try:
                    json_data = response.json()
                    if isinstance(json_data, dict):
                        result["fields"] = list(json_data.keys())
                    elif isinstance(json_data, list) and json_data:
                        if isinstance(json_data[0], dict):
                            result["fields"] = list(json_data[0].keys())
                except:
                    pass
            else:
                result["error"] = response.text[:200] if response.text else str(response.status_code)
            
            return result
            
        except Exception as e:
            return {
                "status_code": 0,
                "duration_ms": 0,
                "response_size": 0,
                "fields": [],
                "error": str(e),
            }
    
    async def compare_across_roles(
        self,
        endpoint: Endpoint,
        roles: list[str],
    ) -> ComparisonResult:
        """
        Compare endpoint behavior across different roles.
        
        Args:
            endpoint: Endpoint to compare
            roles: List of roles to test
            
        Returns:
            ComparisonResult object
        """
        client = AsyncHTTPClient()
        role_results: dict[str, dict[str, Any]] = {}
        
        try:
            for role in roles:
                token = self._role_tokens.get(role)
                result = await self._execute_action(client, endpoint, token)
                role_results[role] = result
                await asyncio.sleep(self.config.request_delay_ms / 1000)
            
        finally:
            await client.close()
        
        anomalies = self._detect_anomalies(role_results)
        timing_diff = self._analyze_timing(role_results)
        
        return ComparisonResult(
            action=f"{endpoint.method.value} {endpoint.url}",
            endpoint=endpoint.url,
            role_results=role_results,
            timing_differences=timing_diff,
            anomalies=anomalies,
        )
    
    async def compare_across_states(
        self,
        endpoint: Endpoint,
        states: list[str],
    ) -> ComparisonResult:
        """
        Compare endpoint behavior across different account states.
        
        Args:
            endpoint: Endpoint to compare
            states: List of states to test
            
        Returns:
            ComparisonResult object
        """
        client = AsyncHTTPClient()
        state_results: dict[str, dict[str, Any]] = {}
        
        try:
            for state in states:
                token = self._state_tokens.get(state)
                result = await self._execute_action(client, endpoint, token)
                state_results[state] = result
                await asyncio.sleep(self.config.request_delay_ms / 1000)
            
        finally:
            await client.close()
        
        anomalies = self._detect_anomalies(state_results)
        timing_diff = self._analyze_timing(state_results)
        
        return ComparisonResult(
            action=f"{endpoint.method.value} {endpoint.url}",
            endpoint=endpoint.url,
            state_results=state_results,
            timing_differences=timing_diff,
            anomalies=anomalies,
        )
    
    def _detect_anomalies(self, results: dict[str, dict]) -> list[str]:
        """Detect anomalies in comparison results."""
        anomalies = []
        
        status_codes = {ctx: r.get("status_code") for ctx, r in results.items()}
        unique_statuses = set(status_codes.values())
        
        if len(unique_statuses) > 1:
            anomalies.append(f"Different status codes: {status_codes}")
        
        all_fields: dict[str, set] = {}
        for ctx, r in results.items():
            fields = r.get("fields", [])
            all_fields[ctx] = set(fields)
        
        if len(set(frozenset(f) for f in all_fields.values())) > 1:
            for ctx1, fields1 in all_fields.items():
                for ctx2, fields2 in all_fields.items():
                    if ctx1 < ctx2:
                        extra = fields1 - fields2
                        if extra:
                            anomalies.append(f"{ctx1} has extra fields vs {ctx2}: {extra}")
        
        contexts_with_200 = [ctx for ctx, r in results.items() if r.get("status_code") == 200]
        contexts_with_403 = [ctx for ctx, r in results.items() if r.get("status_code") == 403]
        
        if contexts_with_200 and contexts_with_403:
            anomalies.append(f"Access allowed for {contexts_with_200}, denied for {contexts_with_403}")
        
        return anomalies
    
    def _analyze_timing(self, results: dict[str, dict]) -> dict[str, float]:
        """Analyze timing differences between contexts."""
        timing = {}
        
        for ctx, r in results.items():
            timing[ctx] = r.get("duration_ms", 0)
        
        if timing:
            avg = sum(timing.values()) / len(timing)
            
            for ctx, t in timing.items():
                if avg > 0 and abs(t - avg) / avg > 0.5:
                    timing[f"{ctx}_anomaly"] = t - avg
        
        return timing
    
    async def run_full_comparison(
        self,
        endpoints: list[Endpoint],
        roles: list[str],
        states: Optional[list[str]] = None,
        max_endpoints: int = 50,
    ) -> list[ComparisonResult]:
        """
        Run full comparison across roles and states.
        
        Args:
            endpoints: Endpoints to compare
            roles: Roles to test
            states: Optional states to test
            max_endpoints: Maximum endpoints to compare
            
        Returns:
            List of ComparisonResult objects
        """
        endpoints_to_test = endpoints[:max_endpoints]
        
        logger.info(f"Running comparison on {len(endpoints_to_test)} endpoints across {len(roles)} roles")
        
        for endpoint in endpoints_to_test:
            try:
                result = await self.compare_across_roles(endpoint, roles)
                self._comparison_results.append(result)
                
                if states:
                    state_result = await self.compare_across_states(endpoint, states)
                    self._comparison_results.append(state_result)
                    
            except Exception as e:
                logger.warning(f"Comparison failed for {endpoint.url}: {e}")
        
        return self._comparison_results
    
    def get_anomalous_results(self) -> list[ComparisonResult]:
        """Get results with detected anomalies."""
        return [r for r in self._comparison_results if r.anomalies]
    
    def save_comparisons(self) -> str:
        """
        Save comparison results.
        
        Returns:
            Path to saved file
        """
        output_path = self.config.get_output_path(
            "recon", "intelligence", "comparison_diffs.json"
        )
        
        anomalous = self.get_anomalous_results()
        
        data = add_meta_to_output(
            {
                "comparisons": [r.model_dump() for r in self._comparison_results],
                "anomalous_count": len(anomalous),
                "anomalies_summary": [
                    {"endpoint": r.endpoint, "anomalies": r.anomalies}
                    for r in anomalous
                ],
            },
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        
        atomic_write_json(output_path, data)
        logger.info(f"Saved {len(self._comparison_results)} comparisons ({len(anomalous)} with anomalies)")
        
        return str(output_path)


async def run_comparison_engine(
    endpoints: list[Endpoint],
    roles: list[str],
    states: Optional[list[str]] = None,
    run_id: Optional[str] = None,
) -> ComparisonEngine:
    """
    Run comparison engine.
    
    Args:
        endpoints: Endpoints to compare
        roles: Roles to test
        states: Optional states to test
        run_id: Run ID
        
    Returns:
        ComparisonEngine instance with results
    """
    engine = ComparisonEngine(run_id=run_id)
    await engine.run_full_comparison(endpoints, roles, states)
    engine.save_comparisons()
    return engine


if __name__ == "__main__":
    from cyberAI.models import HttpMethod
    
    async def main():
        engine = ComparisonEngine()
        
        engine.set_role_token("admin", "admin_token")
        engine.set_role_token("user", "user_token")
        
        endpoint = Endpoint(
            method=HttpMethod.GET,
            url="https://httpbin.org/get",
        )
        
        result = await engine.compare_across_roles(endpoint, ["admin", "user"])
        engine._comparison_results.append(result)
        engine.save_comparisons()
        
        print(f"Anomalies: {result.anomalies}")
        print(f"Timing: {result.timing_differences}")
    
    asyncio.run(main())
