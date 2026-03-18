# ASRTS Concepts Glossary — 100% Understanding

Every term, concept, and line in the ASRTS Implementation Plan is defined here so implementation can be done without ambiguity. Read this before coding.

---

## A

**Abstract Syntax Tree (AST)**  
A tree representation of a request’s structure. For HTTP: URL → segments; query → key/value pairs; body → typed tree (e.g. JSON nodes). Each node can be a literal value or a placeholder (insertion point). Used to find every place where user input is accepted.

**Attack surface**  
The set of all ways an attacker could interact with the app: URLs, forms, API parameters, headers, cookies. “100% of the web” in scope means discovering and mapping this set as completely as possible within authorization limits.

**Authorization (vs authentication)**  
Authentication = who you are (login). Authorization = what you’re allowed to do (permissions). The platform must enforce **authorization** of the **engagement** (what we’re allowed to test), not just user login.

**Authorized testing**  
Testing only targets and data that are explicitly in-scope and permitted by the engagement config. Every request is checked against scope before being sent.

---

## B

**BOLA (Broken Object Level Authorization)**  
When User A can access User B’s object by changing an ID in the request. Same idea as IDOR. Detected by replaying the same request with different roles and comparing responses.

**Burp-style prioritisation**  
Prioritising crawl/audit by (1) **attack surface exposure** (how many unique insertion points) and (2) **interest level** (sensitivity of the endpoint). Implemented as a priority queue with a score per URL/action.

---

## C

**Canonical request**  
A normalised representation of an HTTP request: method, URL template (e.g. `/api/users/{id}`), query params as (name, placeholder), headers, body as AST. Used so we can compare “same” request across roles and sessions.

**Content-addressed storage**  
Identifying content by its hash (e.g. SHA-256). Same content → same ID. Used for WARC segments so deduplication doesn’t break references (many requests can point to one WARC record).

**Crawljax / state-flow crawling**  
Treating the app as a **state machine**: each “state” is a DOM snapshot (hashed); each “transition” is an event (click, submit). We discover states by firing events and seeing if the DOM hash changes. This finds SPA content that link-following misses.

**Crawl frontier**  
The queue of URLs or actions (e.g. “click button X on state Y”) not yet visited. In ASRTS this is a **priority queue**: higher attack-surface value is processed first.

---

## D

**Data minimization**  
Storing only what’s needed for (1) reproducing a finding, (2) reporting, (3) proving remediation. Full response bodies go to WARC; DB holds metadata, hashes, and WARC refs.

**Differential authorization testing**  
For the same request (same URL, same params), send it as Role A and as Role B. Compare responses. If a lower-priv role gets the same success or same data, that’s a BOLA/IDOR finding. Only with synthetic/test objects, never real user data.

**DOM hash**  
A hash (e.g. SHA-256) of the “meaningful” part of the DOM (structure and text), with dynamic bits (timestamps, random IDs) stripped. Two pages with the same DOM hash are treated as the same **state** for state-flow crawling.

**Deep web (in our context)**  
Content reachable only after submitting forms (e.g. search). Discovered by form discovery + adaptive query generation, with rate and result-size caps so we don’t DoS the target.

---

## E

**Engagement**  
A single authorised testing assignment. Has one **engagement config** (scope, identities, rate limits, retention). All crawls and tests are scoped to one engagement.

**Engagement config**  
YAML/JSON that defines: in-scope/out-of-scope URLs, test identities (roles + login), rate limits, data retention, incident contacts. Loaded once per run and enforced on every request.

**Endpoint**  
A single API “address”: method + path pattern (e.g. `GET /api/users/{id}`). Discovered by crawl, OpenAPI, or traffic. Has associated insertion points and optional role requirements.

**Evidence pack**  
A bundle (ZIP or WARC) containing only the request/response pairs (WARC refs) that prove a finding. Used for handoff to developers and auditors.

**Evidence-grade / provenance**  
Every finding points to one or more **WARC capture IDs**. Anyone can re-open the WARC and see the exact request/response. “Evidence-grade” means legally and technically reproducible.

**Execution path (OWASP WSTG)**  
A sequence of steps (pages, clicks, API calls) that the user or app can take. Mapping execution paths = understanding all reachable flows; our state-flow graph and route/transition models do this.

---

## F

