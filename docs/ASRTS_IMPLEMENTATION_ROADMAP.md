# ASRTS End-to-End Implementation Roadmap

This roadmap turns the [ASRTS Implementation Plan](ASRTS_IMPLEMENTATION_PLAN.md) into concrete, file-level tasks so the system can be implemented **end-to-end without errors**, with **100% concept understanding** (see [ASRTS Concepts Glossary](ASRTS_CONCEPTS_GLOSSARY.md)), and so the platform **mines more data**, **explores up to 100% of the in-scope web**, and **dumps and stores everything** for enterprise-grade security testing.

---

## Principles for “Perfect” Implementation

1. **One concept = one place in code.** Each term in the glossary maps to a clear module or data structure; no duplication of responsibility.
2. **Every request passes scope.** No new HTTP path that bypasses the scope validator.
3. **Every finding has evidence refs.** From Phase 1 onward, findings carry WARC refs (or a stable request ID that resolves to WARC once the writer exists).
4. **Test after each phase.** Each phase ends with acceptance criteria and a short test script or manual checklist so we don’t accumulate hidden errors.
5. **Incremental data gain.** Each phase should demonstrably increase: number of unique URLs/states discovered, number of insertion points mapped, quality of authz testing, or reproducibility of reports.

---

## Phase 1: MVP — Safe and Scoped (Foundation)

**Goal:** Authorization and evidence are first-class. No request leaves the system without scope check; every capture can be linked to a finding.

### 1.1 Engagement configuration

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 1.1.1 | `cyberAI/governance/__init__.py` | Create | Package for governance (scope, config). |
| 1.1.2 | `cyberAI/governance/schema.py` | Create | Pydantic models for engagement config: `EngagementConfig`, `TargetDomain`, `OutOfScopePattern`, `TestIdentity`, `RateLimits`, `DataRetention`, `IncidentContact`. Mirror the YAML in ASRTS §2.1. |
| 1.1.3 | `cyberAI/governance/loader.py` | Create | Load engagement config from YAML/JSON path or env; validate with Pydantic; return `EngagementConfig`. Support default path `outputs/engagement_config.yaml` or `config/engagement.yaml`. |
| 1.1.4 | `cyberAI/config.py` | Modify | Add optional `engagement_config_path: Optional[str]`. When set, `get_config()` (or a dedicated getter) loads engagement config once and caches it. |

**Acceptance:** Load a sample `engagement_config.yaml`; access `config.target_domains`, `config.out_of_scope_patterns`, `config.rate_limits.per_host_rps`.

### 1.2 Scope validator and enforcement

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 1.2.1 | `cyberAI/governance/scope.py` | Create | `ScopeValidator` class. Method `is_in_scope(url: str, method: str) -> tuple[bool, str]` (allowed, reason). Normalize URL (strip fragment, sort query); check against `target_domains` and `out_of_scope_patterns`; return (False, "out_of_scope") or (True, "ok"). Pre-compile patterns for speed. |
| 1.2.2 | `cyberAI/utils/http_client.py` | Modify | Introduce `ScopeEnforcingClient` (or wrap inside `AsyncHTTPClient`): before every `request()`, call `ScopeValidator.is_in_scope(url, method)`. If not in scope: do not send; log to logger (and optionally to a list for audit); return a synthetic “blocked” response or raise a custom exception. Use engagement config from config singleton. |
| 1.2.3 | `cyberAI/utils/browser.py` | Modify | When creating Playwright context or page, set `page.route("**/*", handler)` that checks each request URL with `ScopeValidator.is_in_scope`. If out-of-scope, `route.abort()`. Ensure all browser traffic goes through this. |

**Acceptance:** With an engagement config that has one `target_domains` and one `out_of_scope_patterns`, run a crawl; verify that a request to an out-of-scope URL is never sent (check logs or network capture). Verify in-scope requests still succeed.

