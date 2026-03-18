## Cyber Hunt AI

An end-to-end, automated web application security assessment framework.

It is designed to:
- **Discover** an app’s attack surface (routes, APIs, states, async flows)
- **Plan** targeted security tests based on that intelligence
- **Execute** those tests in parallel
- **Verify** and de-duplicate findings
- **Report** in multiple formats for engineers and stakeholders

The system is built so it runs completely **without** an LLM; a RAG/LLM layer can be plugged in later to enrich hypotheses, summaries, and remediation advice.

---

## High-Level Architecture

The pipeline has five main phases, orchestrated by `cyberAI/main.py`:

1. **Reconnaissance (`recon`)**  
   - Crawl the target using a headless browser (Playwright)  
   - Capture DOM, screenshots, actions, and basic page state  
   - Intercept network traffic to build an endpoint inventory  
   - Discover sensitive surfaces, GraphQL, WebSockets, async flows  
   - Build object models, permission hints, workflows, and security control analysis  
   - Aggregate everything into a single `master_intel.json`

2. **Planning (`plan`)**  
   - Read `master_intel.json` and other recon outputs  
   - Generate a set of structured `TestPlan` objects per category (auth, authz, business_logic, etc.)  
   - Write `planning/test_plans.json` and category-specific splits

3. **Testing (`test`)**  
   - Load `TestPlan`s and dispatch them to category-specific testers  
   - Use an async HTTP client and (when needed) a browser to execute real requests  
   - Record responses and evidence as `Finding` objects in `outputs/testing/findings`

4. **Verification (`verify`)**  
   - De-duplicate findings  
   - Run additional checks (false-positive reduction, state validation, cross-role checks, exploit-chain reasoning)  
   - Tag findings with verification status and reliability scores  
   - Persist confirmed/likely findings in `outputs/verification`

5. **Reporting (`report`)**  
   - Load verified findings and severity breakdowns  
   - Produce:
     - Executive summary (MD + TXT)
     - Engineering handoff (MD)
     - Per-finding markdown pages
     - JSON exports and CSV for analysis
     - Remediation queue TXT

Each phase can be run independently or via a single `full` command.

---

## Project Layout

At the root:

- `cyberAI/` – main Python package  
  - `main.py` – CLI orchestrator for all phases  
  - `config.py` – configuration loading (`.env` + environment)  
  - `models.py` – all core Pydantic v2 data models (Routes, Endpoints, Findings, TestPlan, etc.)  
  - `recon/` – steps 1–16 (discovery and intelligence)
  - `planning/` – test planning logic
  - `testing/` – test runner and category-specific testers
  - `verification/` – verification and scoring pipeline
  - `reporting/` – report generation
  - `utils/` – browser/http/proxy/attack-graph helpers
  - `llm/` – stubs for future RAG/LLM integration
- `outputs/` – default output directory (recon, planning, testing, verification, reports, logs)
- `requirements.txt` – Python dependencies

> Note: There is also a `cyberAI/outputs` directory which mirrors the structure but the canonical outputs used by the CLI live under `outputs/` at the repository root (managed by `Config.output_dir`).

---

## Data Model Overview

Defined in `cyberAI/models.py`:

- **Core enums**
  - `Severity` – `critical`, `high`, `medium`, `low`, `info`
  - `HttpMethod` – standard HTTP verbs
  - `TestCategory` – `auth`, `authz`, `business_logic`, `input`, `mass_assignment`, `race`, `multi_session`, `stored_payload`, `file_upload`, `graphql`, `websocket`, `async`, `search`, `export_import`, `billing`, `notification`, `config`
  - `ImpactType` – confidentiality, integrity, availability, financial, compliance

- **Recon models**
  - `Route` – a discovered page/route, with:
    - `slug`, `url`, HTTP method
    - `screenshot_path`, `dom_path`
    - `actions` (clickable elements, forms)
    - `role_context`, `state_context`, `page_title`
    - `linked_requests` (endpoint IDs), `raw_state`, `modals_found`
  - `Endpoint` – a normalized API endpoint:
    - HTTP method, URL, path pattern
    - `classification` (read/create/update/delete/admin/auth/billing/…)
    - `sensitivity_label` (high/medium/low/public)
    - request/response schema (`FieldSchema` list)
    - auth context, tenant IDs, rate-limit info, error fingerprints
  - `AsyncFlow`, `ObjectModel`, `WorkflowGraph`, `PermissionMatrix`, `SecurityControlsReport`, `SensitiveSurface`, `GraphQLIntel`, `WebSocketIntel`, etc.
  - `MasterIntelligence` – aggregates all recon intelligence into one object written as `recon/intelligence/master_intel.json`.

