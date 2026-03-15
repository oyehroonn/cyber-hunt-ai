"""
Step 10: Object Model - Resource type inference and relationship mapping.
Infers object models, ownership, and relationships from captured data.
"""

import re
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import Endpoint, ObjectField, ObjectModel, RequestRecord
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    generate_run_id,
)


class ObjectModelBuilder:
    """
    Builds object models from observed API responses and requests.
    """
    
    HIGH_CRITICALITY_OBJECTS = [
        "user", "account", "admin", "payment", "session", "token",
        "invitation", "credential", "key", "secret", "billing",
    ]
    
    MEDIUM_CRITICALITY_OBJECTS = [
        "project", "organization", "team", "file", "document",
        "workspace", "group", "member", "role",
    ]
    
    OWNERSHIP_FIELDS = [
        "user_id", "userId", "owner_id", "ownerId", "created_by",
        "createdBy", "author_id", "authorId", "org_id", "orgId",
        "organization_id", "organizationId", "tenant_id", "tenantId",
        "team_id", "teamId", "workspace_id", "workspaceId",
    ]
    
    SENSITIVE_FIELD_PATTERNS = [
        "password", "secret", "token", "key", "credential",
        "ssn", "credit_card", "creditCard", "cvv", "pin",
        "private", "hash", "salt", "api_key", "apiKey",
    ]
    
    LIFECYCLE_STATE_PATTERNS = [
        "status", "state", "phase", "stage",
    ]
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._objects: dict[str, ObjectModel] = {}
        self._object_endpoints: dict[str, list[str]] = {}
    
    def _infer_object_name(self, endpoint: Endpoint) -> Optional[str]:
        """
        Infer object name from endpoint URL pattern.
        
        Args:
            endpoint: Endpoint to analyze
            
        Returns:
            Inferred object name
        """
        path = endpoint.path_pattern or endpoint.url
        
        patterns = [
            r'/api/(?:v\d+/)?(\w+)s?/',
            r'/api/(?:v\d+/)?(\w+)s?$',
            r'/(\w+)s?/\{',
            r'/(\w+)s?/[0-9a-f-]+',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, path, re.I)
            if match:
                name = match.group(1).lower()
                if name not in ('api', 'v1', 'v2', 'v3'):
                    return name
        
        return None
    
    def _analyze_id_format(self, values: list[Any]) -> str:
        """
        Analyze ID format from sample values.
        
        Args:
            values: Sample ID values
            
        Returns:
            ID format classification
        """
        if not values:
            return "unknown"
        
        sample = str(values[0])
        
        if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', sample, re.I):
            return "uuid"
        elif sample.isdigit():
            return "integer"
        elif re.match(r'^[a-z0-9-]+$', sample, re.I) and len(sample) < 50:
            return "slug"
        else:
            return "custom"
    
    def _extract_fields(self, data: dict, prefix: str = "") -> list[ObjectField]:
        """
        Extract field information from response data.
        
        Args:
            data: Response data dict
            prefix: Field name prefix for nested fields
            
        Returns:
            List of ObjectField objects
        """
        fields = []
        
        for key, value in data.items():
            full_name = f"{prefix}.{key}" if prefix else key
            
            if value is None:
                field_type = "null"
            elif isinstance(value, bool):
                field_type = "boolean"
            elif isinstance(value, int):
                field_type = "integer"
            elif isinstance(value, float):
                field_type = "number"
            elif isinstance(value, str):
                field_type = "string"
            elif isinstance(value, list):
                field_type = "array"
            elif isinstance(value, dict):
                field_type = "object"
                fields.extend(self._extract_fields(value, full_name))
                continue
            else:
                field_type = "unknown"
            
            is_sensitive = any(
                pattern in key.lower()
                for pattern in self.SENSITIVE_FIELD_PATTERNS
            )
            
            is_identifier = key.lower() in ('id', '_id') or key.lower().endswith('_id')
            
            is_ownership = key in self.OWNERSHIP_FIELDS
            
            fields.append(ObjectField(
                name=full_name,
                field_type=field_type,
                is_sensitive=is_sensitive,
                is_identifier=is_identifier,
                is_ownership=is_ownership,
            ))
        
        return fields
    
    def _infer_lifecycle_states(self, responses: list[dict]) -> list[str]:
        """
        Infer lifecycle states from response data.
        
        Args:
            responses: List of response dicts
            
        Returns:
            List of discovered states
        """
        states = set()
        
        for response in responses:
            for pattern in self.LIFECYCLE_STATE_PATTERNS:
                for key, value in response.items():
                    if pattern in key.lower() and isinstance(value, str):
                        states.add(value.lower())
        
        return list(states)
    
    def _determine_criticality(self, object_name: str) -> str:
        """
        Determine security criticality of an object type.
        
        Args:
            object_name: Object type name
            
        Returns:
            Criticality level (high/medium/low)
        """
        name_lower = object_name.lower()
        
        for pattern in self.HIGH_CRITICALITY_OBJECTS:
            if pattern in name_lower:
                return "high"
        
        for pattern in self.MEDIUM_CRITICALITY_OBJECTS:
            if pattern in name_lower:
                return "medium"
        
        return "low"
    
    def _find_parent_relationships(self, fields: list[ObjectField]) -> dict[str, str]:
        """
        Find parent relationships from fields.
        
        Args:
            fields: List of object fields
            
        Returns:
            Dict of field name to parent object type
        """
        relationships = {}
        
        relationship_patterns = [
            (r'(\w+)_id$', lambda m: m.group(1)),
            (r'(\w+)Id$', lambda m: m.group(1).lower()),
            (r'parent_(\w+)$', lambda m: m.group(1)),
        ]
        
        for field in fields:
            if field.is_identifier and field.name != 'id':
                for pattern, extractor in relationship_patterns:
                    match = re.match(pattern, field.name)
                    if match:
                        parent_type = extractor(match)
                        relationships[field.name] = parent_type
                        break
        
        return relationships
    
    def process_endpoint(
        self,
        endpoint: Endpoint,
        sample_responses: list[dict],
    ) -> Optional[ObjectModel]:
        """
        Process an endpoint to build object model.
        
        Args:
            endpoint: Endpoint to process
            sample_responses: Sample responses from endpoint
            
        Returns:
            ObjectModel if inference successful
        """
        object_name = self._infer_object_name(endpoint)
        if not object_name:
            return None
        
        if object_name in self._objects:
            existing = self._objects[object_name]
            if endpoint.id not in existing.endpoints:
                existing.endpoints.append(endpoint.id)
            return existing
        
        all_fields = []
        for response in sample_responses:
            if isinstance(response, dict):
                all_fields.extend(self._extract_fields(response))
        
        unique_fields = {f.name: f for f in all_fields}
        fields_list = list(unique_fields.values())
        
        id_values = []
        for response in sample_responses:
            if isinstance(response, dict):
                id_val = response.get('id') or response.get('_id')
                if id_val:
                    id_values.append(id_val)
        
        id_format = self._analyze_id_format(id_values)
        
        ownership_fields = [f.name for f in fields_list if f.is_ownership]
        
        sensitive_fields = [f.name for f in fields_list if f.is_sensitive]
        
        readable_fields = fields_list
        
        writable_fields = [
            f for f in fields_list
            if not f.is_identifier and f.name not in ['created_at', 'updated_at']
        ]
        
        lifecycle_states = self._infer_lifecycle_states(sample_responses)
        
        parent_relationships = self._find_parent_relationships(fields_list)
        
        linked_objects = list(set(parent_relationships.values()))
        
        criticality = self._determine_criticality(object_name)
        
        obj_model = ObjectModel(
            name=object_name,
            id_format=id_format,
            ownership_fields=ownership_fields,
            parent_relationships=parent_relationships,
            readable_fields=readable_fields,
            writable_fields=writable_fields,
            sensitive_fields=sensitive_fields,
            lifecycle_states=lifecycle_states,
            linked_objects=linked_objects,
            security_criticality=criticality,
            endpoints=[endpoint.id],
        )
        
        self._objects[object_name] = obj_model
        
        return obj_model
    
    def process_requests(
        self,
        requests: list[RequestRecord],
        endpoints: list[Endpoint],
    ) -> dict[str, ObjectModel]:
        """
        Process requests to build object models.
        
        Args:
            requests: Captured requests
            endpoints: Discovered endpoints
            
        Returns:
            Dict of object name to ObjectModel
        """
        responses_by_endpoint: dict[str, list[dict]] = {}
        
        for record in requests:
            if record.response_json and record.response_status < 400:
                key = f"{record.method}:{record.url}"
                if key not in responses_by_endpoint:
                    responses_by_endpoint[key] = []
                
                if isinstance(record.response_json, dict):
                    responses_by_endpoint[key].append(record.response_json)
                elif isinstance(record.response_json, list):
                    for item in record.response_json[:5]:
                        if isinstance(item, dict):
                            responses_by_endpoint[key].append(item)
        
        for endpoint in endpoints:
            key = f"{endpoint.method}:{endpoint.url}"
            responses = responses_by_endpoint.get(key, [])
            self.process_endpoint(endpoint, responses)
        
        return self._objects
    
    def get_objects(self) -> list[ObjectModel]:
        """Get all discovered object models."""
        return list(self._objects.values())
    
    def get_high_criticality_objects(self) -> list[ObjectModel]:
        """Get high criticality objects."""
        return [o for o in self._objects.values() if o.security_criticality == "high"]
    
    def save_object_graph(self) -> str:
        """
        Save object graph to file.
        
        Returns:
            Path to saved file
        """
        output_path = self.config.get_output_path(
            "recon", "intelligence", "object_graph.json"
        )
        
        graph_data = {
            "nodes": [],
            "edges": [],
        }
        
        for obj in self._objects.values():
            graph_data["nodes"].append({
                "id": obj.name,
                "type": "object",
                "criticality": obj.security_criticality,
                "id_format": obj.id_format,
            })
            
            for field, parent in obj.parent_relationships.items():
                graph_data["edges"].append({
                    "source": obj.name,
                    "target": parent,
                    "relationship": field,
                })
        
        data = add_meta_to_output(
            {
                "objects": [o.model_dump() for o in self._objects.values()],
                "graph": graph_data,
                "summary": {
                    "total_objects": len(self._objects),
                    "high_criticality": len(self.get_high_criticality_objects()),
                    "with_ownership": len([o for o in self._objects.values() if o.ownership_fields]),
                },
            },
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        
        atomic_write_json(output_path, data)
        logger.info(f"Saved {len(self._objects)} object models")
        
        return str(output_path)


def run_object_model_builder(
    requests: list[RequestRecord],
    endpoints: list[Endpoint],
    run_id: Optional[str] = None,
) -> ObjectModelBuilder:
    """
    Run object model building.
    
    Args:
        requests: Captured requests
        endpoints: Discovered endpoints
        run_id: Run ID
        
    Returns:
        ObjectModelBuilder instance with results
    """
    builder = ObjectModelBuilder(run_id=run_id)
    builder.process_requests(requests, endpoints)
    builder.save_object_graph()
    return builder


if __name__ == "__main__":
    from cyberAI.models import HttpMethod
    
    builder = ObjectModelBuilder()
    
    endpoint = Endpoint(
        method=HttpMethod.GET,
        url="https://api.example.com/api/v1/users/123",
        path_pattern="/api/v1/users/{id}",
    )
    
    responses = [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "name": "Test User",
            "org_id": "org-123",
            "status": "active",
            "password_hash": "***",
        }
    ]
    
    obj = builder.process_endpoint(endpoint, responses)
    builder.save_object_graph()
    
    if obj:
        print(f"Object: {obj.name}")
        print(f"ID format: {obj.id_format}")
        print(f"Criticality: {obj.security_criticality}")
        print(f"Ownership fields: {obj.ownership_fields}")
        print(f"Sensitive fields: {obj.sensitive_fields}")
