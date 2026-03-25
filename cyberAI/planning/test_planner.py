"""
Step 17: Test Planner - Generate security test plans from intelligence.
Creates prioritized test plans for each object/role/endpoint combination.
"""

import asyncio
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import (
    Endpoint,
    MasterIntelligence,
    ObjectModel,
    PermissionMatrix,
    TestCategory,
    TestPlan,
    TestPrecondition,
)
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    generate_run_id,
    load_json,
)


class TestPlanner:
    """
    Generates security test plans from reconnaissance intelligence.
    """
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._test_plans: list[TestPlan] = []
        self._plans_by_category: dict[str, list[TestPlan]] = {}
        self._intel: Optional[MasterIntelligence] = None
    
    def load_intelligence(self) -> MasterIntelligence:
        """Load intelligence from recon outputs."""
        intel_path = self.config.get_output_path("recon", "intelligence", "master_intel.json")
        data = load_json(intel_path)
        
        if data:
            if "_meta" in data:
                del data["_meta"]
            self._intel = MasterIntelligence(**data)
        else:
            self._intel = MasterIntelligence()
        
        return self._intel
    
    def _calculate_confidence(
        self,
        endpoint: Optional[Endpoint] = None,
        obj: Optional[ObjectModel] = None,
        has_permission_data: bool = False,
    ) -> float:
        """Calculate confidence score based on available data."""
        score = 0.3
        
        if endpoint:
            score += 0.2
            if endpoint.body_schema:
                score += 0.1
            if endpoint.response_schema:
                score += 0.1
        
        if obj:
            score += 0.15
            if obj.ownership_fields:
                score += 0.05
        
        if has_permission_data:
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_auth_tests(self) -> list[TestPlan]:
        """Generate authentication test plans."""
        plans = []
        
        auth_endpoints = [
            e for e in (self._intel.endpoints if self._intel else [])
            if e.classification.value == "auth"
        ]
        
        plans.append(TestPlan(
            category=TestCategory.AUTH,
            name="test_login_flows",
            description="Test all login paths including SSO, magic link, invite redemption",
            expected_safe_behavior="Login requires valid credentials",
            attack_vector="Authentication bypass",
            confidence_score=0.8,
            priority=1,
        ))
        
        plans.append(TestPlan(
            category=TestCategory.AUTH,
            name="test_session_rotation",
            description="Verify session token changes after login and privilege change",
            expected_safe_behavior="Session tokens rotate on privilege changes",
            attack_vector="Session fixation",
            confidence_score=0.7,
            priority=2,
        ))
        
        plans.append(TestPlan(
            category=TestCategory.AUTH,
            name="test_stale_session_reuse",
            description="Use token from session A after logout; try expired tokens",
            expected_safe_behavior="Old/expired tokens are rejected",
            attack_vector="Stale session reuse",
            confidence_score=0.7,
            priority=2,
        ))
        
        plans.append(TestPlan(
            category=TestCategory.AUTH,
            name="test_password_reset",
            description="Test reset token guessability, expiry, reuse, cross-account use",
            expected_safe_behavior="Reset tokens are unpredictable and single-use",
            attack_vector="Password reset token abuse",
            confidence_score=0.8,
            priority=1,
        ))
        
        plans.append(TestPlan(
            category=TestCategory.AUTH,
            name="test_mfa_bypass",
            description="Skip MFA step, replay MFA token, use token after expiry",
            expected_safe_behavior="MFA cannot be bypassed",
            attack_vector="MFA bypass",
            confidence_score=0.6,
            priority=2,
        ))
        
        return plans
    
    def _generate_authz_tests(self) -> list[TestPlan]:
        """Generate authorization test plans."""
        plans = []
        
        objects = self._intel.objects if self._intel else []
        endpoints = self._intel.endpoints if self._intel else []
        
        for obj in objects:
            plans.append(TestPlan(
                category=TestCategory.AUTHZ,
                name=f"test_horizontal_idor_{obj.name}",
                description=f"Test IDOR for {obj.name}: access other users' objects",
                target_object=obj.name,
                expected_safe_behavior=f"Users cannot access other users' {obj.name}",
                attack_vector="Horizontal privilege escalation (IDOR)",
                confidence_score=self._calculate_confidence(obj=obj),
                priority=1 if obj.security_criticality == "high" else 2,
            ))
        
        admin_endpoints = [e for e in endpoints if e.classification.value == "admin"]
        for endpoint in admin_endpoints[:10]:
            plans.append(TestPlan(
                category=TestCategory.AUTHZ,
                name=f"test_vertical_escalation_{endpoint.id[:8]}",
                description=f"Access admin endpoint as basic user: {endpoint.url}",
                target_endpoint=endpoint.id,
                expected_safe_behavior="Non-admin users cannot access admin endpoints",
                attack_vector="Vertical privilege escalation",
                confidence_score=self._calculate_confidence(endpoint=endpoint),
                priority=1,
            ))
        
        for endpoint in endpoints:
            if endpoint.role_access:
                denied_roles = [r for r, a in endpoint.role_access.items() if not a]
                if denied_roles:
                    plans.append(TestPlan(
                        category=TestCategory.AUTHZ,
                        name=f"test_direct_access_{endpoint.id[:8]}",
                        description=f"Direct endpoint access bypassing UI: {endpoint.url}",
                        target_endpoint=endpoint.id,
                        expected_safe_behavior=f"Roles {denied_roles} cannot access endpoint",
                        attack_vector="Direct endpoint access",
                        confidence_score=0.8,
                        priority=2,
                    ))
        
        return plans
    
    def _generate_business_logic_tests(self) -> list[TestPlan]:
        """Generate business logic test plans."""
        plans = []
        
        workflows = self._intel.workflows if self._intel else []
        
        for workflow in workflows:
            plans.append(TestPlan(
                category=TestCategory.BUSINESS_LOGIC,
                name=f"test_workflow_skip_{workflow.name}",
                description=f"Skip workflow steps in {workflow.name}",
                expected_safe_behavior="Workflow steps cannot be skipped",
                attack_vector="Workflow bypass",
                confidence_score=0.7,
                priority=2,
            ))
            
            if workflow.suspicious_transitions:
                plans.append(TestPlan(
                    category=TestCategory.BUSINESS_LOGIC,
                    name=f"test_suspicious_transition_{workflow.name}",
                    description=f"Test suspicious transitions: {workflow.suspicious_transitions[:3]}",
                    expected_safe_behavior="Invalid transitions are rejected",
                    attack_vector="Workflow state manipulation",
                    confidence_score=0.9,
                    priority=1,
                ))
        
        plans.append(TestPlan(
            category=TestCategory.BUSINESS_LOGIC,
            name="test_duplicate_submission",
            description="Submit same form twice rapidly, check idempotency",
            expected_safe_behavior="Duplicate submissions are handled safely",
            attack_vector="Race condition / duplicate submission",
            confidence_score=0.6,
            priority=3,
        ))
        
        return plans
    
    def _generate_input_tests(self) -> list[TestPlan]:
        """Generate input validation test plans."""
        plans = []
        
        input_schemas = self._intel.input_schemas if self._intel else []
        
        for schema in input_schemas[:20]:
            plans.append(TestPlan(
                category=TestCategory.INPUT,
                name=f"test_input_mutation_{schema.endpoint_id[:16]}",
                description=f"Mutate inputs for {schema.endpoint_url}",
                target_endpoint=schema.endpoint_id,
                expected_safe_behavior="Invalid inputs are rejected with proper validation",
                attack_vector="Input validation bypass",
                payloads=schema.mutation_candidates[:10],
                confidence_score=0.7,
                priority=2,
            ))
        
        return plans
    
    def _generate_mass_assignment_tests(self) -> list[TestPlan]:
        """Generate mass assignment test plans."""
        plans = []
        
        input_schemas = self._intel.input_schemas if self._intel else []
        
        for schema in input_schemas[:15]:
            if schema.hidden_fields:
                plans.append(TestPlan(
                    category=TestCategory.MASS_ASSIGNMENT,
                    name=f"test_mass_assignment_{schema.endpoint_id[:16]}",
                    description=f"Add hidden fields to request: {schema.hidden_fields[:5]}",
                    target_endpoint=schema.endpoint_id,
                    expected_safe_behavior="Hidden fields are not accepted",
                    attack_vector="Mass assignment",
                    payloads=schema.hidden_fields,
                    confidence_score=0.8,
                    priority=1 if any(f in str(schema.hidden_fields).lower() for f in ["role", "admin", "owner"]) else 2,
                ))
        
        return plans
    
    def _generate_race_condition_tests(self) -> list[TestPlan]:
        """Generate race condition test plans."""
        plans = []
        
        endpoints = self._intel.endpoints if self._intel else []
        
        race_targets = [
            e for e in endpoints
            if any(p in e.url.lower() for p in ["balance", "credit", "coupon", "redeem", "approve", "transfer"])
        ]
        
        for endpoint in race_targets[:10]:
            plans.append(TestPlan(
                category=TestCategory.RACE,
                name=f"test_race_{endpoint.id[:16]}",
                description=f"Race condition test for {endpoint.url}",
                target_endpoint=endpoint.id,
                expected_safe_behavior="Concurrent requests are handled atomically",
                attack_vector="Race condition / TOCTOU",
                confidence_score=0.6,
                priority=1,
                is_state_altering=True,
            ))
        
        return plans
    
    def _generate_graphql_tests(self) -> list[TestPlan]:
        """Generate GraphQL test plans."""
        plans = []
        
        if not self._intel or not self._intel.graphql_intel:
            return plans
        
        gql = self._intel.graphql_intel
        
        plans.append(TestPlan(
            category=TestCategory.GRAPHQL,
            name="test_graphql_authorization",
            description="Query all types and fields as each role",
            expected_safe_behavior="Unauthorized queries are rejected",
            attack_vector="GraphQL authorization bypass",
            confidence_score=0.8,
            priority=1,
        ))
        
        if gql.supports_batching:
            plans.append(TestPlan(
                category=TestCategory.GRAPHQL,
                name="test_graphql_batching_abuse",
                description="Send 500 operations in one batch request",
                expected_safe_behavior="Batched requests are rate limited",
                attack_vector="GraphQL batching abuse",
                confidence_score=0.7,
                priority=2,
                is_noisy=True,
            ))
        
        plans.append(TestPlan(
            category=TestCategory.GRAPHQL,
            name="test_graphql_nested_traversal",
            description="Walk nested object relations to cross tenant boundaries",
            expected_safe_behavior="Nested queries respect authorization",
            attack_vector="GraphQL nested traversal",
            confidence_score=0.7,
            priority=1,
        ))
        
        return plans
    
    def _generate_websocket_tests(self) -> list[TestPlan]:
        """Generate WebSocket test plans."""
        plans = []
        
        if not self._intel or not self._intel.websocket_intel:
            return plans
        
        for ws in self._intel.websocket_intel:
            plans.append(TestPlan(
                category=TestCategory.WEBSOCKET,
                name=f"test_ws_auth_{ws.endpoint_url[:30]}",
                description=f"Test WebSocket authorization: {ws.endpoint_url}",
                expected_safe_behavior="WebSocket requires and enforces authentication",
                attack_vector="WebSocket authentication bypass",
                confidence_score=0.7,
                priority=2,
            ))
            
            if ws.channels_discovered:
                plans.append(TestPlan(
                    category=TestCategory.WEBSOCKET,
                    name=f"test_ws_channel_auth_{ws.endpoint_url[:30]}",
                    description=f"Subscribe to other users' channels: {ws.channels_discovered[:3]}",
                    expected_safe_behavior="Cannot subscribe to unauthorized channels",
                    attack_vector="WebSocket channel authorization bypass",
                    confidence_score=0.7,
                    priority=1,
                ))
        
        return plans
    
    def _generate_file_upload_tests(self) -> list[TestPlan]:
        """Generate file upload test plans."""
        plans = []
        
        endpoints = self._intel.endpoints if self._intel else []
        
        upload_endpoints = [
            e for e in endpoints
            if any(p in e.url.lower() for p in ["upload", "file", "attachment", "media"])
        ]
        
        for endpoint in upload_endpoints[:5]:
            plans.append(TestPlan(
                category=TestCategory.FILE_UPLOAD,
                name=f"test_file_type_confusion_{endpoint.id[:16]}",
                description=f"Upload files with mismatched extension/MIME: {endpoint.url}",
                target_endpoint=endpoint.id,
                expected_safe_behavior="Dangerous file types are rejected",
                attack_vector="File type confusion",
                confidence_score=0.7,
                priority=1,
            ))
        
        return plans
    
    def _generate_rag_tests(self) -> list[TestPlan]:
        """
        Generate RAG-driven test plans using the vulnerability knowledge base.
        These plans act as placeholders; the actual RAG tester generates live
        HTTP tests from the knowledge base at execution time.
        """
        plans = []

        config = self.config
        if not getattr(config, "llm_enabled", False):
            return plans

        try:
            import sys
            from pathlib import Path
            _cyberai_dir = str(Path(__file__).parent.parent)
            if _cyberai_dir not in sys.path:
                sys.path.insert(0, _cyberai_dir)

            from llm.rag_engine import create_rag_engine
            data_dir = Path(__file__).parent.parent / "llm" / "data"
            engine = create_rag_engine(data_dir=data_dir)

            obj_model = {}
            perm_matrix = {}
            workflow_map = None

            if self._intel:
                if self._intel.objects:
                    obj_model = {
                        o.name: {
                            "fields": [f.name for f in o.readable_fields[:10]],
                            "ownership": o.ownership_fields,
                            "criticality": o.security_criticality,
                        }
                        for o in self._intel.objects[:15]
                    }
                if self._intel.permission_matrix:
                    pm = self._intel.permission_matrix
                    perm_matrix = {
                        e.role: {e.object_type: {e.action: e.allowed}}
                        for e in (pm.entries if hasattr(pm, "entries") else [])
                    }
                if self._intel.workflows:
                    workflow_map = {
                        w.name: {
                            "states": [n.state for n in w.nodes[:5]],
                            "suspicious": w.suspicious_transitions[:3],
                        }
                        for w in self._intel.workflows[:5]
                    }

            hypotheses = engine.generate_hypotheses(obj_model, perm_matrix, workflow_map)

            for i, h in enumerate(hypotheses[:20]):
                if not isinstance(h, dict):
                    continue
                attack = (
                    h.get("attack_type")
                    or h.get("attack")
                    or h.get("vulnerability_class")
                    or "Unknown"
                )
                desc = h.get("description") or h.get("test_name") or f"RAG hypothesis #{i+1}"
                plans.append(TestPlan(
                    category=TestCategory.RAG,
                    name=f"rag_hypothesis_{i+1}_{attack.lower().replace(' ', '_')[:20]}",
                    description=str(desc)[:200],
                    expected_safe_behavior=h.get("expected_safe", "Application should reject attack"),
                    attack_vector=str(attack),
                    confidence_score=min(float(h.get("confidence", 0.6)), 1.0),
                    priority=int(h.get("priority", 3)),
                ))
        except Exception as e:
            logger.debug(f"RAG hypothesis generation: {e}")

        return plans

    def generate_all_plans(self) -> list[TestPlan]:
        """
        Generate all test plans from intelligence.

        Returns:
            List of TestPlan objects
        """
        if not self._intel:
            self.load_intelligence()

        self._test_plans = []

        self._test_plans.extend(self._generate_auth_tests())
        self._test_plans.extend(self._generate_authz_tests())
        self._test_plans.extend(self._generate_business_logic_tests())
        self._test_plans.extend(self._generate_input_tests())
        self._test_plans.extend(self._generate_mass_assignment_tests())
        self._test_plans.extend(self._generate_race_condition_tests())
        self._test_plans.extend(self._generate_graphql_tests())
        self._test_plans.extend(self._generate_websocket_tests())
        self._test_plans.extend(self._generate_file_upload_tests())
        self._test_plans.extend(self._generate_rag_tests())

        self._test_plans.sort(key=lambda p: (p.priority, -p.confidence_score))
        
        for plan in self._test_plans:
            category = plan.category.value
            if category not in self._plans_by_category:
                self._plans_by_category[category] = []
            self._plans_by_category[category].append(plan)
        
        logger.info(f"Generated {len(self._test_plans)} test plans")
        
        return self._test_plans
    
    def get_rollback_strategies(self) -> dict[str, str]:
        """Get rollback strategies for each object type."""
        strategies = {}
        
        if self._intel:
            for obj in self._intel.objects:
                if obj.lifecycle_states:
                    strategies[obj.name] = f"Reset {obj.name} to initial state via API or direct cleanup"
                else:
                    strategies[obj.name] = f"Delete test {obj.name} objects after testing"
        
        return strategies
    
    def save_plans(self) -> str:
        """
        Save test plans to files.
        
        Returns:
            Path to main plans file
        """
        if not self._test_plans:
            self.generate_all_plans()
        
        plans_path = self.config.get_output_path("planning", "test_plans.json")
        
        data = add_meta_to_output(
            {
                "plans": [p.model_dump() for p in self._test_plans],
                "total_plans": len(self._test_plans),
                "by_category": {
                    cat: len(plans)
                    for cat, plans in self._plans_by_category.items()
                },
                "rollback_strategies": self.get_rollback_strategies(),
            },
            target_url=self.config.target_url,
            phase="planning",
            run_id=self.run_id,
        )
        
        atomic_write_json(plans_path, data)
        
        category_dir = self.config.get_output_path("planning", "test_plans_by_category")
        category_dir.mkdir(parents=True, exist_ok=True)
        
        for category, plans in self._plans_by_category.items():
            cat_path = category_dir / f"{category}.json"
            cat_data = add_meta_to_output(
                {"plans": [p.model_dump() for p in plans]},
                target_url=self.config.target_url,
                phase="planning",
                run_id=self.run_id,
            )
            atomic_write_json(cat_path, cat_data)
        
        logger.info(f"Saved {len(self._test_plans)} test plans")
        
        return str(plans_path)


def run_test_planner(run_id: Optional[str] = None) -> TestPlanner:
    """
    Run test planning.
    
    Args:
        run_id: Run ID
        
    Returns:
        TestPlanner instance with results
    """
    planner = TestPlanner(run_id=run_id)
    planner.load_intelligence()
    planner.generate_all_plans()
    planner.save_plans()
    return planner


if __name__ == "__main__":
    planner = TestPlanner()
    
    planner.load_intelligence()
    plans = planner.generate_all_plans()
    planner.save_plans()
    
    print(f"\nGenerated {len(plans)} test plans:")
    for category, cat_plans in planner._plans_by_category.items():
        print(f"  {category}: {len(cat_plans)} plans")
    
    print("\nTop priority plans:")
    for plan in plans[:5]:
        print(f"  [{plan.category.value}] {plan.name} (priority: {plan.priority})")