- **Planning and testing models**
  - `TestPrecondition` – basic test precondition (description + setup hints)
  - `TestPlan` – a concrete test case:
    - category, name, description
    - target endpoint/object, role, required state
    - `preconditions`, `expected_safe_behavior`, `attack_vector`
    - payloads, confidence score, priority, estimated requests, flags like `is_destructive`
  - `ReproductionStep` – a single step in reproducing a finding
  - `Finding` – result of a test:
    - id, title, severity, category, affected asset
    - affected roles/states, preconditions
    - reproduction steps, request/response proof
    - root cause, impact types, reliability score, status, verification metadata

- **Verification and reporting models**
  - Verified finding wrappers, impact and remediation structures (used inside verification and reporting modules).

---

## Configuration (`config.py`)

`Config` is a dataclass-based singleton (`Config.get()` / `Config.load()`):

- **Target and execution**
  - `target_url` – base URL for recon and HTTP tests
  - `max_workers`, `request_delay_ms`
  - `ignore_robots`, `dry_run`
- **Network**
  - `proxy_enabled`, `proxy_source_url`, `proxy_cache_ttl_minutes`
- **Browser**
  - `headless`, `browser_timeout_ms`, `user_agent_rotation`
- **LLM**
  - `llm_enabled` – off by default
- **Role accounts**
  - `role_accounts` – list of `RoleAccount {role, username, password, mfa_secret}`
- **Paths**
  - `output_dir` – defaults to `outputs`, plus helpers like `get_output_path("recon", "intelligence", "routes.json")`

`.env` (see `.env.example`) and environment variables feed into `Config.load`.

---

## Utilities (`utils/`)

- `browser.py`
  - Manages a **Playwright** browser pool:
    - `get_browser_pool()`, `initialize()`, `close()`
    - `get_browser_context(role=...)`, optional storage state, proxy
  - Convenience helpers:
    - `take_screenshot(page, name)` → `outputs/recon/screenshots/...`
    - `dump_dom(page, name)` → `outputs/recon/dom_snapshots/...`
    - `get_page_actions(page)` – extracts clickable elements, forms, etc.
    - `get_local_storage(page)`, `get_session_storage(page)`

- `http_client.py`
  - `AsyncHTTPClient` built on **httpx.AsyncClient**:
    - Base URL from `Config.target_url`
    - Optional proxy rotation via `proxy_manager`
    - UA rotation via `fake_useragent`
    - `get/post/request` methods that:
      - Apply rate limiting
      - Send requests
      - Wrap responses into `RequestRecord` instances when `record=True`
    - Central place where tests make HTTP calls.

- `proxy_manager.py`
  - Fetches and rotates proxies from a configured source.

- `helpers.py`
  - Core helpers:
    - `generate_run_id()`, `get_timestamp()`, `safe_filename()`
    - `atomic_write_json()`, `atomic_write_text()`
    - `load_json()`, `add_meta_to_output()` (wraps data with a `_meta` block containing target, phase, run_id, version, timestamp)
    - JWT decoding, ID extraction, endpoint classification primitives.

- `attack_graph.py`
  - Utility to build and analyze attack graphs used in advanced testers and verification (e.g. finding multi-step exploit chains).

---

## Reconnaissance Pipeline (`recon/`)

The recon pipeline has 16 conceptual steps; the main orchestrator in `main.py` wires them in a practical sequence:

1. **Core discovery (`core_discovery.py`)**
   - BFS crawl using Playwright:
     - Starts from `target_url`
     - Keeps track of `Route` objects and visited URLs
     - Captures screenshots, DOM snapshots, available actions, basic page “state”
   - Can attach a `NetworkIntelligence` instance to the browser context to capture network requests during the crawl.
   - Writes `recon/intelligence/routes.json`.

2. **Network intelligence (`network_intelligence.py`)**
   - Intercepts requests and responses:
     - Builds `RequestRecord`s and deduplicated `Endpoint`s
     - Infers sensitivity, schema (`FieldSchema`), JWT details, tenant IDs, rate limits, error fingerprints
   - Writes:
     - `recon/requests/all_requests.json`
     - `recon/intelligence/endpoints.json`

