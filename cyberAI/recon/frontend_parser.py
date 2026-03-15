"""
Step 3: Frontend Parser - JavaScript bundle analysis and route extraction.
Downloads, beautifies, and analyzes JS bundles to find hidden routes and API endpoints.
"""

import asyncio
import re
from typing import Any, Optional
from urllib.parse import urljoin

import httpx
import jsbeautifier
from bs4 import BeautifulSoup
from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import Route
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    atomic_write_text,
    generate_run_id,
    safe_filename,
)


class FrontendParser:
    """
    Analyzes JavaScript bundles to extract routes, API endpoints, and other artifacts.
    """
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._js_urls: set[str] = set()
        self._beautified_files: dict[str, str] = {}
        self._extracted_routes: list[dict] = []
        self._api_endpoints: list[dict] = []
        self._role_constants: dict[str, Any] = {}
        self._feature_flags: dict[str, Any] = {}
        self._graphql_operations: list[dict] = []
        self._websocket_events: list[str] = []
        self._upload_endpoints: list[str] = []
        self._validation_schemas: list[dict] = []
    
    async def fetch_js_bundles(self, html_content: str, base_url: str) -> list[str]:
        """
        Extract and download all JavaScript bundle URLs from HTML.
        
        Args:
            html_content: HTML content to parse
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of downloaded JS file paths
        """
        soup = BeautifulSoup(html_content, 'lxml')
        js_urls = set()
        
        for script in soup.find_all('script', src=True):
            src = script['src']
            if src.endswith('.js') or '.js?' in src or 'chunk' in src or 'bundle' in src:
                full_url = urljoin(base_url, src)
                js_urls.add(full_url)
        
        for link in soup.find_all('link', rel='preload'):
            href = link.get('href', '')
            if href.endswith('.js') or link.get('as') == 'script':
                full_url = urljoin(base_url, href)
                js_urls.add(full_url)
        
        js_pattern = r'["\']([^"\']*?\.js(?:\?[^"\']*)?)["\']'
        for match in re.finditer(js_pattern, html_content):
            js_path = match.group(1)
            if not js_path.startswith(('http://', 'https://', '//')):
                js_path = urljoin(base_url, js_path)
            js_urls.add(js_path)
        
        self._js_urls = js_urls
        
        downloaded = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for url in js_urls:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        content = response.text
                        
                        beautified = jsbeautifier.beautify(content, {
                            'indent_size': 2,
                            'preserve_newlines': True,
                            'max_preserve_newlines': 2,
                        })
                        
                        safe_name = safe_filename(url.split('/')[-1].split('?')[0])
                        file_path = self.config.get_output_path(
                            "recon", "js_bundles", f"{safe_name}"
                        )
                        atomic_write_text(file_path, beautified)
                        
                        self._beautified_files[url] = beautified
                        downloaded.append(str(file_path))
                        
                        logger.debug(f"Downloaded JS: {url}")
                        
                except Exception as e:
                    logger.warning(f"Failed to download {url}: {e}")
        
        logger.info(f"Downloaded {len(downloaded)} JS bundles")
        return downloaded
    
    def extract_routes(self, js_content: str) -> list[dict]:
        """
        Extract route definitions from JavaScript content.
        
        Args:
            js_content: Beautified JavaScript content
            
        Returns:
            List of route dictionaries
        """
        routes = []
        
        react_router_patterns = [
            r'<Route\s+(?:[^>]*\s+)?path=["\']([^"\']+)["\']',
            r'path:\s*["\']([^"\']+)["\']',
            r'to:\s*["\']([^"\']+)["\']',
            r'navigate\(["\']([^"\']+)["\']',
            r'history\.push\(["\']([^"\']+)["\']',
            r'router\.push\(["\']([^"\']+)["\']',
        ]
        
        for pattern in react_router_patterns:
            for match in re.finditer(pattern, js_content):
                route_path = match.group(1)
                if route_path and route_path.startswith('/'):
                    routes.append({
                        'path': route_path,
                        'source': 'react_router',
                        'pattern': pattern[:50],
                    })
        
        nextjs_patterns = [
            r'getServerSideProps.*?pathname:\s*["\']([^"\']+)["\']',
            r'getStaticPaths.*?paths:\s*\[(.*?)\]',
            r'useRouter\(\).*?pathname.*?["\']([^"\']+)["\']',
        ]
        
        for pattern in nextjs_patterns:
            for match in re.finditer(pattern, js_content, re.DOTALL):
                route_path = match.group(1)
                routes.append({
                    'path': route_path,
                    'source': 'nextjs',
                    'pattern': pattern[:50],
                })
        
        vue_patterns = [
            r'path:\s*["\']([^"\']+)["\'].*?component:',
            r'\$router\.push\(["\']([^"\']+)["\']',
            r'this\.\$route\.path.*?["\']([^"\']+)["\']',
        ]
        
        for pattern in vue_patterns:
            for match in re.finditer(pattern, js_content):
                route_path = match.group(1)
                if route_path and route_path.startswith('/'):
                    routes.append({
                        'path': route_path,
                        'source': 'vue_router',
                        'pattern': pattern[:50],
                    })
        
        self._extracted_routes.extend(routes)
        return routes
    
    def extract_api_endpoints(self, js_content: str) -> list[dict]:
        """
        Extract API endpoint definitions from JavaScript content.
        
        Args:
            js_content: Beautified JavaScript content
            
        Returns:
            List of API endpoint dictionaries
        """
        endpoints = []
        
        api_base_patterns = [
            r'(?:apiUrl|API_URL|baseURL|BASE_URL|apiBase|API_BASE)\s*[:=]\s*["\']([^"\']+)["\']',
            r'axios\.defaults\.baseURL\s*=\s*["\']([^"\']+)["\']',
        ]
        
        api_bases = []
        for pattern in api_base_patterns:
            for match in re.finditer(pattern, js_content):
                api_bases.append(match.group(1))
        
        fetch_patterns = [
            r'fetch\(["\']([^"\']+)["\']',
            r'axios\.(get|post|put|patch|delete)\(["\']([^"\']+)["\']',
            r'axios\(\{[^}]*url:\s*["\']([^"\']+)["\']',
            r'\$http\.(get|post|put|patch|delete)\(["\']([^"\']+)["\']',
            r'request\(["\']([^"\']+)["\']',
        ]
        
        for pattern in fetch_patterns:
            for match in re.finditer(pattern, js_content):
                groups = match.groups()
                if len(groups) == 2:
                    method, url = groups
                else:
                    method = 'GET'
                    url = groups[0]
                
                endpoints.append({
                    'url': url,
                    'method': method.upper() if method else 'GET',
                    'source': 'fetch/axios',
                })
        
        endpoint_def_patterns = [
            r'["\'](?:GET|POST|PUT|PATCH|DELETE)["\'].*?["\']([/][^"\']+)["\']',
            r'endpoint:\s*["\']([^"\']+)["\']',
            r'url:\s*["\']([/][^"\']+)["\']',
        ]
        
        for pattern in endpoint_def_patterns:
            for match in re.finditer(pattern, js_content):
                url = match.group(1)
                if url.startswith('/'):
                    endpoints.append({
                        'url': url,
                        'method': 'UNKNOWN',
                        'source': 'definition',
                    })
        
        self._api_endpoints.extend(endpoints)
        return endpoints
    
    def extract_role_constants(self, js_content: str) -> dict[str, Any]:
        """
        Extract role-related constants from JavaScript content.
        
        Args:
            js_content: Beautified JavaScript content
            
        Returns:
            Dictionary of role constants
        """
        roles = {}
        
        role_patterns = [
            r'(?:ROLE_|Role\.|role\.)([A-Z_]+)\s*[:=]\s*["\']([^"\']+)["\']',
            r'["\']?(admin|user|guest|moderator|editor|viewer|owner|member)["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'roles?:\s*\[([^\]]+)\]',
            r'userRole\s*[:=]\s*["\']([^"\']+)["\']',
            r'isAdmin\s*[:=]',
            r'hasRole\(["\']([^"\']+)["\']',
            r'checkPermission\(["\']([^"\']+)["\']',
        ]
        
        for pattern in role_patterns:
            for match in re.finditer(pattern, js_content, re.IGNORECASE):
                groups = match.groups()
                if groups:
                    key = groups[0] if groups[0] else 'unknown'
                    value = groups[1] if len(groups) > 1 else True
                    roles[key] = value
        
        permission_patterns = [
            r'permission\.[A-Z_]+\s*[:=]\s*["\']([^"\']+)["\']',
            r'can[A-Z][a-zA-Z]+\s*[:=]',
            r'PERMISSION_([A-Z_]+)',
        ]
        
        for pattern in permission_patterns:
            for match in re.finditer(pattern, js_content):
                if match.groups():
                    roles[f"permission_{match.group(1)}"] = True
        
        self._role_constants.update(roles)
        return roles
    
    def extract_feature_flags(self, js_content: str) -> dict[str, Any]:
        """
        Extract feature flag definitions from JavaScript content.
        
        Args:
            js_content: Beautified JavaScript content
            
        Returns:
            Dictionary of feature flags
        """
        flags = {}
        
        flag_patterns = [
            r'(?:FEATURE_|feature\.|Feature\.)([A-Z_]+)\s*[:=]\s*(true|false|["\'][^"\']+["\'])',
            r'isFeatureEnabled\(["\']([^"\']+)["\']',
            r'featureFlags?\.([a-zA-Z_]+)',
            r'flags?\.([a-zA-Z_]+)\s*(?:===?\s*(?:true|false))?',
            r'["\']([a-zA-Z_]+_(?:enabled|disabled|flag))["\']',
        ]
        
        for pattern in flag_patterns:
            for match in re.finditer(pattern, js_content, re.IGNORECASE):
                groups = match.groups()
                if groups:
                    key = groups[0]
                    value = groups[1] if len(groups) > 1 else True
                    if isinstance(value, str):
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False
                    flags[key] = value
        
        self._feature_flags.update(flags)
        return flags
    
    def extract_graphql_operations(self, js_content: str) -> list[dict]:
        """
        Extract GraphQL operation names and fragments from JavaScript content.
        
        Args:
            js_content: Beautified JavaScript content
            
        Returns:
            List of GraphQL operation dictionaries
        """
        operations = []
        
        gql_patterns = [
            r'(?:query|mutation|subscription)\s+([A-Z][a-zA-Z]+)',
            r'gql`\s*(?:query|mutation|subscription)\s+([A-Z][a-zA-Z]+)',
            r'operationName:\s*["\']([^"\']+)["\']',
            r'\.query\(\{\s*query:\s*([A-Z][a-zA-Z]+)',
            r'\.mutate\(\{\s*mutation:\s*([A-Z][a-zA-Z]+)',
        ]
        
        for pattern in gql_patterns:
            for match in re.finditer(pattern, js_content):
                op_name = match.group(1)
                op_type = 'query'
                if 'mutation' in pattern.lower():
                    op_type = 'mutation'
                elif 'subscription' in pattern.lower():
                    op_type = 'subscription'
                
                operations.append({
                    'name': op_name,
                    'type': op_type,
                })
        
        fragment_pattern = r'fragment\s+([A-Z][a-zA-Z]+)\s+on\s+([A-Z][a-zA-Z]+)'
        for match in re.finditer(fragment_pattern, js_content):
            operations.append({
                'name': match.group(1),
                'type': 'fragment',
                'on_type': match.group(2),
            })
        
        self._graphql_operations.extend(operations)
        return operations
    
    def extract_websocket_events(self, js_content: str) -> list[str]:
        """
        Extract WebSocket event names from JavaScript content.
        
        Args:
            js_content: Beautified JavaScript content
            
        Returns:
            List of event names
        """
        events = set()
        
        ws_patterns = [
            r'socket\.on\(["\']([^"\']+)["\']',
            r'socket\.emit\(["\']([^"\']+)["\']',
            r'socket\.once\(["\']([^"\']+)["\']',
            r'addEventListener\(["\']message["\']',
            r'ws\.send\(',
            r'io\(["\']([^"\']+)["\']',
            r'channel:\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in ws_patterns:
            for match in re.finditer(pattern, js_content):
                if match.groups():
                    events.add(match.group(1))
        
        self._websocket_events.extend(list(events))
        return list(events)
    
    def extract_upload_endpoints(self, js_content: str) -> list[str]:
        """
        Extract file upload endpoint URLs from JavaScript content.
        
        Args:
            js_content: Beautified JavaScript content
            
        Returns:
            List of upload endpoint URLs
        """
        endpoints = set()
        
        upload_patterns = [
            r'upload[Uu]rl\s*[:=]\s*["\']([^"\']+)["\']',
            r'FormData.*?fetch\(["\']([^"\']+)["\']',
            r'multipart/form-data.*?["\']([^"\']+)["\']',
            r'["\']([^"\']*(?:upload|file|attachment|media)[^"\']*)["\']',
        ]
        
        for pattern in upload_patterns:
            for match in re.finditer(pattern, js_content, re.IGNORECASE):
                url = match.group(1)
                if url.startswith('/') or url.startswith('http'):
                    endpoints.add(url)
        
        self._upload_endpoints.extend(list(endpoints))
        return list(endpoints)
    
    def extract_validation_schemas(self, js_content: str) -> list[dict]:
        """
        Extract validation schema definitions (Yup, Zod, Joi) from JavaScript content.
        
        Args:
            js_content: Beautified JavaScript content
            
        Returns:
            List of validation schema dictionaries
        """
        schemas = []
        
        yup_pattern = r'yup\.object\(\{([^}]+)\}\)'
        for match in re.finditer(yup_pattern, js_content):
            schema_content = match.group(1)
            fields = re.findall(r'(\w+):\s*yup\.(\w+)', schema_content)
            schemas.append({
                'type': 'yup',
                'fields': {f[0]: f[1] for f in fields},
            })
        
        zod_pattern = r'z\.object\(\{([^}]+)\}\)'
        for match in re.finditer(zod_pattern, js_content):
            schema_content = match.group(1)
            fields = re.findall(r'(\w+):\s*z\.(\w+)', schema_content)
            schemas.append({
                'type': 'zod',
                'fields': {f[0]: f[1] for f in fields},
            })
        
        joi_pattern = r'Joi\.object\(\{([^}]+)\}\)'
        for match in re.finditer(joi_pattern, js_content):
            schema_content = match.group(1)
            fields = re.findall(r'(\w+):\s*Joi\.(\w+)', schema_content)
            schemas.append({
                'type': 'joi',
                'fields': {f[0]: f[1] for f in fields},
            })
        
        self._validation_schemas.extend(schemas)
        return schemas
    
    def analyze_all(self) -> dict:
        """
        Run all extraction methods on all downloaded JS content.
        
        Returns:
            Dictionary of all extracted artifacts
        """
        for url, content in self._beautified_files.items():
            logger.debug(f"Analyzing {url}")
            
            self.extract_routes(content)
            self.extract_api_endpoints(content)
            self.extract_role_constants(content)
            self.extract_feature_flags(content)
            self.extract_graphql_operations(content)
            self.extract_websocket_events(content)
            self.extract_upload_endpoints(content)
            self.extract_validation_schemas(content)
        
        return {
            'routes': self._extracted_routes,
            'api_endpoints': self._api_endpoints,
            'role_constants': self._role_constants,
            'feature_flags': self._feature_flags,
            'graphql_operations': self._graphql_operations,
            'websocket_events': self._websocket_events,
            'upload_endpoints': self._upload_endpoints,
            'validation_schemas': self._validation_schemas,
        }
    
    def find_hidden_routes(self, crawled_routes: list[Route]) -> list[dict]:
        """
        Find routes present in JS but not discovered during crawl.
        
        Args:
            crawled_routes: Routes discovered during crawl
            
        Returns:
            List of hidden route dictionaries
        """
        crawled_paths = {r.slug for r in crawled_routes}
        crawled_paths.update(r.url for r in crawled_routes)
        
        hidden = []
        for route in self._extracted_routes:
            path = route['path']
            normalized = path.strip('/').replace('/', '_')
            
            if normalized not in crawled_paths and path not in crawled_paths:
                hidden.append(route)
        
        return hidden
    
    def save_analysis(self, crawled_routes: Optional[list[Route]] = None) -> str:
        """
        Save all extracted artifacts to files.
        
        Args:
            crawled_routes: Optional list of crawled routes for hidden route detection
            
        Returns:
            Path to saved analysis file
        """
        analysis = self.analyze_all()
        
        if crawled_routes:
            hidden_routes = self.find_hidden_routes(crawled_routes)
            
            hidden_path = self.config.get_output_path(
                "recon", "intelligence", "hidden_routes.json"
            )
            hidden_data = add_meta_to_output(
                {"hidden_routes": hidden_routes},
                target_url=self.config.target_url,
                phase="recon",
                run_id=self.run_id,
            )
            atomic_write_json(hidden_path, hidden_data)
            logger.info(f"Found {len(hidden_routes)} hidden routes")
        
        analysis_path = self.config.get_output_path(
            "recon", "intelligence", "frontend_analysis.json"
        )
        analysis_data = add_meta_to_output(
            analysis,
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        atomic_write_json(analysis_path, analysis_data)
        
        logger.info(f"Saved frontend analysis with {len(self._extracted_routes)} routes, "
                   f"{len(self._api_endpoints)} API endpoints")
        
        return str(analysis_path)


async def run_frontend_parser(
    html_content: str,
    base_url: str,
    crawled_routes: Optional[list[Route]] = None,
    run_id: Optional[str] = None,
) -> FrontendParser:
    """
    Run frontend parsing on HTML content.
    
    Args:
        html_content: HTML content to parse
        base_url: Base URL for resolving relative paths
        crawled_routes: Optional routes from crawl for hidden route detection
        run_id: Run ID
        
    Returns:
        FrontendParser instance with analysis results
    """
    parser = FrontendParser(run_id=run_id)
    await parser.fetch_js_bundles(html_content, base_url)
    parser.save_analysis(crawled_routes)
    return parser


if __name__ == "__main__":
    async def main():
        import sys
        
        html = """
        <html>
        <head>
            <script src="/static/js/main.chunk.js"></script>
            <script src="/static/js/bundle.js"></script>
        </head>
        <body></body>
        </html>
        """
        
        base = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
        
        parser = FrontendParser()
        await parser.fetch_js_bundles(html, base)
        analysis = parser.analyze_all()
        
        print(f"Routes found: {len(analysis['routes'])}")
        print(f"API endpoints: {len(analysis['api_endpoints'])}")
        print(f"Role constants: {analysis['role_constants']}")
        
        parser.save_analysis()
    
    asyncio.run(main())
