"""
NetworkX-based attack graph builder for CyberAI platform.
Builds and analyzes graphs of attack surfaces, transitions, and vulnerabilities.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import networkx as nx
from loguru import logger

from cyberAI.config import get_config
from cyberAI.utils.helpers import atomic_write_json, atomic_write_text


class AttackGraph:
    """
    Builds and manages an attack graph using NetworkX.
    Nodes represent (endpoint, role, state) tuples.
    Edges represent observed transitions with evidence.
    """
    
    def __init__(self):
        self._graph = nx.DiGraph()
        self._transitions: list[dict] = []
        self._suspicious_paths: list[list[str]] = []
        self._lock_nodes: set[str] = set()
    
    def _make_node_id(
        self,
        endpoint: str,
        role: Optional[str] = None,
        state: Optional[str] = None
    ) -> str:
        """Create a unique node ID from endpoint, role, and state."""
        parts = [endpoint]
        if role:
            parts.append(f"role:{role}")
        if state:
            parts.append(f"state:{state}")
        return "|".join(parts)
    
    def add_node(
        self,
        endpoint: str,
        role: Optional[str] = None,
        state: Optional[str] = None,
        node_type: str = "endpoint",
        **attributes
    ) -> str:
        """
        Add a node to the attack graph.
        
        Args:
            endpoint: Endpoint URL or identifier
            role: Role context
            state: State context
            node_type: Type of node (endpoint, state, role, object)
            **attributes: Additional node attributes
            
        Returns:
            Node ID
        """
        node_id = self._make_node_id(endpoint, role, state)
        
        self._graph.add_node(
            node_id,
            endpoint=endpoint,
            role=role,
            state=state,
            node_type=node_type,
            created_at=datetime.utcnow().isoformat(),
            **attributes
        )
        
        return node_id
    
    def add_transition(
        self,
        actor: str,
        obj: str,
        endpoint: str,
        from_state: str,
        to_state: str,
        evidence: Optional[dict] = None,
        **attributes
    ) -> tuple[str, str]:
        """
        Add a transition (edge) to the attack graph.
        
        Args:
            actor: Actor performing the transition (role/user)
            obj: Object being acted upon
            endpoint: Endpoint used for the transition
            from_state: Source state
            to_state: Target state
            evidence: Evidence dict (request/response data)
            **attributes: Additional edge attributes
            
        Returns:
            Tuple of (from_node_id, to_node_id)
        """
        from_node = self.add_node(endpoint, role=actor, state=from_state, object=obj)
        to_node = self.add_node(endpoint, role=actor, state=to_state, object=obj)
        
        edge_data = {
            "actor": actor,
            "object": obj,
            "endpoint": endpoint,
            "from_state": from_state,
            "to_state": to_state,
            "evidence": evidence or {},
            "observed_at": datetime.utcnow().isoformat(),
            **attributes
        }
        
        self._graph.add_edge(from_node, to_node, **edge_data)
        
        self._transitions.append({
            "from": from_node,
            "to": to_node,
            **edge_data
        })
        
        return from_node, to_node
    
    def add_access_edge(
        self,
        from_endpoint: str,
        to_endpoint: str,
        role: str,
        access_type: str = "normal",
        **attributes
    ) -> None:
        """
        Add an access edge between endpoints.
        
        Args:
            from_endpoint: Source endpoint
            to_endpoint: Target endpoint
            role: Role performing the access
            access_type: Type of access (normal, elevated, unauthorized)
            **attributes: Additional edge attributes
        """
        from_node = self.add_node(from_endpoint, role=role)
        to_node = self.add_node(to_endpoint, role=role)
        
        self._graph.add_edge(
            from_node,
            to_node,
            access_type=access_type,
            role=role,
            **attributes
        )
    
    def mark_suspicious(self, node_id: str, reason: str) -> None:
        """Mark a node as suspicious."""
        if node_id in self._graph:
            self._graph.nodes[node_id]["suspicious"] = True
            self._graph.nodes[node_id]["suspicious_reason"] = reason
    
    def find_suspicious_paths(
        self,
        expected_preconditions: Optional[dict[str, list[str]]] = None
    ) -> list[list[str]]:
        """
        Find paths that skip expected preconditions or cross role boundaries.
        
        Args:
            expected_preconditions: Dict mapping states to required predecessor states
            
        Returns:
            List of suspicious path lists
        """
        expected_preconditions = expected_preconditions or {}
        suspicious_paths = []
        
        for target_state, required_states in expected_preconditions.items():
            target_nodes = [
                n for n, d in self._graph.nodes(data=True)
                if d.get("state") == target_state
            ]
            
            for target_node in target_nodes:
                predecessors = list(self._graph.predecessors(target_node))
                for pred in predecessors:
                    pred_data = self._graph.nodes[pred]
                    pred_state = pred_data.get("state")
                    
                    if pred_state and pred_state not in required_states:
                        path = [pred, target_node]
                        suspicious_paths.append(path)
                        logger.warning(
                            f"Suspicious transition: {pred_state} -> {target_state} "
                            f"(expected from: {required_states})"
                        )
        
        roles_per_node = {}
        for node, data in self._graph.nodes(data=True):
            endpoint = data.get("endpoint", "")
            role = data.get("role")
            if endpoint not in roles_per_node:
                roles_per_node[endpoint] = set()
            if role:
                roles_per_node[endpoint].add(role)
        
        for endpoint, roles in roles_per_node.items():
            if len(roles) > 1:
                nodes = [
                    n for n, d in self._graph.nodes(data=True)
                    if d.get("endpoint") == endpoint
                ]
                for i, node1 in enumerate(nodes):
                    for node2 in nodes[i + 1:]:
                        if self._graph.has_edge(node1, node2):
                            role1 = self._graph.nodes[node1].get("role")
                            role2 = self._graph.nodes[node2].get("role")
                            if role1 != role2:
                                suspicious_paths.append([node1, node2])
        
        self._suspicious_paths = suspicious_paths
        return suspicious_paths
    
    def find_all_paths(
        self,
        source: str,
        target: str,
        max_length: int = 10
    ) -> list[list[str]]:
        """
        Find all paths between two nodes.
        
        Args:
            source: Source node ID
            target: Target node ID
            max_length: Maximum path length
            
        Returns:
            List of paths (each path is a list of node IDs)
        """
        try:
            paths = list(nx.all_simple_paths(
                self._graph, source, target, cutoff=max_length
            ))
            return paths
        except nx.NodeNotFound:
            return []
    
    def get_reachable_from(self, node_id: str, max_depth: int = 5) -> set[str]:
        """Get all nodes reachable from a given node."""
        if node_id not in self._graph:
            return set()
        return set(nx.descendants(self._graph, node_id))
    
    def get_node_info(self, node_id: str) -> Optional[dict]:
        """Get information about a node."""
        if node_id in self._graph:
            return dict(self._graph.nodes[node_id])
        return None
    
    def get_edge_info(self, from_node: str, to_node: str) -> Optional[dict]:
        """Get information about an edge."""
        if self._graph.has_edge(from_node, to_node):
            return dict(self._graph.edges[from_node, to_node])
        return None
    
    def get_statistics(self) -> dict:
        """Get graph statistics."""
        return {
            "node_count": self._graph.number_of_nodes(),
            "edge_count": self._graph.number_of_edges(),
            "transition_count": len(self._transitions),
            "suspicious_path_count": len(self._suspicious_paths),
            "is_connected": nx.is_weakly_connected(self._graph) if self._graph.number_of_nodes() > 0 else False,
            "density": nx.density(self._graph) if self._graph.number_of_nodes() > 0 else 0,
        }
    
    def export_to_json(self, path: Path) -> None:
        """
        Export the graph to JSON format.
        
        Args:
            path: Output file path
        """
        data = {
            "_meta": {
                "generated_at": datetime.utcnow().isoformat(),
                "version": "1.0.0",
            },
            "statistics": self.get_statistics(),
            "nodes": [
                {"id": n, **d}
                for n, d in self._graph.nodes(data=True)
            ],
            "edges": [
                {"source": u, "target": v, **d}
                for u, v, d in self._graph.edges(data=True)
            ],
            "transitions": self._transitions,
            "suspicious_paths": self._suspicious_paths,
        }
        
        atomic_write_json(path, data)
        logger.info(f"Exported attack graph to {path}")
    
    def export_to_dot(self, path: Path) -> None:
        """
        Export the graph to DOT format for visualization.
        
        Args:
            path: Output file path
        """
        dot_lines = ["digraph AttackGraph {"]
        dot_lines.append('    rankdir=LR;')
        dot_lines.append('    node [shape=box, style=filled, fillcolor=lightblue];')
        
        for node, data in self._graph.nodes(data=True):
            label = data.get("endpoint", node)[:50]
            role = data.get("role", "")
            state = data.get("state", "")
            
            if role:
                label += f"\\n[{role}]"
            if state:
                label += f"\\n({state})"
            
            color = "lightblue"
            if data.get("suspicious"):
                color = "salmon"
            elif data.get("node_type") == "state":
                color = "lightgreen"
            
            safe_node = node.replace('"', '\\"').replace('|', '_')
            dot_lines.append(f'    "{safe_node}" [label="{label}", fillcolor={color}];')
        
        for u, v, data in self._graph.edges(data=True):
            safe_u = u.replace('"', '\\"').replace('|', '_')
            safe_v = v.replace('"', '\\"').replace('|', '_')
            
            label = data.get("from_state", "")
            if data.get("to_state"):
                label += f" -> {data['to_state']}"
            
            color = "black"
            if data.get("access_type") == "unauthorized":
                color = "red"
            elif data.get("access_type") == "elevated":
                color = "orange"
            
            dot_lines.append(f'    "{safe_u}" -> "{safe_v}" [label="{label}", color={color}];')
        
        dot_lines.append("}")
        
        content = "\n".join(dot_lines)
        atomic_write_text(path, content)
        logger.info(f"Exported attack graph to DOT: {path}")
    
    def import_from_json(self, path: Path) -> None:
        """
        Import a graph from JSON format.
        
        Args:
            path: Input file path
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self._graph = nx.DiGraph()
        
        for node_data in data.get("nodes", []):
            node_id = node_data.pop("id")
            self._graph.add_node(node_id, **node_data)
        
        for edge_data in data.get("edges", []):
            source = edge_data.pop("source")
            target = edge_data.pop("target")
            self._graph.add_edge(source, target, **edge_data)
        
        self._transitions = data.get("transitions", [])
        self._suspicious_paths = data.get("suspicious_paths", [])
        
        logger.info(f"Imported attack graph from {path}")
    
    def merge(self, other: "AttackGraph") -> None:
        """
        Merge another attack graph into this one.
        
        Args:
            other: Another AttackGraph instance
        """
        self._graph = nx.compose(self._graph, other._graph)
        self._transitions.extend(other._transitions)
        self._suspicious_paths.extend(other._suspicious_paths)
    
    def clear(self) -> None:
        """Clear the graph."""
        self._graph = nx.DiGraph()
        self._transitions.clear()
        self._suspicious_paths.clear()