### 1.3 Rate limiting and politeness

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 1.3.1 | `cyberAI/governance/rate_limiter.py` | Create | Per-host token bucket (or sliding window): `async def acquire(host: str) -> None` that blocks until a token is available. Use `rate_limits.per_host_rps` and optional `global_rps` from engagement config. |
| 1.3.2 | `cyberAI/utils/http_client.py` | Modify | Before each request, call rate limiter `acquire(parsed_host)`. On 5xx, apply exponential backoff (configurable) before retry. |

**Acceptance:** Set `per_host_rps: 2`; run 10 requests to the same host; verify delays between requests and no more than 2/sec.

### 1.4 WARC writer and capture ID

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 1.4.1 | `cyberAI/storage/__init__.py` | Create | Package for storage (WARC, future object store). |
| 1.4.2 | `cyberAI/storage/warc_writer.py` | Create | `WARCWriter` class. Method `write_record(request_bytes, response_bytes, request_headers, response_headers, url, method) -> str` that appends one WARC record (request + response blocks per ISO 28500) to a file under `outputs/warc/{run_id}/` and returns a **WARC ref** (e.g. `{run_id}/{filename}#{offset}_{length}` or content-addressed ID). Use standard WARC record types (request, response). |
| 1.4.3 | `cyberAI/recon/network_intelligence.py` | Modify | When saving a `RequestRecord`, optionally call WARC writer (if enabled) and attach the returned `warc_ref` to the record. Persist `warc_ref` in the JSON output (e.g. add `warc_ref` to serialized request). |
| 1.4.4 | `cyberAI/models.py` | Modify | Add `warc_ref: Optional[str] = None` to `RequestRecord`. Add `evidence_warc_refs: list[str] = Field(default_factory=list)` to `Finding`. |

**Acceptance:** Run recon; open the WARC file under `outputs/warc/`; verify at least one request and one response record; verify a finding (or a saved request) contains a non-empty `warc_ref` / `evidence_warc_refs` when WARC is enabled.

### 1.5 Wire scope and WARC through recon and reporting

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 1.5.1 | `cyberAI/main.py` | Modify | Before recon: load engagement config if path is set; pass scope validator to any component that needs it (or rely on http_client and browser already using it). Ensure WARC writer is initialized with run_id and output path. |
| 1.5.2 | `cyberAI/reporting/*` | Modify | When generating findings (e.g. in reporter or engineering handoff), include `evidence_warc_refs` in the output. If a finding has `request_proof` with `warc_ref`, add that to `evidence_warc_refs`. |

**Acceptance:** Full run (recon → plan → test → report). Confirm engagement config is used, out-of-scope is blocked, and report contains `evidence_warc_refs` for at least one finding (or placeholder “N/A” if no WARC yet for that finding).

---

## Phase 2: Core platform — Crawl intelligence and differential auth

**Goal:** Priority-based crawl, insertion point mapping, multi-identity sessions, and differential authorization testing so we mine more data and find BOLA/IDOR with evidence.

### 2.1 Insertion point extraction and canonical request

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 2.1.1 | `cyberAI/recon/insertion_point_extractor.py` | Create | `RequestCanonicalizer`: input = `RequestRecord` or raw request/response; output = `CanonicalRequest` (method, url_template, query_params as list of {name, value_placeholder}, headers, body_ast). Implement URL template: replace numeric/UUID path segments with `{id}`. Body: parse JSON/form; replace literal values with placeholders (`<INT>`, `<STR>`, etc.). |
| 2.1.2 | `cyberAI/recon/insertion_point_extractor.py` | Create | `InsertionPointExtractor`: walk `CanonicalRequest` AST; emit list of `InsertionPoint` (location e.g. `path_segment_2`, `query.q`, `body.user.id`, `header.X-Role`; encoding_layers; inferred_type). Support one level of nested encoding (e.g. base64-decode then parse JSON); cap depth at 3. |
| 2.1.3 | `cyberAI/models.py` | Modify | Add `CanonicalRequest`, `InsertionPoint` (location, encoding_layers, inferred_type, request_id). Add `InsertionPoint` to `Endpoint` or a new `insertion_points` list in recon output. |

