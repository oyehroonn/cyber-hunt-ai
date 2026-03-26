# CyberHunt AI — Complete Agent Architecture Redesign
## Full Technical Specification & Developer Implementation Prompt

**Version:** 2.0
**Prepared:** March 2026
**Scope:** End-to-end autonomous security assessment agent with 20 tools, multi-session IDOR testing, OOB SSRF verification, automated authentication, and production-grade reporting

---

## PART 1 — DIAGNOSIS: WHY THE CURRENT SYSTEM FAILS

Before building the new architecture, understand precisely what is broken and why.

### Problem 1 — Shallow Recon (1 route, 2 endpoints)

The current recon module crawled 1 route and produced 2 endpoints on a full web application that has 100+ API surfaces. This is near-zero coverage. The root causes are:

- No JavaScript bundle analysis — every modern SPA hides most routes inside compiled JS chunks. Juice Shop's `/api/` endpoints are only discoverable by parsing `main.js`.
- No sitemap/robots.txt crawl to seed the spider
- No authenticated crawl — endpoints behind login were never seen
- No API schema discovery (Swagger/OpenAPI at `/api-docs`, `/swagger.json`, GraphQL introspection at `/graphql`)
- No brute-force path expansion using wordlists (SecLists)

### Problem 2 — IDOR Detection Is Not IDOR Testing

The system found "admin-looking URLs returning 200 when it expected 403" and called this IDOR with medium severity. This is not IDOR. IDOR requires:

1. User A authenticating and accessing User A's owned resource — **baseline**
2. User A swapping User B's resource ID into the same request — **cross-account probe**
3. The server returning User B's data — **the exploit**

None of these three steps happened. What happened was: unauthenticated request to `/rest/admin/application-configuration` returned 200. On Juice Shop, that is intentional. Even on a real app, that is information disclosure, not IDOR.

### Problem 3 — SSRF "Detection" Is String Matching on Error Pages

The SSRF test sent `GET /redirect?to=http://localhost:80` and the server replied 406 with an error page that contained the string "localhost" in its body. The system pattern-matched on that string and declared SSRF. This is a false positive. A real SSRF requires:

- The server to actually initiate an outbound HTTP or DNS request to your controlled domain
- You to observe that outbound request on a listening server (Out-of-Band / OOB)
- The 406 response proves the opposite — the server rejected the redirect target

### Problem 4 — target_url Mismatch (example.com in Reports)

The metadata `_meta.target_url` says `https://example.com` while the actual scan was on `demo.owasp-juice.shop`. This means the run config or report generator is reading a stale default. Every downstream system that reads that metadata is poisoned.

### Problem 5 — "Need More Data" Is an Architectural Bug, Not a Data Problem

The agent returned 5 findings as "needs_more_data". This means the verifier ran out of evidence to make a decision and gave up. An autonomous agent should instead generate additional test actions to collect the missing evidence, execute them, and re-evaluate. "Need more data" should trigger a tool call to gather more data, not terminate the finding.

### Problem 6 — No Authentication = No Real Testing

Web application security testing without authenticated sessions only tests the public surface. All business logic bugs (IDOR, BFLA, race conditions, privilege escalation) live behind authentication. The agent must be able to:

- Register a new account on any web application
- Log in as multiple user roles
- Maintain concurrent sessions
- Inject auth tokens into every test request

### Problem 7 — The Agent Has Too Few Tools (3–5) With No Real Capabilities

The current agent calls `run_pipeline_phase` as its main tool — a subprocess wrapper that just re-runs the CLI. This means the agent cannot inspect intermediate data, pivot on findings, retry specific tests, or adapt its strategy. It is a shell script, not an agent.

---

## PART 2 — TARGET ARCHITECTURE

### Overview

The new system is a **memory-augmented agentic loop** where a single LLM (DeepSeek-R1 via OpenRouter, with Ollama fallback) retains the complete assessment state across all pipeline phases, uses 20 specialized tools to collect evidence, and produces confirmed vulnerability reports.

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT CORE (LLM Loop)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ System Prompt │  │   RAG Layer  │  │  Persistent Mem  │  │
│  │  (per phase) │  │ ChromaDB+KB  │  │  (state store)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────┬───────────────────────────┘
                                  │ 20 Tool Calls
         ┌────────────────────────┼───────────────────────┐
         ▼                        ▼                       ▼
  [RECON TOOLS]           [ATTACK TOOLS]         [INFRA TOOLS]
  crawl_target            test_idor              oob_register
  analyze_js              test_ssrf_oob          auth_register
  fetch_api_schema        test_race_condition    auth_login
  discover_endpoints      test_auth_bypass       session_pool
  extract_objects         test_sqli_fuzz         store_finding
  analyze_headers         test_mass_assign       read_finding
  check_tls               verify_finding         write_report
                          replay_request         get_phase_logs
                          diff_responses         error_retry
```

### Memory Model

The agent maintains three memory layers that persist across the entire session:

**Layer 1 — Structured State** (JSON file: `run_state.json`):
```json
{
  "run_id": "a77cb3b5",
  "target": "https://demo.owasp-juice.shop",
  "phase": "testing",
  "sessions": {
    "user_a": {"email": "auto_user_a@test.local", "jwt": "eyJ...", "user_id": 3},
    "user_b": {"email": "auto_user_b@test.local", "jwt": "eyJ...", "user_id": 4},
    "admin":  {"email": "admin@juice-sh.op", "jwt": "eyJ...", "user_id": 1}
  },
  "endpoints": [
    {"path": "/api/Users", "methods": ["GET","POST"], "auth_required": true, "params": ["id"]},
    ...
  ],
  "findings": [
    {"id": "F-001", "type": "IDOR", "status": "confirmed", "evidence": {...}},
    ...
  ],
  "pending_verifications": ["F-003", "F-007"],
  "tested_endpoints": ["/api/Users/1", "/api/Users/2"],
  "errors": []
}
```

**Layer 2 — Phase Log Store** (SQLite: `logs.db`):
Every subprocess log line from every phase is written to a SQLite table with columns: `timestamp, phase, level, module, message, run_id`. The agent queries this with `get_phase_logs(run_id, phase, level_filter)`.

**Layer 3 — RAG Context** (ChromaDB):
The existing knowledge base of 242 bug reports. Expanded with real-time additions: each confirmed finding from this run is added as a new document so future queries benefit.

---

## PART 3 — THE 20 AGENT TOOLS

Each tool is defined here with its exact Python function signature, what it does, and what it returns. These are the tools the LLM calls. Every tool writes its output to the structured state AND returns a compact summary to the LLM context so the agent doesn't consume its context window with raw bytes.

---

### Tool 1 — `crawl_target`
**Phase:** Recon
**Purpose:** Deep web crawling using Playwright's headless Chromium. Captures all page navigations, XHR/fetch calls, form submissions, and WebSocket handshakes. Crucially, runs crawls in both unauthenticated and authenticated modes.

```python
async def crawl_target(
    target_url: str,
    session_name: str | None = None,   # None = unauthenticated, or key from sessions pool
    max_pages: int = 200,
    follow_js_redirects: bool = True,
    capture_network: bool = True,       # intercept all XHR/fetch calls
    run_id: str = ...
) -> dict:
    """
    Returns:
    {
      "pages_crawled": 47,
      "routes_discovered": ["GET /api/Users", "POST /api/Users/login", ...],
      "forms_found": [{"url": "/register", "fields": ["email","password","passwordRepeat"], ...}],
      "js_bundles": ["https://target/vendor.js", "https://target/main.js"],
      "cookies_set": {"token": "..."},
      "errors": []
    }
    All routes written to state['endpoints'] and logs.db.
    """
```

**Implementation notes:**
- Use `playwright.chromium.launch(headless=True)` with request interception
- Attach `page.on('request', ...)` and `page.on('response', ...)` to capture all API calls
- After each page navigation, call `page.evaluate("performance.getEntriesByType('resource')")` to get any lazily loaded API calls
- Set session cookies from `sessions[session_name]['jwt']` before navigation
- Deduplicate routes by normalizing URL patterns: `/api/Users/3` → `/api/Users/{id}`

---

### Tool 2 — `analyze_js_bundles`
**Phase:** Recon
**Purpose:** Download all JavaScript bundles found by `crawl_target`, extract hidden API endpoints, constants, role names, and hardcoded credentials using both regex and AST analysis.

```python
async def analyze_js_bundles(
    bundle_urls: list[str],
    target_origin: str,
    run_id: str = ...
) -> dict:
    """
    Returns:
    {
      "new_endpoints": ["/api/SecurityAnswers", "/api/Recycles/..."],
      "hidden_routes": ["/administration", "/accounting"],
      "role_constants": ["admin", "accounting", "deluxe"],
      "potential_secrets": ["ql0wjRL3..."],   # flagged but never logged in full
      "graphql_schema_hints": ["query {Products", "mutation AddProductReview"],
      "source_maps_exposed": true
    }
    """
