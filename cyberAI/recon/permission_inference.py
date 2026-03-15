"""
Step 11: Permission Inference - Build permission matrix from observations.
Infers allowed/denied permissions from role diffs, UI conditionals, and error patterns.
"""

from typing import Any, Optional

import pandas as pd
from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import (
    Endpoint,
    ObjectModel,
    PermissionEntry,
    PermissionMatrix,
    RoleDiff,
)
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    generate_run_id,
)


class PermissionInference:
    """
    Infers permission matrix from observed behavior across roles.
    """
    
    COMMON_ACTIONS = ["read", "create", "update", "delete", "list", "admin"]
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._matrix = PermissionMatrix()
        self._roles: set[str] = set()
        self._objects: set[str] = set()
        self._actions: set[str] = set()
    
    def _infer_action_from_method(self, method: str) -> str:
        """Infer action from HTTP method."""
        method = method.upper()
        if method == "GET":
            return "read"
        elif method == "POST":
            return "create"
        elif method in ("PUT", "PATCH"):
            return "update"
        elif method == "DELETE":
            return "delete"
        return "other"
    
    def _infer_object_from_endpoint(self, endpoint_url: str) -> str:
        """Extract object type from endpoint URL."""
        import re
        
        patterns = [
            r'/api/(?:v\d+/)?(\w+)s?(?:/|$)',
            r'/(\w+)s?/[0-9a-f-]+',
            r'/(\w+)s?$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, endpoint_url, re.I)
            if match:
                obj = match.group(1).lower()
                if obj not in ('api', 'v1', 'v2', 'v3'):
                    return obj
        
        return "unknown"
    
    def process_role_diffs(self, role_diffs: list[RoleDiff]) -> None:
        """
        Process role diffs to infer permissions.
        
        Args:
            role_diffs: List of RoleDiff objects
        """
        for diff in role_diffs:
            obj_type = self._infer_object_from_endpoint(diff.endpoint_url)
            self._objects.add(obj_type)
            
            method_match = diff.endpoint_url.split(":")[0] if ":" in diff.endpoint_url else "GET"
            action = self._infer_action_from_method(method_match)
            self._actions.add(action)
            
            for role in diff.roles_with_access:
                self._roles.add(role)
                entry = PermissionEntry(
                    role=role,
                    object_type=obj_type,
                    action=action,
                    allowed=True,
                    source="role_diff",
                    evidence=f"Has access to {diff.endpoint_url}",
                )
                self._matrix.entries.append(entry)
            
            for role in diff.roles_without_access:
                self._roles.add(role)
                entry = PermissionEntry(
                    role=role,
                    object_type=obj_type,
                    action=action,
                    allowed=False,
                    source="role_diff",
                    evidence=f"No access to {diff.endpoint_url}",
                )
                self._matrix.entries.append(entry)
    
    def process_endpoints(self, endpoints: list[Endpoint]) -> None:
        """
        Process endpoints to infer permissions from access patterns.
        
        Args:
            endpoints: List of discovered endpoints
        """
        for endpoint in endpoints:
            obj_type = self._infer_object_from_endpoint(endpoint.url)
            self._objects.add(obj_type)
            
            action = self._infer_action_from_method(endpoint.method.value)
            self._actions.add(action)
            
            for role, has_access in endpoint.role_access.items():
                self._roles.add(role)
                entry = PermissionEntry(
                    role=role,
                    object_type=obj_type,
                    action=action,
                    allowed=has_access,
                    source="endpoint_observation",
                    evidence=f"Observed via {endpoint.method} {endpoint.url}",
                )
                self._matrix.entries.append(entry)
    
    def process_objects(self, objects: list[ObjectModel]) -> None:
        """
        Add objects to the permission matrix.
        
        Args:
            objects: List of ObjectModel objects
        """
        for obj in objects:
            self._objects.add(obj.name)
    
    def add_permission_hint(
        self,
        role: str,
        obj: str,
        action: str,
        allowed: Optional[bool],
        source: str,
        evidence: str = "",
    ) -> None:
        """
        Add a permission hint to the matrix.
        
        Args:
            role: Role name
            obj: Object type
            action: Action name
            allowed: Permission value (None = unknown)
            source: Source of inference
            evidence: Supporting evidence
        """
        self._roles.add(role)
        self._objects.add(obj)
        self._actions.add(action)
        
        entry = PermissionEntry(
            role=role,
            object_type=obj,
            action=action,
            allowed=allowed,
            source=source,
            evidence=evidence,
        )
        self._matrix.entries.append(entry)
    
    def fill_unknown_cells(self) -> None:
        """
        Fill unknown cells in the permission matrix.
        Marks combinations without observations as unknown.
        """
        existing = set()
        for entry in self._matrix.entries:
            existing.add((entry.role, entry.object_type, entry.action))
        
        for role in self._roles:
            for obj in self._objects:
                for action in self._actions:
                    if (role, obj, action) not in existing:
                        entry = PermissionEntry(
                            role=role,
                            object_type=obj,
                            action=action,
                            allowed=None,
                            source="unknown",
                            evidence="No observation",
                        )
                        self._matrix.entries.append(entry)
    
    def consolidate_matrix(self) -> PermissionMatrix:
        """
        Consolidate the permission matrix by deduplicating entries.
        
        Returns:
            Consolidated PermissionMatrix
        """
        consolidated: dict[tuple, PermissionEntry] = {}
        
        for entry in self._matrix.entries:
            key = (entry.role, entry.object_type, entry.action)
            
            if key not in consolidated:
                consolidated[key] = entry
            elif entry.allowed is not None and consolidated[key].allowed is None:
                consolidated[key] = entry
            elif entry.source in ("tested", "observed") and consolidated[key].source == "inferred":
                consolidated[key] = entry
        
        self._matrix.entries = list(consolidated.values())
        self._matrix.roles = list(self._roles)
        self._matrix.objects = list(self._objects)
        self._matrix.actions = list(self._actions)
        self._matrix.unknown_count = len([e for e in self._matrix.entries if e.allowed is None])
        
        return self._matrix
    
    def get_matrix(self) -> PermissionMatrix:
        """Get the current permission matrix."""
        return self._matrix
    
    def get_unknown_permissions(self) -> list[PermissionEntry]:
        """Get list of unknown permissions for targeted testing."""
        return [e for e in self._matrix.entries if e.allowed is None]
    
    def export_to_dataframe(self) -> pd.DataFrame:
        """
        Export permission matrix to pandas DataFrame.
        
        Returns:
            DataFrame representation of the matrix
        """
        data = []
        
        for entry in self._matrix.entries:
            data.append({
                "role": entry.role,
                "object": entry.object_type,
                "action": entry.action,
                "allowed": entry.allowed,
                "source": entry.source,
            })
        
        return pd.DataFrame(data)
    
    def save_matrix(self) -> tuple[str, str]:
        """
        Save permission matrix to JSON and CSV files.
        
        Returns:
            Tuple of (json_path, csv_path)
        """
        self.consolidate_matrix()
        
        json_path = self.config.get_output_path(
            "recon", "intelligence", "permission_matrix.json"
        )
        
        data = add_meta_to_output(
            {
                "matrix": self._matrix.model_dump(),
                "summary": {
                    "roles": len(self._roles),
                    "objects": len(self._objects),
                    "actions": len(self._actions),
                    "total_entries": len(self._matrix.entries),
                    "unknown_count": self._matrix.unknown_count,
                },
            },
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        
        atomic_write_json(json_path, data)
        
        csv_path = self.config.get_output_path(
            "recon", "intelligence", "permission_matrix.csv"
        )
        
        df = self.export_to_dataframe()
        df.to_csv(csv_path, index=False)
        
        logger.info(f"Saved permission matrix with {len(self._matrix.entries)} entries")
        
        return str(json_path), str(csv_path)


def run_permission_inference(
    role_diffs: list[RoleDiff],
    endpoints: list[Endpoint],
    objects: list[ObjectModel],
    run_id: Optional[str] = None,
) -> PermissionInference:
    """
    Run permission inference.
    
    Args:
        role_diffs: Role difference data
        endpoints: Discovered endpoints
        objects: Discovered objects
        run_id: Run ID
        
    Returns:
        PermissionInference instance with results
    """
    inference = PermissionInference(run_id=run_id)
    inference.process_role_diffs(role_diffs)
    inference.process_endpoints(endpoints)
    inference.process_objects(objects)
    inference.fill_unknown_cells()
    inference.save_matrix()
    return inference


if __name__ == "__main__":
    inference = PermissionInference()
    
    inference.add_permission_hint("admin", "user", "read", True, "test")
    inference.add_permission_hint("admin", "user", "delete", True, "test")
    inference.add_permission_hint("user", "user", "read", True, "test")
    inference.add_permission_hint("user", "user", "delete", False, "test")
    inference.add_permission_hint("guest", "user", "read", False, "test")
    
    inference.fill_unknown_cells()
    inference.save_matrix()
    
    df = inference.export_to_dataframe()
    print(df.to_string())
    
    unknown = inference.get_unknown_permissions()
    print(f"\nUnknown permissions: {len(unknown)}")