**Acceptance:** Run canonicalizer on a sample `RequestRecord` with JSON body and path with ID; verify url_template and body_ast; verify insertion points list includes path, query, and body fields.

### 2.2 Novelty index and priority queue (crawl frontier)

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 2.2.1 | `cyberAI/recon/novelty_index.py` | Create | `NoveltyIndex`: in-memory (or Redis later) set of `shape_hash` (hash of method + url_template + sorted param names). `add(shape_hash) -> bool` (True if new). `is_novel(shape_hash) -> bool`. Optional: persist to `outputs/recon/intelligence/novelty_index.json` for debugging. |
| 2.2.2 | `cyberAI/recon/core_discovery.py` | Modify | Replace BFS queue with a **priority queue** (heap). `FrontierItem`: url_or_action, depth, priority_score, source. Score = f(depth, novelty, content_type, path_sensitivity). When we discover a new URL, compute shape_hash from canonical path pattern; if novelty_index.add(shape_hash), boost score. Pop highest score first. Cap frontier size (e.g. 50k). |

**Acceptance:** Run crawl with priority queue; verify that high-value URLs (e.g. containing “api”, “admin”) are visited earlier in the log than trivial static pages (if such exist).

### 2.3 State-flow crawling (Crawljax-style)

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 2.3.1 | `cyberAI/recon/state_flow.py` | Create | `StateFlowCrawler`: (1) **DOM hasher**: serialize DOM (strip script/style, normalize dynamic attrs); SHA-256 → `state_id`. (2) For current page, get all clickable/submittable elements (reuse or mirror `get_page_actions`). (3) For each element, fire event; wait for network idle + short delay; compute new DOM hash. (4) If hash changed, record transition (from_state, to_state, event_type, selector); enqueue new state for exploration. (5) Maintain `states: dict[state_id, CrawlState]`, `transitions: list`. Cap total states (e.g. 2000). |
| 2.3.2 | `cyberAI/models.py` | Modify | Add `CrawlState` (state_id, dom_hash, url, warc_ref, discovered_at), `CrawlTransition` (from_state_id, to_state_id, event_type, selector). |
| 2.3.3 | `cyberAI/recon/core_discovery.py` | Modify | After initial BFS/priority crawl, optionally run `StateFlowCrawler` on a subset of discovered routes (e.g. top 50 by priority) to discover SPA states. Merge new URLs and states into recon output. Or run state-flow as a separate step in main.py. |

**Acceptance:** Run against a simple SPA (or a page with a modal); verify at least two states and one transition; verify new URLs or requests captured that weren’t in the link-only crawl.

### 2.4 Identity layer: session pool and login macro

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 2.4.1 | `cyberAI/identity/__init__.py` | Create | Package for identity/session management. |
| 2.4.2 | `cyberAI/identity/session_store.py` | Create | In-memory (or Redis) store: key `session:{engagement_id}:{role}`; value = dict of cookies + optional auth headers. `get(engagement_id, role)`, `set(engagement_id, role, cookies, headers)`, `invalidate(engagement_id, role)`. |
| 2.4.3 | `cyberAI/identity/login_sequence.py` | Create | `LoginSequence` model: list of steps (navigate, fill, click, wait_for_selector, assert_url_contains). Load from engagement config (login_sequence_ref). `LoginRunner`: run sequence in Playwright; on success (e.g. URL contains dashboard), extract cookies and return; write to session_store. |
| 2.4.4 | `cyberAI/identity/session_health.py` | Create | `SessionHealthChecker`: given a “session check” URL (from config), perform GET with session cookies; if 401/403 or redirect to login path → return False. `SessionRepairRunner`: call LoginRunner and update session_store. |
| 2.4.5 | `cyberAI/main.py` / `cyberAI/recon/core_discovery.py` | Modify | When role accounts are present, before crawl for role R: get session from session_store; if missing or health check fails, run SessionRepairRunner; inject cookies into browser context. After N requests or on 401, re-check health and repair if needed. |