**Feature vector (for prioritisation)**  
A list of numbers describing a frontier item: e.g. insertion-point count, depth, content-type score, role sensitivity. The **priority score** is a weighted sum of this vector. Used in neural/semantic prioritisation.

**Finding**  
A security issue identified by the platform (e.g. BOLA, IDOR). Must include **evidence_warc_refs** so the exact request/response can be retrieved.

**Form mining (deep web)**  
Discovering forms (search, filters), then submitting **adaptive queries** (based on what we’ve seen) to expose more endpoints/data. We cap rate and result size to avoid DoS.

**Frontier**  
Same as **crawl frontier**: the priority queue of work to do next in the crawler.

---

## G

**Governance layer**  
The part of the system that enforces **authorization and scope**: engagement config, scope validator, data retention. Nothing runs without passing this layer.

**Graph (knowledge graph)**  
Neo4j-style model: **nodes** (Endpoint, Parameter, Role, Finding, WARCRef) and **edges** (REQUIRES_AUTH, EXPOSES, EVIDENCE_IN). Used to query “all endpoints that require admin” or “all findings with evidence in this WARC file”.

---

## I

**Identity layer**  
Manages **test identities** (roles): credentials, login sequences, session pool, session health, session repair. Crawl and test workers get a session per role from here.

**Insertion point**  
Any place in an HTTP request where user (or attacker) input is accepted: path segment, query param, body field, header, cookie. The platform enumerates all of these and tracks **encoding layers** (e.g. JSON then base64).

**Insertion point shape**  
A fingerprint of the set of insertion points for a request: e.g. hash of (method, path_template, set of param names). Used for **novelty**: have we seen this shape before? New shapes get higher priority.

**In-scope / out-of-scope**  
In-scope = domain/URL pattern allowed by engagement config. Out-of-scope = explicitly forbidden (e.g. production payment URL). Out-of-scope requests are dropped and logged, never sent.

---

## K

**Kafka**  
Message backbone. Topics: `raw_captures`, `parsed_requests`, `insertion_points`, `test_events`, `findings`. Producers (crawlers, test workers) publish; consumers (parsers, WARC writer, graph builder) subscribe. Decouples stages and allows replay.

**Knowledge graph**  
The Neo4j (or equivalent) store of nodes and edges linking endpoints, parameters, roles, sessions, findings, and WARC refs. Enables “show me everything that requires admin” or “all evidence for this finding”.

---

## L

**Login sequence / login macro**  
A recorded series of steps (navigate, fill, click, wait) that logs in a test user. Stored in engagement config and replayed by **session repair** when the session expires. Like Burp’s “recorded login sequence”.

**LSH (Locality-Sensitive Hashing)**  
Used with **MinHash** to quickly find similar sets (e.g. similar pages). Helps deduplicate and cluster at scale.

---

## M

**MinHash**  
A technique to estimate how similar two sets are (e.g. two response bodies). Used for deduplication and clustering. Often combined with LSH.

**Multi-identity**  
Testing with several roles (e.g. guest, user, admin). Each role has its own session and its own view of the app; **differential auth testing** compares across roles.

---

## N

**Neural prioritisation**  
Using a small ML model (e.g. classifier on HTML or URL) to score “security relevance” or “expected insertion points” before fully crawling. That score feeds the **frontier priority queue**. Based on “Neural Prioritisation for Web Crawling” (2025).

**Novelty index**  
A store (Redis or Postgres) of **insertion point shapes** we’ve already seen. When a new request has a new shape, we mark it novel and boost its priority; this maximises coverage of *distinct* attack surface.

**Novelty (of a request/endpoint)**  
Whether this exact “shape” (method + path template + param set) has been seen before. High novelty = high priority for crawl and test.

---

## O

**Out-of-scope**  
See **In-scope / out-of-scope**.

---

## P

**Payload surface**  
The union of all **insertion points** across the app. “Maximising payload surface coverage” = finding and testing every place that accepts input.

**Policy enforcement**  
Applying the engagement config to every action: scope check before request, retention rules on storage. Implemented in the **scope validator** and **data retention controller**.

**Priority queue (frontier)**  
Crawl work is a heap: we always take the item with the **highest priority score** (attack surface, novelty, role sensitivity). This gives “20x” better coverage per unit time than BFS.

**Provenance**  
Traceability from a finding back to the exact **WARC** capture(s). Every finding has `evidence_warc_refs`.

---

## R

