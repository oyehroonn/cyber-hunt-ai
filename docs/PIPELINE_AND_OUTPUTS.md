# Pipeline & output inventory

This document describes **what each phase does**, **what data it reads**, **what it writes** (under the default `outputs/` directory), and **how phases chain together**. Use it for UI design, integrations, or second-pass AI planning.

All JSON artifacts that the platform writes include a `_meta` block where applicable (`target_url`, `phase`, `run_id`, `version`, `generated_at`).

---

## Data flow (high level)

```text
recon  →  recon/intelligence/master_intel.json (+ many recon artifacts)
   ↓
plan   →  planning/test_plans.json (+ per-category JSON)
   ↓
test   →  testing/findings/all_findings.json (+ optional per-finding JSON)
   ↓
verify →  verification/confirmed/verified_findings.json (+ per-finding JSON for confirmed)
   ↓
report →  reports/{markdown,json,csv,txt}/...
```

**Logs:** Each phase writes `outputs/logs/<phase>_<run_id>.log` when `setup_logging` runs (see `cyberAI/main.py`).

---

## Phase 1: Reconnaissance (`recon`)

**CLI:** `python -m cyberAI.main recon --target <URL> [--run-id <id>] [--proxy] [--env <path/to/.env>]`

**Entry:** `cyberAI/main.py` → `run_recon()`

### Optional governance (ASRTS)

Before crawling, the orchestrator may load an **engagement config** (YAML/JSON) via `ENGAGEMENT_CONFIG_PATH` or default paths (`outputs/engagement_config.yaml`, `config/engagement.yaml`, etc.). When loaded:

- **Scope:** `ScopeValidator` blocks HTTP/browser requests outside `target_domains` (see `cyberAI/governance/`).
- **Rate limits:** `RateLimiter` enforces per-host/global RPS from the engagement file.

If no engagement file is present or PyYAML is missing for YAML files, recon runs **without** scope enforcement (browser may follow external links during state-flow exploration).

### Recon steps (order in `run_recon`)

| Step | Description | Primary outputs |
|------|-------------|-----------------|
| 1 | **WP/Woo discovery** — `robots.txt`, sitemaps, `/wp-json/` | `recon/intelligence/wp_discovery.json`, `wp_routes.json` |
| 2 | **Core discovery** — Playwright crawl + `NetworkIntelligence` | `recon/intelligence/routes.json`, `recon/requests/all_requests.json`, `recon/intelligence/endpoints.json`, screenshots, DOM snapshots |
| 2.5 | **Insertion points** — canonical requests + extracted parameters | `recon/intelligence/insertion_points.json`, `novelty_index.json` |
| 2.6 | **State-flow crawl** — SPA-style state exploration (Crawljax-like); `max_states` and wall-clock timeout configured in `main.py` | `recon/intelligence/state_flow.json` |
| 3 | Network intel checkpoint | (re-saves requests/endpoints as needed) |
| 3.5 | **Form mining** | (requests captured via `network_intel`) |
| 3.6 | **API spec discovery** (OpenAPI/Swagger) | under `recon/intelligence/` as implemented |
| 3.7 | **Sensitive exposure** (lexical patterns in responses) | exposure artifacts under `recon/intelligence/` |
| 4 | **Frontend parser** — HTML + JS bundles | `recon/intelligence/frontend_analysis.json`, `hidden_routes.json`, `recon/js_bundles/*` |
| 5 | **Role discovery** | only if `ROLE_ACCOUNTS` set — `recon/intelligence/role_diff.json`, etc. |
| 5b | **Account state discovery** | `recon/intelligence/state_diff.json` |
| 6 | **Sensitive surfaces** — probe common paths | `recon/intelligence/sensitive_surfaces.json` |
| 7 | **GraphQL discovery** | `recon/intelligence/graphql_intel.json` (may merge insertion points) |
| 8 | **WebSocket discovery** | `recon/intelligence/websocket_intel.json` |
| 9 | **Async flow discovery** | `recon/intelligence/async_flows.json` |
| 10 | **Object model** | `recon/intelligence/object_graph.json` |
| 11 | **Permission inference** | `recon/intelligence/permission_matrix.json` (+ CSV if present) |
| 12 | **Workflow mapper** | `recon/intelligence/workflows.json`, optional `.dot` graphs |
| 13 | **Input schema analysis** | `recon/intelligence/input_schemas.json` |
| 14 | **Security controls** | `recon/intelligence/security_controls.json` |
| 15 | **Comparison engine** | `recon/intelligence/comparison_diffs.json` (if roles + endpoints) |
| 16 | **Intelligence aggregation** | `master_intel.json`, `route_map.json`, `endpoint_inventory.json`, `hidden_surface_report.md`, optional `role_state_matrix.csv` |
| 17 | **Knowledge graph** (file-backed) | graph artifacts under `outputs/` as built by `storage/graph_builder.py` |

### Evidence & session stores (ASRTS)