**Acceptance:** Configure two roles with form_replay credentials; run recon for each role; verify different sets of requests (e.g. admin sees more endpoints). Simulate session expiry (e.g. invalidate after 5 requests); verify repair runs and crawl continues.

### 2.5 Differential authorization testing

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 2.5.1 | `cyberAI/testing/authorization_testing.py` | Modify | Add `differential_auth_test`: for each endpoint from recon that has an ID placeholder, (1) get session for role_admin and role_user from identity layer. (2) Build request (e.g. GET /api/users/123) with admin session; record response A. (3) Same request with user session; record response B. (4) If user got 200 and response B “looks like” same resource (e.g. same JSON keys, or same size band), create Finding (BOLA/IDOR) with request_proof and response_proof for both, and attach evidence_warc_refs for both requests. Use only synthetic IDs (e.g. 1, 2, test-obj-id). |
| 2.5.2 | `cyberAI/testing/runner.py` | Modify | When running authz tests, pass session store or identity layer so that differential_auth_test can get per-role sessions. Ensure findings include evidence_warc_refs. |

**Acceptance:** Run against a test app where user can access another’s resource; verify one BOLA finding with two request_proofs (admin and user) and evidence_warc_refs populated (if WARC is on).

---

## Phase 3: Advanced — Prioritisation, forms, API discovery, sensitive exposure

**Goal:** Neural/semantic prioritisation, deep web form mining, OpenAPI/GraphQL/WebSocket discovery, and sensitive exposure detection so we mine “everything” that’s reachable and high-value.

### 3.1 Neural/semantic prioritisation

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 3.1.1 | `cyberAI/recon/priority_scorer.py` | Create | `SecurityRelevanceScorer`: input = URL + optional HTML snippet; output = score 0–1. Use heuristics: path contains (api, admin, user, upload, login, settings); form count; input count. Optional: small sklearn TF-IDF + logistic regression trained on labeled URLs (e.g. “high” if path contains admin/api). |
| 3.1.2 | `cyberAI/recon/core_discovery.py` | Modify | When pushing to frontier, call SecurityRelevanceScorer and add score to priority. Combine with novelty and depth so high-relevance + novel items are crawled first. |

**Acceptance:** Crawl; verify that high-relevance URLs (e.g. /api/, /admin/) appear earlier in the crawl order than low-relevance (e.g. /about). |

### 3.2 Deep web form mining

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 3.2.1 | `cyberAI/recon/form_mining.py` | Create | Discover forms (search, filters) from crawled pages; fingerprint (action URL, method, field names). For each form, submit a small set of **adaptive queries** (e.g. from a word list or from spec); cap submissions per form (e.g. 10) and total result size or response count to avoid DoS. Record new URLs and request/response to WARC and network intel. |
| 3.2.2 | `cyberAI/main.py` | Modify | After core discovery (and state-flow), run form_mining on discovered routes; merge new endpoints and requests into intelligence. |

**Acceptance:** Run against a site with a search form; verify new endpoints or responses from form submissions; verify caps are respected (no thousands of requests). |

### 3.3 API discovery (OpenAPI, GraphQL, traffic)

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 3.3.1 | `cyberAI/recon/api_spec_discovery.py` | Create | Fetch known paths: `/openapi.json`, `/swagger.json`, `/api-docs`, etc. If JSON, parse; extract endpoints and params; add to endpoints and insertion points. Same for GraphQL: POST to known `/graphql` with introspection query; parse schema; add types and operations as endpoints. |
| 3.3.2 | `cyberAI/recon/network_intelligence.py` | Modify | Already capturing XHR/fetch; ensure all are classified and stored. Add “source: api_spec” vs “source: traffic” for endpoints. |
| 3.3.3 | `cyberAI/recon/graphql_discovery.py` | Modify | Ensure introspection results are normalized into Endpoint + InsertionPoint (e.g. each operation + variables). |

