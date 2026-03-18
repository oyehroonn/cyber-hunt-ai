"""
Step 18: Test Runner - Parallel test orchestrator.
Distributes test plans across worker pools and manages execution.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Callable, Optional

from loguru import logger
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table

from cyberAI.config import get_config
from cyberAI.models import Finding, TestCategory, TestPlan
from cyberAI.utils.attack_graph import get_attack_graph
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    generate_run_id,
    load_json,
)

console = Console()


class TestRunner:
    """
    Orchestrates parallel execution of security tests.
    """
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._test_plans: list[TestPlan] = []
        self._findings: list[Finding] = []
        self._discovery_queue: asyncio.Queue = asyncio.Queue()
        self._attack_graph = get_attack_graph()
        self._stats = {
            "tests_run": 0,
            "findings_discovered": 0,
            "pending": 0,
            "in_progress": 0,
            "by_category": {},
        }
        self._testers: dict[str, Any] = {}
    
    def load_test_plans(self, categories: Optional[list[str]] = None) -> list[TestPlan]:
        """Load test plans from planning output."""
        plans_path = self.config.get_output_path("planning", "test_plans.json")
        data = load_json(plans_path)
        
        if data and "plans" in data:
            self._test_plans = [TestPlan(**p) for p in data["plans"]]
            
            if categories:
                self._test_plans = [
                    p for p in self._test_plans
                    if p.category.value in categories
                ]
            
            self._stats["pending"] = len(self._test_plans)
        
        return self._test_plans
    
    def register_tester(self, category: str, tester: Any) -> None:
        """Register a tester for a category."""
        self._testers[category] = tester
    
    async def _run_single_test(self, plan: TestPlan) -> list[Finding]:
        """Run a single test plan."""
        category = plan.category.value
        tester = self._testers.get(category)
        
        if not tester:
            logger.warning(f"No tester registered for category: {category}")
            return []
        
        try:
            self._stats["in_progress"] += 1
            self._stats["pending"] -= 1
            
            if hasattr(tester, plan.name):
                method = getattr(tester, plan.name)
                findings = await method() if asyncio.iscoroutinefunction(method) else method()
            else:
                findings = await tester.run_test(plan) if hasattr(tester, 'run_test') else []
            
            self._stats["tests_run"] += 1
            self._stats["in_progress"] -= 1
            self._stats["findings_discovered"] += len(findings)
            
            if category not in self._stats["by_category"]:
                self._stats["by_category"][category] = {"run": 0, "findings": 0}
            self._stats["by_category"][category]["run"] += 1
            self._stats["by_category"][category]["findings"] += len(findings)
            
            return findings
            
        except Exception as e:
            logger.error(f"Test failed: {plan.name} - {e}")
            self._stats["in_progress"] -= 1
            return []
    
    async def run_category(
        self,
        category: str,
        max_concurrent: int = 5,
    ) -> list[Finding]:
        """Run all tests for a category."""
        # ASRTS §4.2: optional api_fuzz category (no plans required)
        if category == "api_fuzz":
            try:
                from cyberAI.testing.api_fuzzer import run_api_fuzzer
                return await run_api_fuzzer(
                    self.config.target_url or "",
                    run_id=self.config.run_id,
                )
            except Exception as e:
                logger.debug(f"API fuzzer: {e}")
                return []

        plans = [p for p in self._test_plans if p.category.value == category]
        
        if not plans:
            return []
        
        logger.info(f"Running {len(plans)} tests for category: {category}")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        findings = []
        
        async def run_with_semaphore(plan: TestPlan) -> list[Finding]:
            async with semaphore:
                return await self._run_single_test(plan)
        
        tasks = [run_with_semaphore(plan) for plan in plans]
        results = await asyncio.gather(*tasks)
        
        for result in results:
            findings.extend(result)
        
        # ASRTS Phase 2.5: differential auth when we have multiple role accounts
        if category == "authz" and len(self.config.role_accounts) >= 2:
            tester = self._testers.get("authz")
            if tester and hasattr(tester, "test_differential_auth"):
                roles = [acc.role for acc in self.config.role_accounts]
                try:
                    diff_findings = await tester.test_differential_auth(
                        role_high=roles[0],
                        role_low=roles[1],
                        engagement_id=self.config.run_id or "default",
                    )
                    findings.extend(diff_findings)
                except Exception as e:
                    logger.debug(f"Differential auth test: {e}")
        
        return findings
    
    async def run_all(
        self,
        max_workers: int = None,
        categories: Optional[list[str]] = None,
    ) -> list[Finding]:
        """
        Run all test plans.
        
        Args:
            max_workers: Maximum concurrent workers per category
            categories: Optional list of categories to run
            
        Returns:
            List of all findings
        """
        max_workers = max_workers or self.config.max_workers
        
        if not self._test_plans:
            self.load_test_plans(categories)
        
        all_categories = set(p.category.value for p in self._test_plans)
        if categories:
            all_categories = all_categories & set(categories)
            if "api_fuzz" in categories:
                all_categories.add("api_fuzz")
        
        with Progress() as progress:
            main_task = progress.add_task("[cyan]Running security tests...", total=len(all_categories))
            
            for category in all_categories:
                progress.update(main_task, description=f"[cyan]Testing: {category}")
                
                category_findings = await self.run_category(category, max_workers)
                self._findings.extend(category_findings)
                
                progress.advance(main_task)
        
        self._save_findings()
        self._save_state()
        
        return self._findings
    
    async def handle_discovery(self, discovery: dict) -> None:
        """Handle new discovery from a test worker."""
        await self._discovery_queue.put(discovery)
        
        if discovery.get("type") == "endpoint":
            logger.info(f"New endpoint discovered: {discovery.get('url')}")
        elif discovery.get("type") == "finding":
            self._findings.append(discovery.get("finding"))
    
    def add_finding(self, finding: Finding) -> None:
        """Add a finding from a test."""
        self._findings.append(finding)
        self._stats["findings_discovered"] += 1
        
        findings_path = self.config.get_output_path(
            "testing", "findings", f"finding_{finding.id}.json"
        )
        atomic_write_json(findings_path, finding.model_dump())
    
    def _save_findings(self) -> str:
        """Save all findings to file."""
        findings_path = self.config.get_output_path("testing", "findings", "all_findings.json")
        
        data = add_meta_to_output(
            {
                "findings": [f.model_dump() for f in self._findings],
                "total": len(self._findings),
                "by_severity": {
                    sev: len([f for f in self._findings if f.severity.value == sev])
                    for sev in ["critical", "high", "medium", "low", "info"]
                },
            },
            target_url=self.config.target_url,
            phase="testing",
            run_id=self.run_id,
        )
        
        atomic_write_json(findings_path, data)
        return str(findings_path)
    
    def _save_state(self) -> str:
        """Save runner state."""
        state_path = self.config.get_output_path("testing", "runner_state.json")
        
        data = add_meta_to_output(
            {
                "stats": self._stats,
                "completed_at": datetime.utcnow().isoformat(),
            },
            target_url=self.config.target_url,
            phase="testing",
            run_id=self.run_id,
        )
        
        atomic_write_json(state_path, data)
        return str(state_path)
    
    def print_summary(self) -> None:
        """Print test execution summary."""
        table = Table(title="Test Execution Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Tests Run", str(self._stats["tests_run"]))
        table.add_row("Findings Discovered", str(self._stats["findings_discovered"]))
        
        for category, stats in self._stats["by_category"].items():
            table.add_row(f"  {category}", f"{stats['run']} tests, {stats['findings']} findings")
        
        console.print(table)


def _register_all_testers(runner: TestRunner, run_id: Optional[str] = None) -> None:
    """Register all category testers with the runner so plans are executed."""
    from cyberAI.testing.auth_testing import AuthTester
    from cyberAI.testing.authorization_testing import AuthorizationTester
    from cyberAI.testing.business_logic import BusinessLogicTester
    from cyberAI.testing.input_mutation import InputMutationTester
    from cyberAI.testing.mass_assignment import MassAssignmentTester
    from cyberAI.testing.race_conditions import RaceConditionTester
    from cyberAI.testing.multi_session import MultiSessionTester
    from cyberAI.testing.stored_payload import StoredPayloadTester
    from cyberAI.testing.file_upload import FileUploadTester
    from cyberAI.testing.graphql_testing import GraphQLTester
    from cyberAI.testing.websocket_testing import WebSocketTester
    from cyberAI.testing.async_testing import AsyncTester
    from cyberAI.testing.search_filter import SearchFilterTester
    from cyberAI.testing.export_import import ExportImportTester
    from cyberAI.testing.billing_testing import BillingTester
    from cyberAI.testing.notification_testing import NotificationTester
    from cyberAI.testing.config_testing import ConfigTester

    r_id = run_id or runner.run_id
    runner.register_tester("auth", AuthTester(run_id=r_id))
    runner.register_tester("authz", AuthorizationTester(run_id=r_id))
    runner.register_tester("business_logic", BusinessLogicTester(run_id=r_id))
    runner.register_tester("input", InputMutationTester(run_id=r_id))
    runner.register_tester("mass_assignment", MassAssignmentTester(run_id=r_id))
    runner.register_tester("race", RaceConditionTester(run_id=r_id))
    runner.register_tester("multi_session", MultiSessionTester(run_id=r_id))
    runner.register_tester("stored_payload", StoredPayloadTester(run_id=r_id))
    runner.register_tester("file_upload", FileUploadTester(run_id=r_id))
    runner.register_tester("graphql", GraphQLTester(run_id=r_id))
    runner.register_tester("websocket", WebSocketTester(run_id=r_id))
    runner.register_tester("async", AsyncTester(run_id=r_id))
    runner.register_tester("search", SearchFilterTester(run_id=r_id))
    runner.register_tester("export_import", ExportImportTester(run_id=r_id))
    runner.register_tester("billing", BillingTester(run_id=r_id))
    runner.register_tester("notification", NotificationTester(run_id=r_id))
    runner.register_tester("config", ConfigTester(run_id=r_id))


async def run_tests(
    categories: Optional[list[str]] = None,
    max_workers: int = None,
    run_id: Optional[str] = None,
) -> TestRunner:
    """
    Run security tests.
    
    Args:
        categories: Optional list of categories to run
        max_workers: Maximum concurrent workers
        run_id: Run ID
        
    Returns:
        TestRunner instance with results
    """
    runner = TestRunner(run_id=run_id)
    runner.load_test_plans(categories)
    _register_all_testers(runner, run_id=run_id)
    await runner.run_all(max_workers, categories)
    runner.print_summary()
    return runner


if __name__ == "__main__":
    async def main():
        runner = TestRunner()
        runner.load_test_plans()
        
        print(f"Loaded {len(runner._test_plans)} test plans")
        
        runner.print_summary()
    
    asyncio.run(main())
