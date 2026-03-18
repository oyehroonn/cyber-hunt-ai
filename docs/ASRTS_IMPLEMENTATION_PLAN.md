# Authorized Security Reconnaissance and Testing System (ASRTS)
## Full Implementation Plan — Enterprise-Grade Architecture

This document is the detailed, opinionated implementation plan for revamping the Cyber Hunt AI platform into a professional-grade ASRTS. It integrates:

- **Your deep research** ([deep-research-report.md](/Users/oyehroonn/Downloads/deep-research-report.md)): neural prioritisation, state-flow crawling, insertion points, WARC/Kafka/Neo4j, differential auth testing, BACScan/RESTler/Silent Spill.
- **Industry references**: [Burp Suite full crawl and audit](https://portswigger.net/burp/documentation/desktop/running-scans/webapp-scans/full-crawl-and-audit), [Wapiti advanced crawling](https://github.com/wapiti-scanner/wapiti/wiki/Advanced-Crawling), [OWASP WSTG mapping execution paths](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/01-Information_Gathering/07-Map_Execution_Paths_Through_Application), [OWASP WSTG metafiles](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/01-Information_Gathering/03-Review_Webserver_Metafiles_for_Information_Leakage).

---

## SECTION 1: SYSTEM OVERVIEW AND COMPONENT MAP

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                        AUTHORIZATION & SCOPE (Governance Layer)                           │
│  Engagement Config (YAML/JSON) → Scope Validator → Policy Engine → Data Retention Ctrl   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
                    ▼                       ▼                       ▼
┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
│   CRAWL ORCHESTRATOR     │ │   IDENTITY / SESSION      │ │   EVIDENCE & STORAGE       │
│   - Frontier PQ           │ │   - Multi-role accounts   │ │   - WARC writer            │
│   - Neural prioritizer    │ │   - Login sequence        │ │   - Content-addressed IDs   │
│   - Seed injection        │ │   - Session health        │ │   - Retention TTL           │
└─────────────┬─────────────┘ └─────────────┬─────────────┘ └─────────────┬─────────────┘
              │                             │                             │
              ▼                             ▼                             │
┌───────────────────────────┐ ┌───────────────────────────┐              │
│   BROWSER CRAWL WORKERS   │ │   AUTH / SESSION POOL     │              │
│   (Playwright)            │ │   - Per-role contexts     │              │
│   - State-flow explorer   │ │   - Repair macros         │              │
│   - Network intercept     │ │   - Cookie/token store    │              │
└─────────────┬─────────────┘ └─────────────┬─────────────┘              │
              │                             │                             │
              │    ┌────────────────────────┴────────────────────────┐   │
              │    │           APACHE KAFKA (event log)               │   │
              │    │  Topics: raw_captures | parsed_requests |       │   │
              │    │          insertion_points | test_events          │   │
              │    └────────────────────────┬────────────────────────┘   │
              │                             │                             │
              ▼                             ▼                             ▼
┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
│   PARSING / ENRICHMENT    │ │   SECURITY TEST WORKERS   │ │   STORAGE LAYER            │
│   - Request canonicalizer │ │   - Authz differential    │ │   - WARC → object store    │
│   - Insertion point       │ │   - IDOR/BOLA replayer    │ │   - PostgreSQL (structured)│
│     extractor             │ │   - API fuzzer (RESTler) │ │   - Neo4j (knowledge graph)│
│   - Security markers      │ │   - GraphQL/WS checks    │ │   - OpenSearch (search)    │
└─────────────┬─────────────┘ └─────────────┬─────────────┘ └─────────────┬─────────────┘
              │                             │                             │
              └────────────────────────────┼─────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│   KNOWLEDGE GRAPH (Neo4j)                                                                │
│   Nodes: Endpoint | Parameter | Role | Session | Finding | WARCRef                       │
│   Edges: requires_auth | exposes | controlled_by_role | inserts_into | evidence_in       │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│   REPORTING & TRIAGE                                                                     │
│   - Executive summary | Engineering handoff | Evidence pack (WARC refs) | Remediation  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

**Data flow in one sentence:** Engagement config gates all actions → Crawl workers (Playwright + state-flow) and auth layer produce raw traffic → Kafka → Parsers extract insertion points and security markers → Test workers consume parsed events and run authz/API tests → All raw bytes go to WARC; structured data to Postgres/Neo4j → Knowledge graph and report generator consume from DB + WARC refs.

---

## SECTION 2: COMPONENT DEEP DIVES

### 2.1 Governance Layer (Authorization and Scope Enforcement)

**Purpose:** Ensure every outbound request and every stored datum is permitted by an explicit engagement configuration. No request leaves the system without passing the scope validator.

**Technology stack:**
- **Config format:** YAML or JSON with a strict schema (JSON Schema or Pydantic). Stored per-engagement (e.g. `engagements/{engagement_id}/scope.yaml`).
- **Enforcement point:** A **network-level proxy or client wrapper** that every HTTP client (Playwright, httpx, etc.) uses. In Python: a custom `httpx.AsyncClient` subclass or a **mitmproxy add-on** that receives all requests from the browser workers and drops/redirects out-of-scope requests before they hit the wire.
- **Recommendation:** Implement a **ScopeEnforcingClient** that wraps the real client and calls `ScopeValidator.is_in_scope(url, method)` before every request. Log dropped requests to an audit topic in Kafka.

**Data model (engagement config):**
```yaml
engagement_id: uuid
name: string
target_domains: [ "https://target.example.com" ]
out_of_scope_patterns: [ "*.staging.*", "*/admin/delete/*" ]
allowed_schemes: [ "https" ]
test_identities:
  - role: admin
    credentials: { type: recorded_login | form_replay | oauth }
    login_sequence_ref: path/to/macro.json
  - role: user
    credentials: { type: form_replay, username: "...", password: "..." }
rate_limits:
  per_host_rps: 10
  global_rps: 50
  backoff_on_5xx: exponential
data_retention:
  raw_capture_ttl_days: 90
  structured_ttl_days: 365
  permitted_data_classes: [ "request_response_meta", "finding_evidence", "insertion_point_schema" ]
incident_contacts: [ "security@client.com" ]
```

**Key algorithms:**
- **Scope check:** Normalize URL (strip fragment, sort query params), then match against allowed domains and exclude out-of-scope regex/glob. Return allow / deny / log-only.
- **Data retention controller:** A scheduled job (e.g. daily) that deletes WARC files and DB rows older than `raw_capture_ttl_days` and `structured_ttl_days`, and that redacts response bodies except for permitted_data_classes (e.g. keep only status, headers, and a hash for reproducibility).

**Integration:** Crawl orchestrator, all browser workers, and test workers load the same engagement config and pass every URL through the scope validator before sending. Kafka consumers that write to WARC tag each record with `engagement_id` and `permitted_data_class` for retention enforcement.

**Hard problems:**
- **Redirects and same-origin iframes:** A request might start in-scope and end up at an out-of-scope URL after redirects. **Solution:** Scope check the **final URL** after redirects; if final URL is out of scope, do not store response body (or store only hash + status) and log.
- **Third-party scripts:** In-browser traffic may include analytics or CDNs. **Solution:** Maintain an explicit allow-list of third-party domains that are in-scope (e.g. CDN for the app); everything else is out-of-scope unless the config says otherwise.

---

### 2.2 Intelligent Crawling and Discovery Engine (Recon Layer)

**Purpose:** Discover the full attack surface of the target application via browser-powered, state-aware crawling and API discovery, with prioritisation so high-value surfaces are covered first.

**Technology stack:**
- **Browser automation:** **Playwright** (Python). Justification: cross-browser (Chromium, Firefox, WebKit), robust waiting APIs, first-class network interception (`page.route`, `context.request`), and good stability for long-running crawls.
- **State-flow logic:** Custom implementation inspired by Crawljax: DOM hash (meaningful subtree, strip timestamps/random IDs), state transition detection, graph of states and edges (event → new state).
- **Prioritisation:** **Priority queue (heap)** for the crawl frontier. Each item = (URL or action descriptor, feature vector, priority score). Score = weighted sum of: insertion-point novelty, depth from authenticated entry, content-type value (API > HTML form > static), role sensitivity (admin path vs public).
- **API discovery:** Same Playwright run; record all XHR/fetch in network listener. Additionally: spec ingestion (OpenAPI/Swagger at `/openapi.json`, etc.), GraphQL introspection at known endpoints, and sitemap/wp-json (already in your codebase) for WordPress/WooCommerce.

**Data model:**
- **CrawlState (node):** `state_id`, `dom_hash`, `url`, `screenshot_path`, `warc_ref`, `discovered_at`.
- **CrawlTransition (edge):** `from_state_id`, `to_state_id`, `event_type` (click, submit, input), `selector`, `payload_preview`.
- **FrontierItem:** `url_or_action`, `depth`, `priority_score`, `feature_vector` (dict), `source` (sitemap | link | api_spec | graphql_introspection).

**Key algorithms:**
- **State hashing:** Serialize DOM with script/style and obvious dynamic attributes stripped; SHA-256 of canonical string. Use a library (e.g. `trafilatura`-style extraction or custom selector set) so that “meaningful” structure is hashed, not every pixel.
- **Neural/semantic prioritisation (Phase 3):** When full HTML is available, run a lightweight classifier (e.g. small BERT or a TF-IDF + logistic regression) that predicts “security relevance” (login, admin, upload, API, form-heavy). Use that score as one feature in the frontier. Optionally use “expected insertion point count” from a small learned model trained on your own past crawls.
- **Infinite scroll / lazy load:** After each state is recorded, run a short scroll-and-wait loop (e.g. scroll to bottom, wait 1s, repeat 3 times) and re-hash; if DOM hash changed, treat as new state and enqueue.

**Integration:** Crawl orchestrator pulls from Kafka topic `seed_urls` (from sitemap, wp-json, and config). It pushes `raw_captures` (URL, request, response, warc_ref) to Kafka. Downstream parsers consume `raw_captures` and produce `parsed_requests` and `insertion_points`. Scope validator is called before every navigation and before every recorded request is written to WARC.

**Hard problems:**
- **State explosion:** SPAs can have thousands of states. **Solution:** Cap states per run (e.g. 10k), and prioritize by “novelty” and “attack surface contribution.” Prune low-score states from the frontier. Use similarity (e.g. SimHash of DOM) to merge “duplicate” states and avoid re-crawling.
- **Login and session expiry:** Handled in Identity Layer; crawler receives a session pool that is refreshed by the session repair macro when 401/403 or redirect-to-login is detected.

---

### 2.3 Insertion Point Mapping and Payload Surface (Analysis Layer)

**Purpose:** Turn every observed HTTP request into a canonical AST and identify every place where user-controllable input can be supplied (insertion points). Track novelty and coverage for prioritisation and testing.

**Technology stack:**
- **Request parsing:** **httpx**-style request/response objects; custom **RequestCanonicalizer** that produces a typed AST (URL segments, query params, headers, body as JSON/XML/form tree).
- **Insertion point extraction:** Walk the AST; mark nodes that are “variable” (path params, query values, body fields, headers like `X-User-Id`). Support **nested insertion points** (e.g. JSON value that is base64-encoded and contains another JSON). Use a small rule set + optional encoding detectors (base64, URL-encode, JSON-in-JSON).
- **Novelty index:** In-memory or Redis set of “insertion point shapes” (e.g. hash of (method, path_template, param_names)). When a new request is canonicalized, compute shape hash; if new, increment novelty and boost priority for that endpoint in the frontier/test queue.

**Data model:**
- **CanonicalRequest:** `request_id`, `method`, `url_template` (path with placeholders), `query_params` [ {name, value_placeholder} ], `headers` [ {name, value_placeholder} ], `body_ast` (tree with leaf types and placeholders), `warc_ref`.
- **InsertionPoint:** `request_id`, `location` (path_segment_3 | query.search | body.user.id | header.X-Role), `encoding_layers` [ "json", "base64" ], `inferred_type` (id | string | token).
- **NoveltyIndex:** Distributed set (Redis or Postgres) of `shape_hash → first_seen_at`; count of unique shapes per endpoint.

**Key algorithms:**
- **AST construction:** For JSON body, parse and replace literal values with placeholders (e.g. `{ "id": 123 }` → `{ "id": "<INT>" }`). For form-data, same. For URL path, replace numeric/UUID segments with `{id}`. Normalize query keys and treat values as placeholders.
- **Nested encoding:** When a value looks like base64, decode and re-parse; recursively run insertion point extraction on the inner structure. Cap depth (e.g. 3) to avoid DoS.

**Integration:** Consumes `raw_captures` from Kafka (or reads from WARC by ref). Publishes `insertion_points` and updates novelty index. Security test workers subscribe to `insertion_points` and run differential auth tests and payload tests.

**Hard problems:**
- **Opaque binary or custom encoding:** Not every body is JSON. **Solution:** Content-type–driven parsers (JSON, XML, form, multipart). For “application/octet-stream” or unknown, treat entire body as a single insertion point with type “blob” and no nested extraction.
- **CSRF and nonces:** Insertion point extractor should tag tokens that look like CSRF/nonce (e.g. name contains `csrf`, `token`, `nonce`). Test workers must then fetch a fresh token from a designated “token provider” URL before replaying; do not treat these as fuzzable insertion points in the same way as `user_id`.

---

### 2.4 Authenticated Testing and Session Management (Identity Layer)

**Purpose:** Run crawls and tests as multiple roles (admin, user, guest), maintain session health, and support complex login flows (recorded macros, OAuth) so that privileged attack surface is fully covered.

**Technology stack:**
- **Session store:** **Redis** or **Postgres** for session cookies/tokens per (engagement_id, role). Key: `session:{engagement_id}:{role}`; value: JSON of cookies/headers; TTL aligned with engagement.
- **Login automation:** **Playwright** for recording and replay. Record: user performs login in a dedicated browser; script records navigation, form fills, clicks, and final URL/cookies. Replay: same script with parameterized credentials. Store as JSON (or a small DSL) in engagement config.
- **Session health:** After each N requests (or on 401/403), call a **SessionHealthChecker** that requests a known “session check” URL (e.g. `/api/me` or dashboard URL). If response is 401/403 or redirect to login, trigger **SessionRepairRunner** to re-run the login macro and refresh the session store.
- **Differential auth testing:** **ReplayEngine** that, for each (endpoint, method, insertion_point_set), replays the same request with each role’s session and compares responses (status, and optionally structural diff of JSON). Flag when a lower-priv role receives the same success or same data as a higher-priv role (BOLA/IDOR).

**Data model:**
- **TestIdentity:** `role`, `credentials_ref`, `login_sequence_ref`, `session_ref` (pointer to current cookies/tokens).
- **LoginSequence:** `steps`: [ { action: navigate | fill | click | wait }, selector, value_ref ].
- **AuthzInvariant:** `endpoint_pattern`, `role`, `expected` (allow | deny), `source` (observed | configured).

**Key algorithms:**
- **Session repair macro:** Execute login sequence in a headless browser; on “success” (e.g. URL contains dashboard or response sets cookie), extract all cookies and optional auth headers; write to session store and mark session as healthy.
- **Differential comparison:** For each role pair (e.g. admin vs user), replay request as admin, then as user. If user gets 200 and response body “looks like” the same resource (e.g. same JSON keys or same content-length band), mark as potential BOLA and attach both responses as evidence (WARC refs).

**Integration:** Crawl workers request a session handle from Identity Layer before starting a crawl for a given role. All requests from that worker use that session. When SessionHealthChecker fails, Identity Layer runs repair and notifies workers to refresh. Test workers pull (endpoint, insertion_points) from Kafka and pull sessions from Identity Layer for each role.

**Hard problems:**
- **OAuth/SSO:** Full OAuth flow may require a real browser and user interaction for consent. **Solution:** Support “pre-recorded token” in engagement config (paste a refresh token or access token with expiry). Optionally integrate with a headless OAuth library that can do device flow or client-credentials where applicable.
- **CAPTCHA and 2FA:** Recorded login sequences can include a “pause for human” step (manual solve) or integration with a designated CAPTCHA solver service (e.g. 2captcha) only when explicitly configured and in scope.

---

### 2.5 Data Pipeline and Knowledge Graph (Infrastructure Layer)

**Purpose:** Ingest raw captures at scale, deduplicate, enrich, and store in a queryable knowledge graph and evidence store so that every finding is traceable to a WARC capture.

**Technology stack:**
- **Message backbone:** **Apache Kafka**. Topics: `raw_captures`, `parsed_requests`, `insertion_points`, `test_events`, `findings`. Retention 7–30 days depending on engagement.
- **Raw storage:** **WARC (ISO 28500)** written by a dedicated service that consumes `raw_captures` and appends to engagement-scoped WARC files. Store WARC in **S3-compatible object storage** (e.g. MinIO, AWS S3). Content-addressed: optionally segment by `(engagement_id, date, hash_prefix)` for dedup.
- **Structured store:** **PostgreSQL** for endpoints, insertion points, sessions, findings, and audit logs. Schema: endpoints, requests (with warc_ref), insertion_points, findings, engagement_config.
- **Graph store:** **Neo4j** for the knowledge graph. Nodes: Endpoint, Parameter, Role, Session, Finding, WARCRef. Edges: REQUIRES_AUTH, EXPOSES, CONTROLLED_BY_ROLE, INSERTS_INTO, EVIDENCE_IN.
- **Search:** **OpenSearch** (or Elasticsearch) for full-text search over URL paths, response snippets, and finding titles. Index only metadata and truncated snippets; store full content in WARC.
- **Deduplication:** **SimHash** (e.g. 64-bit) for HTML response bodies to drop near-duplicate pages. **MinHash + LSH** for set similarity if you need to cluster “similar” endpoints. Apply before writing to WARC (write one representative capture per cluster and reference it from multiple logical requests).

**Data model (Postgres core):**
- **endpoints:** id, method, url_template, host, classification, sensitivity, auth_required, first_seen, last_seen.
- **requests:** id, endpoint_id, warc_ref, canonical_request_id, role, timestamp.
- **insertion_points:** id, request_id, location, encoding_layers, inferred_type, shape_hash.
- **findings:** id, title, severity, category, asset, evidence_warc_refs [], status, engagement_id.

**Data model (Neo4j):**
- Nodes: `(:Endpoint {id, url_template, method})`, `(:Parameter {name, location})`, `(:Role {name})`, `(:Finding {id, severity})`, `(:WARCRef {id, path})`.
- Edges: `(Endpoint)-[:EXPOSES]->(Parameter)`, `(Endpoint)-[:REQUIRES_AUTH]->(Role)`, `(Finding)-[:EVIDENCE_IN]->(WARCRef)`.

**Key algorithms:**
- **WARC writer:** For each `raw_capture` event, append a WARC record (request block + response block). Generate content-addressed ID (e.g. SHA-256 of request line + first 1KB of body). Link from Postgres and Neo4j via this ID.
- **Enrichment pipeline:** Consume `raw_captures` → content-type detection → security marker extraction (auth headers, Set-Cookie, CSRF token patterns) → insertion point extraction → publish `parsed_requests` and `insertion_points`. Optionally run SimHash and skip storing duplicate body in WARC (store ref to canonical WARC ID).
- **Retention job:** Periodically delete WARC files and DB rows where `created_at < now() - ttl_days` and engagement is closed. Redact response bodies in DB if permitted_data_classes do not include “full_body”.

**Integration:** All crawlers and test workers publish to Kafka. Only the scope-approved requests are written to WARC. Parsing workers are stateless and horizontally scalable. Neo4j is updated by a dedicated “graph builder” consumer that listens to `parsed_requests` and `findings`.

**Hard problems:**
- **Throughput:** At 1000 pages/minute, WARC and Kafka must keep up. **Solution:** Partition Kafka by engagement_id; multiple WARC writer instances per engagement (shard by hash of request_id). Use batching for WARC writes (e.g. buffer 100 records or 10s window).
- **Provenance:** Every finding must point to one or more WARC refs. **Solution:** When a test worker generates a finding, it includes the `request_id` and `response_id` that were used; the pipeline resolves these to WARC refs before writing to DB and report.

---

### 2.6 Reporting and Triage

**Purpose:** Produce executive summary, engineering handoff, evidence pack (with WARC refs), and remediation queue so that developers can fix issues and auditors can verify.

**Technology stack:** Keep existing **reporting** module (Markdown, JSON, CSV, TXT). Extend so that:
- Every finding has `evidence_warc_refs: [ "warc://engagement_id/file.warc.gz#offset_length" ]`.
- **Evidence pack generator:** For each finding, copy the referenced WARC records into a separate “evidence pack” WARC or a ZIP of request/response pairs for that finding.

**Integration:** Reporting reads from Postgres (findings, endpoints) and from WARC (by ref) to build the evidence pack. No new technology required; ensure schema includes `evidence_warc_refs` and that the pipeline populates it.

---

## SECTION 3: PHASED BUILD ROADMAP

| Phase | Name | Deliverables | Dependencies | Complexity | Capability unlocked |
|-------|------|--------------|--------------|------------|---------------------|
| **1** | **MVP: Safe and scoped** | Engagement config schema and loader; ScopeEnforcingClient wrapping all HTTP; per-host rate limit and backoff; WARC writer (single-thread); existing crawl + test + report wired to scope and WARC refs. | None | M | Authorized-only testing; evidence linked to raw captures; no out-of-scope requests. |
| **2** | **Core platform** | Kafka between crawl → parse → test; Insertion point canonicalizer and novelty index; sitemap/wp-json + state-flow crawler (Crawljax-style); multi-identity session pool and session health + repair macro; differential auth testing (replay same request as role A and B, compare). | Phase 1 | L | High coverage crawl; BOLA/IDOR findings with evidence; session-aware recon. |
| **3** | **Advanced** | Neural/semantic prioritisation (frontier PQ with feature vector + optional small classifier); deep web form mining (form discovery + adaptive query caps); API discovery from OpenAPI + traffic; GraphQL introspection and depth limits; Sensitive exposure detection (lexical + optional OCR) gated by relevance. | Phase 2 | L | Prioritised crawl; form-driven discovery; API and GraphQL coverage; PII/secret leak detection. |
| **4** | **Top-tier** | Full Neo4j knowledge graph and Cypher queries; RESTler-style stateful API fuzzing sequences; OCR pipeline for high-risk content; optional Spark batch for historical analysis; engagement-scoped retention and TTL automation. | Phase 3 | XL | Graph-based reasoning; automated API fuzzing; large-scale historical analysis; compliance-ready retention. |

---

## SECTION 4: TECHNOLOGY SELECTION TABLE

| Component | Recommended technology | Why | Alternatives considered |
|-----------|-------------------------|-----|--------------------------|
| Browser automation | Playwright (Python) | Cross-browser, network intercept, stability, good async support. | Selenium (heavier, less modern); Puppeteer (JS-only). |
| Message backbone | Apache Kafka | Durable log, replay, high throughput, decouples producers/consumers. | RabbitMQ (broker model; good for tasks, less for event log); Redis Streams (simpler but less durable). |
| Raw evidence store | WARC (ISO 28500) in S3-compatible storage | Standard, replayable, content-addressable; audit-friendly. | Custom binary format (not standard); DB BLOBs (expensive at scale). |
| Relational store | PostgreSQL | Mature, JSON support, good for endpoints/findings/audit. | MySQL (similar); SQLite (single-node only). |
| Graph store | Neo4j | Property graph model fits endpoints–roles–findings–evidence; Cypher is expressive. | Amazon Neptune (managed); JanusGraph (if you need very large scale). |
| Search | OpenSearch | Full-text over paths/snippets; open-source, compatible with Elasticsearch. | Elasticsearch (same family); Meilisearch (lighter). |
| Session store | Redis | Fast, TTL support for session expiry. | Postgres (simpler but slower for hot path). |
| Prioritisation (Phase 3) | Custom PQ + optional small BERT or sklearn classifier | Burp-like “attack surface + interest”; neural prioritisation from research. | Rule-based only (simpler but less adaptive). |
| Deduplication | SimHash (64-bit) + MinHash/LSH for clustering | Standard in crawl literature; SimHash for near-dup; MinHash for set similarity. | Exact hash only (misses near-dups). |

---

## SECTION 5: THE FIVE HARDEST ENGINEERING CHALLENGES

**1. State explosion in state-flow crawling**  
- **Problem:** SPAs can have millions of possible states; naive Crawljax-style exploration does not finish.  
- **Solution:** Cap total states (e.g. 10k per run). Use a **priority queue** for “which state to expand next” by attack-surface contribution (number of new forms/inputs/links). Use **SimHash** on DOM to merge states that are “visually equivalent” and avoid re-exploring. Prune low-value states (e.g. pure static content) from the frontier.

**2. Nested insertion points and encoding layers**  
- **Problem:** Parameters can be base64(JSON(gzip(data))); missing layers causes under-coverage or broken replay.  
- **Solution:** Pipeline of **encoding detectors** (e.g. try base64 decode and re-parse as JSON; try gzip decompress). Cap recursion depth (e.g. 3). Tag each insertion point with `encoding_layers: ["json", "base64"]`. Replay engine must apply the same layers when generating payloads.

**3. Session repair and login macro reliability**  
- **Problem:** Login flows change (new CAPTCHA, 2FA); recorded macro breaks.  
- **Solution:** Design macros as **step sequences with selectors and value refs**, not raw coordinates. Add “wait for selector” and “assert URL contains” steps. Support **manual pause** step for human intervention (e.g. solve CAPTCHA once). Run a **session check** after repair and retry repair up to N times; if still failing, alert and pause crawl for that role.

**4. Provenance at scale (every finding → WARC ref)**  
- **Problem:** At millions of requests, storing full response in DB is infeasible; yet every finding must point to evidence.  
- **Solution:** Store only **WARC record ID** (file path + offset + length) in the finding. Evidence pack generator **reads on demand** from WARC when building the report. Use content-addressed WARC segment IDs so that dedup does not break refs (one content hash = one WARC segment; multiple logical requests can point to same segment).

**5. Scope enforcement without slowing the pipeline**  
- **Problem:** Checking every URL in a central DB or config could become a bottleneck.  
- **Solution:** **Pre-compile** scope into a fast structure (e.g. list of allowed domain suffixes + list of out-of-scope regexes). Scope validator is a **synchronous in-process function** (no network call). Run it in the client layer before `httpx` or Playwright sends the request. For Playwright, use `page.route()` to intercept and abort out-of-scope navigations before they are sent.

---

## SECTION 6: WHAT MAKES THIS TOP 1% GLOBALLY

- **Authorization as a first-class layer:** Scope and engagement config are not an afterthought; every request is gated. This matches how high-assurance testing is done at enterprises and avoids the “run everything and apologize later” anti-pattern.
- **Evidence-grade archiving (WARC + provenance):** Every finding traces to a WARC capture ID. Reports and evidence packs are reproducible and defensible in audits, matching NIST and professional testing guidance.
- **State-flow crawling plus prioritisation:** Combining Crawljax-style state exploration with **attack-surface–driven prioritisation** (insertion point novelty, role sensitivity) means you cover the high-value states first, not random order. This aligns with Burp’s documented prioritisation and with “Neural Prioritisation for Web Crawling”–style value estimation.
- **Differential authorization testing by design:** Multi-identity session pool + replay engine that compares responses across roles is the standard way to find BOLA/IDOR at scale; building it into the pipeline (not as an ad-hoc script) matches BACScan and OWASP API Security Top 10.
- **Insertion point model and nested encoding:** Explicit AST and insertion point extraction with encoding-layer tracking matches what Burp documents for “nested insertion points.” Few open-source scanners model this as deeply.
- **Modular, event-driven pipeline (Kafka):** Decoupled crawl → parse → test → store allows independent scaling and replay. This is how large-scale crawlers (e.g. Common Crawl–style) and commercial scanners are built.
- **Data minimization and retention:** Default to storing only what’s needed for reproducibility and reporting; WARC and structured data have engagement-scoped TTL. This meets governance and privacy expectations for “authorized testing” and aligns with your deep research report.

---

## Integration with Current Cyber Hunt AI Codebase

To revamp the existing system toward this plan:

1. **Governance:** Add `engagement_config` loader and `ScopeEnforcingClient` in `cyberAI/utils/http_client.py` (or a dedicated `scope.py`). Wire all `AsyncHTTPClient` and Playwright usage through it.
2. **Crawl:** Extend `core_discovery.py` with state-flow logic (DOM hash, transition detection) and feed frontier from sitemap/wp-discovery (already done). Add optional Kafka producer for `raw_captures` if you introduce Kafka.
3. **Insertion points:** Add `cyberAI/recon/insertion_point_extractor.py` (canonicalizer + AST walker). Run it in the pipeline after network intelligence and persist to `recon/intelligence/insertion_points.json` and novelty index.
4. **Auth layer:** Add `cyberAI/identity/` (or under `utils/`) for session pool, login sequence runner, and session health + repair. Integrate with browser pool so crawl and test use per-role sessions.
5. **Differential auth:** Extend `authorization_testing.py` to (a) use only endpoints from recon, (b) replay same request with multiple roles from identity layer, (c) compare responses and attach WARC refs.
6. **WARC:** Add a small `cyberAI/storage/warc_writer.py` that writes request/response pairs to WARC and returns refs; link from `RequestRecord` and from findings.
7. **Reporting:** Extend finding model and report templates to include `evidence_warc_refs` and optional evidence-pack generation that pulls from WARC by ref.

This plan is designed so that a senior team can implement it phase by phase, with clear dependencies and without ambiguity on where scope enforcement, evidence, and prioritisation live.

---

## Research-Backed Capabilities Coverage

| Capability | Where in plan | References |
|------------|----------------|------------|
| 1. Neural/semantic crawl prioritisation | §2.2 (frontier PQ, feature vector); Phase 3 (classifier) | Neural Prioritisation for Web Crawling (2025); Burp audit prioritisation |
| 2. State-flow graph crawling for SPAs | §2.2 (Crawljax-style, DOM hash, transitions) | Crawljax/Mesbah et al.; OWASP ZAP AJAX Spider; your deep research |
| 3. Deep web form mining | §2.2 (form discovery); Phase 3 (adaptive query, caps) | Deep Web Crawling survey; Minimum Executable Pattern; WSTG execution paths |
| 4. Authenticated scanning + session repair | §2.4 (multi-identity, login macro, health, repair) | Burp recorded login + session handling rules; Wapiti advanced crawling |
| 5. API surface discovery | §2.2 (spec + traffic); Phase 3 (OpenAPI, GraphQL, WS) | Burp API scanning; OWASP WSTG metafiles; RESTler |
| 6. Differential authorization testing | §2.4 (replay engine, role-pair comparison) | OWASP WSTG authz; API Top 10 BOLA; BACScan (CCS 2025) |
| 7. Sensitive exposure at scale | Phase 3 (lexical + OCR, gated by relevance) | The Silent Spill (2026); your deep research |
| 8. Evidence-grade archiving (WARC + provenance) | §2.1, §2.5 (WARC writer, content-addressed, retention) | ISO 28500; Common Crawl; NIST SP 800-115 |