**Acceptance:** Point at an app with OpenAPI at /openapi.json; verify endpoints from spec appear in intelligence. For GraphQL, verify operations and variables are in insertion point list. |

### 3.4 Sensitive exposure detection

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 3.4.1 | `cyberAI/recon/sensitive_exposure.py` | Create | **Lexical pass**: regex patterns for PII, credentials, API keys, tokens in response bodies (from stored requests or WARC). Flag matches; do not store full body in finding—store WARC ref and snippet. **Relevance gate**: only run on responses that passed security relevance scorer above a threshold. Optional: for high-value URLs, trigger dynamic render + OCR (Phase 4). |
| 3.4.2 | `cyberAI/main.py` or pipeline | Modify | After recon, run sensitive_exposure on captured responses; emit findings (e.g. “Possible credential in response”) with evidence_warc_refs. |

**Acceptance:** Run against a page that contains a fake API key in HTML; verify one finding with WARC ref and no raw secret in the report. |

---

## Phase 4: Top-tier — Knowledge graph, API fuzzing, OCR, retention

**Goal:** Full knowledge graph (Neo4j), RESTler-style API fuzzing, OCR for high-risk content, and automated retention so the platform is enterprise- and compliance-ready.

### 4.1 Knowledge graph (Neo4j)

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 4.1.1 | `cyberAI/storage/graph_builder.py` | Create | Consume endpoints, insertion points, roles, findings from recon and testing output (or from Kafka in future). Create Neo4j nodes: Endpoint, Parameter, Role, Finding, WARCRef. Create edges: Endpoint-EXPOSES->Parameter, Endpoint-REQUIRES_AUTH->Role, Finding-EVIDENCE_IN->WARCRef. Use Neo4j driver; optional so platform runs without Neo4j if not configured. |
| 4.1.2 | `cyberAI/config.py` | Modify | Add `neo4j_uri`, `neo4j_user`, `neo4j_password` (optional). |
| 4.1.3 | `cyberAI/main.py` | Modify | After aggregation (and after test/report), if Neo4j configured, run graph_builder to sync current run. |

**Acceptance:** Run full pipeline with Neo4j; query: “match (e:Endpoint)-[:REQUIRES_AUTH]->(r:Role) return e,r”; verify results. |

### 4.2 RESTler-style stateful API fuzzing

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 4.2.1 | `cyberAI/testing/api_fuzzer.py` | Create | From OpenAPI spec (or endpoint list), build **dependency graph**: e.g. POST /users creates user_id; GET /users/{id} needs user_id. Generate sequences: create user → get user; create order → get order. Fuzz parameters (strings, ints) with safe values and boundary values; record crashes or 5xx. Attach WARC refs to any finding. |
| 4.2.2 | `cyberAI/testing/runner.py` | Modify | Optional category “api_fuzz”; when selected and spec exists, run api_fuzzer. |

**Acceptance:** Run against a simple API with create/read; verify sequence is generated and at least one fuzz request is sent; no requirement to find a bug. |

### 4.3 OCR pipeline (high-risk content)

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 4.3.1 | `cyberAI/recon/ocr_extract.py` | Create | For responses that are images or PDFs (content-type or file extension), and only when relevance score is high: run OCR (e.g. Tesseract or cloud API); run same lexical sensitive-exposure patterns on extracted text; create findings with WARC ref. Gate by config (e.g. max 100 pages per run). |
| 4.3.2 | `cyberAI/recon/sensitive_exposure.py` | Modify | Optionally call ocr_extract for image/PDF URLs before lexical pass. |

**Acceptance:** Run against a test URL that returns an image containing fake “password: xyz”; verify finding with WARC ref (and optionally OCR snippet). |

### 4.4 Data retention and TTL