3. **Frontend parser (`frontend_parser.py`)**
   - Parses HTML and downloaded JS bundles:
     - Extracts additional routes (e.g. client-side routers)
     - Locates API endpoints embedded in JS
     - Finds GraphQL endpoints, fragments, operations
   - Writes `recon/intelligence/frontend_analysis.json` and `hidden_routes.json`.

4. **WP/Woo discovery (`wp_discovery.py`)**
   - Best-effort enrichment for WordPress / WooCommerce-style targets:
     - Fetches and parses `robots.txt`
     - Fetches and parses `sitemap.xml` / `sitemap_index.xml` to extract canonical URLs (up to a safe cap)
     - Fetches `/wp-json/` and enumerates public routes when available
   - Writes:
     - `recon/intelligence/wp_discovery.json`
     - `recon/intelligence/wp_routes.json` (extra crawl targets; aggregated into `hidden_routes` in `master_intel.json`)
   - **Purpose:** maximize coverage on CMS targets without destructive actions or anti-bot evasion.

5. **Role discovery (`role_discovery.py`)**
   - Optional, if `ROLE_ACCOUNTS` configured:
     - Logs in as different roles (guest/user/admin, etc.)
     - Crawls per-role variants, collecting routes and endpoints
     - Compares access fields to derive `RoleDiff`s and permission hints
   - Writes `recon/intelligence/role_diff.json` and per-role route/endpoint files.

6. **Account state discovery (`account_state.py`)**
   - Explores application “states” (trial, paid, active, etc.) per role using repeated crawls.
   - Writes `recon/intelligence/state_diff.json`.

7. **Sensitive surfaces (`sensitive_surfaces.py`)**
   - Probes common sensitive paths:
     - `/admin`, `/backup`, `/debug`, `/actuator`, etc.
   - Classifies responses; flags potential exposures.
   - Writes `recon/intelligence/sensitive_surfaces.json`.

7. **GraphQL discovery (`graphql_discovery.py`)**
   - Detects GraphQL endpoints:
     - From requests, HTML, and JS bundles
   - Probes schema (introspection) where possible.
   - Writes `recon/intelligence/graphql_intel.json`.

8. **WebSocket discovery (`websocket_discovery.py`)**
   - Identifies WebSocket endpoints from network captures.
   - Writes `recon/intelligence/websocket_intel.json`.

9. **Async flow discovery (`async_flow_discovery.py`)**
   - Analyzes async patterns:
     - Export jobs, queues, status / download URLs
   - Writes `recon/intelligence/async_flows.json`.

10. **Object model (`object_model.py`)**
    - Builds application object models from endpoints and responses:
      - Entities, relationships, ownership fields, security-critical attributes.
    - Writes `recon/intelligence/object_graph.json`.

11. **Permission inference (`permission_inference.py`)**
    - Uses `RoleDiff`s, endpoints, and object models:
      - Infers a coarse permission matrix across roles, actions, and objects.
    - Writes `recon/intelligence/permission_matrix.json` (+ CSV).

12. **Workflow mapper (`workflow_mapper.py`)**
    - Maps multi-step workflows (state transitions, actions).
    - Writes `recon/intelligence/workflows.json` and optionally DOT graphs.

13. **Input schema analysis (`input_schema.py`)**
    - Inspects request/response bodies to infer input schemas and hidden fields.
    - Writes `recon/intelligence/input_schemas.json`.

14. **Security controls analysis (`security_controls.py`)**
    - Analyzes security headers and cookie attributes from responses:
      - CSP, HSTS, X-Frame-Options, SameSite, etc.
    - Attempts to detect token storage mechanisms (localStorage/sessionStorage/cookies) from JS and responses.
    - Writes `recon/intelligence/security_controls.json`.

15. **Comparison engine (`comparison_engine.py`)**
    - When roles and endpoints are available:
      - Compares responses across roles/states to detect inconsistent access.
    - Writes `recon/intelligence/comparison_diffs.json`.

16. **Intelligence aggregation (`intelligence_outputs.py`)**
    - `IntelligenceAggregator.aggregate_from_files()` reads all of the above and populates `MasterIntelligence`.
    - `save_all_outputs()` writes:
      - `master_intel.json`
      - `route_map.json`
      - `endpoint_inventory.json`
      - CSV and summary artifacts for debugging.