_attack_graph: Optional[AttackGraph] = None


def get_attack_graph() -> AttackGraph:
    """Get the global attack graph instance."""
    global _attack_graph
    if _attack_graph is None:
        _attack_graph = AttackGraph()
    return _attack_graph


if __name__ == "__main__":
    graph = AttackGraph()
    
    graph.add_node("/api/users", role="user", state="authenticated")
    graph.add_node("/api/admin", role="admin", state="authenticated")
    graph.add_node("/api/admin", role="user", state="authenticated")
    
    graph.add_transition(
        actor="user",
        obj="profile",
        endpoint="/api/profile",
        from_state="draft",
        to_state="published",
        evidence={"status_code": 200}
    )
    
    graph.add_transition(
        actor="user",
        obj="profile",
        endpoint="/api/profile",
        from_state="draft",
        to_state="approved",
        evidence={"status_code": 200}
    )
    
    suspicious = graph.find_suspicious_paths(
        expected_preconditions={
            "approved": ["submitted", "pending_review"],
        }
    )
    print(f"Suspicious paths found: {len(suspicious)}")
    
    stats = graph.get_statistics()
    print(f"Graph statistics: {stats}")
    
    config = get_config()
    json_path = config.get_output_path("testing", "attack_graph.json")
    graph.export_to_json(json_path)
    
    dot_path = config.get_output_path("testing", "attack_graph.dot")
    graph.export_to_dot(dot_path)
    
    print("Attack graph tests completed.")
