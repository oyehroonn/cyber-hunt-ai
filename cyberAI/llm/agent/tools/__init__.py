"""
CyberHunt AI — All 20 agent tools.

Import all tool functions for use in the agent loop dispatcher.
"""

from cyberAI.llm.agent.tools.auth import auth_register_and_login
from cyberAI.llm.agent.tools.crawl import crawl_target, analyze_js_bundles
from cyberAI.llm.agent.tools.schema import fetch_api_schema
from cyberAI.llm.agent.tools.discover import discover_endpoints, build_endpoint_inventory
from cyberAI.llm.agent.tools.headers import analyze_security_headers
from cyberAI.llm.agent.tools.idor import test_idor
from cyberAI.llm.agent.tools.ssrf import test_ssrf_oob
from cyberAI.llm.agent.tools.authz import test_auth_bypass, test_mass_assignment
from cyberAI.llm.agent.tools.race import test_race_condition
from cyberAI.llm.agent.tools.sqli import test_sqli_blind
from cyberAI.llm.agent.tools.replay import replay_request_with_variants, diff_responses
from cyberAI.llm.agent.tools.verify import verify_finding
from cyberAI.llm.agent.tools.findings import store_finding
from cyberAI.llm.agent.tools.logs import get_phase_logs
from cyberAI.llm.agent.tools.report import write_report
from cyberAI.llm.agent.tools.retry import error_retry

__all__ = [
    "auth_register_and_login",
    "crawl_target",
    "analyze_js_bundles",
    "fetch_api_schema",
    "discover_endpoints",
    "build_endpoint_inventory",
    "analyze_security_headers",
    "test_idor",
    "test_ssrf_oob",
    "test_auth_bypass",
    "test_mass_assignment",
    "test_race_condition",
    "test_sqli_blind",
    "replay_request_with_variants",
    "diff_responses",
    "verify_finding",
    "store_finding",
    "get_phase_logs",
    "write_report",
    "error_retry",
]
