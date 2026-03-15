"""
Step 12: Workflow Mapper - Multi-step workflow state machine discovery.
Identifies workflows, builds state graphs, and flags suspicious transitions.
"""

from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import (
    RequestRecord,
    Route,
    WorkflowEdge,
    WorkflowGraph,
    WorkflowNode,
)
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    atomic_write_text,
    generate_run_id,
)


class WorkflowMapper:
    """
    Maps multi-step workflows and builds state transition graphs.
    """
    
    WORKFLOW_INDICATORS = [
        "step", "stage", "phase", "wizard", "onboarding",
        "checkout", "signup", "registration", "verification",
        "approval", "review", "publish", "submit",
    ]
    
    STATE_PATTERNS = [
        "draft", "pending", "submitted", "in_review", "approved",
        "rejected", "published", "archived", "deleted", "active",
        "inactive", "suspended", "completed", "cancelled", "expired",
    ]
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._workflows: dict[str, WorkflowGraph] = {}
        self._observed_transitions: list[dict] = []
    
    def _identify_workflow_from_url(self, url: str) -> Optional[str]:
        """Identify workflow name from URL pattern."""
        url_lower = url.lower()
        
        for indicator in self.WORKFLOW_INDICATORS:
            if indicator in url_lower:
                return indicator
        
        return None
    
    def _extract_state_from_response(self, response: dict) -> Optional[str]:
        """Extract state from response data."""
        state_keys = ['status', 'state', 'phase', 'stage', 'step']
        
        for key in state_keys:
            if key in response:
                value = response[key]
                if isinstance(value, str):
                    return value.lower()
        
        return None
    
    def _detect_workflow_step(self, route: Route) -> Optional[dict]:
        """
        Detect if a route is part of a workflow.
        
        Args:
            route: Route to analyze
            
        Returns:
            Workflow step info if detected
        """
        workflow_name = self._identify_workflow_from_url(route.url)
        
        if not workflow_name:
            for action in route.actions:
                if action.text:
                    text_lower = action.text.lower()
                    for indicator in self.WORKFLOW_INDICATORS:
                        if indicator in text_lower:
                            workflow_name = indicator
                            break
                if workflow_name:
                    break
        
        if not workflow_name:
            return None
        
        step_number = None
        import re
        step_match = re.search(r'step[_-]?(\d+)', route.url, re.I)
        if step_match:
            step_number = int(step_match.group(1))
        
        return {
            "workflow": workflow_name,
            "step": step_number,
            "route": route,
        }
    
    def process_routes(self, routes: list[Route]) -> None:
        """
        Process routes to identify workflow patterns.
        
        Args:
            routes: List of discovered routes
        """
        workflow_routes: dict[str, list[dict]] = {}
        
        for route in routes:
            step_info = self._detect_workflow_step(route)
            if step_info:
                workflow = step_info["workflow"]
                if workflow not in workflow_routes:
                    workflow_routes[workflow] = []
                workflow_routes[workflow].append(step_info)
        
        for workflow_name, steps in workflow_routes.items():
            self._build_workflow_graph(workflow_name, steps)
    
    def process_requests(self, requests: list[RequestRecord]) -> None:
        """
        Process requests to identify state transitions.
        
        Args:
            requests: List of request records
        """
        for i, record in enumerate(requests[:-1]):
            if not record.response_json:
                continue
            
            current_state = self._extract_state_from_response(record.response_json)
            if not current_state:
                continue
            
            for next_record in requests[i+1:i+5]:
                if next_record.response_json:
                    next_state = self._extract_state_from_response(next_record.response_json)
                    if next_state and next_state != current_state:
                        self._observed_transitions.append({
                            "from_state": current_state,
                            "to_state": next_state,
                            "action_url": next_record.url,
                            "method": next_record.method.value,
                        })
                        break
    
    def _build_workflow_graph(self, name: str, steps: list[dict]) -> WorkflowGraph:
        """
        Build a workflow graph from discovered steps.
        
        Args:
            name: Workflow name
            steps: List of step info dicts
            
        Returns:
            WorkflowGraph object
        """
        nodes = []
        edges = []
        
        steps_sorted = sorted(steps, key=lambda x: x.get("step") or 0)
        
        for i, step in enumerate(steps_sorted):
            step_num = step.get("step") or i
            state = f"step_{step_num}"
            
            node = WorkflowNode(
                id=f"{name}_{state}",
                state=state,
                description=step["route"].page_title,
                is_initial=(i == 0),
                is_terminal=(i == len(steps_sorted) - 1),
            )
            nodes.append(node)
        
        for i in range(len(nodes) - 1):
            edge = WorkflowEdge(
                from_state=nodes[i].state,
                to_state=nodes[i + 1].state,
                action="next",
                is_reversible=True,
            )
            edges.append(edge)
        
        graph = WorkflowGraph(
            name=name,
            nodes=nodes,
            edges=edges,
        )
        
        self._workflows[name] = graph
        return graph
    
    def add_workflow_from_transitions(
        self,
        name: str,
        transitions: list[tuple[str, str, str]],
    ) -> WorkflowGraph:
        """
        Build workflow from known transitions.
        
        Args:
            name: Workflow name
            transitions: List of (from_state, to_state, action) tuples
            
        Returns:
            WorkflowGraph object
        """
        states = set()
        for from_s, to_s, _ in transitions:
            states.add(from_s)
            states.add(to_s)
        
        nodes = []
        for state in states:
            node = WorkflowNode(
                id=f"{name}_{state}",
                state=state,
            )
            nodes.append(node)
        
        edges = []
        for from_s, to_s, action in transitions:
            edge = WorkflowEdge(
                from_state=from_s,
                to_state=to_s,
                action=action,
            )
            edges.append(edge)
        
        graph = WorkflowGraph(
            name=name,
            nodes=nodes,
            edges=edges,
        )
        
        self._workflows[name] = graph
        return graph
    
    def find_suspicious_transitions(self) -> list[str]:
        """
        Find suspicious transitions that might be exploitable.
        
        Returns:
            List of suspicious transition descriptions
        """
        suspicious = []
        
        terminal_states = {"completed", "approved", "published", "paid"}
        initial_states = {"draft", "pending", "created", "new"}
        
        for workflow in self._workflows.values():
            terminal_nodes = [n for n in workflow.nodes if n.is_terminal or n.state in terminal_states]
            
            for edge in workflow.edges:
                from_state = edge.from_state.lower()
                to_state = edge.to_state.lower()
                
                if from_state in initial_states and to_state in terminal_states:
                    desc = f"{workflow.name}: Direct jump from {from_state} to {to_state}"
                    suspicious.append(desc)
                    workflow.suspicious_transitions.append(desc)
                
                if not edge.is_reversible:
                    for other_edge in workflow.edges:
                        if other_edge.from_state == edge.to_state and other_edge.to_state == edge.from_state:
                            desc = f"{workflow.name}: Reverse of irreversible transition {edge.from_state} -> {edge.to_state}"
                            suspicious.append(desc)
        
        return suspicious
    
    def export_to_dot(self, workflow: WorkflowGraph) -> str:
        """
        Export workflow to DOT format.
        
        Args:
            workflow: WorkflowGraph to export
            
        Returns:
            DOT format string
        """
        lines = [f"digraph {workflow.name} {{"]
        lines.append("    rankdir=LR;")
        lines.append('    node [shape=box, style=filled, fillcolor=lightblue];')
        
        for node in workflow.nodes:
            color = "lightblue"
            if node.is_initial:
                color = "lightgreen"
            elif node.is_terminal:
                color = "lightyellow"
            
            if node.state in [t.split()[-1] for t in workflow.suspicious_transitions]:
                color = "salmon"
            
            lines.append(f'    "{node.state}" [fillcolor={color}];')
        
        for edge in workflow.edges:
            style = ""
            if edge.requires_approval:
                style = ", style=dashed"
            elif edge.requires_payment:
                style = ", color=green"
            
            label = edge.action
            if edge.preconditions:
                label += f" [{', '.join(edge.preconditions)}]"
            
            lines.append(f'    "{edge.from_state}" -> "{edge.to_state}" [label="{label}"{style}];')
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def save_workflows(self) -> str:
        """
        Save all workflows to files.
        
        Returns:
            Path to main JSON file
        """
        json_path = self.config.get_output_path(
            "recon", "intelligence", "workflows.json"
        )
        
        suspicious = self.find_suspicious_transitions()
        
        data = add_meta_to_output(
            {
                "workflows": {
                    name: wf.model_dump()
                    for name, wf in self._workflows.items()
                },
                "observed_transitions": self._observed_transitions,
                "suspicious_transitions": suspicious,
            },
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        
        atomic_write_json(json_path, data)
        
        for name, workflow in self._workflows.items():
            dot_content = self.export_to_dot(workflow)
            dot_path = self.config.get_output_path(
                "recon", "intelligence", f"workflow_{name}.dot"
            )
            atomic_write_text(dot_path, dot_content)
        
        logger.info(f"Saved {len(self._workflows)} workflows")
        
        return str(json_path)


def run_workflow_mapper(
    routes: list[Route],
    requests: list[RequestRecord],
    run_id: Optional[str] = None,
) -> WorkflowMapper:
    """
    Run workflow mapping.
    
    Args:
        routes: Discovered routes
        requests: Captured requests
        run_id: Run ID
        
    Returns:
        WorkflowMapper instance with results
    """
    mapper = WorkflowMapper(run_id=run_id)
    mapper.process_routes(routes)
    mapper.process_requests(requests)
    mapper.save_workflows()
    return mapper


if __name__ == "__main__":
    mapper = WorkflowMapper()
    
    mapper.add_workflow_from_transitions(
        "order",
        [
            ("draft", "submitted", "submit"),
            ("submitted", "in_review", "assign_reviewer"),
            ("in_review", "approved", "approve"),
            ("in_review", "rejected", "reject"),
            ("approved", "completed", "fulfill"),
            ("draft", "completed", "skip_review"),
        ]
    )
    
    suspicious = mapper.find_suspicious_transitions()
    print(f"Suspicious transitions: {suspicious}")
    
    mapper.save_workflows()