- **WARC:** `outputs/warc/` — raw HTTP evidence when `WARCWriter` is enabled during recon.
- **Sessions:** `outputs/sessions/` — file-backed session store when identity/session population runs.

### Key recon files (for dashboards)

| Path | Purpose |
|------|---------|
| `recon/intelligence/routes.json` | Discovered pages: URLs, actions, screenshots, DOM paths |
| `recon/intelligence/endpoints.json` | Normalized API endpoints from traffic |
| `recon/requests/all_requests.json` | Raw request/response records |
| `recon/intelligence/master_intel.json` | **Single rollup** consumed by planning |
| `recon/intelligence/insertion_points.json` | Parameters / mutation targets for testing |
| `recon/intelligence/state_flow.json` | UI state machine (states + transitions) |

---

## Phase 2: Planning (`plan`)

**CLI:** `python -m cyberAI.main plan [--run-id <id>]`

**Entry:** `cyberAI/planning/test_planner.py` → `run_test_planner()`

**Reads:** Primarily `recon/intelligence/master_intel.json` (and related recon intel via `Config.get_output_path`).

**Writes:**

| Path | Purpose |
|------|---------|
| `planning/test_plans.json` | All `TestPlan` objects (`plans` array + metadata) |
| `planning/test_plans_by_category/<category>.json` | Split by `TestCategory` |

---

## Phase 3: Testing (`test`)

**CLI:** `python -m cyberAI.main test [--target URL] [-c auth,authz,...] [-w workers] [--run-id <id>]`

**Entry:** `cyberAI/testing/runner.py` → `run_tests()`

**Reads:** `planning/test_plans.json`

**Writes:**

| Path | Purpose |
|------|---------|
| `testing/findings/all_findings.json` | Aggregated findings + counts |
| `testing/findings/finding_<id>.json` | Optional per-finding files (when emitted) |
| `testing/runner_state.json` | Runner progress / stats |

Testers live under `cyberAI/testing/*.py` (auth, authz, business logic, GraphQL, etc.) and use `AsyncHTTPClient` / browser pool.

---

## Phase 4: Verification (`verify`)

**CLI:** `python -m cyberAI.main verify [--run-id <id>]`

**Entry:** `cyberAI/verification/pipeline.py` → `run_verification()`

**Reads:** `testing/findings/all_findings.json`

**Processing (current orchestrator):** Loads findings → deduplicates by `(asset, category, title)` → assigns verification status using **reliability_score** heuristics → saves.

> **Note:** The repository also contains additional verifier modules (`false_positive.py`, `state_validation.py`, …) exported from `cyberAI/verification/__init__.py`. The **default** `VerificationPipeline` in `pipeline.py` is the orchestration path wired by the CLI; extended pipelines can incorporate those modules in future work.

**Writes:**

| Path | Purpose |
|------|---------|
| `verification/confirmed/verified_findings.json` | All verified findings + summary counts |
| `verification/confirmed/finding_<id>.json` | One file per **confirmed** finding |

---

## Phase 5: Reporting (`report`)

**CLI:** `python -m cyberAI.main report [--run-id <id>]`

**Entry:** `cyberAI/reporting/reporter.py` → `run_report_generation()` → `ReportGenerator.save_all_outputs()`

**Reads:** `verification/confirmed/verified_findings.json`

**Writes:**

| Path | Purpose |
|------|---------|
| `reports/markdown/executive_summary.md` | Executive narrative |
| `reports/markdown/engineering_handoff.md` | Engineering-focused write-up |
| `reports/markdown/findings/finding_<first8ofid>.md` | Per-finding markdown |
| `reports/json/all_findings.json` | Full finding payloads (+ `_meta`) |
| `reports/json/severity_breakdown.json` | Counts by severity |
| `reports/csv/findings.csv` | Tabular export for spreadsheets / BI |
| `reports/txt/executive_summary.txt` | Plain-text exec summary |
| `reports/txt/remediation_queue.txt` | Prioritized remediation list |

---

## Full assessment (`full`)

**CLI:** `python -m cyberAI.main full --target <URL> [options]`

Runs `recon` → `plan` → `test` → `verify` → `report` with a **single generated `run_id`** for the whole assessment (see `run_full()` in `main.py`).

---

## Retention (optional)

**CLI:** `python -m cyberAI.main retention [--engagement-config ...] [--dry-run]`

Uses `cyberAI/governance/retention.py` to apply TTL rules from engagement config to raw/structured stores (e.g. WARC).

---

## Correlating a run with `run_id`

Pass the same `--run-id` to each phase (e.g. `full_1`) so logs and `_meta.run_id` line up. Phases still **overwrite** canonical paths like `master_intel.json` and `test_plans.json` on each run unless you change `OUTPUT_DIR` or archive outputs between runs.

---

## Model source of truth

Structured types are defined in `cyberAI/models.py` (`Route`, `Endpoint`, `TestPlan`, `Finding`, `VerifiedFinding`, `MasterIntelligence`, etc.).
