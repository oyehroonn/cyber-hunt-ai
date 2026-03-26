"""
Step 13: Input Schema - Request body analysis and mutation inventory.
Analyzes input schemas, compares client vs server validation, identifies hidden fields.
"""

import re
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import Endpoint, FieldSchema, InputSchema, RequestRecord
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    generate_run_id,
)


class InputSchemaAnalyzer:
    """
    Analyzes input schemas for endpoints and builds mutation inventories.
    """
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._schemas: dict[str, InputSchema] = {}
        self._client_validations: dict[str, dict] = {}
        self._server_accepts: dict[str, set] = {}
    
    def _infer_field_type(self, value: Any) -> str:
        """Infer field type from sample value."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}', value, re.I):
                return "uuid"
            elif re.match(r'^[\w.-]+@[\w.-]+\.\w+$', value):
                return "email"
            elif re.match(r'^https?://', value):
                return "url"
            elif re.match(r'^\d{4}-\d{2}-\d{2}', value):
                return "datetime"
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        return "unknown"
    
    def _infer_constraints(self, field_name: str, values: list[Any]) -> dict:
        """Infer constraints from field name and sample values."""
        constraints = {}
        
        if not values:
            return constraints
        
        string_values = [v for v in values if isinstance(v, str)]
        if string_values:
            lengths = [len(v) for v in string_values]
            if len(set(lengths)) == 1:
                constraints["fixed_length"] = lengths[0]
            else:
                constraints["min_length"] = min(lengths)
                constraints["max_length"] = max(lengths)
        
        num_values = [v for v in values if isinstance(v, (int, float))]
        if num_values:
            constraints["min_value"] = min(num_values)
            constraints["max_value"] = max(num_values)
        
        if len(values) > 1 and len(set(str(v) for v in values)) <= 5:
            constraints["enum_values"] = list(set(str(v) for v in values))
        
        name_lower = field_name.lower()
        if "email" in name_lower:
            constraints["format"] = "email"
        elif "url" in name_lower or "link" in name_lower:
            constraints["format"] = "url"
        elif "phone" in name_lower:
            constraints["format"] = "phone"
        elif "date" in name_lower:
            constraints["format"] = "date"
        
        return constraints
    
    def _extract_fields_from_body(
        self,
        body,
        prefix: str = "",
    ) -> list[FieldSchema]:
        """
        Extract field schemas from request body.

        Args:
            body: Request body — may be a dict, list, or scalar (JSON allows all types)
            prefix: Field name prefix for nested fields

        Returns:
            List of FieldSchema objects
        """
        # Handle list bodies (e.g. batch API calls that POST a JSON array)
        if isinstance(body, list):
            if body and isinstance(body[0], dict):
                return self._extract_fields_from_body(body[0], f"{prefix}[]" if prefix else "[]")
            return []

        # If body is not a dict (int, str, bool, None) there are no named fields to extract
        if not isinstance(body, dict):
            return []

        fields = []

        for key, value in body.items():
            full_name = f"{prefix}.{key}" if prefix else key
            
            field_type = self._infer_field_type(value)
            
            schema = FieldSchema(
                name=full_name,
                field_type=field_type,
                required=False,
            )
            
            if isinstance(value, dict):
                nested = self._extract_fields_from_body(value, full_name)
                schema.nested_schema = {f.name: f.model_dump() for f in nested}
                fields.extend(nested)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                nested = self._extract_fields_from_body(value[0], f"{full_name}[]")
                schema.nested_schema = {f.name: f.model_dump() for f in nested}
                fields.extend(nested)
            
            fields.append(schema)
        
        return fields
    
    def add_client_validation(
        self,
        endpoint_key: str,
        validations: dict[str, str],
    ) -> None:
        """
        Add client-side validation rules from JS analysis.
        
        Args:
            endpoint_key: Endpoint identifier
            validations: Dict of field name to validation rule
        """
        self._client_validations[endpoint_key] = validations
    
    def process_request(self, record: RequestRecord) -> Optional[InputSchema]:
        """
        Process a request record to build input schema.
        
        Args:
            record: Request record to process
            
        Returns:
            InputSchema if request has body
        """
        if not record.body_json:
            return None
        
        endpoint_key = f"{record.method}:{record.url}"
        
        if endpoint_key in self._schemas:
            existing = self._schemas[endpoint_key]
            
            new_fields = self._extract_fields_from_body(record.body_json)
            existing_names = {f.name for f in existing.fields}
            
            for field in new_fields:
                if field.name not in existing_names:
                    existing.fields.append(field)
            
            return existing
        
        fields = self._extract_fields_from_body(record.body_json)
        
        client_validation = self._client_validations.get(endpoint_key, {})
        
        schema = InputSchema(
            endpoint_id=endpoint_key,
            endpoint_url=record.url,
            fields=fields,
            client_validation=client_validation,
        )
        
        self._schemas[endpoint_key] = schema
        
        return schema
    
    def process_requests_batch(self, requests: list[RequestRecord]) -> list[InputSchema]:
        """
        Process a batch of requests.
        
        Args:
            requests: List of request records
            
        Returns:
            List of InputSchema objects
        """
        for record in requests:
            if record.method.value in ("POST", "PUT", "PATCH"):
                self.process_request(record)
        
        return list(self._schemas.values())
    
    def detect_hidden_fields(
        self,
        endpoints: list[Endpoint],
        requests: list[RequestRecord],
    ) -> None:
        """
        Detect hidden fields (accepted by API but not in UI).
        
        Args:
            endpoints: Discovered endpoints
            requests: Captured requests
        """
        ui_fields: dict[str, set] = {}
        
        for record in requests:
            if record.body_json:
                endpoint_key = f"{record.method}:{record.url}"
                if endpoint_key not in ui_fields:
                    ui_fields[endpoint_key] = set()
                ui_fields[endpoint_key].update(record.body_json.keys())
        
        response_fields: dict[str, set] = {}
        
        for record in requests:
            if record.response_json and isinstance(record.response_json, dict):
                endpoint_key = f"{record.method}:{record.url}"
                if endpoint_key not in response_fields:
                    response_fields[endpoint_key] = set()
                response_fields[endpoint_key].update(record.response_json.keys())
        
        for endpoint_key, schema in self._schemas.items():
            ui = ui_fields.get(endpoint_key, set())
            response = response_fields.get(endpoint_key, set())
            
            potential_hidden = response - ui
            
            hidden = [f for f in potential_hidden if not f.startswith('_') and f not in ('id', 'created_at', 'updated_at')]
            
            schema.hidden_fields = list(hidden)
    
    def build_mutation_inventory(self) -> None:
        """
        Build mutation-ready parameter inventories for each endpoint.
        """
        high_priority_fields = [
            "role", "is_admin", "isAdmin", "admin", "owner_id", "ownerId",
            "user_id", "userId", "org_id", "orgId", "tenant_id", "tenantId",
            "plan", "credits", "balance", "approved", "verified", "status",
            "permissions", "scope", "feature_flags", "billing_status",
        ]
        
        for schema in self._schemas.values():
            candidates = []
            
            for field in schema.fields:
                candidates.append(field.name)
            
            for field in schema.hidden_fields:
                if field not in candidates:
                    candidates.append(field)
            
            for field in high_priority_fields:
                if field not in candidates:
                    candidates.append(field)
            
            schema.mutation_candidates = candidates
    
    def compare_client_server_validation(self) -> dict[str, list[str]]:
        """
        Compare client-side vs server-side validation.
        
        Returns:
            Dict of endpoint to list of validation differences
        """
        differences = {}
        
        for endpoint_key, schema in self._schemas.items():
            endpoint_diffs = []
            
            client_rules = schema.client_validation
            
            for field in schema.fields:
                if field.name in client_rules:
                    rule = client_rules[field.name]
                    
                    if "required" in rule.lower() and not field.required:
                        endpoint_diffs.append(
                            f"{field.name}: client=required, server=optional"
                        )
                    
                    if field.max_length and "max" not in rule.lower():
                        endpoint_diffs.append(
                            f"{field.name}: server has max_length={field.max_length}, client may not"
                        )
            
            if endpoint_diffs:
                differences[endpoint_key] = endpoint_diffs
        
        return differences
    
    def save_schemas(self) -> str:
        """
        Save input schemas to file.
        
        Returns:
            Path to saved file
        """
        self.build_mutation_inventory()
        validation_diff = self.compare_client_server_validation()
        
        output_path = self.config.get_output_path(
            "recon", "intelligence", "input_schemas.json"
        )
        
        data = add_meta_to_output(
            {
                "schemas": {
                    key: schema.model_dump()
                    for key, schema in self._schemas.items()
                },
                "validation_differences": validation_diff,
                "summary": {
                    "total_endpoints": len(self._schemas),
                    "with_hidden_fields": len([s for s in self._schemas.values() if s.hidden_fields]),
                    "validation_mismatches": len(validation_diff),
                },
            },
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        
        atomic_write_json(output_path, data)
        logger.info(f"Saved {len(self._schemas)} input schemas")
        
        return str(output_path)


def run_input_schema_analysis(
    requests: list[RequestRecord],
    endpoints: list[Endpoint],
    run_id: Optional[str] = None,
) -> InputSchemaAnalyzer:
    """
    Run input schema analysis.
    
    Args:
        requests: Captured requests
        endpoints: Discovered endpoints
        run_id: Run ID
        
    Returns:
        InputSchemaAnalyzer instance with results
    """
    analyzer = InputSchemaAnalyzer(run_id=run_id)
    analyzer.process_requests_batch(requests)
    analyzer.detect_hidden_fields(endpoints, requests)
    analyzer.save_schemas()
    return analyzer


if __name__ == "__main__":
    from cyberAI.models import HttpMethod
    
    analyzer = InputSchemaAnalyzer()
    
    record = RequestRecord(
        method=HttpMethod.POST,
        url="https://api.example.com/users",
        headers={},
        body='{"name": "Test", "email": "test@example.com", "role": "user"}',
        body_json={"name": "Test", "email": "test@example.com", "role": "user"},
        response_status=201,
        response_json={"id": 1, "name": "Test", "email": "test@example.com", "role": "user", "is_admin": False},
    )
    
    schema = analyzer.process_request(record)
    analyzer.detect_hidden_fields([], [record])
    analyzer.save_schemas()
    
    if schema:
        print(f"Fields: {[f.name for f in schema.fields]}")
        print(f"Hidden fields: {schema.hidden_fields}")
        print(f"Mutation candidates: {schema.mutation_candidates}")
