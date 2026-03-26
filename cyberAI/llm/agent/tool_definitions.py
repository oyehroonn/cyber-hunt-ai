"""
All 20 tool definitions in OpenAI function calling format.
Used by the agent loop to pass tools to the LLM.
"""

from __future__ import annotations

ALL_TOOL_DEFINITIONS: list[dict] = [
    # ------------------------------------------------------------------ #
    # Tool 1 — auth_register_and_login
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "auth_register_and_login",
            "description": (
                "Register and log in multiple test users via API or Playwright form. "
                "Returns session JWTs for user_a, user_b, and optionally admin. "
                "MUST be called first before any other tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target_url": {"type": "string", "description": "Base URL of the target application"},
                    "num_users": {"type": "integer", "description": "Number of regular users to register (default: 2)", "default": 2},
                    "also_try_admin": {"type": "boolean", "description": "Try known admin credentials", "default": True},
                    "run_id": {"type": "string", "description": "Assessment run ID"},
                },
                "required": ["target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 2 — crawl_target
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "crawl_target",
            "description": (
                "Playwright headless browser crawl of the target. "
                "Intercepts all network requests, extracts forms, discovers JS bundles. "
                "Run once unauthenticated and once per session for full coverage."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target_url": {"type": "string", "description": "Base URL to crawl"},
                    "session_name": {"type": "string", "description": "Session to use (e.g. user_a, admin). Omit for unauthenticated crawl."},
                    "max_pages": {"type": "integer", "description": "Maximum pages to crawl (default: 50)", "default": 50},
                    "run_id": {"type": "string"},
                },
                "required": ["target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 3 — analyze_js_bundles
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "analyze_js_bundles",
            "description": (
                "Fetch and analyze JavaScript bundles for hidden endpoints, routes, API paths, "
                "role constants, hardcoded secrets, and GraphQL queries. "
                "Critical for SPAs like React/Angular where routes are in JS code."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "bundle_urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of JS bundle URLs from the crawl",
                    },
                    "target_url": {"type": "string"},
                    "run_id": {"type": "string"},
                },
                "required": ["bundle_urls", "target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 4 — fetch_api_schema
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "fetch_api_schema",
            "description": (
                "Probe all common schema paths for OpenAPI/Swagger JSON or GraphQL introspection. "
                "Returns all endpoints if schema found."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target_url": {"type": "string"},
                    "session_name": {"type": "string", "description": "Optional session for authenticated schema discovery"},
                    "run_id": {"type": "string"},
                },
                "required": ["target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 5 — discover_endpoints
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "discover_endpoints",
            "description": (
                "Active directory/path brute-forcing using built-in wordlist (100+ paths) "
                "plus AI-generated extensions. Finds endpoints missed by crawling."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target_url": {"type": "string"},
                    "session_name": {"type": "string"},
                    "concurrent_requests": {"type": "integer", "default": 30},
                    "ai_extend": {"type": "boolean", "default": True},
                    "run_id": {"type": "string"},
                },
                "required": ["target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 6 — analyze_security_headers
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "analyze_security_headers",
            "description": (
                "Check all security headers: CSP, HSTS, X-Frame-Options, CORS, cookie flags, "
                "server version disclosure. Generates findings for missing or misconfigured headers."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target_url": {"type": "string"},
                    "sample_endpoints": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Extra paths to check beyond root",
                    },
                    "run_id": {"type": "string"},
                },
                "required": ["target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 7 — build_endpoint_inventory
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "build_endpoint_inventory",
            "description": (
                "Consolidate all discovered endpoints, deduplicate, probe auth, compute risk scores. "
                "Returns prioritized inventory. MUST call before entering test phase."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target_url": {"type": "string"},
                    "run_id": {"type": "string"},
                },
                "required": ["target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 8 — test_idor
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "test_idor",
            "description": (
                "Full cross-session IDOR test. "
                "Step 1: User A accesses own object (baseline). "
                "Step 2: User A accesses User B's object (attack). "
                "Step 3: Confirm User B's data is in response. "
                "ONLY confirmed if user_b's email/id is in attack response or bodies differ."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "endpoint": {
                        "type": "object",
                        "description": "Endpoint dict with path, methods, params",
                        "properties": {
                            "path": {"type": "string"},
                            "methods": {"type": "array", "items": {"type": "string"}},
                            "params": {"type": "array"},
                        },
                        "required": ["path"],
                    },
                    "target_url": {"type": "string"},
                    "run_id": {"type": "string"},
                    "num_swaps": {"type": "integer", "default": 10},
                    "test_vertical": {"type": "boolean", "default": True},
                },
                "required": ["endpoint", "target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 9 — test_ssrf_oob
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "test_ssrf_oob",
            "description": (
                "True OOB SSRF testing via Interactsh. "
                "Injects callback URLs into query params, body fields, and headers. "
                "ONLY confirms SSRF on DNS/HTTP OOB interaction — NOT on error pages. "
                "Falls back to reflection check if Interactsh unavailable."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target_url": {"type": "string"},
                    "injection_points": {
                        "type": "array",
                        "description": "List of injection point dicts. If omitted, auto-detected from state.",
                    },
                    "session_name": {"type": "string", "default": "user_a"},
                    "run_id": {"type": "string"},
                },
                "required": ["target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 10 — test_auth_bypass
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "test_auth_bypass",
            "description": (
                "Systematic auth enforcement testing. Tests 4 scenarios per endpoint: "
                "no auth, expired JWT, user role, admin role. "
                "Reports endpoints returning 200 without valid authentication."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "endpoints": {
                        "type": "array",
                        "description": "List of endpoint dicts to test",
                    },
                    "target_url": {"type": "string"},
                    "run_id": {"type": "string"},
                },
                "required": ["endpoints", "target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 11 — test_mass_assignment
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "test_mass_assignment",
            "description": (
                "Detect mass assignment by injecting privilege-escalating fields "
                "(role, isAdmin, admin, balance) into PUT/PATCH requests. "
                "Confirmed only if re-fetching shows the injected values were stored."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "update_endpoints": {
                        "type": "array",
                        "description": "PUT/PATCH endpoints from inventory",
                    },
                    "target_url": {"type": "string"},
                    "session_name": {"type": "string", "default": "user_a"},
                    "run_id": {"type": "string"},
                },
                "required": ["update_endpoints", "target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 12 — test_race_condition
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "test_race_condition",
            "description": (
                "Send N identical state-changing requests simultaneously. "
                "Detects race conditions on coupon redemption, counters, inventory. "
                "Confirmed if > 1 request succeeds for a single-use operation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "endpoint": {"type": "object", "description": "Endpoint dict"},
                    "payload": {"type": "object", "description": "Request body"},
                    "target_url": {"type": "string"},
                    "num_concurrent": {"type": "integer", "default": 25},
                    "window_ms": {"type": "number", "default": 50.0},
                    "session_name": {"type": "string", "default": "user_a"},
                    "run_id": {"type": "string"},
                },
                "required": ["endpoint", "payload", "target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 13 — test_sqli_blind
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "test_sqli_blind",
            "description": (
                "Blind SQL injection detection: boolean-based (AND 1=1 vs 1=2), "
                "time-based (SLEEP/WAITFOR), and error-based. "
                "Tests all query/body parameters on the endpoint."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "endpoint": {"type": "object", "description": "Endpoint dict with path, methods, params"},
                    "target_url": {"type": "string"},
                    "session_name": {"type": "string", "default": "user_a"},
                    "run_id": {"type": "string"},
                },
                "required": ["endpoint", "target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 14 — replay_request_with_variants
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "replay_request_with_variants",
            "description": (
                "Replay a captured HTTP request with systematic variations: "
                "different sessions, modified path params, headers, body fields. "
                "Returns each variant's response with diff from the base request."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "base_request": {
                        "type": "object",
                        "description": "{method, url, headers, body, session_name}",
                    },
                    "variants": {
                        "type": "array",
                        "description": "List of {field, value, description} dicts",
                    },
                    "target_url": {"type": "string"},
                    "run_id": {"type": "string"},
                },
                "required": ["base_request", "variants", "target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 15 — diff_responses
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "diff_responses",
            "description": (
                "Structured diff between two HTTP responses. "
                "Returns changed fields, PII differences, and a verdict: "
                "idor_confirmed, same_data, access_denied, error_response, or inconclusive."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "response_a": {
                        "type": "object",
                        "description": "{status, body}",
                    },
                    "response_b": {
                        "type": "object",
                        "description": "{status, body}",
                    },
                    "context": {
                        "type": "string",
                        "description": "Context hint: idor_check, auth_check, etc.",
                        "default": "idor_check",
                    },
                },
                "required": ["response_a", "response_b"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 16 — verify_finding
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "verify_finding",
            "description": (
                "Run targeted verification for a finding to reach confirmed/false_positive. "
                "IDOR: reproduce 3 times. SSRF: 3 fresh OOB domains. "
                "Auth: 4-role matrix. Mass assignment: before/after diff. "
                "No finding should remain needs_more_data after this."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "finding_id": {"type": "string", "description": "Finding ID e.g. F-003"},
                    "target_url": {"type": "string"},
                    "run_id": {"type": "string"},
                },
                "required": ["finding_id", "target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 17 — store_finding
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "store_finding",
            "description": (
                "Write a confirmed finding with all evidence to state storage. "
                "Only for CONFIRMED findings — never for speculative ones. "
                "Automatically assigns a finding_id and writes to RAG knowledge base."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "finding_type": {"type": "string", "description": "IDOR, SSRF, AUTH_BYPASS, RACE_CONDITION, SQLI, MASS_ASSIGNMENT"},
                    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"]},
                    "title": {"type": "string"},
                    "endpoint": {"type": "string"},
                    "method": {"type": "string"},
                    "evidence": {"type": "object", "description": "Raw requests, responses, diffs, OOB logs"},
                    "cvss_score": {"type": "number"},
                    "owasp_category": {"type": "string"},
                    "cwe_id": {"type": "string"},
                    "remediation": {"type": "string"},
                    "target_url": {"type": "string"},
                    "run_id": {"type": "string"},
                    "subtype": {"type": "string"},
                    "reproduction_steps": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["finding_type", "severity", "title", "endpoint", "method",
                             "evidence", "cvss_score", "owasp_category", "cwe_id", "remediation"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 18 — get_phase_logs
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "get_phase_logs",
            "description": (
                "Query SQLite logs from any phase. Use after each tool call to check for errors. "
                "Filter by phase, level (ERROR/WARNING/INFO), or keyword search."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "run_id": {"type": "string"},
                    "phase": {
                        "type": "string",
                        "description": "recon, plan, test, verify, report — or omit for all",
                    },
                    "level": {"type": "string", "enum": ["ERROR", "WARNING", "INFO"]},
                    "search": {"type": "string", "description": "Keyword to filter messages"},
                    "last_n": {"type": "integer", "default": 100},
                },
                "required": ["run_id"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 19 — write_report
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "write_report",
            "description": (
                "Generate final security assessment report in markdown, JSON, and CSV. "
                "Includes executive summary, all confirmed findings with evidence, "
                "endpoint inventory, and error log. Call at end of assessment."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "run_id": {"type": "string"},
                    "target_url": {"type": "string"},
                    "formats": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["markdown", "json", "csv"]},
                        "default": ["markdown", "json", "csv"],
                    },
                    "include_raw_evidence": {"type": "boolean", "default": True},
                    "executive_summary": {"type": "boolean", "default": True},
                },
                "required": ["run_id", "target_url"],
            },
        },
    },
    # ------------------------------------------------------------------ #
    # Tool 20 — error_retry
    # ------------------------------------------------------------------ #
    {
        "type": "function",
        "function": {
            "name": "error_retry",
            "description": (
                "Analyze a tool failure and determine retry strategy. "
                "402 → switch to Ollama. 429 → backoff. 503 → retry with delay. "
                "ConnectionError → check target. TimeoutError → reduce concurrency. "
                "401 → refresh auth sessions. Returns action: retry/skip/switch_model."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "failed_tool": {"type": "string", "description": "Name of the tool that failed"},
                    "error": {"type": "string", "description": "Error message or exception string"},
                    "original_args": {"type": "object", "description": "Args originally passed to the failed tool"},
                    "run_id": {"type": "string"},
                    "attempt": {"type": "integer", "default": 1, "description": "Retry attempt number (1-3)"},
                },
                "required": ["failed_tool", "error", "original_args"],
            },
        },
    },
]
