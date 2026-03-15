"""
Shared utility functions for the CyberAI platform.
"""

import asyncio
import base64
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, TypeVar
from uuid import uuid4

from loguru import logger

T = TypeVar("T")


def generate_run_id() -> str:
    """Generate a unique run ID for this execution."""
    return str(uuid4())


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat()


def get_timestamp_filename() -> str:
    """Get timestamp suitable for filenames."""
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def safe_filename(name: str, max_length: int = 200) -> str:
    """
    Convert a string to a safe filename.
    
    Args:
        name: Original string
        max_length: Maximum filename length
        
    Returns:
        Safe filename string
    """
    safe = re.sub(r'[^\w\-.]', '_', name)
    safe = re.sub(r'_+', '_', safe)
    safe = safe.strip('_')
    if len(safe) > max_length:
        hash_suffix = hashlib.md5(name.encode()).hexdigest()[:8]
        safe = safe[:max_length - 9] + '_' + hash_suffix
    return safe or "unnamed"


def atomic_write_json(path: Path, data: Any, indent: int = 2) -> None:
    """
    Atomically write JSON data to a file.
    Writes to a temp file first, then renames.
    
    Args:
        path: Target file path
        data: Data to serialize
        indent: JSON indentation
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    tmp_path = path.with_suffix('.tmp')
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, default=str, ensure_ascii=False)
        tmp_path.rename(path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def atomic_write_text(path: Path, content: str) -> None:
    """
    Atomically write text content to a file.
    
    Args:
        path: Target file path
        content: Text content to write
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    tmp_path = path.with_suffix('.tmp')
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        tmp_path.rename(path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def load_json(path: Path) -> Optional[Any]:
    """
    Load JSON from a file.
    
    Args:
        path: File path
        
    Returns:
        Parsed JSON data or None if file doesn't exist
    """
    path = Path(path)
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load JSON from {path}: {e}")
        return None


def decode_jwt_payload(token: str) -> Optional[dict]:
    """
    Decode the payload section of a JWT without verification.
    
    Args:
        token: JWT string
        
    Returns:
        Decoded payload dict or None
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return None


def extract_ids_from_text(text: str) -> dict[str, list[str]]:
    """
    Extract various ID formats from text.
    
    Args:
        text: Text to search
        
    Returns:
        Dict mapping ID type to list of found IDs
    """
    patterns = {
        'uuid': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        'integer_id': r'\b(?:id|ID|_id)["\']?\s*[:=]\s*(\d+)',
        'slug': r'/([a-z0-9-]{3,50})(?:/|$|\?)',
        'base64_id': r'[A-Za-z0-9+/]{20,}={0,2}',
    }
    
    results: dict[str, list[str]] = {}
    for id_type, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        results[id_type] = list(set(matches))
    
    return results


def extract_urls_from_text(text: str) -> list[str]:
    """Extract URLs from text."""
    pattern = r'https?://[^\s<>"\')\]]+(?:\.[^\s<>"\')\]]+)*'
    return list(set(re.findall(pattern, text)))


def classify_endpoint(method: str, url: str) -> str:
    """
    Classify an endpoint based on method and URL patterns.
    
    Args:
        method: HTTP method
        url: Endpoint URL
        
    Returns:
        Classification string
    """
    url_lower = url.lower()
    method = method.upper()
    
    admin_patterns = ['/admin', '/internal', '/manage', '/staff', '/console']
    auth_patterns = ['/auth', '/login', '/logout', '/register', '/password', '/mfa', '/session']
    billing_patterns = ['/billing', '/payment', '/invoice', '/subscription', '/plan', '/credit']
    file_patterns = ['/upload', '/download', '/file', '/attachment', '/media', '/asset']
    export_patterns = ['/export', '/import', '/download', '/report']
    
    for pattern in admin_patterns:
        if pattern in url_lower:
            return "admin"
    
    for pattern in auth_patterns:
        if pattern in url_lower:
            return "auth"
    
    for pattern in billing_patterns:
        if pattern in url_lower:
            return "billing"
    
    for pattern in file_patterns:
        if pattern in url_lower:
            return "files"
    
    for pattern in export_patterns:
        if pattern in url_lower:
            return "exports"
    
    if method == "GET":
        return "read"
    elif method == "POST":
        return "create"
    elif method in ("PUT", "PATCH"):
        return "update"
    elif method == "DELETE":
        return "delete"
    
    return "other"


def extract_tenant_identifiers(headers: dict, body: Optional[str], url: str) -> dict[str, str]:
    """
    Extract potential tenant identifiers from request data.
    
    Args:
        headers: Request headers
        body: Request body
        url: Request URL
        
    Returns:
        Dict of identifier names to values
    """
    identifiers: dict[str, str] = {}
    
    tenant_headers = [
        'x-tenant-id', 'x-org-id', 'x-organization-id', 'x-workspace-id',
        'x-team-id', 'x-account-id', 'x-client-id'
    ]
    
    for header in tenant_headers:
        for key, value in headers.items():
            if key.lower() == header:
                identifiers[header] = value
    
    if body:
        tenant_fields = ['tenant_id', 'org_id', 'organization_id', 'workspace_id', 'team_id', 'account_id']
        for field in tenant_fields:
            pattern = rf'"{field}"\s*:\s*"?([^",}}\s]+)'
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                identifiers[field] = match.group(1)
    
    tenant_params = ['tenant', 'org', 'organization', 'workspace', 'team']
    for param in tenant_params:
        pattern = rf'[?&]{param}[_]?(?:id)?=([^&]+)'
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            identifiers[f"param_{param}"] = match.group(1)
    
    return identifiers


def parse_rate_limit_headers(headers: dict) -> Optional[dict]:
    """
    Parse rate limit information from response headers.
    
    Args:
        headers: Response headers
        
    Returns:
        Rate limit info dict or None
    """
    rate_limit_headers = {
        'x-ratelimit-limit': 'limit',
        'x-ratelimit-remaining': 'remaining',
        'x-ratelimit-reset': 'reset',
        'retry-after': 'retry_after',
        'x-rate-limit-limit': 'limit',
        'x-rate-limit-remaining': 'remaining',
        'x-rate-limit-reset': 'reset',
    }
    
    info: dict[str, Any] = {}
    for header, key in rate_limit_headers.items():
        for h, v in headers.items():
            if h.lower() == header:
                try:
                    info[key] = int(v)
                except ValueError:
                    info[key] = v
    
    return info if info else None


def hash_request(method: str, url: str, body: Optional[str] = None) -> str:
    """
    Create a hash for deduplicating requests.
    
    Args:
        method: HTTP method
        url: Request URL
        body: Request body
        
    Returns:
        Hash string
    """
    content = f"{method}|{url}|{body or ''}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def chunk_list(lst: list[T], chunk_size: int) -> list[list[T]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


async def run_with_timeout(coro, timeout_seconds: float, default: T = None) -> T:
    """
    Run a coroutine with a timeout.
    
    Args:
        coro: Coroutine to run
        timeout_seconds: Timeout in seconds
        default: Default value if timeout
        
    Returns:
        Result or default
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        return default


def merge_dicts_deep(base: dict, override: dict) -> dict:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        override: Override dictionary
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts_deep(result[key], value)
        else:
            result[key] = value
    return result


def sanitize_for_log(data: Any, sensitive_keys: Optional[set] = None) -> Any:
    """
    Sanitize data for logging by redacting sensitive fields.
    
    Args:
        data: Data to sanitize
        sensitive_keys: Set of keys to redact
        
    Returns:
        Sanitized data
    """
    if sensitive_keys is None:
        sensitive_keys = {
            'password', 'secret', 'token', 'api_key', 'apikey', 'authorization',
            'cookie', 'session', 'credential', 'credit_card', 'ssn'
        }
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if any(s in key.lower() for s in sensitive_keys):
                result[key] = "[REDACTED]"
            else:
                result[key] = sanitize_for_log(value, sensitive_keys)
        return result
    elif isinstance(data, list):
        return [sanitize_for_log(item, sensitive_keys) for item in data]
    else:
        return data


def create_meta(target_url: str = "", phase: str = "", run_id: str = "") -> dict:
    """
    Create metadata dict for output files.
    
    Args:
        target_url: Target URL
        phase: Current phase
        run_id: Run ID
        
    Returns:
        Meta dictionary
    """
    return {
        "generated_at": get_timestamp(),
        "target_url": target_url,
        "phase": phase,
        "version": "1.0.0",
        "run_id": run_id or generate_run_id(),
    }


def add_meta_to_output(data: dict, target_url: str = "", phase: str = "", run_id: str = "") -> dict:
    """Add _meta key to output data."""
    return {
        "_meta": create_meta(target_url, phase, run_id),
        **data
    }


if __name__ == "__main__":
    print("Testing helpers...")
    
    print(f"Run ID: {generate_run_id()}")
    print(f"Timestamp: {get_timestamp()}")
    print(f"Safe filename: {safe_filename('Test/File:Name?.txt')}")
    
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    payload = decode_jwt_payload(jwt)
    print(f"JWT payload: {payload}")
    
    text = "User ID: 12345, UUID: 550e8400-e29b-41d4-a716-446655440000"
    ids = extract_ids_from_text(text)
    print(f"Extracted IDs: {ids}")
    
    print(f"Endpoint classification: {classify_endpoint('POST', '/api/admin/users')}")
