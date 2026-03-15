"""
Step 7: GraphQL Discovery - GraphQL endpoint detection and schema analysis.
Detects GraphQL endpoints, attempts introspection, and extracts operations.
"""

import asyncio
import json
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import GraphQLIntel, GraphQLOperation
from cyberAI.utils.http_client import AsyncHTTPClient
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    generate_run_id,
)


class GraphQLDiscovery:
    """
    Discovers and analyzes GraphQL endpoints.
    """
    
    COMMON_GRAPHQL_PATHS = [
        "/graphql",
        "/graphql/",
        "/api/graphql",
        "/api/graphql/",
        "/v1/graphql",
        "/query",
        "/gql",
    ]
    
    INTROSPECTION_QUERY = """
    query IntrospectionQuery {
      __schema {
        queryType { name }
        mutationType { name }
        subscriptionType { name }
        types {
          kind
          name
          description
          fields(includeDeprecated: true) {
            name
            description
            args {
              name
              description
              type {
                kind
                name
                ofType { kind name ofType { kind name } }
              }
              defaultValue
            }
            type {
              kind
              name
              ofType { kind name ofType { kind name } }
            }
            isDeprecated
            deprecationReason
          }
          inputFields {
            name
            description
            type {
              kind
              name
              ofType { kind name }
            }
            defaultValue
          }
          interfaces { kind name }
          enumValues(includeDeprecated: true) {
            name
            description
            isDeprecated
            deprecationReason
          }
          possibleTypes { kind name }
        }
        directives {
          name
          description
          locations
          args {
            name
            description
            type { kind name ofType { kind name } }
            defaultValue
          }
        }
      }
    }
    """
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._graphql_endpoints: list[str] = []
        self._intel: Optional[GraphQLIntel] = None
        self._schema: Optional[dict] = None
        self._observed_operations: list[GraphQLOperation] = []
    
    async def detect_graphql_endpoint(
        self,
        client: AsyncHTTPClient,
        base_url: str,
    ) -> Optional[str]:
        """
        Detect GraphQL endpoint by probing common paths.
        
        Args:
            client: HTTP client
            base_url: Base URL of target
            
        Returns:
            GraphQL endpoint URL if found
        """
        for path in self.COMMON_GRAPHQL_PATHS:
            url = f"{base_url.rstrip('/')}{path}"
            
            try:
                response, _ = await client.post(
                    url,
                    json_data={"query": "{ __typename }"},
                    headers={"Content-Type": "application/json"},
                    record=False,
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if "data" in data or "errors" in data:
                            logger.info(f"Found GraphQL endpoint: {url}")
                            self._graphql_endpoints.append(url)
                            return url
                    except json.JSONDecodeError:
                        pass
                
                response, _ = await client.get(url, record=False)
                if response.status_code == 200:
                    text = response.text.lower()
                    if "graphql" in text or "playground" in text or "graphiql" in text:
                        logger.info(f"Found GraphQL interface: {url}")
                        self._graphql_endpoints.append(url)
                        return url
                        
            except Exception as e:
                logger.debug(f"Error probing {path}: {e}")
        
        return None
    
    async def attempt_introspection(
        self,
        client: AsyncHTTPClient,
        endpoint_url: str,
    ) -> Optional[dict]:
        """
        Attempt to run introspection query on GraphQL endpoint.
        
        Args:
            client: HTTP client
            endpoint_url: GraphQL endpoint URL
            
        Returns:
            Introspection schema if successful
        """
        try:
            response, _ = await client.post(
                endpoint_url,
                json_data={"query": self.INTROSPECTION_QUERY},
                headers={"Content-Type": "application/json"},
                record=False,
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"].get("__schema"):
                    logger.info("Introspection query successful")
                    self._schema = data["data"]["__schema"]
                    return self._schema
                elif "errors" in data:
                    error_msg = str(data["errors"])
                    if "introspection" in error_msg.lower():
                        logger.info("Introspection is disabled")
                    else:
                        logger.debug(f"Introspection error: {error_msg}")
                        
        except Exception as e:
            logger.debug(f"Introspection failed: {e}")
        
        return None
    
    def _parse_schema_types(self, schema: dict) -> list[dict]:
        """Parse types from introspection schema."""
        types = []
        
        for type_def in schema.get("types", []):
            if type_def["name"].startswith("__"):
                continue
            
            type_info = {
                "name": type_def["name"],
                "kind": type_def["kind"],
                "fields": [],
            }
            
            if type_def.get("fields"):
                for field in type_def["fields"]:
                    field_info = {
                        "name": field["name"],
                        "type": self._get_type_name(field.get("type", {})),
                        "args": [arg["name"] for arg in field.get("args", [])],
                    }
                    type_info["fields"].append(field_info)
            
            types.append(type_info)
        
        return types
    
    def _get_type_name(self, type_def: dict) -> str:
        """Extract type name from GraphQL type definition."""
        if not type_def:
            return "Unknown"
        
        kind = type_def.get("kind", "")
        name = type_def.get("name", "")
        
        if name:
            return name
        elif kind == "NON_NULL":
            inner = type_def.get("ofType", {})
            return f"{self._get_type_name(inner)}!"
        elif kind == "LIST":
            inner = type_def.get("ofType", {})
            return f"[{self._get_type_name(inner)}]"
        
        return "Unknown"
    
    def _extract_operations_from_schema(self, schema: dict) -> list[GraphQLOperation]:
        """Extract operations from introspection schema."""
        operations = []
        
        query_type_name = schema.get("queryType", {}).get("name", "Query")
        mutation_type_name = schema.get("mutationType", {}).get("name", "Mutation")
        subscription_type_name = schema.get("subscriptionType", {}).get("name", "Subscription")
        
        for type_def in schema.get("types", []):
            type_name = type_def.get("name", "")
            
            if type_name == query_type_name:
                op_type = "query"
            elif type_name == mutation_type_name:
                op_type = "mutation"
            elif type_name == subscription_type_name:
                op_type = "subscription"
            else:
                continue
            
            for field in type_def.get("fields", []):
                args = {}
                for arg in field.get("args", []):
                    args[arg["name"]] = self._get_type_name(arg.get("type", {}))
                
                operation = GraphQLOperation(
                    name=field["name"],
                    operation_type=op_type,
                    arguments=args,
                )
                operations.append(operation)
        
        return operations
    
    def _identify_sensitive_fields(self, schema: dict) -> list[str]:
        """Identify potentially sensitive fields in schema."""
        sensitive_patterns = [
            "password", "secret", "token", "key", "credential",
            "ssn", "credit", "card", "hash", "salt", "private",
            "internal", "admin", "role", "permission", "auth",
        ]
        
        sensitive_fields = []
        
        for type_def in schema.get("types", []):
            type_name = type_def.get("name", "")
            
            for field in type_def.get("fields", []):
                field_name = field.get("name", "").lower()
                
                for pattern in sensitive_patterns:
                    if pattern in field_name:
                        sensitive_fields.append(f"{type_name}.{field['name']}")
                        break
        
        return sensitive_fields
    
    async def test_batching(
        self,
        client: AsyncHTTPClient,
        endpoint_url: str,
    ) -> bool:
        """
        Test if endpoint supports query batching.
        
        Args:
            client: HTTP client
            endpoint_url: GraphQL endpoint URL
            
        Returns:
            True if batching is supported
        """
        batch_query = [
            {"query": "{ __typename }"},
            {"query": "{ __typename }"},
        ]
        
        try:
            response, _ = await client.post(
                endpoint_url,
                json_data=batch_query,
                headers={"Content-Type": "application/json"},
                record=False,
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) == 2:
                    logger.info("Batching is supported")
                    return True
                    
        except Exception as e:
            logger.debug(f"Batch test failed: {e}")
        
        return False
    
    async def test_depth_limit(
        self,
        client: AsyncHTTPClient,
        endpoint_url: str,
        type_name: str = "Query",
    ) -> Optional[int]:
        """
        Test query depth limits.
        
        Args:
            client: HTTP client
            endpoint_url: GraphQL endpoint URL
            type_name: Type to use for depth testing
            
        Returns:
            Depth limit if detected
        """
        for depth in [5, 10, 15, 20, 50]:
            nested = "{ __typename " + "{ __typename " * depth + "}" * depth + "}"
            
            try:
                response, _ = await client.post(
                    endpoint_url,
                    json_data={"query": f"query {{ __schema {nested} }}"},
                    headers={"Content-Type": "application/json"},
                    record=False,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "errors" in data:
                        error_msg = str(data["errors"]).lower()
                        if "depth" in error_msg or "complexity" in error_msg:
                            logger.info(f"Depth limit detected around {depth}")
                            return depth
                            
            except Exception:
                pass
        
        return None
    
    async def discover(self, base_url: str) -> Optional[GraphQLIntel]:
        """
        Run full GraphQL discovery.
        
        Args:
            base_url: Base URL of target
            
        Returns:
            GraphQLIntel object with discovery results
        """
        client = AsyncHTTPClient(base_url=base_url)
        
        try:
            endpoint_url = await self.detect_graphql_endpoint(client, base_url)
            
            if not endpoint_url:
                logger.info("No GraphQL endpoint found")
                return None
            
            schema = await self.attempt_introspection(client, endpoint_url)
            
            operations = []
            sensitive_fields = []
            
            if schema:
                operations = self._extract_operations_from_schema(schema)
                sensitive_fields = self._identify_sensitive_fields(schema)
                
                schema_path = self.config.get_output_path(
                    "recon", "intelligence", "graphql_schema.json"
                )
                atomic_write_json(schema_path, schema)
            
            supports_batching = await self.test_batching(client, endpoint_url)
            
            depth_limit = await self.test_depth_limit(client, endpoint_url)
            
            self._intel = GraphQLIntel(
                endpoint_url=endpoint_url,
                introspection_enabled=schema is not None,
                schema_path=str(self.config.get_output_path("recon", "intelligence", "graphql_schema.json")) if schema else None,
                operations=operations,
                supports_batching=supports_batching,
                supports_aliases=True,
                depth_limit=depth_limit,
                sensitive_fields=sensitive_fields,
            )
            
            return self._intel
            
        finally:
            await client.close()
    
    def add_observed_operation(self, operation: GraphQLOperation) -> None:
        """Add an observed operation from traffic."""
        self._observed_operations.append(operation)
    
    def save_intel(self) -> str:
        """
        Save GraphQL intelligence to file.
        
        Returns:
            Path to saved file
        """
        output_path = self.config.get_output_path(
            "recon", "intelligence", "graphql_intel.json"
        )
        
        data = add_meta_to_output(
            {
                "intel": self._intel.model_dump() if self._intel else None,
                "observed_operations": [op.model_dump() for op in self._observed_operations],
                "endpoints_found": self._graphql_endpoints,
            },
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        
        atomic_write_json(output_path, data)
        logger.info(f"Saved GraphQL intelligence")
        
        return str(output_path)


async def run_graphql_discovery(
    base_url: str,
    run_id: Optional[str] = None,
) -> GraphQLDiscovery:
    """
    Run GraphQL discovery.
    
    Args:
        base_url: Base URL of target
        run_id: Run ID
        
    Returns:
        GraphQLDiscovery instance with results
    """
    discovery = GraphQLDiscovery(run_id=run_id)
    await discovery.discover(base_url)
    discovery.save_intel()
    return discovery


if __name__ == "__main__":
    async def main():
        import sys
        
        url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
        
        discovery = GraphQLDiscovery()
        intel = await discovery.discover(url)
        discovery.save_intel()
        
        if intel:
            print(f"\nGraphQL endpoint: {intel.endpoint_url}")
            print(f"Introspection enabled: {intel.introspection_enabled}")
            print(f"Operations found: {len(intel.operations)}")
            print(f"Supports batching: {intel.supports_batching}")
            print(f"Sensitive fields: {len(intel.sensitive_fields)}")
        else:
            print("No GraphQL endpoint found")
    
    asyncio.run(main())
