"""
Step 6: Sensitive Surfaces Discovery - Probing for sensitive paths and endpoints.
Probes a large wordlist of sensitive paths and analyzes responses.
"""

import asyncio
from typing import Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import SensitiveSurface
from cyberAI.utils.http_client import AsyncHTTPClient
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    generate_run_id,
)


class SensitiveSurfacesDiscovery:
    """
    Probes sensitive paths and analyzes responses for security-relevant information.
    """
    
    SENSITIVE_PATHS = [
        "/admin",
        "/admin/",
        "/administrator",
        "/internal",
        "/internal/",
        "/billing",
        "/billing/",
        "/export",
        "/exports",
        "/import",
        "/imports",
        "/tokens",
        "/api-tokens",
        "/api/tokens",
        "/audit",
        "/audit-logs",
        "/audit/logs",
        "/graphql",
        "/graphql/",
        "/graphql/playground",
        "/graphiql",
        "/swagger",
        "/swagger/",
        "/swagger-ui",
        "/swagger-ui.html",
        "/swagger-ui/",
        "/openapi.json",
        "/openapi.yaml",
        "/api/docs",
        "/api-docs",
        "/docs",
        "/redoc",
        "/health",
        "/healthz",
        "/health/live",
        "/health/ready",
        "/debug",
        "/debug/",
        "/metrics",
        "/prometheus",
        "/.well-known/",
        "/.well-known/security.txt",
        "/.well-known/openid-configuration",
        "/robots.txt",
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/__admin",
        "/__admin/",
        "/staff",
        "/staff/",
        "/superuser",
        "/console",
        "/console/",
        "/manage",
        "/manage/",
        "/management",
        "/api/v1/admin",
        "/api/v2/admin",
        "/api/internal",
        "/api/private",
        "/.env",
        "/.git",
        "/.git/config",
        "/.git/HEAD",
        "/.gitignore",
        "/.htaccess",
        "/config",
        "/config/",
        "/configuration",
        "/settings",
        "/system",
        "/actuator",
        "/actuator/health",
        "/actuator/info",
        "/actuator/env",
        "/actuator/beans",
        "/actuator/mappings",
        "/trace",
        "/elmah.axd",
        "/phpinfo.php",
        "/info.php",
        "/test",
        "/test/",
        "/testing",
        "/dev",
        "/development",
        "/staging",
        "/backup",
        "/backups",
        "/dump",
        "/sql",
        "/database",
        "/db",
        "/phpmyadmin",
        "/pma",
        "/adminer",
        "/status",
        "/server-status",
        "/server-info",
        "/_debug",
        "/_profiler",
        "/profiler",
        "/api/debug",
        "/api/status",
        "/api/health",
        "/api/info",
        "/api/version",
        "/version",
        "/version.txt",
        "/changelog",
        "/CHANGELOG.md",
        "/README.md",
        "/license",
        "/LICENSE",
        "/webpack.config.js",
        "/package.json",
        "/composer.json",
        "/Gemfile",
        "/requirements.txt",
        "/.dockerenv",
        "/Dockerfile",
        "/docker-compose.yml",
        "/api/webhooks",
        "/webhooks",
        "/callback",
        "/callbacks",
        "/oauth",
        "/oauth/",
        "/oauth/authorize",
        "/oauth/token",
        "/.aws/credentials",
        "/credentials",
        "/secrets",
        "/private",
        "/restricted",
        "/confidential",
    ]
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._surfaces: list[SensitiveSurface] = []
        self._additional_paths: list[str] = []
    
    def add_paths_from_js_analysis(self, js_paths: list[str]) -> None:
        """
        Add additional paths derived from JS bundle analysis.
        
        Args:
            js_paths: Paths extracted from JS bundles
        """
        for path in js_paths:
            if path.startswith('/') and path not in self.SENSITIVE_PATHS:
                self._additional_paths.append(path)
    
    def _classify_response(
        self,
        status_code: int,
        response_body: Optional[str],
        headers: dict,
    ) -> str:
        """
        Classify the response type.
        
        Args:
            status_code: HTTP status code
            response_body: Response body
            headers: Response headers
            
        Returns:
            Classification string
        """
        if 200 <= status_code < 300:
            if response_body and len(response_body) > 100:
                return "RESPONDS"
            return "OPEN"
        elif status_code in (301, 302, 303, 307, 308):
            return "REDIRECTS"
        elif status_code in (401, 403):
            return "BLOCKS"
        elif status_code == 404:
            return "NOT_FOUND"
        elif status_code >= 500:
            return "ERROR"
        return "UNKNOWN"
    
    def _detect_metadata_leakage(
        self,
        response_body: Optional[str],
        headers: dict,
    ) -> tuple[bool, list[str]]:
        """
        Detect if sensitive metadata is leaked in the response.
        
        Args:
            response_body: Response body
            headers: Response headers
            
        Returns:
            Tuple of (leaks_metadata, list of leaked items)
        """
        leaked = []
        
        sensitive_headers = [
            'x-powered-by',
            'server',
            'x-aspnet-version',
            'x-runtime',
            'x-version',
            'x-generator',
        ]
        
        for header in sensitive_headers:
            for key, value in headers.items():
                if key.lower() == header:
                    leaked.append(f"header:{key}={value}")
        
        if response_body:
            import re
            
            version_patterns = [
                (r'version["\s:]+([0-9]+\.[0-9]+(?:\.[0-9]+)?)', 'version'),
                (r'php/([0-9]+\.[0-9]+)', 'php_version'),
                (r'apache/([0-9]+\.[0-9]+)', 'apache_version'),
                (r'nginx/([0-9]+\.[0-9]+)', 'nginx_version'),
                (r'node(?:js)?[/\s]+v?([0-9]+\.[0-9]+)', 'node_version'),
            ]
            
            for pattern, name in version_patterns:
                match = re.search(pattern, response_body, re.IGNORECASE)
                if match:
                    leaked.append(f"{name}:{match.group(1)}")
            
            sensitive_patterns = [
                (r'stack\s*trace', 'stack_trace'),
                (r'exception', 'exception'),
                (r'error\s*at\s+', 'error_trace'),
                (r'/home/\w+/', 'file_path'),
                (r'/var/www/', 'file_path'),
                (r'c:\\\\', 'file_path'),
                (r'internal\s*server\s*error', 'internal_error'),
            ]
            
            for pattern, name in sensitive_patterns:
                if re.search(pattern, response_body, re.IGNORECASE):
                    leaked.append(name)
        
        return bool(leaked), leaked
    
    async def probe_path(
        self,
        client: AsyncHTTPClient,
        base_url: str,
        path: str,
    ) -> Optional[SensitiveSurface]:
        """
        Probe a single path and analyze the response.
        
        Args:
            client: HTTP client
            base_url: Base URL of target
            path: Path to probe
            
        Returns:
            SensitiveSurface if interesting, None otherwise
        """
        url = f"{base_url.rstrip('/')}{path}"
        
        try:
            response, record = await client.get(
                url,
                headers={"Accept": "text/html,application/json,*/*"},
                record=False,
            )
            
            classification = self._classify_response(
                response.status_code,
                response.text if response.status_code < 400 else None,
                dict(response.headers),
            )
            
            if classification == "NOT_FOUND":
                return None
            
            leaks_metadata, metadata_leaked = self._detect_metadata_leakage(
                response.text if response.status_code < 400 else None,
                dict(response.headers),
            )
            
            redirect_target = None
            if classification == "REDIRECTS":
                redirect_target = response.headers.get("location")
            
            if leaks_metadata:
                classification = "LEAKS_METADATA"
            
            return SensitiveSurface(
                path=path,
                status_code=response.status_code,
                response_size=len(response.text) if response.text else 0,
                redirect_target=redirect_target,
                leaks_metadata=leaks_metadata,
                metadata_leaked=metadata_leaked,
                classification=classification,
            )
            
        except Exception as e:
            logger.debug(f"Error probing {path}: {e}")
            return None
    
    async def probe_all_paths(
        self,
        base_url: str,
        max_concurrent: int = 10,
    ) -> list[SensitiveSurface]:
        """
        Probe all sensitive paths.
        
        Args:
            base_url: Base URL of target
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of discovered SensitiveSurface objects
        """
        all_paths = self.SENSITIVE_PATHS + self._additional_paths
        
        logger.info(f"Probing {len(all_paths)} sensitive paths...")
        
        client = AsyncHTTPClient(base_url=base_url)
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def probe_with_semaphore(path: str) -> Optional[SensitiveSurface]:
            async with semaphore:
                await asyncio.sleep(self.config.request_delay_ms / 1000)
                return await self.probe_path(client, base_url, path)
        
        tasks = [probe_with_semaphore(path) for path in all_paths]
        results = await asyncio.gather(*tasks)
        
        self._surfaces = [r for r in results if r is not None]
        
        await client.close()
        
        logger.info(f"Found {len(self._surfaces)} interesting surfaces")
        
        return self._surfaces
    
    def get_by_classification(self, classification: str) -> list[SensitiveSurface]:
        """Get surfaces by classification."""
        return [s for s in self._surfaces if s.classification == classification]
    
    def get_leaking_surfaces(self) -> list[SensitiveSurface]:
        """Get surfaces that leak metadata."""
        return [s for s in self._surfaces if s.leaks_metadata]
    
    def get_open_surfaces(self) -> list[SensitiveSurface]:
        """Get surfaces that are openly accessible."""
        return [s for s in self._surfaces if s.classification in ("RESPONDS", "OPEN")]
    
    def save_surfaces(self) -> str:
        """
        Save discovered surfaces to file.
        
        Returns:
            Path to saved file
        """
        output_path = self.config.get_output_path(
            "recon", "intelligence", "sensitive_surfaces.json"
        )
        
        by_classification = {}
        for surface in self._surfaces:
            if surface.classification not in by_classification:
                by_classification[surface.classification] = []
            by_classification[surface.classification].append(surface.model_dump())
        
        data = add_meta_to_output(
            {
                "surfaces": [s.model_dump() for s in self._surfaces],
                "by_classification": by_classification,
                "summary": {
                    "total_probed": len(self.SENSITIVE_PATHS) + len(self._additional_paths),
                    "total_found": len(self._surfaces),
                    "leaking_metadata": len(self.get_leaking_surfaces()),
                    "open_access": len(self.get_open_surfaces()),
                    "blocked": len(self.get_by_classification("BLOCKS")),
                },
            },
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        
        atomic_write_json(output_path, data)
        logger.info(f"Saved {len(self._surfaces)} sensitive surfaces")
        
        return str(output_path)


async def run_sensitive_surfaces_discovery(
    base_url: str,
    js_paths: Optional[list[str]] = None,
    run_id: Optional[str] = None,
) -> SensitiveSurfacesDiscovery:
    """
    Run sensitive surfaces discovery.
    
    Args:
        base_url: Base URL of target
        js_paths: Optional paths from JS analysis
        run_id: Run ID
        
    Returns:
        SensitiveSurfacesDiscovery instance with results
    """
    discovery = SensitiveSurfacesDiscovery(run_id=run_id)
    
    if js_paths:
        discovery.add_paths_from_js_analysis(js_paths)
    
    await discovery.probe_all_paths(base_url)
    discovery.save_surfaces()
    
    return discovery


if __name__ == "__main__":
    async def main():
        import sys
        
        url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
        
        discovery = SensitiveSurfacesDiscovery()
        surfaces = await discovery.probe_all_paths(url)
        discovery.save_surfaces()
        
        print(f"\nFound {len(surfaces)} interesting surfaces:")
        for surface in surfaces[:20]:
            print(f"  [{surface.classification}] {surface.path} ({surface.status_code})")
    
    asyncio.run(main())