| Task | File(s) | Action | Detail |
|------|---------|--------|--------|
| 4.4.1 | `cyberAI/governance/retention.py` | Create | `RetentionJob`: read engagement config TTL; list WARC files and DB rows (if any) older than raw_capture_ttl_days and structured_ttl_days; delete or redact. For findings, keep metadata but optionally redact response_proof beyond hash. Run as scheduled (e.g. daily cron) or CLI command. |
| 4.4.2 | `cyberAI/main.py` or CLI | Modify | Add subcommand `retention` or `retention-run` that runs RetentionJob for a given engagement. |

**Acceptance:** Set ttl_days=0 for a test engagement; run retention; verify old WARC and recon outputs are removed or redacted. |

---

## Implementation order (summary)

- **Phase 1** must be done first: scope + WARC + rate limits are the foundation. Order within Phase 1: 1.1 → 1.2 → 1.3 → 1.4 → 1.5.
- **Phase 2** builds on Phase 1: 2.1 (insertion points) and 2.2 (novelty + priority) can be parallel; then 2.3 (state-flow); then 2.4 (identity); then 2.5 (differential auth).
- **Phase 3** can be parallelised (3.1–3.4) once Phase 2 is stable.
- **Phase 4** is optional for “top-tier”; 4.1 and 4.4 are most valuable for enterprise; 4.2 and 4.3 add depth.

---

## File creation checklist (quick reference)

| Path | Phase |
|------|--------|
| `cyberAI/governance/__init__.py` | 1 |
| `cyberAI/governance/schema.py` | 1 |
| `cyberAI/governance/loader.py` | 1 |
| `cyberAI/governance/scope.py` | 1 |
| `cyberAI/governance/rate_limiter.py` | 1 |
| `cyberAI/governance/retention.py` | 4 |
| `cyberAI/storage/__init__.py` | 1 |
| `cyberAI/storage/warc_writer.py` | 1 |
| `cyberAI/storage/graph_builder.py` | 4 |
| `cyberAI/identity/__init__.py` | 2 |
| `cyberAI/identity/session_store.py` | 2 |
| `cyberAI/identity/login_sequence.py` | 2 |
| `cyberAI/identity/session_health.py` | 2 |
| `cyberAI/recon/insertion_point_extractor.py` | 2 |
| `cyberAI/recon/novelty_index.py` | 2 |
| `cyberAI/recon/state_flow.py` | 2 |
| `cyberAI/recon/priority_scorer.py` | 3 |
| `cyberAI/recon/form_mining.py` | 3 |
| `cyberAI/recon/api_spec_discovery.py` | 3 |
| `cyberAI/recon/sensitive_exposure.py` | 3 |
| `cyberAI/recon/ocr_extract.py` | 4 |
| `cyberAI/testing/api_fuzzer.py` | 4 |

---

## How this gets “100% of the web” and enterprise-level testing

- **State-flow + priority queue + form mining + API discovery** → Maximises reachable URLs and states (SPA, deep web, APIs). “100%” is bounded by scope, caps, and politeness—we get as much as safely possible.
- **Insertion point + novelty** → Every input location is mapped and prioritised; no blind spots for testing.
- **Multi-identity + differential auth** → Full coverage of role-specific and authenticated surfaces; BOLA/IDOR with evidence.
- **WARC + evidence_warc_refs + retention** → Every mined request/response is stored once, linked to findings, and retained only as long as needed; reproducible and auditable.
- **Knowledge graph** → Enables queries (“all admin endpoints”, “findings with evidence in this WARC”) and future automation (e.g. “test every endpoint that requires auth”).
- **Scope and governance** → Ensures the system is used only for authorised testing and stays within legal and contractual bounds—what makes it “enterprise” and “future-level” rather than just “big crawler”.

Implementing this roadmap phase by phase, with the glossary and plan as references, will make the system mine more data, explore the in-scope app exhaustively, and support enterprise-grade security testing with full provenance and no out-of-scope or unreferenced findings.