The `recon` CLI command (`python -m cyberAI.main recon --target https://target`) orchestrates these steps and produces the full intelligence set.

---

## Planning Phase (`planning/`)

`planning/test_planner.py`:

- Loads `master_intel.json` and other recon outputs via `Config.get_output_path`.
- Uses `TestPlanner` to generate `TestPlan`s for multiple categories:
  - Auth (login flows, session rotation, stale session reuse, etc.)
  - Authz (IDORs across `Endpoint`s and object models)
  - Business logic (workflows, async flows, exports/imports, billing, notifications)
  - Other categories (input, mass assignment, race, file upload, etc.) as heuristics allow.
- Writes:
  - `planning/test_plans.json` – flat list of `TestPlan`s
  - `planning/test_plans_by_category/*.json` – per-category splits

The `plan` CLI command (`python -m cyberAI.main plan`) runs this phase.

---

## Testing Phase (`testing/`)

- **Test runner (`testing/runner.py`)**
  - `TestRunner` orchestrates:
    - Loading `TestPlan`s from `planning/test_plans.json`
    - Registering category-specific testers (auth, authz, business_logic, etc.)
    - Running tests in parallel with a configurable concurrency limit
    - Tracking stats: tests run, findings discovered, per-category breakdown
    - Persisting findings to:
      - Per-finding JSON files (`testing/findings/finding_*.json`)
      - Aggregated `testing/findings/all_findings.json` with severity counts
      - Runner state (`testing/runner_state.json`)

  - `run_tests(categories, max_workers, run_id)`:
    - Optionally filter by categories (e.g. `["auth", "authz"]`)
    - Register testers
    - Call `run_all` to execute all plans in those categories
    - Print a summary table.

- **Testers (`testing/*.py`)**
  - `auth_testing.AuthTester`
    - Login flows, session rotation, stale session reuse, password reset, etc.
  - `authorization_testing.AuthorizationTester`
    - Horizontal/vertical IDORs against discovered endpoints and objects.
  - `business_logic.BusinessLogicTester`
    - Multi-step workflows and state transitions with business impact.
  - `input_mutation.InputMutationTester`
  - `mass_assignment.MassAssignmentTester`
  - `race_conditions.RaceConditionTester`
  - `multi_session.MultiSessionTester`
  - `stored_payload.StoredPayloadTester`
  - `file_upload.FileUploadTester`
  - `graphql_testing.GraphQLTester`
  - `websocket_testing.WebSocketTester`
  - `async_testing.AsyncTester`
  - `search_filter.SearchFilterTester`
  - `export_import.ExportImportTester`
  - `billing_testing.BillingTester`
  - `notification_testing.NotificationTester`
  - `config_testing.ConfigTester`

Each tester:
- Receives a `TestPlan`
- Uses `AsyncHTTPClient` and/or the browser pool
- Produces `Finding` objects via the runner’s `add_finding` or return values.

The `test` CLI command (`python -m cyberAI.main test --categories auth,authz`) runs this phase.

### Accuracy guardrails (important)

To reduce false positives and improve evidence quality:
- **Authz / IDOR tests** disable redirects for probes and require **JSON API responses** before emitting HIGH-severity findings.
- **Requests are evidence-first**: findings can carry `request_proof` and a truncated `response_proof` preview for rapid human validation.
- The HTTP recording layer stores redirect chains, content-type, and response hashes/previews to make verification and triage easier.

---

## Verification Phase (`verification/`)

Located under `verification/`:

- `pipeline.py`
  - Loads testing findings
  - `deduplicate()` – merges duplicates
  - `run_verification()`:
    - Applies:
      - `false_positive.py`
      - `state_validation.py`
      - `cross_role_validation.py`
      - `race_confirmation.py`
      - `stored_confirmation.py`
      - `control_bypass.py`
      - `impact_proof.py`
      - `boundary_verification.py`
      - `exploit_chain.py`
    - Produces a final set of verified findings with:
      - statuses (`confirmed`, `likely`, `needs_more_data`, `false_positive`)
      - reliability scores
  - Writes outputs in `outputs/verification`.

The `verify` CLI command (`python -m cyberAI.main verify`) runs this phase.

---

## Reporting Phase (`reporting/`)

Key files:

