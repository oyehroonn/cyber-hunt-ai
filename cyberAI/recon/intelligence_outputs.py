"""
Step 16: Intelligence Outputs - Aggregate all recon into master intelligence report.
Combines all recon phases into comprehensive output files.
"""

from pathlib import Path
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import (
    AsyncFlow,
    Endpoint,
    GraphQLIntel,
    MasterIntelligence,
    ObjectModel,
    PermissionMatrix,
    Route,
    SecurityControlsReport,
    SensitiveSurface,
    WebSocketIntel,
    WorkflowGraph,
)
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    atomic_write_text,
    generate_run_id,
    load_json,
)


class IntelligenceAggregator:
    """
    Aggregates all reconnaissance data into master intelligence outputs.
    """
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._master_intel: Optional[MasterIntelligence] = None
    
    def _load_from_file(self, filename: str) -> Optional[dict]:
        """Load data from an intelligence file."""
        path = self.config.get_output_path("recon", "intelligence", filename)
        return load_json(path)
    
    def aggregate(
        self,
        routes: Optional[list[Route]] = None,
        endpoints: Optional[list[Endpoint]] = None,
        objects: Optional[list[ObjectModel]] = None,
        permission_matrix: Optional[PermissionMatrix] = None,
        workflows: Optional[list[WorkflowGraph]] = None,
        graphql_intel: Optional[GraphQLIntel] = None,
        websocket_intel: Optional[list[WebSocketIntel]] = None,
        async_flows: Optional[list[AsyncFlow]] = None,
        security_controls: Optional[SecurityControlsReport] = None,
        sensitive_surfaces: Optional[list[SensitiveSurface]] = None,
    ) -> MasterIntelligence:
        """
        Aggregate all intelligence data.
        
        Args:
            routes: Discovered routes
            endpoints: Discovered endpoints
            objects: Discovered object models
            permission_matrix: Permission matrix
            workflows: Workflow graphs
            graphql_intel: GraphQL intelligence
            websocket_intel: WebSocket intelligence
            async_flows: Async flow data
            security_controls: Security controls report
            sensitive_surfaces: Sensitive surfaces
            
        Returns:
            MasterIntelligence object
        """
        self._master_intel = MasterIntelligence(
            routes=routes or [],
            endpoints=endpoints or [],
            objects=objects or [],
            permission_matrix=permission_matrix or PermissionMatrix(),
            workflows=workflows or [],
            graphql_intel=graphql_intel,
            websocket_intel=websocket_intel or [],
            async_flows=async_flows or [],
            security_controls=security_controls or SecurityControlsReport(),
            sensitive_surfaces=sensitive_surfaces or [],
        )
        
        return self._master_intel
    
    def aggregate_from_files(self) -> MasterIntelligence:
        """
        Aggregate intelligence from saved files.
        
        Returns:
            MasterIntelligence object
        """
        routes_data = self._load_from_file("routes.json")
        routes = []
        if routes_data and "routes" in routes_data:
            routes = [Route(**r) for r in routes_data["routes"]]
        
        endpoints_data = self._load_from_file("endpoints.json")
        endpoints = []
        if endpoints_data and "endpoints" in endpoints_data:
            endpoints = [Endpoint(**e) for e in endpoints_data["endpoints"]]
        
        objects_data = self._load_from_file("object_graph.json")
        objects = []
        if objects_data and "objects" in objects_data:
            objects = [ObjectModel(**o) for o in objects_data["objects"]]
        
        perm_data = self._load_from_file("permission_matrix.json")
        permission_matrix = PermissionMatrix()
        if perm_data and "matrix" in perm_data:
            permission_matrix = PermissionMatrix(**perm_data["matrix"])
        
        workflow_data = self._load_from_file("workflows.json")
        workflows = []
        if workflow_data and "workflows" in workflow_data:
            for name, wf in workflow_data["workflows"].items():
                workflows.append(WorkflowGraph(**wf))
        
        gql_data = self._load_from_file("graphql_intel.json")
        graphql_intel = None
        if gql_data and "intel" in gql_data and gql_data["intel"]:
            graphql_intel = GraphQLIntel(**gql_data["intel"])
        
        ws_data = self._load_from_file("websocket_intel.json")
        websocket_intel = []
        if ws_data and "intel" in ws_data:
            websocket_intel = [WebSocketIntel(**i) for i in ws_data["intel"]]
        
        async_data = self._load_from_file("async_flows.json")
        async_flows = []
        if async_data and "flows" in async_data:
            async_flows = [AsyncFlow(**f) for f in async_data["flows"]]
        
        sec_data = self._load_from_file("security_controls.json")
        security_controls = SecurityControlsReport()
        if sec_data and "report" in sec_data:
            security_controls = SecurityControlsReport(**sec_data["report"])
        
        surf_data = self._load_from_file("sensitive_surfaces.json")
        sensitive_surfaces = []
        if surf_data and "surfaces" in surf_data:
            sensitive_surfaces = [SensitiveSurface(**s) for s in surf_data["surfaces"]]
        
        hidden_data = self._load_from_file("hidden_routes.json")
        hidden_routes = []
        if hidden_data and "hidden_routes" in hidden_data:
            for r in hidden_data["hidden_routes"]:
                hidden_routes.append(Route(
                    slug=r.get("path", "").strip("/").replace("/", "_"),
                    url=r.get("path", ""),
                    is_hidden=True,
                    source=r.get("source", "js_bundle"),
                ))
        
        role_diff_data = self._load_from_file("role_diff.json")
        role_diffs = []
        if role_diff_data and "role_diffs" in role_diff_data:
            from cyberAI.models import RoleDiff
            role_diffs = [RoleDiff(**d) for d in role_diff_data["role_diffs"]]
        
        state_diff_data = self._load_from_file("state_diff.json")
        state_diffs = []
        if state_diff_data and "state_diffs" in state_diff_data:
            from cyberAI.models import StateDiff
            for state, diff in state_diff_data["state_diffs"].items():
                state_diffs.append(StateDiff(**diff))
        
        input_data = self._load_from_file("input_schemas.json")
        input_schemas = []
        if input_data and "schemas" in input_data:
            from cyberAI.models import InputSchema
            for key, schema in input_data["schemas"].items():
                input_schemas.append(InputSchema(**schema))
        
        comparison_data = self._load_from_file("comparison_diffs.json")
        comparison_results = []
        if comparison_data and "comparisons" in comparison_data:
            from cyberAI.models import ComparisonResult
            comparison_results = [ComparisonResult(**c) for c in comparison_data["comparisons"]]
        
        self._master_intel = MasterIntelligence(
            routes=routes,
            endpoints=endpoints,
            objects=objects,
            permission_matrix=permission_matrix,
            workflows=workflows,
            graphql_intel=graphql_intel,
            websocket_intel=websocket_intel,
            async_flows=async_flows,
            security_controls=security_controls,
            sensitive_surfaces=sensitive_surfaces,
            hidden_routes=hidden_routes,
            role_diffs=role_diffs,
            state_diffs=state_diffs,
            input_schemas=input_schemas,
            comparison_results=comparison_results,
        )
        
        return self._master_intel
    
    def generate_route_map(self) -> dict:
        """Generate route map with screenshots and actions."""
        if not self._master_intel:
            self.aggregate_from_files()
        
        route_map = []
        for route in self._master_intel.routes:
            route_entry = {
                "slug": route.slug,
                "url": route.url,
                "screenshot_path": route.screenshot_path,
                "dom_path": route.dom_path,
                "actions": [a.model_dump() for a in route.actions],
                "linked_requests": route.linked_requests,
                "role_context": route.role_context,
                "is_hidden": route.is_hidden,
            }
            route_map.append(route_entry)
        
        return {"routes": route_map}
    
    def generate_endpoint_inventory(self) -> dict:
        """Generate endpoint inventory with schemas and auth context."""
        if not self._master_intel:
            self.aggregate_from_files()
        
        inventory = []
        for endpoint in self._master_intel.endpoints:
            entry = {
                "method": endpoint.method.value,
                "url": endpoint.url,
                "path_pattern": endpoint.path_pattern,
                "classification": endpoint.classification.value,
                "sensitivity": endpoint.sensitivity_label.value,
                "auth_context": endpoint.auth_context,
                "body_schema": [f.model_dump() for f in endpoint.body_schema],
                "response_schema": [f.model_dump() for f in endpoint.response_schema],
                "role_access": endpoint.role_access,
                "rate_limited": endpoint.rate_limited,
            }
            inventory.append(entry)
        
        return {"endpoints": inventory}
    
    def generate_hidden_surface_report(self) -> str:
        """Generate hidden surface report in Markdown."""
        if not self._master_intel:
            self.aggregate_from_files()
        
        lines = ["# Hidden Surface Report\n"]
        
        lines.append("## Hidden Routes (from JS bundles)\n")
        for route in self._master_intel.hidden_routes:
            lines.append(f"- `{route.url}` (source: {route.source})")
        
        lines.append("\n## GraphQL Surface\n")
        if self._master_intel.graphql_intel:
            gql = self._master_intel.graphql_intel
            lines.append(f"- Endpoint: `{gql.endpoint_url}`")
            lines.append(f"- Introspection: {'enabled' if gql.introspection_enabled else 'disabled'}")
            lines.append(f"- Operations: {len(gql.operations)}")
            lines.append(f"- Batching: {'supported' if gql.supports_batching else 'not supported'}")
            if gql.sensitive_fields:
                lines.append(f"- Sensitive fields: {', '.join(gql.sensitive_fields[:10])}")
        else:
            lines.append("- No GraphQL endpoint detected")
        
        lines.append("\n## WebSocket Surface\n")
        if self._master_intel.websocket_intel:
            for ws in self._master_intel.websocket_intel:
                lines.append(f"- `{ws.endpoint_url}`")
                lines.append(f"  - Auth: {ws.auth_mechanism} (enforced at {ws.auth_enforced_at})")
                lines.append(f"  - Channels: {', '.join(ws.channels_discovered[:5])}")
        else:
            lines.append("- No WebSocket endpoints detected")
        
        lines.append("\n## Async Flows\n")
        for flow in self._master_intel.async_flows:
            guessable = "⚠️ GUESSABLE" if flow.is_guessable else ""
            lines.append(f"- {flow.name}: `{flow.trigger_endpoint}` (ID format: {flow.job_id_format}) {guessable}")
        
        lines.append("\n## Sensitive Surfaces\n")
        open_surfaces = [s for s in self._master_intel.sensitive_surfaces if s.classification in ("RESPONDS", "OPEN")]
        leaking_surfaces = [s for s in self._master_intel.sensitive_surfaces if s.leaks_metadata]
        
        if open_surfaces:
            lines.append("### Open Access\n")
            for surf in open_surfaces[:20]:
                lines.append(f"- `{surf.path}` ({surf.status_code})")
        
        if leaking_surfaces:
            lines.append("\n### Leaking Metadata\n")
            for surf in leaking_surfaces[:20]:
                lines.append(f"- `{surf.path}`: {', '.join(surf.metadata_leaked)}")
        
        return "\n".join(lines)
    
    def save_all_outputs(self) -> dict[str, str]:
        """
        Save all aggregated outputs.
        
        Returns:
            Dict of output name to file path
        """
        if not self._master_intel:
            self.aggregate_from_files()
        
        outputs = {}
        
        master_path = self.config.get_output_path(
            "recon", "intelligence", "master_intel.json"
        )
        data = add_meta_to_output(
            self._master_intel.model_dump(),
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        atomic_write_json(master_path, data)
        outputs["master_intel"] = str(master_path)
        
        route_map = self.generate_route_map()
        route_map_path = self.config.get_output_path(
            "recon", "intelligence", "route_map.json"
        )
        atomic_write_json(route_map_path, add_meta_to_output(
            route_map, target_url=self.config.target_url, phase="recon", run_id=self.run_id
        ))
        outputs["route_map"] = str(route_map_path)
        
        endpoint_inv = self.generate_endpoint_inventory()
        endpoint_inv_path = self.config.get_output_path(
            "recon", "intelligence", "endpoint_inventory.json"
        )
        atomic_write_json(endpoint_inv_path, add_meta_to_output(
            endpoint_inv, target_url=self.config.target_url, phase="recon", run_id=self.run_id
        ))
        outputs["endpoint_inventory"] = str(endpoint_inv_path)
        
        hidden_report = self.generate_hidden_surface_report()
        hidden_report_path = self.config.get_output_path(
            "recon", "intelligence", "hidden_surface_report.md"
        )
        atomic_write_text(hidden_report_path, hidden_report)
        outputs["hidden_surface_report"] = str(hidden_report_path)
        
        import pandas as pd
        
        if self._master_intel.permission_matrix.entries:
            perm_data = []
            for entry in self._master_intel.permission_matrix.entries:
                perm_data.append({
                    "role": entry.role,
                    "object": entry.object_type,
                    "action": entry.action,
                    "allowed": entry.allowed,
                    "source": entry.source,
                })
            
            df = pd.DataFrame(perm_data)
            csv_path = self.config.get_output_path(
                "recon", "intelligence", "role_state_matrix.csv"
            )
            df.to_csv(csv_path, index=False)
            outputs["role_state_matrix"] = str(csv_path)
        
        logger.info(f"Saved {len(outputs)} intelligence output files")
        
        return outputs
    
    def get_summary(self) -> dict:
        """Get summary of aggregated intelligence."""
        if not self._master_intel:
            self.aggregate_from_files()
        
        return {
            "routes_count": len(self._master_intel.routes),
            "hidden_routes_count": len(self._master_intel.hidden_routes),
            "endpoints_count": len(self._master_intel.endpoints),
            "objects_count": len(self._master_intel.objects),
            "workflows_count": len(self._master_intel.workflows),
            "has_graphql": self._master_intel.graphql_intel is not None,
            "websocket_endpoints": len(self._master_intel.websocket_intel),
            "async_flows_count": len(self._master_intel.async_flows),
            "sensitive_surfaces_count": len(self._master_intel.sensitive_surfaces),
            "missing_security_controls": self._master_intel.security_controls.missing_controls,
            "weak_security_controls": self._master_intel.security_controls.weak_controls,
        }


def run_intelligence_aggregation(run_id: Optional[str] = None) -> IntelligenceAggregator:
    """
    Run intelligence aggregation.
    
    Args:
        run_id: Run ID
        
    Returns:
        IntelligenceAggregator instance with results
    """
    aggregator = IntelligenceAggregator(run_id=run_id)
    aggregator.aggregate_from_files()
    aggregator.save_all_outputs()
    return aggregator


if __name__ == "__main__":
    aggregator = IntelligenceAggregator()
    
    intel = aggregator.aggregate_from_files()
    outputs = aggregator.save_all_outputs()
    summary = aggregator.get_summary()
    
    print("Intelligence Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\nOutput files:")
    for name, path in outputs.items():
        print(f"  {name}: {path}")