```

**Implementation notes:**
- Download each bundle URL with `httpx.AsyncClient`
- Run regex sweeps: `r'["\']/(api|rest|graphql|admin)[^"\']{0,100}["\']'` for endpoint strings
- Run LinkFinder regex: composite of 4 expressions for relative paths, absolute paths, query strings
- Use `subprocess.run(['node', 'ast_extract.js', bundle_path])` for deeper AST analysis (write a companion `ast_extract.js` that uses acorn)
- Flag any string matching `(password|secret|key|token|auth)[^'"]{0,50}` as a potential credential

---

### Tool 3 — `fetch_api_schema`
**Phase:** Recon
**Purpose:** Attempt to discover and download API schema in OpenAPI, Swagger, GraphQL introspection, or WADL format.

```python
async def fetch_api_schema(
    target_url: str,
    session_name: str | None = None,
    run_id: str = ...
) -> dict:
    """
    Probes common schema paths. Returns:
    {
      "schema_type": "openapi_v3",   # or "graphql", "swagger_v2", "none"
      "schema_url": "/api-docs",
      "endpoints_parsed": 156,
      "schemas": [{"path": "/api/Users/{id}", "method": "GET", "params": [...]}],
      "graphql_types": ["User", "Product", "Order", ...],
      "graphql_mutations": ["addToBasket", "updateUserProfile", ...]
    }
    """
```

**Probe paths (try all):**
`/swagger.json`, `/swagger.yaml`, `/api-docs`, `/api-docs.json`, `/openapi.json`, `/openapi.yaml`, `/v1/api-docs`, `/api/v1/swagger.json`, `/graphql`, `/__graphql`, `/graphql/schema`, `/.well-known/openapi`

For GraphQL: send `{ __schema { types { name } } }` introspection query. If it responds, fully dump the schema.

---

### Tool 4 — `discover_endpoints`
**Phase:** Recon
**Purpose:** Active directory/path brute-forcing using curated wordlists, extended by AI-suggested paths based on already-discovered endpoints.

```python
async def discover_endpoints(
    target_url: str,
    wordlist: str = "raft-medium-directories",   # uses SecLists
    concurrent_requests: int = 30,
    session_name: str | None = None,
    ai_extend: bool = True,   # use LLM to suggest additional paths from discovered context
    run_id: str = ...
) -> dict:
    """
    Returns:
    {
      "new_paths_found": ["/administration", "/metrics", "/health"],
      "interesting_status_codes": {"/admin": 200, "/actuator": 200, "/metrics": 401},
      "total_probed": 4729
    }
    """
```

**Implementation notes:**
- Use `asyncio.Semaphore(concurrent_requests)` to rate-limit
- Prioritize wordlist paths that match already-known path segments (e.g., if `/api/Users` exists, also try `/api/Users/admin`, `/api/Users/export`, `/api/Users/search`)
- For `ai_extend=True`: call the LLM with the discovered endpoint list and ask it to suggest 50 additional paths based on patterns (this is a recursive tool call, not an LLM message)
- Track 200/301/302/401/403 separately; 401 and 403 are interesting (path exists but blocked)

---

### Tool 5 — `analyze_security_headers`
**Phase:** Recon
**Purpose:** Fetch target homepage and all discovered API endpoints, analyze all security-relevant HTTP response headers.

```python
async def analyze_security_headers(
    target_url: str,
    sample_endpoints: list[str],
    run_id: str = ...
) -> dict:
    """
    Returns:
    {
      "missing_headers": ["Content-Security-Policy", "Strict-Transport-Security"],
      "weak_headers": {"X-Frame-Options": "SAMEORIGIN (not DENY)", "CORS": "Access-Control-Allow-Origin: *"},
      "cookies_insecure": [{"name": "token", "secure": false, "httponly": false, "samesite": null}],
      "tls_issues": [],
      "server_disclosure": "Server: Express",
      "findings": [{"type": "CORS_WILDCARD", "severity": "medium", "endpoint": "/api/Users"}]
    }
    """
```

---

### Tool 6 — `auth_register_and_login`
**Phase:** Recon (setup) / all phases
**Purpose:** Automatically register N new user accounts and log in. Handles CSRF tokens, multi-step registration flows, email confirmation stubs, and CAPTCHAs (where bypassable). Creates the session pool used by all subsequent tests.

```python
async def auth_register_and_login(
    target_url: str,
    num_users: int = 3,    # creates user_a, user_b, user_c
    also_try_admin: bool = True,   # attempt known admin credentials
    run_id: str = ...
) -> dict:
    """
    Returns:
    {
      "sessions_created": {
        "user_a": {"email": "cai_a_a77c@proton.me.local", "user_id": 3, "jwt": "eyJ...", "role": "user"},
        "user_b": {"email": "cai_b_a77c@proton.me.local", "user_id": 4, "jwt": "eyJ...", "role": "user"},
        "admin":  {"email": "admin@juice-sh.op", "user_id": 1, "jwt": "eyJ...", "role": "admin"}
      },
      "registration_method": "form",   # or "api", "oauth"
      "csrf_token_handling": "auto",
      "errors": []
    }
    Writes all sessions to state['sessions'].
    """
```

**Implementation notes (this is the most complex tool):**

**Step 1 — Discovery:** Use `crawl_target` output to find registration form. Look for forms with `password` + `email` fields. Also try common API registration endpoints: `POST /api/Users`, `POST /auth/register`, `POST /api/register`.

**Step 2 — CSRF handling:** Fetch the registration page first. Extract CSRF token via regex `(csrf_token|_token|authenticity_token)[^"]{0,5}"value="([^"]+)"` or `name="(csrf[^"]*)".*?value="([^"]+)"`. If using HTTP API (JSON), most APIs don't require CSRF.

**Step 3 — Registration payload:** Generate unique emails: `cai_{role}_{run_id[:8]}@cyberhunt.local`. On Juice Shop specifically: `POST /api/Users` with `{"email": "...", "password": "...", "passwordRepeat": "...", "securityQuestion": {...}, "securityAnswer": "..."}`. Use the API schema from `fetch_api_schema` to know required fields.

**Step 4 — Login:** After registration, call the login endpoint with the same credentials. Extract the JWT from: response body (most common), `Authorization` header, or `Set-Cookie` with `token=`.

**Step 5 — Admin detection:** Try known default credentials first: `admin@juice-sh.op / admin123`, `admin@admin.com / admin`, `admin / password`. If none work, try to find admin via BFLA (attempt admin-only endpoints as user_a; if they respond 200, user_a might be admin or authz is broken).

**Step 6 — Session validation:** After obtaining each session, make an authenticated request to a known user-specific endpoint (e.g., `GET /api/Users/{user_id}`) and verify the response contains the expected email. If it doesn't, mark the session as invalid and retry.

---

### Tool 7 — `build_endpoint_inventory`
**Phase:** Recon (final step)
**Purpose:** Consolidate all endpoints discovered across all previous recon tools into a single structured inventory with metadata about each endpoint.

```python
async def build_endpoint_inventory(run_id: str) -> dict:
    """
    Reads from state and logs.db. Deduplicates, normalizes, enriches.
    Returns:
    {
      "total_endpoints": 156,
      "endpoint_inventory": [
        {
          "path": "/api/Users/{id}",
          "methods": ["GET", "DELETE"],
          "auth_required": true,
          "inferred_roles": ["user", "admin"],
          "has_id_param": true,
          "id_param_type": "integer",
          "response_schema_hint": {"id": 1, "email": "...", "role": "..."},
          "discovery_sources": ["crawl", "js_analysis", "schema"],
          "risk_score": 8.5,   # computed: has ID param + returns PII + not rate limited
          "test_priority": "critical"
        }
      ],
      "high_priority_count": 23
    }
    """
```

**Risk scoring formula per endpoint:**
- `+3` if has numeric/UUID ID parameter
- `+2` if returns PII fields (email, phone, address, name, SSN-like)
- `+2` if accessible by low-privilege role
- `+2` if also accessible unauthenticated
- `+1` if has file/data export functionality
- `-1` if has rate limiting header (`X-RateLimit-*`)
- `-1` if responds 403 to unauthenticated probe

---

### Tool 8 — `test_idor`
**Phase:** Testing
**Purpose:** Automated IDOR testing using cross-session replay with the exact Autorize/OWASP WSTG methodology. This is the most important test tool.

```python
async def test_idor(
    endpoint: dict,        # from endpoint inventory
    run_id: str = ...,
    num_swaps: int = 10,   # how many cross-user ID swaps to try
    test_vertical: bool = True   # also test user session -> admin objects
) -> dict:
    """
    Runs the full IDOR testing protocol:
    1. As user_a, create or retrieve an object → get its ID
    2. As user_b, request user_a's object by ID
    3. Unauthenticated request to user_a's object
    4. If admin session exists, verify admin CAN access (positive control)

    Returns:
    {
      "endpoint": "/api/Users/{id}",
      "tests_run": 10,
      "confirmed_idor": true,
      "idor_type": "horizontal",   # horizontal = same role, vertical = privilege escalation
      "evidence": {
        "baseline_request": "GET /api/Users/3 with user_a session → 200, email: user_a@test",
        "attack_request":   "GET /api/Users/4 with user_a session → 200, email: user_b@test",
        "user_b_data_in_response": true,
        "pii_fields_exposed": ["email", "username"],
        "baseline_response_hash": "sha256:abc...",
        "attack_response_hash": "sha256:def...",   # different = different user's data
        "attack_response_contains_user_b_email": true
      },
      "cvss_score": 8.1,
      "finding_id": "F-003"
    }
    """
```

**Implementation — The Cross-Session IDOR Algorithm:**

```python
# Step 1: Map IDs owned by each user
# For /api/Users/{id}: user_a's ID is in their session JWT (sub claim)
# For /api/Baskets/{id}: POST /api/Baskets to create a basket, record the ID
# For /api/Orders/{id}: POST /api/Orders, record the ID

# Step 2: Baseline — User A accesses User A's object (expect 200)
baseline_resp = await client_a.get(f"/api/Users/{user_a_id}")
assert baseline_resp.status_code == 200
baseline_body = baseline_resp.json()
baseline_pii = extract_pii_fields(baseline_body)  # finds email, name, etc.

# Step 3: Attack — User A accesses User B's object (SHOULD return 403 if secure)
attack_resp = await client_a.get(f"/api/Users/{user_b_id}")

# Step 4: Decision
if attack_resp.status_code == 200:
    attack_body = attack_resp.json()
    # Confirm this is ACTUALLY user_b's data, not a generic response
    if user_b_email in str(attack_body) or \
       attack_body.get('id') == user_b_id or \
       body_differs_from_baseline(baseline_body, attack_body):
        # CONFIRMED IDOR
        return confirmed_finding(severity="high", type="horizontal_idor")
    else:
        return ambiguous_finding()  # same data for all users = not IDOR
elif attack_resp.status_code in [401, 403]:
    return no_finding("authorization properly enforced")
else:
    return ambiguous_finding(f"unexpected status {attack_resp.status_code}")
```

---

### Tool 9 — `test_ssrf_oob`
**Phase:** Testing
**Purpose:** True OOB SSRF testing using Interactsh. Injects controlled callback URLs into every possible injection point and monitors for DNS/HTTP callbacks that prove server-side request execution.

```python
async def test_ssrf_oob(
    target_url: str,
    injection_points: list[dict],   # from recon: params, headers, body fields that accept URLs
    interactsh_server: str = "oast.me",   # public Interactsh server
    session_name: str = "user_a",
    run_id: str = ...
) -> dict:
    """
    Returns:
    {
      "oob_interactions": [
        {
          "injection_point": "GET /redirect?to=",
          "payload": "http://abc123def456.oast.me/path",
          "interaction_type": "dns",  # or "http"
          "source_ip": "104.21.14.5",  # target server's egress IP
          "timestamp": "2026-03-25T17:00:01Z",
          "confirmed_ssrf": true,
          "severity": "critical"
        }
      ],
      "tested_points": 34,
      "confirmed_count": 1
    }
    """
```

**Implementation — OOB SSRF Protocol:**

```python
# Step 1: Start Interactsh client
# Use the Python wrapper: pip install interactsh-client
# OR call the CLI: interactsh-client -server oast.me -json
# Generate unique domain per test: abc123def456.oast.me

# Step 2: Identify injection points from recon
injection_candidates = [
    # URL parameters that accept URLs
    {"type": "query_param", "endpoint": "/redirect", "param": "to", "method": "GET"},
    {"type": "query_param", "endpoint": "/api/Feedbacks", "param": "comment", "method": "POST"},
    # Request headers
    {"type": "header", "header": "X-Forwarded-For"},
    {"type": "header", "header": "Referer"},
    # Body fields containing URL-like patterns
    {"type": "body_field", "endpoint": "/api/Products", "field": "image"},
]

# Step 3: For each injection point, generate a unique callback URL
for point in injection_candidates:
    unique_id = generate_id()  # correlates interaction to test
    callback_url = f"http://{unique_id}.{interactsh_host}"

    # Inject and send request
    await send_request_with_injection(point, callback_url, session)

    # Wait 3 seconds for DNS propagation
    await asyncio.sleep(3)

    # Poll Interactsh for interactions
    interactions = await interactsh_client.poll(filter=unique_id)

    if interactions:
        # CONFIRMED SSRF — server made outbound request/lookup
        record_confirmed_ssrf(point, interactions[0])

# Step 4: Distinguish blind SSRF from reflection
# Reflection = your URL appears in the response body (server is echoing it back)
# SSRF = an interaction appears on Interactsh server (server made a request)
# These are completely different! Check for BOTH but only count SSRF as critical
```

**Interactsh Integration Code:**
```python
import subprocess, json, asyncio

class InteractshClient:
    def __init__(self, server="oast.me"):
        self.server = server
        self.proc = None
        self.domains = {}  # unique_id → domain

    async def start(self):
        self.proc = await asyncio.create_subprocess_exec(
            "interactsh-client", "-server", self.server, "-json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )

    def generate_url(self, unique_id: str) -> str:
        """Get a unique OOB URL for this test"""
        domain = f"{unique_id}.{self.server}"
        self.domains[unique_id] = domain
        return f"http://{domain}"

    async def poll(self, timeout=5.0) -> list[dict]:
        """Read any interactions from the subprocess stdout"""
        interactions = []
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            try:
                line = await asyncio.wait_for(
                    self.proc.stdout.readline(), timeout=0.5
                )
                if line:
                    interactions.append(json.loads(line.decode()))
            except asyncio.TimeoutError:
                break
        return interactions
```

---

### Tool 10 — `test_auth_bypass`
**Phase:** Testing
**Purpose:** Systematic testing of authentication enforcement on every discovered endpoint. Uses the session pool to test: unauthenticated, user, admin. Identifies endpoints accessible without auth or by wrong role.

```python
async def test_auth_bypass(
    endpoints: list[dict],
    run_id: str = ...
) -> dict:
    """
    For each endpoint, tests 4 auth scenarios:
    1. No auth (no token) → expect 401/403
    2. Invalid/expired JWT → expect 401
    3. user_a JWT → expect role-appropriate response
    4. admin JWT → expect 200 (positive control)

    Returns findings where unauthenticated or wrong-role gets 200.
    {
      "auth_bypass_findings": [
        {
          "endpoint": "GET /api/Users",
          "scenario": "no_auth",
          "status": 200,
          "response_contains_pii": true,
          "severity": "high",
          "finding_id": "F-002"
        }
      ]
    }
    """
```

---

### Tool 11 — `test_mass_assignment`
**Phase:** Testing
**Purpose:** Detect mass assignment vulnerabilities by sending extra, undocumented fields in PUT/PATCH/POST body to escalate privilege or modify protected fields.

```python
async def test_mass_assignment(
    update_endpoints: list[dict],   # PUT/PATCH endpoints from inventory
    session_name: str = "user_a",
    run_id: str = ...
) -> dict:
    """
    Sends requests with extra privilege-escalating fields appended to legitimate body.
    Tests fields like: role, isAdmin, admin, is_admin, verified, credit, balance,
                       permissions, scope, group, tier, subscription

    Decision rule: if update succeeds (200/204) AND re-fetching the object shows
    the injected field was stored → confirmed mass assignment.

    Returns confirmed findings with exact payload and before/after diff.
    """
```

---

### Tool 12 — `test_race_condition`
**Phase:** Testing
**Purpose:** Detect race condition vulnerabilities by sending N identical state-changing requests simultaneously using asyncio and precise timing control.

```python
async def test_race_condition(
    endpoint: dict,
    payload: dict,
    num_concurrent: int = 25,
    window_ms: float = 50.0,   # target all requests within this window
    session_name: str = "user_a",
    run_id: str = ...
) -> dict:
    """
    Creates N HTTP clients, pre-stages requests, releases all simultaneously.
    Monitors for: multiple 200 responses to a state-change that should only
    allow one (e.g., coupon redemption, limited-use tokens, inventory decrement).

    Returns:
    {
      "requests_sent": 25,
      "success_responses": 14,   # should be 1 if no race condition
      "confirmed_race": true,
      "state_after": {"balance": 420.00},   # verifies actual state change
      "finding_id": "F-007"
    }
    """
```

---

### Tool 13 — `test_sqli_blind`
**Phase:** Testing
**Purpose:** Blind SQL injection detection using boolean-based and time-based techniques on every parameter in the endpoint inventory.

```python
async def test_sqli_blind(
    endpoint: dict,
    session_name: str = "user_a",
    run_id: str = ...
) -> dict:
    """
    Tests boolean-based: inject 'AND 1=1--' vs 'AND 1=2--', compare responses
    Tests time-based: inject 'SLEEP(3)' / 'WAITFOR DELAY 0:0:3', measure response time
    Tests error-based: look for DB error strings in response

    Only runs on endpoints with string/integer parameters, not binary/file.

    Returns confirmed findings with: vulnerable parameter, payload, technique, evidence.
    """
```

---

### Tool 14 — `replay_request_with_variants`
**Phase:** Testing/Verification
**Purpose:** Take any captured HTTP request and replay it with systematic variations: different sessions, modified headers, parameter mutations, encoding variations. Used by the agent to deep-dive on promising findings.

```python
async def replay_request_with_variants(
    base_request: dict,   # {method, url, headers, body, session}
    variants: list[dict], # [{field: "path_param", value: "1337", description: "admin ID"}]
    run_id: str = ...
) -> dict:
    """
    Returns each variant's response with diff from base:
    {
      "results": [
        {
          "description": "admin ID in path",
          "request": {...},
          "response": {"status": 200, "body_hash": "...", "pii_fields": [...]},
          "diff_from_base": {"body_changed": true, "new_fields": ["role", "admin_token"]}
        }
      ]
    }
    """
```

---

### Tool 15 — `diff_responses`
**Phase:** Verification
**Purpose:** Structured diff between two HTTP responses. Determines if they represent different user data (IDOR evidence), same data (no vuln), or a server error.

```python
def diff_responses(
    response_a: dict,
    response_b: dict,
    context: str = "idor_check"
) -> dict:
    """
    Returns:
    {
      "status_match": true/false,
      "body_identical": false,
      "changed_fields": ["email", "username"],
      "a_specific_values": {"email": "user_a@test"},
      "b_specific_values": {"email": "user_b@test"},
      "pii_in_b_not_in_a": ["user_b_email", "user_b_phone"],
      "verdict": "idor_confirmed",  # or "same_data", "error_response", "empty"
      "confidence": 0.95
    }
    """
```

---

### Tool 16 — `verify_finding`
**Phase:** Verification
**Purpose:** Given a finding marked "likely" or "needs_more_data", run a targeted verification protocol specific to that finding type to reach a confirmed/false-positive verdict. No finding should ever remain "needs_more_data" — the agent must keep running this tool until it resolves.

```python
async def verify_finding(
    finding_id: str,
    run_id: str = ...
) -> dict:
    """
    Reads the finding from state, determines what additional evidence is needed,
    executes targeted tests, updates the finding status.

    For IDOR: runs cross_session_idor_proof()
    For SSRF: runs oob_ssrf_proof() with fresh Interactsh domain
    For auth_bypass: runs auth_matrix_check() across all 4 role combinations
    For mass_assignment: runs before_after_state_diff()

    Returns:
    {
      "finding_id": "F-003",
      "previous_status": "needs_more_data",
      "new_status": "confirmed",  # or "false_positive"
      "verification_method": "cross_session_replay",
      "evidence_added": {...},
      "confidence": 0.98
    }
    """
```

---

### Tool 17 — `store_finding`
**Phase:** All
**Purpose:** Write a finding (with all evidence) to the structured state and to the RAG knowledge base for future retrieval.

```python
def store_finding(
    finding_type: str,          # "IDOR", "SSRF", "AUTH_BYPASS", "RACE_CONDITION", etc.
    severity: str,              # "critical", "high", "medium", "low", "info"
    title: str,
    endpoint: str,
    method: str,
    evidence: dict,             # raw requests/responses, diffs, OOB interaction logs
    cvss_score: float,
    owasp_category: str,        # "API1:2023 BOLA", "A07:2021 Identification and Auth Failures"
    cwe_id: str,                # "CWE-284", "CWE-918", etc.
    remediation: str,
    run_id: str = ...
) -> str:
    """Returns the finding_id (e.g., "F-007")"""
```

---

### Tool 18 — `get_phase_logs`
**Phase:** All (meta-tool)
**Purpose:** Query the SQLite log store for logs from any completed phase. The agent calls this after every phase subprocess completes to understand what happened, what errors occurred, and what data was collected.

```python
def get_phase_logs(
    run_id: str,
    phase: str | None = None,    # "recon", "plan", "test", "verify", "report"
    level: str | None = None,    # "ERROR", "WARNING", "INFO"
    search: str | None = None,   # keyword filter
    last_n: int = 100
) -> dict:
    """
    Returns:
    {
      "total_log_lines": 4829,
      "errors": [{"timestamp": "...", "module": "recon.spider", "message": "..."}],
      "warnings": [...],
      "summary": {
        "phases_run": ["recon", "plan"],
        "error_count": 2,
        "warning_count": 7,
        "key_events": ["Crawled 47 pages", "Found 156 endpoints", "2 JS bundles analyzed"]
      }
    }
    """
```

---

### Tool 19 — `write_report`
**Phase:** Report
**Purpose:** Generate the final report from all stored findings, evidence, and phase logs. Produces multiple output formats.

```python
async def write_report(
    run_id: str,
    formats: list[str] = ["markdown", "json", "csv"],
    include_raw_evidence: bool = True,
    executive_summary: bool = True
) -> dict:
    """
    Reads all findings, evidence, session data, endpoint inventory, and phase logs.
    Generates:
    - Executive summary (severity counts, risk score, top 3 critical findings)
    - Technical findings (one section per finding with: title, severity, CVSS, OWASP,
      description, reproduction steps, raw request/response, remediation)
    - Endpoint inventory appendix
    - Phase timeline (what happened when)
    - Error log (any tool failures, retries, skipped tests)

    Returns: {"reports_written": ["output/a77c_report.md", "output/a77c_findings.json"]}
    """
```

---

### Tool 20 — `error_retry`
**Phase:** All (meta-tool)
**Purpose:** When any tool fails (HTTP error, timeout, subprocess crash), this tool analyzes the error, determines whether to retry with modified parameters, skip, or escalate. Ensures the agent never gets stuck.

```python
async def error_retry(
    failed_tool: str,
    error: str,
    original_args: dict,
    run_id: str = ...
) -> dict:
    """
    Error → Strategy mapping:
    - 402 Payment Required (OpenRouter) → switch to Ollama fallback model
    - 429 Rate Limited → add exponential backoff, retry after delay
    - 503 Service Unavailable → retry with 3s delay, max 3 attempts
    - ConnectionError → check target is up via HEAD /, retry
    - TimeoutError → reduce concurrent_requests, retry
    - ParseError (bad JSON) → re-fetch with different Accept header
    - AuthError (401 on scan) → re-run auth_register_and_login, refresh sessions

    Returns: {"action": "retry", "modified_args": {...}} or {"action": "skip", "reason": "..."}
    """
```

---

## PART 4 — PHASE-BY-PHASE AGENT SYSTEM PROMPTS

These are the actual system prompts injected into the LLM at each phase. They must be detailed enough that the agent knows exactly what to do without further guidance.

---

### RECON PHASE SYSTEM PROMPT

```
You are the Recon Agent for CyberHunt AI, an autonomous web application security assessment system.

Your mission for this phase: achieve MAXIMUM coverage of the target's attack surface using every available tool.
Do NOT finish recon until you have:
  ✓ Crawled the target both unauthenticated AND with all registered sessions
  ✓ Analyzed all JavaScript bundles for hidden endpoints
  ✓ Attempted API schema discovery (OpenAPI, GraphQL)
  ✓ Run active directory brute-forcing
  ✓ Built the final endpoint inventory with risk scores
  ✓ Created at minimum 2 user accounts AND attempted admin access
  ✓ Analyzed all security headers

MANDATORY TOOL CALL SEQUENCE:
1. Call auth_register_and_login FIRST. You need sessions before crawling.
   - If registration fails: read the error via error_retry, adapt the payload, try again.
   - Keep trying until you have at least 2 valid user sessions.
   - Check for admin via known-credential attempts (admin@juice-sh.op/admin123 is standard for OWASP Juice Shop).

2. Call crawl_target with session_name=None (unauthenticated crawl).

3. Call crawl_target again for EACH session created in step 1.
   Authenticated crawls reveal orders, profiles, admin panels, and user-specific APIs.

4. Call analyze_js_bundles with ALL bundle URLs found in the crawls.
   JS bundles are the primary source of hidden endpoints in SPAs.

5. Call fetch_api_schema. Even if the schema path is not obvious, try all probe paths.
   A schema gives you 10x more endpoint coverage than crawling alone.

6. Call discover_endpoints with ai_extend=true.
   This uses wordlists PLUS AI-generated path suggestions based on what you've already found.

7. Call analyze_security_headers.

8. Call build_endpoint_inventory.
   This is your output. Every subsequent phase reads from this inventory.

CRITICAL RULES:
- If ANY tool returns an error, immediately call error_retry. Never give up without retrying.
- After each tool call, call get_phase_logs to check for errors or warnings in subprocesses.
- If recon finds 0 endpoints after crawl + JS analysis, the target may require CAPTCHA bypass
  or may be truly empty. Log this clearly but keep trying with different approaches.
- A complete recon should discover 50+ endpoints on any real web application.
  If you have fewer, you have not finished. Use more tools.
- Juice Shop specifically: the app is a React SPA. ALL routes are in the JS bundle.
  Do not consider recon complete until analyze_js_bundles has run.
- Store everything: every endpoint, every route pattern, every form field name.
  The test phase needs ALL of this.

WHAT "DONE" LOOKS LIKE:
- endpoint_inventory contains 50+ endpoints with risk scores
- sessions pool contains at minimum: user_a, user_b, (ideally admin)
- JS bundles analyzed
- Security header analysis complete
- Phase log shows no unresolved ERROR lines
```

---

### PLANNING PHASE SYSTEM PROMPT

```
You are the Test Planner Agent for CyberHunt AI.

Your mission: generate a prioritized, concrete test plan from the endpoint inventory.
Do NOT generate vague categories. Generate SPECIFIC test cases with SPECIFIC endpoints,
SPECIFIC payloads, and SPECIFIC tool calls.

You have access to:
- The complete endpoint inventory from recon (read from state)
- The RAG knowledge base of 242 bug reports (your training data)
- get_phase_logs to inspect what recon found

PLANNING METHODOLOGY:

Step 1 — Classify every endpoint by vulnerability class:
  IDOR candidates: endpoints with {id} or {uuid} in path AND return user-specific data
  Auth bypass candidates: endpoints accessible by non-admin that start with /admin, /internal, /config
  Race condition candidates: endpoints that decrement a counter, apply a coupon, transfer funds
  Mass assignment candidates: PUT/PATCH endpoints that update user objects
  SSRF candidates: endpoints with URL parameters, import/export/webhook functionality
  SQLi candidates: endpoints with string search parameters, name/search/q parameters
  Information disclosure: any endpoint returning version, config, debug, health data

Step 2 — For each IDOR candidate, create test cases:
  - Primary test: user_a access user_b's object (cross-user)
  - Secondary test: unauthenticated access to user_a's object
  - Tertiary test (if admin session): user role access to admin-owned objects

Step 3 — Assign confidence scores using RAG lookup:
  For each vulnerability class, call the RAG system with a query like:
  "IDOR on user profile endpoint in REST API, numeric ID in path"
  Use the matching historical reports to calibrate confidence.
  High confidence: 3+ similar confirmed bugs in knowledge base for this pattern
  Medium confidence: 1-2 similar bugs, or same class but different endpoint type
  Low confidence: no similar bugs, purely heuristic

Step 4 — Output the test plan as a prioritized list:
  Sort by: severity × confidence × exploitability
  Critical findings that are easy to test come first.

Step 5 — Identify data dependencies:
  Some tests require data created by prior tests.
  Example: to test IDOR on /api/Orders/{id}, you first need to create an order.
  Map these dependencies and note them so the test agent knows the order.

OUTPUT FORMAT (write to state as 'test_plan'):
[
  {
    "test_id": "T-001",
    "vulnerability_class": "IDOR",
    "subtype": "horizontal",
    "endpoint": "/api/Users/{id}",
    "method": "GET",
    "tool": "test_idor",
    "tool_args": {"endpoint": {...}, "num_swaps": 20},
    "prerequisites": [],
    "confidence": 0.92,
    "severity_if_confirmed": "high",
    "rag_references": ["HackerOne #847291", "Juice Shop Known Vuln #12"],
    "estimated_duration_seconds": 15
  },
  ...
]
```

---

### TESTING PHASE SYSTEM PROMPT

```
You are the Test Execution Agent for CyberHunt AI.

Your mission: execute EVERY test in the test plan and collect CONFIRMED evidence for each finding.
You must NEVER stop because a test returned ambiguous results.
Instead, follow the decision tree below for every result.

DECISION TREE (apply after every tool call):

IF tool returns error:
  → Call error_retry immediately
  → Apply the suggested action (retry/skip/modify)
  → Log what happened in state['errors']

IF test returns confirmed finding:
  → Call store_finding with ALL evidence: request, response, diffs, OOB logs
  → Continue to next test

IF test returns "likely" or "needs_more_data":
  → You are NOT done. Generate additional targeted tests.
  → For IDOR "likely": run with num_swaps=50, try more ID values, check more response fields
  → For SSRF "likely": run test_ssrf_oob with 5 fresh OOB domains on the same injection point
  → For auth "likely": test ALL 4 role combinations (unauth, expired, user, admin)
  → After additional tests: call verify_finding to reach confirmed/false_positive verdict
  → Store the result. NEVER leave a finding as "needs_more_data" in the final state.

IF test returns false_positive or "no_finding":
  → Log it as tested-and-cleared
  → Continue

BEFORE EVERY IDOR TEST:
  Verify you have actual IDs to test. Call crawl_target with each session
  if you don't have IDs for both user_a and user_b.
  For example, if testing /api/Baskets/{id}:
  1. Create a basket as user_a → record basket_id_a
  2. Create a basket as user_b → record basket_id_b
  3. Now run test_idor using user_a session with basket_id_b in the path

BEFORE EVERY SSRF TEST:
  Always use test_ssrf_oob, NOT string-matching on error pages.
  A 406 response that echoes the URL is NOT SSRF. Only OOB DNS/HTTP interaction is evidence.

CONCURRENCY RULES:
  Run tests in parallel where there are no dependencies (up to 5 concurrent).
  Never run tests with the same session concurrently if they modify state.

AUTHENTICATION FAILURES:
  If any test returns 401 on what should be an authenticated endpoint:
  → Your session may have expired. Call auth_register_and_login to refresh tokens.
  → Retry the test with the refreshed session.

WHEN YOU ARE DONE:
  The test phase is complete ONLY when:
  - Every test in the test plan has been executed
  - Every finding has status: confirmed OR false_positive (no "needs_more_data")
  - Phase log shows no unresolved errors that affect test coverage

  Call get_phase_logs(run_id, phase="test", level="ERROR") before declaring done.
  If there are errors, either retry or document why they couldn't be resolved.
```

---

### VERIFICATION PHASE SYSTEM PROMPT

```
You are the Verification Agent for CyberHunt AI.

Your mission: independently verify every finding marked "confirmed" or "likely" from the test phase.
Treat every finding with skepticism. Your job is to either:
  A) Prove it beyond doubt (add more evidence)
  B) Disprove it (mark false_positive with explanation)

For each finding, apply the appropriate verification protocol:

IDOR VERIFICATION PROTOCOL:
  1. Reproduce the exact exploit 3 times (not just once)
  2. Verify the data in the cross-session response is ACTUALLY user_b's private data
     (not generic data that all users share)
  3. Perform the vertical check: does the same endpoint also leak admin data to a regular user?
  4. Check if any logged-off/deleted user's data is also accessible
  If all 3 reproduction runs succeed AND the data is clearly user-specific → CONFIRMED

SSRF VERIFICATION PROTOCOL:
  1. If OOB interaction was already received → check source IP is the target server
  2. Re-run test_ssrf_oob with 3 fresh Interactsh domains on the same injection point
  3. Distinguish between: (a) DNS-only interaction (likely SSRF, server tried to resolve)
     vs (b) HTTP interaction (confirmed SSRF, server made the request)
     vs (c) no interaction (not SSRF, or OOB blocked by firewall)
  4. Try localhost bypass payloads: 127.0.0.1, [::1], 0x7f000001, 017700000001, 2130706433
  If OOB HTTP interaction received from target's IP → CONFIRMED CRITICAL SSRF

AUTH BYPASS VERIFICATION PROTOCOL:
  1. Test all 4 scenarios: unauth, expired JWT, user role, admin role
  2. Confirm the endpoint returns real data (not just 200 with empty body)
  3. Verify the same endpoint properly restricts access after login (else it's intentionally public)
  4. If the endpoint is documented in the API schema as public → note this, reduce severity

FALSE POSITIVE CRITERIA:
  - IDOR: if cross-session response body is identical (same data for all users), not IDOR
  - SSRF: if no OOB interaction after 3 attempts with fresh domains, mark as false_positive
  - Auth bypass: if the endpoint is genuinely public by design (documented), mark info/low

OUTPUT: Every finding must exit verification with status "confirmed" or "false_positive".
Update findings in state. Call verify_finding for each ambiguous finding.
```

---

### REPORT PHASE SYSTEM PROMPT

```
You are the Report Generation Agent for CyberHunt AI.

Your mission: produce a complete, accurate, professional security assessment report
that contains ALL findings with ALL evidence. No finding should be vague.
Every finding must have: proof, reproduction steps, remediation.

Call write_report with include_raw_evidence=true.

The report MUST contain these sections:

1. EXECUTIVE SUMMARY
   - Target URL and assessment date
   - Total findings by severity (Critical/High/Medium/Low/Info)
   - Overall risk score (calculate: sum of CVSS scores, weighted by severity)
   - Top 3 critical findings in one sentence each
   - Recommended immediate actions (max 5 bullet points)

2. METHODOLOGY
   - Tools used (list all 20 tools with brief descriptions)
   - Coverage statistics (endpoints discovered, tests run, sessions used)
   - Phases completed (recon/plan/test/verify) with timestamps and duration

3. TECHNICAL FINDINGS (one section per finding)
   For each confirmed finding:

   ### Finding [ID]: [Title]
   **Severity:** [Critical/High/Medium/Low] | **CVSS Score:** [X.X]
   **OWASP Category:** [Category] | **CWE:** [CWE-XXX]
   **Endpoint:** [METHOD /path]
   **Status:** Confirmed (N/N reproduction attempts succeeded)

   **Description:**
   [2-3 sentences explaining exactly what the vulnerability is and why it is dangerous]

   **Reproduction Steps:**
   1. Authenticate as user_a (email: ..., any password)
   2. Send the following request:
      ```http
      GET /api/Users/4 HTTP/1.1
      Host: target.com
      Authorization: Bearer [user_a_jwt]
      ```
   3. Observe response contains user_b's private data:
      ```json
      {"id": 4, "email": "user_b@test.com", "role": "customer", ...}
      ```
   4. Compare with expected behaviour (403 Forbidden)

   **Evidence:**
   - Baseline request/response (user accessing own data): [attached]
   - Attack request/response (user accessing other's data): [attached]
   - Diff showing: fields [email, username] differ, confirming cross-user data access
   - OOB interaction log (for SSRF): [attached if applicable]

   **Remediation:**
   [Specific, actionable fix. E.g.: "In the Users router, add ownership check:
   if request.user.id != requested_id and request.user.role != 'admin': return 403"]

   **References:**
   - OWASP WSTG-ATHZ-04 (IDOR Testing)
   - OWASP API1:2023 Broken Object Level Authorization
   - Similar historical finding: [from RAG knowledge base]

4. ENDPOINT INVENTORY APPENDIX
   Full table of all discovered endpoints with risk scores.

5. ERRORS AND LIMITATIONS
   Any tests that could not be completed, and why.
   Any endpoints that required capabilities not available (e.g. email confirmation).
   This section must be honest — do not omit limitations.

CRITICAL REPORT QUALITY RULES:
- NEVER write "endpoint returned 200 when 403 was expected" without proving WHY this is a bug.
  An endpoint that returns 200 because it's meant to be public is NOT a finding.
- EVERY IDOR finding must include proof that the data belongs to a different user.
- EVERY SSRF finding must include OOB interaction evidence, not just error page patterns.
- DO NOT include any finding marked false_positive in the main findings section.
  Put these in an appendix as "Investigated and Cleared".
- The report target_url must match the actual target. Read from state['target'].
```

---

## PART 5 — AUTHENTICATION AUTOMATION: DETAILED IMPLEMENTATION

This is the section that addresses "we cannot ask users to create accounts manually." The system must handle this end-to-end.

### Strategy Hierarchy

The auth engine tries strategies in this order, stopping at the first success:

```
Strategy 1: Direct API registration
  → POST /api/Users with JSON body (works for Juice Shop, most Node/Rails APIs)

Strategy 2: Form-based registration
  → Playwright: navigate to /register, fill form, submit
  → Handles CSRF tokens automatically

Strategy 3: OAuth/SSO registration
  → Not supported (requires external provider)
  → Log as limitation, continue with what sessions we have

Strategy 4: Known test credentials
  → Try: admin@juice-sh.op/admin123, test@test.com/test123,
         admin/admin, user@example.com/user123
```

### Playwright-Based Form Registration

```python
async def form_register(page: Page, target_url: str, user: dict) -> dict:
    """
    Automatically fills and submits a registration form.
    """
    # Navigate to registration page
    # Try common paths: /register, /signup, /auth/register, /account/create
    for path in ['/register', '/signup', '/#/register', '/auth/register']:
        try:
            await page.goto(target_url + path, wait_until='networkidle')
            # Check if we're on a registration form (look for password field)
            if await page.query_selector('input[type="password"]'):
                break
        except:
            continue

    # Find and fill email/username field
    email_field = await page.query_selector(
        'input[type="email"], input[name="email"], input[placeholder*="email" i]'
    )
    if email_field:
        await email_field.fill(user['email'])

    # Fill password fields
    for selector in ['input[type="password"]', 'input[name="password"]',
                     'input[name="passwordRepeat"]', 'input[name="confirm_password"]']:
        field = await page.query_selector(selector)
        if field:
            await field.fill(user['password'])

    # Handle security questions (Juice Shop specific)
    security_q = await page.query_selector('select[aria-label*="question" i]')
    if security_q:
        await security_q.select_option(index=0)  # pick first option
        answer_field = await page.query_selector('input[aria-label*="answer" i]')
        if answer_field:
            await answer_field.fill('automated_test_answer')

    # Handle CSRF token (extract from hidden input)
    csrf = await page.evaluate("""
        () => {
            const el = document.querySelector('input[name*="csrf"], input[name*="_token"]');
            return el ? el.value : null;
        }
    """)

    # Submit the form
    submit_btn = await page.query_selector(
        'button[type="submit"], input[type="submit"], button:text("Register"), button:text("Sign Up")'
    )
    if submit_btn:
        await submit_btn.click()
        await page.wait_for_load_state('networkidle')

    # Extract session from result
    cookies = await page.context.cookies()
    jwt_cookie = next((c['value'] for c in cookies if 'token' in c['name'].lower()), None)

    return {'success': jwt_cookie is not None, 'jwt': jwt_cookie}
```

### Admin Discovery Without Known Credentials

When no known admin credentials work, try:

1. **Check JWT payload**: Decode the base64-encoded JWT payload (middle section). Look for `role: "admin"` or `isAdmin: true`. Some JWTs contain privilege information that reveals roles.

2. **Privilege escalation test**: Use `test_mass_assignment` on the user profile update endpoint with `{"role": "admin"}`. If it works, user_a is now admin.

3. **SQL injection in login**: Try `admin'--` as email. If login succeeds, you have admin.

4. **Default admin credentials list**: Try 50 common credential combos. Rate-limit aware (slow down if getting 429).

---

## PART 6 — INTERACTSH INTEGRATION FOR OOB SSRF

### Setup

Install the Interactsh client on the machine running CyberHunt AI:

```bash
# Install via Go
go install -v github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest

# OR download the binary from GitHub releases
# https://github.com/projectdiscovery/interactsh/releases

# Test it works:
interactsh-client -server oast.me -json &
# Should start outputting: {"unique-id":"...","full-id":"...","interaction-type":"dns"}
```

### Python Wrapper

```python
# cyberAI/infra/oob.py

import asyncio
import json
import uuid
import subprocess
from dataclasses import dataclass
from typing import Optional

@dataclass
class OOBInteraction:
    unique_id: str
    interaction_type: str  # "dns", "http", "smtp"
    source_ip: str
    timestamp: str
    raw_request: Optional[str] = None

class InteractshManager:
    """
    Manages the Interactsh client subprocess and provides async polling.
    Singleton per run: one server connection, unlimited unique domains.
    """

    def __init__(self, server: str = "oast.me"):
        self.server = server
        self.proc: Optional[asyncio.subprocess.Process] = None
        self.interactions: list[OOBInteraction] = []
        self.domain_map: dict[str, str] = {}  # unique_id → correlation_tag
        self._reader_task: Optional[asyncio.Task] = None

    async def start(self) -> str:
        """Start Interactsh client, return the base domain"""
        self.proc = await asyncio.create_subprocess_exec(
            "interactsh-client",
            "-server", self.server,
            "-json",
            "-v",    # verbose: includes source IP
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        # Read the first line which contains our assigned domain
        first_line = await asyncio.wait_for(
            self.proc.stdout.readline(), timeout=10.0
        )
        data = json.loads(first_line.decode())
        self.base_domain = data.get("full-id", f"unknown.{self.server}")

        # Start background reader
        self._reader_task = asyncio.create_task(self._read_interactions())
        return self.base_domain

    async def _read_interactions(self):
        """Background task: continuously read interactions from stdout"""
        while True:
            try:
                line = await self.proc.stdout.readline()
                if not line:
                    break
                data = json.loads(line.decode())
                if "interaction-type" in data:
                    interaction = OOBInteraction(
                        unique_id=data.get("unique-id", ""),
                        interaction_type=data.get("interaction-type", ""),
                        source_ip=data.get("remote-address", "").split(":")[0],
                        timestamp=data.get("timestamp", ""),
                        raw_request=data.get("raw-request")
                    )
                    self.interactions.append(interaction)
            except (json.JSONDecodeError, asyncio.CancelledError):
                break

    def generate_url(self, correlation_tag: str) -> str:
        """Generate a unique OOB URL tied to a specific test"""
        unique_id = uuid.uuid4().hex[:16]
        self.domain_map[unique_id] = correlation_tag
        return f"http://{unique_id}.{self.base_domain}"

    async def wait_for_interaction(
        self, unique_id: str, timeout: float = 5.0
    ) -> list[OOBInteraction]:
        """Wait for interactions matching a specific unique_id"""
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            matching = [i for i in self.interactions if unique_id in i.unique_id]
            if matching:
                return matching
            await asyncio.sleep(0.2)
        return []

    async def stop(self):
        if self.proc:
            self.proc.terminate()
        if self._reader_task:
            self._reader_task.cancel()
```

---

## PART 7 — MULTI-SESSION IDOR TESTING: COMPLETE ALGORITHM

This is the exact algorithm that produces CONFIRMED IDOR findings, not heuristics.

```python
# cyberAI/testing/idor.py

import asyncio
import hashlib
import json
from typing import Optional

async def run_idor_test(
    endpoint: dict,
    sessions: dict,      # {name: {jwt, user_id, email, ...}}
    state: dict,
    oob: "InteractshManager"
) -> Optional[dict]:
    """
    Complete IDOR test for one endpoint.
    Returns a finding dict or None if no vulnerability found.
    """

    # Step 1: Determine if endpoint has an ID parameter
    id_params = extract_id_params(endpoint)   # finds {id}, {userId}, ?id=, etc.
    if not id_params:
        return None  # No ID params = no IDOR to test

    # Step 2: Ensure we have owned objects for each user
    object_ids = {}
    for user_name in ["user_a", "user_b"]:
        if user_name not in sessions:
            continue
        obj_id = await get_or_create_owned_object(
            endpoint, sessions[user_name], state
        )
        if obj_id:
            object_ids[user_name] = obj_id

    if len(object_ids) < 2:
        # Can't do cross-user test without 2 users' objects
        # Try with known IDs (1, 2, 3 are often user IDs)
        object_ids = await guess_object_ids(endpoint, sessions, state)
        if len(object_ids) < 2:
            return {"status": "needs_data", "reason": "Could not obtain IDs for 2 users"}

    # Step 3: Baseline — User A accesses own object
    client_a = make_client(sessions["user_a"]["jwt"])
    baseline_url = fill_id_param(endpoint["path"], object_ids["user_a"])
    baseline_resp = await client_a.request(endpoint["method"], baseline_url)

    if baseline_resp.status_code not in [200, 201]:
        return {"status": "skip", "reason": f"Baseline failed with {baseline_resp.status_code}"}

    baseline_body = parse_body(baseline_resp)
    baseline_hash = hashlib.sha256(
        json.dumps(baseline_body, sort_keys=True).encode()
    ).hexdigest()

    # Step 4: Attack — User A accesses User B's object
    attack_url = fill_id_param(endpoint["path"], object_ids["user_b"])
    attack_resp = await client_a.request(endpoint["method"], attack_url)
    attack_body = parse_body(attack_resp)
    attack_hash = hashlib.sha256(
        json.dumps(attack_body, sort_keys=True).encode()
    ).hexdigest()

    # Step 5: Decision
    if attack_resp.status_code in [401, 403, 404]:
        # Authorization properly enforced
        return None

    if attack_resp.status_code == 200:
        # Need to prove this is user_b's DATA, not public data
        user_b_email = sessions["user_b"]["email"]
        user_b_id = str(sessions["user_b"]["user_id"])

        attack_body_str = json.dumps(attack_body)

        evidence_of_user_b_data = any([
            user_b_email in attack_body_str,
            user_b_id == str(attack_body.get("id")),
            baseline_hash != attack_hash,   # different data returned
        ])

        if evidence_of_user_b_data:
            pii_fields = find_pii_fields(attack_body)

            return {
                "type": "IDOR",
                "subtype": "horizontal",
                "endpoint": endpoint["path"],
                "method": endpoint["method"],
                "severity": determine_severity(pii_fields, endpoint),
                "cvss": calculate_cvss_idor(pii_fields, authenticated=True),
                "owasp": "API1:2023 Broken Object Level Authorization",
                "cwe": "CWE-284",
                "evidence": {
                    "baseline": {
                        "url": baseline_url,
                        "request": format_request(endpoint, baseline_url, sessions["user_a"]["jwt"]),
                        "response_status": baseline_resp.status_code,
                        "response_body": censor_sensitive(baseline_body),
                        "hash": baseline_hash
                    },
                    "attack": {
                        "url": attack_url,
                        "request": format_request(endpoint, attack_url, sessions["user_a"]["jwt"]),
                        "response_status": attack_resp.status_code,
                        "response_body": censor_sensitive(attack_body),
                        "hash": attack_hash
                    },
                    "diff": diff_json(baseline_body, attack_body),
                    "user_b_identifiers_in_response": {
                        "email_present": user_b_email in attack_body_str,
                        "id_matches": user_b_id == str(attack_body.get("id")),
                        "body_differs": baseline_hash != attack_hash
                    },
                    "pii_fields_exposed": pii_fields,
                    "reproduction_count": 1
                },
                "status": "confirmed",
                "reproduction_runs_needed": 2   # verify_finding will run 2 more
            }
        else:
            # Status 200 but no user_b data = public endpoint by design
            return None

    return None  # Unexpected status codes = ambiguous, treat as not confirmed
```

---

## PART 8 — COMPLETE DEVELOPER IMPLEMENTATION PROMPT

Copy this prompt directly into your task management system for the AI developer. Include all files referenced.

---

```
TASK: Rebuild the CyberHunt AI agent layer from scratch as described in this spec.
This is a complete replacement of cyberAI/llm/agent/ and related modules.
The core pipeline phases (recon, plan, test, verify, report) can remain as subprocess
commands but the agent MUST be enhanced to deeply interact with their outputs.

BACKGROUND: Read the full architecture spec document before starting.
The key problems to solve are:
1. Agent must have 20 tools (not 3-5)
2. Agent must persist and read ALL logs from every phase
3. Agent must do real IDOR testing (multi-session cross-user swap), not heuristics
4. Agent must use Interactsh for OOB SSRF verification
5. Agent must auto-register user accounts
6. "needs_more_data" must be eliminated by the agent collecting more data

==============================================================
FILE STRUCTURE TO CREATE
==============================================================

cyberAI/
├── llm/
│   └── agent/
│       ├── loop.py              # REWRITE: the main agent loop
│       ├── chat_client.py       # KEEP but add Ollama fallback
│       ├── tools/
│       │   ├── __init__.py      # NEW: exports all 20 tools
│       │   ├── crawl.py         # NEW: crawl_target, analyze_js_bundles
│       │   ├── schema.py        # NEW: fetch_api_schema
│       │   ├── discover.py      # NEW: discover_endpoints, build_endpoint_inventory
│       │   ├── headers.py       # NEW: analyze_security_headers
│       │   ├── auth.py          # NEW: auth_register_and_login (Playwright-based)
│       │   ├── idor.py          # NEW: test_idor
│       │   ├── ssrf.py          # NEW: test_ssrf_oob
│       │   ├── authz.py         # NEW: test_auth_bypass, test_mass_assignment
│       │   ├── race.py          # NEW: test_race_condition
│       │   ├── sqli.py          # NEW: test_sqli_blind
│       │   ├── replay.py        # NEW: replay_request_with_variants, diff_responses
│       │   ├── verify.py        # NEW: verify_finding
│       │   ├── findings.py      # NEW: store_finding
│       │   ├── logs.py          # NEW: get_phase_logs
│       │   ├── report.py        # NEW: write_report
│       │   └── retry.py         # NEW: error_retry
│       ├── state.py             # NEW: RunState class (JSON + SQLite)
│       ├── prompts.py           # NEW: all phase system prompts
│       └── tool_definitions.py  # REWRITE: 20 tool definitions for OpenAI function calling
├── infra/
│   ├── __init__.py
│   ├── oob.py                   # NEW: InteractshManager
│   └── sessions.py              # NEW: SessionPool class
└── llm/
    └── llm_client.py            # KEEP: add write_to_chroma on confirmed findings

==============================================================
STEP 1: STATE MANAGEMENT (cyberAI/llm/agent/state.py)
==============================================================

Create a RunState class that wraps two storage backends:

class RunState:
    """
    Persistent state for a single assessment run.
    JSON file: run_state_{run_id}.json
    SQLite: logs_{run_id}.db
    """

    def __init__(self, run_id: str, target: str, output_dir: str = "./output"):
        self.run_id = run_id
        self.target = target
        self.state_file = f"{output_dir}/{run_id}/run_state.json"
        self.db_file = f"{output_dir}/{run_id}/logs.db"
        self._state = self._load_or_create()
        self._db = self._init_db()

    def _load_or_create(self) -> dict:
        """Load existing state or create fresh state"""
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "run_id": self.run_id,
            "target": self.target,        # NEVER "example.com" — use the real target
            "phase": "init",
            "sessions": {},
            "endpoints": [],
            "test_plan": [],
            "findings": [],
            "tested_endpoints": [],
            "errors": [],
            "phase_summaries": {}
        }

    def _init_db(self):
        """Initialize SQLite for log storage"""
        conn = sqlite3.connect(self.db_file)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                phase TEXT,
                level TEXT,
                module TEXT,
                message TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        return conn

    def save(self):
        """Write state to JSON file"""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self._state, f, indent=2)

    # Implement: get, set, add_finding, add_endpoint, add_session,
    #            add_error, get_findings, get_sessions, etc.
    # All mutations call self.save() after updating

==============================================================
STEP 2: LOG INGESTION (modify pipeline phase subprocesses)
==============================================================

After running each phase subprocess (recon, plan, test, verify, report),
capture BOTH stdout and stderr, and write EVERY line to SQLite:

async def _run_pipeline_phase(phase: str, cmd: list, run_id: str, state: RunState):
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Read stdout and stderr concurrently
    async def ingest_stream(stream, level):
        async for line in stream:
            decoded = line.decode().strip()
            if decoded:
                # Parse loguru format: "2026-03-25 16:49:04.395 | INFO | module:fn:42 - message"
                timestamp, log_level, module, message = parse_loguru_line(decoded)
                state.write_log(run_id, phase, log_level, module, message, timestamp)

    await asyncio.gather(
        ingest_stream(proc.stdout, "stdout"),
        ingest_stream(proc.stderr, "stderr")
    )

    return_code = await proc.wait()
    state.set(f"phase_summaries.{phase}.return_code", return_code)
    state.save()

    return return_code

The agent can then call get_phase_logs() to read and analyze these logs.

==============================================================
STEP 3: THE AGENT LOOP (cyberAI/llm/agent/loop.py)
==============================================================

The new loop is fundamentally different from the current one.
It is NOT just "run phase X subprocess, move to next phase."
It is a THINKING loop that inspects every phase output and adapts.

PSEUDO-CODE FOR NEW LOOP:

async def run_agent_loop(target: str, run_id: str, max_turns: int = 50):
    state = RunState(run_id, target)  # state['target'] = target (NEVER example.com)
    oob = InteractshManager()
    await oob.start()

    # Build initial messages with phase-appropriate system prompt
    messages = [
        {"role": "system", "content": get_phase_prompt("recon")},
        {"role": "user", "content": f"""
        Assessment run ID: {run_id}
        Target: {target}
        Current state: {json.dumps(state.summary(), indent=2)}

        Begin the assessment. Start with recon phase.
        Your first tool call MUST be auth_register_and_login.
        Do NOT call run_pipeline_phase for recon — use the individual recon tools directly.
        """}
    ]

    for turn in range(max_turns):
        # Call LLM with all 20 tool definitions
        resp = chat_completion(messages, tools=ALL_TOOL_DEFINITIONS)

        # Parse response
        if resp.finish_reason == "stop":
            final_message = resp.message.content
            if "__FINISH__" in final_message:
                break

        if resp.finish_reason == "tool_calls":
            # Execute each tool call
            tool_results = []
            for tool_call in resp.message.tool_calls:
                result = await execute_tool(
                    name=tool_call.function.name,
                    args=json.loads(tool_call.function.arguments),
                    state=state,
                    oob=oob
                )
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

                # Auto-detect phase transition and swap system prompt
                if tool_is_completing_phase(tool_call.function.name, result):
                    new_phase = determine_next_phase(state)
                    messages[0] = {"role": "system", "content": get_phase_prompt(new_phase)}

            messages.append(resp.message.to_dict())
            messages.extend(tool_results)

    await oob.stop()
    return state.get_final_summary()

IMPORTANT: The agent loop has 50 turns (not 24).
The current 24 turns is too few for a thorough assessment.
Recon alone may need 8-10 turns for a complex target.

==============================================================
STEP 4: TOOL DEFINITIONS (tool_definitions.py)
==============================================================

Define all 20 tools in OpenAI function calling format:

ALL_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "auth_register_and_login",
            "description": "Register new user accounts and log in to create the session pool. ALWAYS call this first before any crawling or testing. Handles CSRF tokens, form-based and API-based registration automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_url": {"type": "string", "description": "The base URL of the target application"},
                    "num_users": {"type": "integer", "default": 3, "description": "Number of test accounts to create"},
                    "also_try_admin": {"type": "boolean", "default": True}
                },
                "required": ["target_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crawl_target",
            "description": "Deep crawl the target using Playwright. Call once unauthenticated, then once for each session. Returns all discovered routes, API calls, forms, and JS bundles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_url": {"type": "string"},
                    "session_name": {"type": "string", "description": "Session from sessions pool, or null for unauthenticated"},
                    "max_pages": {"type": "integer", "default": 200},
                    "capture_network": {"type": "boolean", "default": True}
                },
                "required": ["target_url"]
            }
        }
    },
    # ... define all 20 tools following the same pattern
    # Each tool description MUST include:
    # - When to call it (trigger condition)
    # - What it returns
    # - What state it reads/writes
]

==============================================================
STEP 5: FIXING THE LLM CLIENT (chat_client.py)
==============================================================

Current problem: 402 error from OpenRouter → entire run fails.
Fix: add Ollama fallback.

def chat_completion(messages, tools=None, model=None):
    # Try primary (OpenRouter/DeepSeek)
    try:
        return _openrouter_completion(messages, tools, model or "deepseek/deepseek-r1")
    except HTTPStatusError as e:
        if e.response.status_code == 402:
            logger.warning("OpenRouter 402 — switching to Ollama fallback")
            return _ollama_completion(messages, tools, model="deepseek-r1:8b")
        elif e.response.status_code == 429:
            import time
            time.sleep(5)  # rate limit backoff
            return _openrouter_completion(messages, tools, model)
        raise

def _ollama_completion(messages, tools=None, model="deepseek-r1:8b"):
    """
    Ollama local API at http://localhost:11434/api/chat
    Note: Ollama does NOT support OpenAI function calling natively.
    Workaround: encode tool calls in system prompt as JSON-in-text,
    parse the LLM response with regex to extract tool calls.
    """
    # Simple implementation: inject tool definitions into system message
    if tools:
        tool_schema = json.dumps(tools, indent=2)
        messages[0]["content"] += f"\n\n## Available Tools\n{tool_schema}\n\nTo call a tool, output JSON in this exact format:\n<tool_call>{{\"name\": \"tool_name\", \"arguments\": {{...}}}}</tool_call>"

    resp = httpx.post(
        "http://localhost:11434/api/chat",
        json={"model": model, "messages": messages, "stream": False}
    )
    return parse_ollama_response(resp.json())

==============================================================
STEP 6: FIX THE target_url BUG
==============================================================

In cyberAI/main.py, wherever the report is generated or the run metadata is written,
replace any hardcoded "https://example.com" default with the actual target.

Search for: "example.com" in all files
For every occurrence that is a default value or placeholder, replace with:
  target_url = run_state.get("target")  # reads from state, which is set from CLI arg

Also in the report generator: verify the _meta block:
meta = {
    "target_url": state["target"],  # NOT a hardcoded default
    "run_id": state["run_id"],
    "assessment_date": datetime.now().isoformat(),
    "tool_version": "2.0.0"
}

==============================================================
STEP 7: ENHANCED PHASE SUBPROCESS OUTPUTS
==============================================================

The existing recon/plan/test/verify/report subprocesses need to write
richer machine-readable outputs that the agent can parse.

For RECON (cyberAI/recon/ modules):
- Write to output/{run_id}/recon/endpoints.json (every endpoint found)
- Write to output/{run_id}/recon/sessions.json (sessions created)
- Write to output/{run_id}/recon/js_analysis.json (from JS bundle parsing)
All of these must be JSON arrays/objects parseable by the agent tools.

For PLAN:
- Write to output/{run_id}/plan/test_plan.json
- Each test case must have: test_id, tool, tool_args, endpoint, method, priority

For TEST:
- Write to output/{run_id}/test/findings_raw.json
- Each finding must have: all evidence fields as defined in the finding schema
- NEVER write "needs_more_data" as final status — write "unverified" and let verify fix it

For VERIFY:
- Write to output/{run_id}/verify/findings_verified.json
- Status must be "confirmed" or "false_positive" for every finding

For REPORT:
- Write to output/{run_id}/report/report.md (full markdown report)
- Write to output/{run_id}/report/findings.json (machine-readable)
- Write to output/{run_id}/report/executive_summary.json

==============================================================
STEP 8: DEPENDENCY INSTALLATION
==============================================================

Add to requirements.txt (or pyproject.toml):

# New dependencies
playwright>=1.40.0          # browser automation for registration + crawling
interactsh-client           # OOB SSRF verification (also install Go binary)
sqlite3                     # already in stdlib, just import it
jsbeautifier>=1.14.9        # JavaScript beautification for JS analysis

# Run after installing:
playwright install chromium

# Install Interactsh binary:
go install github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest
# OR download from: https://github.com/projectdiscovery/interactsh/releases

==============================================================
STEP 9: COMPLETE FINDING SCHEMA
==============================================================

Every finding stored via store_finding must match this schema exactly:

FINDING_SCHEMA = {
    "id": "F-001",                    # auto-generated, sequential
    "run_id": "a77cb3b5",
    "target": "https://demo.owasp-juice.shop",  # ACTUAL TARGET, not example.com
    "type": "IDOR",                   # IDOR|SSRF|AUTH_BYPASS|MASS_ASSIGN|RACE_CONDITION|SQLI|INFO_DISC|CORS|etc.
    "subtype": "horizontal",          # horizontal|vertical|blind|stored|reflected
    "title": "Horizontal IDOR on /api/Users/{id}",
    "severity": "high",               # critical|high|medium|low|info
    "cvss_score": 8.1,
    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N",
    "owasp_category": "API1:2023 Broken Object Level Authorization",
    "cwe_id": "CWE-284",
    "endpoint": "/api/Users/{id}",
    "method": "GET",
    "status": "confirmed",            # confirmed|likely|false_positive|unverified
    "reproduction_count": 3,          # number of times successfully reproduced
    "evidence": {
        "baseline_request": "GET /api/Users/3 HTTP/1.1\nHost: ...\nAuthorization: Bearer ...",
        "baseline_response": {"status": 200, "body": {...}},
        "attack_request": "GET /api/Users/4 HTTP/1.1\nHost: ...\nAuthorization: Bearer ...",
        "attack_response": {"status": 200, "body": {...}},
        "diff": {"changed_fields": ["email", "username", "id"], "verdict": "different_user_data"},
        "pii_exposed": ["email", "username"],
        "oob_interactions": []    # populated for SSRF findings
    },
    "reproduction_steps": [
        "Register as user_a (POST /api/Users with any email/password)",
        "Log in as user_a (POST /rest/user/login)",
        "Note user_a's ID from JWT payload",
        "Send: GET /api/Users/4 with user_a's JWT",
        "Observe: response contains user_b's email and profile data"
    ],
    "remediation": "Add ownership check in the GET /api/Users/:id handler: if (req.user.id !== req.params.id && req.user.role !== 'admin') return res.status(403).json({error: 'Forbidden'});",
    "rag_references": ["HackerOne #847291 (Shopify IDOR)", "OWASP WSTG-ATHZ-04"],
    "discovered_at": "2026-03-25T17:01:22Z",
    "verified_at": "2026-03-25T17:13:55Z"
}

==============================================================
STEP 10: TESTING YOUR IMPLEMENTATION
==============================================================

Test against OWASP Juice Shop (http://localhost:3000 if running locally).
Known confirmed vulnerabilities to use as ground truth:

1. IDOR: GET /api/Users/1 as any user → returns admin profile (CVE-like, intentional)
2. Auth bypass: GET /api/Deliveries with no auth → 200 OK with delivery data
3. Admin access: GET /rest/admin/application-configuration → full config without auth
4. JWT forgery: POST /rest/user/login with email "' OR 1=1--" → admin login
5. Mass assignment: PUT /api/Users/{id} with {"role":"admin"} in body

Your implementation passes if:
- All 5 above appear in findings.json with status "confirmed"
- No false positives (e.g., intentionally public endpoints NOT marked as critical bugs)
- Report target_url = "https://demo.owasp-juice.shop" (not example.com)
- Coverage: 50+ endpoints in endpoint inventory
- Sessions: at minimum 2 user sessions + admin session
- No "needs_more_data" in final findings

EXPECTED RUNTIME: 15-25 minutes for a full Juice Shop assessment.
If it runs in < 5 minutes, it's not thorough enough.
If it runs > 45 minutes, add parallelism.

==============================================================
KNOWN JUICE SHOP QUIRKS
==============================================================

1. Registration: POST /api/Users with body:
   {"email": "test@example.com", "password": "Test1234!", "passwordRepeat": "Test1234!",
    "securityQuestion": {"id": 1, "question": "...", "createdAt": "...", "updatedAt": "..."},
    "securityAnswer": "automated"}
   Get security question list first: GET /api/SecurityQuestions

2. Login: POST /rest/user/login with {"email": "...", "password": "..."}
   JWT is in response body: {"authentication": {"token": "eyJ...", "umail": "..."}}
   Use as: Authorization: Bearer eyJ...

3. Admin credentials: admin@juice-sh.op / admin123 (this is public knowledge for a training app)

4. Juice Shop runs on port 3000 locally or use the demo at demo.owasp-juice.shop
   The demo may be rate-limited; local is better for testing.

5. All /api/ endpoints require: Content-Type: application/json

==============================================================
ANTI-PATTERNS TO AVOID
==============================================================

❌ DO NOT: Mark any endpoint returning 200 as a finding without cross-session proof
❌ DO NOT: Use error page string matching as SSRF evidence
❌ DO NOT: Leave any finding as "needs_more_data" in the final report
❌ DO NOT: Hardcode example.com anywhere as a target placeholder
❌ DO NOT: Stop the agent loop when it hits the first error (use error_retry)
❌ DO NOT: Limit the agent to 24 turns (it needs 50 for thorough testing)
❌ DO NOT: Run only unauthenticated tests (auth bypass != IDOR)
❌ DO NOT: Report a 406 from /redirect as SSRF (it's the opposite — blocked redirect)

✅ DO: Always test with 2+ user sessions for IDOR
✅ DO: Always use OOB domain (Interactsh) for SSRF verification
✅ DO: Ingest and analyze ALL subprocess logs after each phase
✅ DO: Retry on 402/429/503 errors automatically
✅ DO: Auto-register accounts before testing
✅ DO: Reproduce every finding 3x before marking confirmed
✅ DO: Produce separate output for false positives (not mixed with real findings)
```

---

## PART 9 — EXPECTED OUTPUT QUALITY

After implementing this architecture, a run against OWASP Juice Shop should produce:

### Endpoint Inventory
- 100+ endpoints (Juice Shop has ~150 API routes)
- All with risk scores, parameter types, authentication requirements

### Findings
- 8-15 confirmed findings including:
  - IDOR on `/api/Users/{id}` (horizontal, any user can read any user's profile)
  - Admin panel auth bypass (`/rest/admin/application-configuration`, `/rest/admin/application-version`)
  - JWT forgery via SQL injection in login
  - Missing authorization on delivery/order endpoints
  - Mass assignment in profile update
  - Information disclosure (server version, application config)
  - CORS issues if present

### Report Quality
- Every finding has exact reproduction steps that any developer can follow
- Every finding has actual request/response evidence
- No "needs_more_data" findings
- Correct `target_url` throughout
- Executive summary with CVSS-weighted risk score
- Clear remediation per finding

### Session Coverage
- 3 user accounts registered automatically
- Admin session obtained (via known credentials or exploitation)
- All tests run across all applicable session/role combinations

---

## APPENDIX — QUICK REFERENCE: VULNERABILITY CLASS → TOOL MAPPING

| Vulnerability | Primary Tool | Verification Tool | Evidence Type |
|--------------|-------------|------------------|---------------|
| IDOR/BOLA | `test_idor` | `verify_finding` | Cross-session response diff |
| BFLA | `test_auth_bypass` | `verify_finding` | Role matrix 4-way test |
| SSRF | `test_ssrf_oob` | `verify_finding` | OOB DNS/HTTP interaction |
| Mass Assignment | `test_mass_assignment` | `replay_request_with_variants` | Before/after state diff |
| Race Condition | `test_race_condition` | `test_race_condition` x3 | Multiple 200s on 1-use resource |
| SQL Injection | `test_sqli_blind` | `replay_request_with_variants` | Time delta / boolean diff |
| Auth Bypass | `test_auth_bypass` | `verify_finding` | Unauth/wrong-role 200 response |
| Info Disclosure | `analyze_security_headers` + `crawl_target` | `diff_responses` | Sensitive data in public response |
| CORS | `analyze_security_headers` | `replay_request_with_variants` | Header analysis |