**Rate limit (our side)**  
We throttle ourselves: per-host RPS, global RPS, backoff on 5xx. Protects the target and keeps us within engagement rules.

**Request canonicalization**  
Converting a raw HTTP request into a **canonical request** (AST, URL template, placeholders). Same logical request always produces the same canonical form.

**Replay (request)**  
Sending the same request again, possibly with a different session (different role). Used for **differential authorization testing**.

**Retention (data)**  
How long we keep WARC and DB rows. Defined per engagement (`raw_capture_ttl_days`, `structured_ttl_days`). A **retention job** deletes or redacts data past TTL.

**Role**  
A test identity: e.g. admin, user, guest. Each has credentials and a session. We compare behaviour across roles to find BOLA/IDOR.

---

## S

**Scope**  
What we’re allowed to test: domains, URL patterns. **Scope validator** checks every URL against engagement config; out-of-scope = drop + log.

**ScopeEnforcingClient**  
A wrapper around our HTTP client (e.g. httpx, or the client used by Playwright) that calls the scope validator before every request. If out-of-scope, the request is not sent.

**Security marker**  
A piece of data extracted from a response that matters for security: auth token, CSRF token, role indicator, Set-Cookie, error signature, stack trace. Extracted in the enrichment pipeline.

**Session health**  
Whether the current session (cookies/tokens) is still valid. Checked by requesting a known “session check” URL (e.g. `/api/me`). If 401/403 or redirect-to-login → **session repair**.

**Session repair**  
When a session is invalid, re-run the **login macro** to get fresh cookies/tokens and update the session store. Crawl and test workers then continue with the new session.

**SimHash**  
A fingerprint that makes similar content get similar hashes. Used to detect **near-duplicate** pages so we don’t store and process the same content repeatedly.

**State (UI state)**  
In state-flow crawling, a “state” is a distinct DOM snapshot (identified by **DOM hash**). The app moves from state to state via events (click, submit).

**State-flow graph**  
Graph where nodes = **states** (DOM hashes), edges = events that caused a transition. Built by Crawljax-style exploration. Enables “explore 100% of reachable UI” within caps.

**State transition**  
Firing an event (e.g. click) and observing a new **DOM hash**. If the hash changed, we have a transition to a new state.

---

## T

**Test identity**  
Same as **role**: one authorised account we use for testing (e.g. role_user, role_admin). Stored in engagement config; session stored in Redis/Postgres.

**Traffic-driven discovery**  
Finding API endpoints by observing browser network traffic (XHR/fetch) during a Playwright crawl. Complements **spec-driven** (OpenAPI/GraphQL introspection) discovery.

---

## W

**WARC (Web ARChive format, ISO 28500)**  
Standard format for storing HTTP request/response pairs. Each record has headers and payload. Used by the Internet Archive and Common Crawl. We write every scope-approved capture to WARC and reference by ID from findings.

**WARC ref / WARC capture ID**  
An identifier for a single WARC record (e.g. file path + offset + length, or content-addressed ID). Stored in `evidence_warc_refs` on a finding so we can retrieve the exact evidence later.

**WARC writer**  
Service or module that consumes `raw_captures` (from Kafka or in-process), writes request+response to a WARC file, and returns the WARC ref. Writes to object storage (S3-compatible) in production.

---

## How this ties to “mining more data” and “100% of the web”

- **Scope + governance** → We only mine **in-scope** targets; no accidental out-of-scope traffic.
- **State-flow + browser crawl** → We reach SPA and JS-rendered content (most of “the web” today), not just static links.
- **Frontier priority queue + novelty** → We spend effort on high-value, not-yet-seen surfaces first, so we get **more unique data** per run.
- **Insertion point mapping** → We know **every** place to test; no blind spots.
- **Multi-identity + differential auth** → We mine and test **authenticated** and **role-specific** surfaces, where most critical bugs are.
- **WARC + provenance** → Every mined request/response is stored once and referenced everywhere; we can analyse and re-analyse without re-crawling.
- **Deduplication (SimHash/MinHash)** → We store one canonical copy per “same” content, so storage stays bounded while we crawl “100%” of reachable states.

Implementing the ASRTS plan end-to-end means implementing each of these concepts in code and wiring them so the system mines maximum reliable data, explores up to 100% of the in-scope app, and dumps everything into a structured, evidence-linked store for enterprise-grade security testing.
