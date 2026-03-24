## Cyber Hunt AI

An end-to-end, automated web application security assessment framework.

It is designed to:
- **Discover** an app’s attack surface (routes, APIs, states, async flows)
- **Plan** targeted security tests based on that intelligence
- **Execute** those tests in parallel
- **Verify** and de-duplicate findings
- **Report** in multiple formats for engineers and stakeholders

The system is built so it runs completely **without** an LLM; a RAG/LLM layer can be plugged in later to enrich hypotheses, summaries, and remediation advice.

**Full pipeline & output inventory:** see [`docs/PIPELINE_AND_OUTPUTS.md`](docs/PIPELINE_AND_OUTPUTS.md) for every phase, artifact path, and data-flow diagram (intended for UI/integrations and second-pass tooling).

---

## High-Level Architecture

The assessment is orchestrated by `cyberAI/main.py` in **five phases**. Each phase reads/writes under `outputs/` (or `OUTPUT_DIR` from `.env`). JSON outputs include `_meta` (`target_url`, `phase`, `run_id`, etc.) where implemented.

| Phase | CLI | Primary inputs | Primary outputs |
|-------|-----|----------------|-----------------|
| **1. Recon** | `recon` | Target URL, optional engagement config | `recon/intelligence/master_intel.json`, routes, endpoints, requests, insertion points, state-flow, screenshots, … |
| **2. Plan** | `plan` | `master_intel.json` | `planning/test_plans.json`, `planning/test_plans_by_category/*.json` |
| **3. Test** | `test` | `test_plans.json` | `testing/findings/all_findings.json`, `runner_state.json` |
| **4. Verify** | `verify` | `all_findings.json` | `verification/confirmed/verified_findings.json`, per-finding JSON for confirmed |
| **5. Report** | `report` | `verified_findings.json` | `reports/markdown/*`, `reports/json/*`, `reports/csv/*`, `reports/txt/*` |

**Full run:** `full --target <url>` runs all five phases with one generated `run_id`.

### ASRTS / enterprise hooks (recon)

- **Governance:** Optional engagement YAML/JSON (`ENGAGEMENT_CONFIG_PATH` or default paths) loads **scope** (`ScopeValidator`) and **rate limits** (`RateLimiter`) so HTTP and Playwright traffic can be restricted to approved hosts/paths.
- **Evidence:** WARC capture (`outputs/warc/`), session store (`outputs/sessions/`) when identity flows run.
- **Deep recon:** Insertion-point extraction, SPA **state-flow** crawl, form mining, API spec discovery, sensitive exposure scan, knowledge graph — all wired in `run_recon()` in `main.py` (see the doc above for the exact order).

### End-to-end data flow (concise)

```text
recon → master_intel.json
  → plan → test_plans.json
    → test → all_findings.json
      → verify → verified_findings.json
        → report → executive_summary.md, engineering_handoff.md, CSV/JSON, …
```

Use the **same `--run-id`** across commands so logs (`outputs/logs/<phase>_<run_id>.log`) and `_meta` line up.

---

## Project Layout

At the root:

- `cyberAI/` – main Python package  
  - `main.py` – CLI orchestrator for all phases (`recon`, `plan`, `test`, `verify`, `report`, `full`, `retention`)  
  - `config.py` – configuration (`.env` + environment, `OUTPUT_DIR`, `ENGAGEMENT_CONFIG_PATH`, …)  
  - `models.py` – Pydantic v2 models (`Route`, `Endpoint`, `TestPlan`, `Finding`, `MasterIntelligence`, …)  
  - `recon/` – discovery modules (crawl, network intel, WP, state-flow, forms, GraphQL, …)  
  - `planning/` – `TestPlanner` → `test_plans.json`  
  - `testing/` – `TestRunner` + category testers  
  - `verification/` – `VerificationPipeline` + optional verifier modules  
  - `reporting/` – `ReportGenerator`, Jinja2 templates  
  - `governance/` – engagement config, scope, rate limit, retention  
  - `identity/` – session population helpers (when `ROLE_ACCOUNTS` is set)  
  - `storage/` – WARC writer, knowledge graph builder  
  - `utils/` – browser, HTTP client, helpers, proxy, attack graph  
  - `llm/` – stubs for future RAG/LLM integration  
- `config/` – example engagement config (`engagement_config.example.yaml`)  
- `docs/` – pipeline documentation (`PIPELINE_AND_OUTPUTS.md`, implementation notes)  
- `outputs/` – **canonical** runtime output directory (recon, planning, testing, verification, reports, logs, warc, sessions)  
- `cyberAI/requirements.txt` – Python dependencies (`pip install -r cyberAI/requirements.txt`)

> Note: If a `cyberAI/outputs` directory exists from older runs, the CLI still uses `outputs/` at the repo root unless `OUTPUT_DIR` is changed.

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
- **Governance (optional)**
  - `engagement_config_path` / `ENGAGEMENT_CONFIG_PATH` – YAML or JSON engagement file for **in-scope domains**, rate limits, retention (see `config/engagement_config.example.yaml`)

