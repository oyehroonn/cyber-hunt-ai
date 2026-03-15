"""
Step 18.18: Adaptive Loop - Dynamic test adjustment based on discoveries.
"""

import asyncio
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import Finding, TestPlan
from cyberAI.utils.attack_graph import get_attack_graph
from cyberAI.utils.helpers import generate_run_id


class AdaptiveLoop:
    """
    Monitors discoveries and dynamically adjusts test execution.
    """
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._discovery_queue: asyncio.Queue = asyncio.Queue()
        self._attack_graph = get_attack_graph()
        self._high_signal_endpoints: set[str] = set()
        self._new_test_plans: list[TestPlan] = []
        self._running = False
    
    async def watch_discovery_queue(self) -> None:
        """Background coroutine that monitors discoveries."""
        self._running = True
        
        while self._running:
            try:
                discovery = await asyncio.wait_for(
                    self._discovery_queue.get(),
                    timeout=1.0
                )
                
                await self._process_discovery(discovery)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing discovery: {e}")
    
    async def _process_discovery(self, discovery: dict) -> None:
        """Process a new discovery."""
        discovery_type = discovery.get("type")
        
        if discovery_type == "endpoint":
            endpoint = discovery.get("url")
            logger.info(f"New endpoint discovered: {endpoint}")
            
            if discovery.get("has_anomaly"):
                self._high_signal_endpoints.add(endpoint)
        
        elif discovery_type == "finding":
            finding = discovery.get("finding")
            if finding and finding.severity.value in ("critical", "high"):
                self._high_signal_endpoints.add(finding.asset)
        
        self._attack_graph.add_node(
            discovery.get("url", "unknown"),
            node_type=discovery_type,
        )
    
    async def add_discovery(self, discovery: dict) -> None:
        """Add a discovery to the queue."""
        await self._discovery_queue.put(discovery)
    
    def escalate_priority(self, endpoint: str) -> None:
        """Mark an endpoint for priority escalation."""
        self._high_signal_endpoints.add(endpoint)
        logger.info(f"Priority escalated for: {endpoint}")
    
    def get_high_signal_endpoints(self) -> list[str]:
        """Get endpoints that show high signal."""
        return list(self._high_signal_endpoints)
    
    def get_new_test_plans(self) -> list[TestPlan]:
        """Get dynamically generated test plans."""
        return self._new_test_plans
    
    def stop(self) -> None:
        """Stop the adaptive loop."""
        self._running = False


if __name__ == "__main__":
    async def main():
        loop = AdaptiveLoop()
        
        task = asyncio.create_task(loop.watch_discovery_queue())
        
        await loop.add_discovery({
            "type": "endpoint",
            "url": "/api/new-endpoint",
            "has_anomaly": True,
        })
        
        await asyncio.sleep(2)
        
        loop.stop()
        task.cancel()
        
        print(f"High signal endpoints: {loop.get_high_signal_endpoints()}")
    
    asyncio.run(main())