- `reporter.py`
  - `run_report_generation(run_id)`:
    - Loads verified findings and severity breakdowns
    - Uses helpers:
      - `executive_summary.py`
      - `engineering_handoff.py`
      - `impact_analysis.py`
      - `priority_ranking.py`
      - `business_context.py`
      - `pattern_analysis.py`
      - `remediation.py`
      - `learning_loop.py`
      - `evidence_pack.py`
    - Produces:
      - `reports/markdown/executive_summary.md`
      - `reports/markdown/engineering_handoff.md`
      - Per-finding markdown summaries in `reports/markdown/findings/`
      - `reports/json/all_findings.json`
      - `reports/json/severity_breakdown.json`
      - `reports/csv/findings.csv`
      - `reports/txt/executive_summary.txt`
      - `reports/txt/remediation_queue.txt`

The `report` CLI command (`python -m cyberAI.main report`) runs this phase.

---

## LLM / RAG Integration (`llm/`)

Current status: **stubs only**.

- `llm/llm_client.py` defines but does not implement:
  - `call_llm(prompt, context=[])`
  - `summarize_finding(finding_dict)`
  - `generate_attack_hypothesis(intel_dict)`
  - `suggest_test_cases(object_model, permission_matrix)`
  - `analyze_code_for_vulnerabilities(code, language)`
  - `generate_remediation_advice(finding_dict)`
  - `explain_impact(finding_dict, business_context="")`

By design:
- The system works fully without any LLM.
- When you are ready to integrate a RAG/LLM backend:
  1. Replace stub bodies with calls into your client.
  2. Set `LLM_ENABLED=true` in `.env`.
  3. Wire LLM calls into planning/reporting where appropriate (e.g. use `summarize_finding` when generating markdown).

---

## Orchestrator (`main.py`) and CLI

`main.py` exposes a single entrypoint:

```bash
python -m cyberAI.main <command> [options]
```

Commands:

- `recon` – run reconnaissance
  - `--target / -t` (required): base URL
  - `--role`: roles (not yet heavily used)
  - `--proxy`: enable proxy rotation
  - `--run-id`: optional run id

- `plan` – generate test plans from recon outputs
  - `--recon-dir`: optional location of recon outputs
  - `--run-id`

- `test` – execute tests
  - `--target / -t`: explicitly set target (otherwise taken from last recon’s `_meta.target_url`)
  - `--plan-dir`: optional planning output directory
  - `--categories / -c`: comma-separated categories (e.g. `auth,authz`)
  - `--workers / -w`: max concurrent workers (defaults to 4 or `Config.max_workers`)
  - `--run-id`

- `verify` – verify and deduplicate findings
  - `--findings-dir`
  - `--run-id`

- `report` – generate reports
  - `--verified-dir`
  - `--run-id`

- `full` – run all phases sequentially
  - `--target / -t` (required)
  - `--proxy`
  - `--workers`
  - `--categories`
  - `--dry-run`
  - `--ignore-robots`

All commands also accept `--env` at the top level to point to a specific `.env` file.

---

## Typical End-to-End Run

From the repository root:

```bash
# 1) Recon
python3 -m cyberAI.main recon --target https://example.com

# 2) Plan
python3 -m cyberAI.main plan

# 3) Test (auth + authz)
python3 -m cyberAI.main test --categories auth,authz

# 4) Verify
python3 -m cyberAI.main verify

# 5) Report
python3 -m cyberAI.main report
```

Or in one shot:

```bash
python3 -m cyberAI.main full --target https://example.com
```

Outputs will be written under `outputs/` (or the directory configured via `OUTPUT_DIR`).

---

## Extending the System

- **Add a new recon step**
  - Create a module under `recon/`
  - Use `Config.get_output_path("recon", "intelligence", "...")` for outputs
  - Wire it into `run_recon` in `main.py`, ensuring it reads/writes from/to the same output dir as `IntelligenceAggregator`.

- **Add a new test category**
  - Add a new enum value in `TestCategory`
  - Implement a tester class in `testing/` with `run_test(plan: TestPlan) -> list[Finding]` methods
  - Register the tester in `_register_all_testers` in `testing/runner.py`
  - Update `TestPlanner` to emit `TestPlan`s for the new category.

- **Integrate LLM/RAG**
  - Replace implementations in `llm/llm_client.py`
  - Call LLM helpers from planning/reporting where you want richer summaries, hypotheses, or remediation advice.

---

## Security Note

This tool is intended **only** for authorized security testing and research.  
Always obtain explicit permission from the application owner before running any recon, testing, or exploitation activities. The authors are not responsible for misuse.