`.env` (see `cyberAI/.env.example`) and environment variables feed into `Config.load`. You can pass `--env /path/to/.env` on any CLI invocation.

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
    - TLS verification is disabled (`verify=False`) to align with Playwright’s `ignore_https_errors` and to reduce friction on lab/self-signed targets (use only on authorized systems).
    - Optional proxy rotation via `proxy_manager`
    - UA rotation via `fake_useragent`
    - Optional **scope** and **rate-limit** checks when engagement governance is loaded
    - `get/post/request` methods that apply rate limiting, send requests, and wrap responses into `RequestRecord` when `record=True`

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

`run_recon()` in `cyberAI/main.py` executes a **fixed progress-tracked sequence** (not the older “step 1–16” narrative only). Conceptually it covers:

| Area | Modules (examples) | Notable outputs |
|------|--------------------|-----------------|
| **CMS / seed URLs** | `wp_discovery.py` | `wp_discovery.json`, `wp_routes.json` |
| **Crawl + traffic** | `core_discovery.py`, `network_intelligence.py` | `routes.json`, `all_requests.json`, `endpoints.json`, screenshots, DOM |
| **Attack surface parameters** | `insertion_point_extractor.py`, `novelty_index.py` | `insertion_points.json`, `novelty_index.json` |
| **SPA states** | `state_flow.py` | `state_flow.json` (may follow links off-origin unless scope is enforced) |
| **Forms / specs / leaks** | `form_mining.py`, `api_spec_discovery.py`, `sensitive_exposure.py` | (captured into network intel + intel JSONs) |
| **Client-side** | `frontend_parser.py` | `frontend_analysis.json`, `hidden_routes.json`, `js_bundles/` |
| **Roles & states** | `role_discovery.py`, `account_state.py` | `role_diff.json`, `state_diff.json` (when configured) |
| **Surfaces & APIs** | `sensitive_surfaces.py`, `graphql_discovery.py`, `websocket_discovery.py` | `sensitive_surfaces.json`, `graphql_intel.json`, `websocket_intel.json` |
| **Models & workflows** | `object_model.py`, `permission_inference.py`, `workflow_mapper.py`, `input_schema.py`, `security_controls.py`, `comparison_engine.py` | `object_graph.json`, `permission_matrix.json`, `workflows.json`, `input_schemas.json`, `security_controls.json`, `comparison_diffs.json` |
| **Roll-up** | `intelligence_outputs.py` | **`master_intel.json`**, `route_map.json`, `endpoint_inventory.json`, `hidden_surface_report.md`, optional `role_state_matrix.csv` |
| **Graph** | `storage/graph_builder.py` | Knowledge graph files for visualization/debug |

**CLI:** `python -m cyberAI.main recon --target https://target [--run-id <id>]`

For a **line-by-line step order and every file path**, see [`docs/PIPELINE_AND_OUTPUTS.md`](docs/PIPELINE_AND_OUTPUTS.md).

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

- **`pipeline.py` (wired by the CLI)**  
  - Loads `testing/findings/all_findings.json`  
  - `deduplicate()` – merges duplicates by `(asset, category, title)`  
  - `run_verification()` – assigns each finding a `VerifiedFinding` status using **reliability_score** heuristics (`confirmed` / `likely` / `needs_more_data`)  
  - Writes:
    - `verification/confirmed/verified_findings.json` (summary + all verified rows)
    - `verification/confirmed/finding_<id>.json` for **confirmed** items

- **Additional modules** (`false_positive.py`, `state_validation.py`, `cross_role_validation.py`, `race_confirmation.py`, `stored_confirmation.py`, `control_bypass.py`, `impact_proof.py`, `boundary_verification.py`, `exploit_chain.py`, etc.) are available under `cyberAI/verification/` for richer verification logic; the default `VerificationPipeline` is the orchestration path used by `python -m cyberAI.main verify` today.

The `verify` CLI command (`python -m cyberAI.main verify [--run-id <id>]`) runs this phase.

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

- `retention` – apply TTL / cleanup to raw and structured evidence (see `cyberAI/governance/retention.py`)
  - `--engagement-config`, `--raw-ttl-days`, `--structured-ttl-days`, `--dry-run`

All commands also accept `--env` at the top level to point to a specific `.env` file.

---

## Typical End-to-End Run

From the repository root (after `pip install -r cyberAI/requirements.txt` and `playwright install chromium`):

```bash
# Use one run id for traceability across logs and _meta
export RUN_ID=my_assessment_1

python3 -m cyberAI.main recon  --target https://example.com --run-id "$RUN_ID"
python3 -m cyberAI.main plan    --run-id "$RUN_ID"
python3 -m cyberAI.main test    --target https://example.com --categories auth,authz --run-id "$RUN_ID"
python3 -m cyberAI.main verify  --run-id "$RUN_ID"
python3 -m cyberAI.main report  --run-id "$RUN_ID"
```

Or in one shot (generates its own run id):

```bash
python3 -m cyberAI.main full --target https://example.com --workers 4
```

Outputs are written under `outputs/` unless `OUTPUT_DIR` is set. Phase logs: `outputs/logs/<phase>_<run_id>.log`.

**Optional data retention cleanup:** `python3 -m cyberAI.main retention [--dry-run] [--engagement-config ...]`

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

**Scope:** Without an engagement config, crawlers may follow links to **third-party origins** (e.g. documentation sites). For production assessments, configure **engagement scope** (`ENGAGEMENT_CONFIG_PATH` / `config/engagement_config.example.yaml`) so traffic stays within approved domains.

