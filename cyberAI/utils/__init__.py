"""
Utility modules for the CyberAI platform.
"""

from cyberAI.utils.helpers import (
    atomic_write_json,
    atomic_write_text,
    classify_endpoint,
    create_meta,
    decode_jwt_payload,
    extract_ids_from_text,
    extract_tenant_identifiers,
    generate_run_id,
    get_timestamp,
    hash_request,
    load_json,
    parse_rate_limit_headers,
    safe_filename,
    sanitize_for_log,
)
from cyberAI.utils.proxy_manager import ProxyManager, get_proxy_manager
from cyberAI.utils.captcha_solver import CaptchaSolver, get_captcha_solver
from cyberAI.utils.browser import (
    BrowserPool,
    browser_session,
    cleanup_browser_pool,
    dump_dom,
    get_browser_pool,
    get_cookies,
    get_local_storage,
    get_page_actions,
    get_session_storage,
    take_screenshot,
)
from cyberAI.utils.http_client import (
    AsyncHTTPClient,
    HTTPClientPool,
    cleanup_http_client,
    get_http_client,
)
from cyberAI.utils.attack_graph import AttackGraph, get_attack_graph

__all__ = [
    "atomic_write_json",
    "atomic_write_text",
    "classify_endpoint",
    "create_meta",
    "decode_jwt_payload",
    "extract_ids_from_text",
    "extract_tenant_identifiers",
    "generate_run_id",
    "get_timestamp",
    "hash_request",
    "load_json",
    "parse_rate_limit_headers",
    "safe_filename",
    "sanitize_for_log",
    "ProxyManager",
    "get_proxy_manager",
    "CaptchaSolver",
    "get_captcha_solver",
    "BrowserPool",
    "browser_session",
    "cleanup_browser_pool",
    "dump_dom",
    "get_browser_pool",
    "get_cookies",
    "get_local_storage",
    "get_page_actions",
    "get_session_storage",
    "take_screenshot",
    "AsyncHTTPClient",
    "HTTPClientPool",
    "cleanup_http_client",
    "get_http_client",
    "AttackGraph",
    "get_attack_graph",
]
