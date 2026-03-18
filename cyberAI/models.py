"""
Pydantic v2 data models for the CyberAI reconnaissance and vulnerability testing platform.
All modules use these shared models for consistent data persistence.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from uuid import uuid4


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class EndpointClassification(str, Enum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ADMIN = "admin"
    AUTH = "auth"
    BILLING = "billing"
    FILES = "files"
    EXPORTS = "exports"
    OTHER = "other"


class SensitivityLabel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    PUBLIC = "public"


class FindingStatus(str, Enum):
    CONFIRMED = "confirmed"
    LIKELY = "likely"
    NEEDS_MORE_DATA = "needs_more_data"
    FALSE_POSITIVE = "false_positive"


class TestCategory(str, Enum):
    AUTH = "auth"
    AUTHZ = "authz"
    BUSINESS_LOGIC = "business_logic"
    INPUT = "input"
    MASS_ASSIGNMENT = "mass_assignment"
    RACE = "race"
    MULTI_SESSION = "multi_session"
    STORED_PAYLOAD = "stored_payload"
    FILE_UPLOAD = "file_upload"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    ASYNC = "async"
    SEARCH = "search"
    EXPORT_IMPORT = "export_import"
    BILLING = "billing"
    NOTIFICATION = "notification"
    CONFIG = "config"


class ImpactType(str, Enum):
    CONFIDENTIALITY = "confidentiality"
    INTEGRITY = "integrity"
    AVAILABILITY = "availability"
    FINANCIAL = "financial"
    COMPLIANCE = "compliance"


class BaseMeta(BaseModel):
    """Metadata included in all output files."""
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    target_url: str = ""
    phase: str = ""
    version: str = "1.0.0"
    run_id: str = Field(default_factory=lambda: str(uuid4()))


class Action(BaseModel):
    """Represents a UI action (button, link, form submit)."""
    action_type: str  # click, submit, navigate, toggle
    selector: str
    text: Optional[str] = None
    href: Optional[str] = None
    form_fields: list[str] = Field(default_factory=list)


class Route(BaseModel):
    """Represents a discovered application route/page."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    slug: str
    url: str
    method: HttpMethod = HttpMethod.GET
    screenshot_path: Optional[str] = None
    dom_path: Optional[str] = None
    actions: list[Action] = Field(default_factory=list)
    linked_requests: list[str] = Field(default_factory=list)  # endpoint IDs
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    role_context: Optional[str] = None
    state_context: Optional[str] = None
    page_title: Optional[str] = None
    is_hidden: bool = False
    source: str = "crawl"  # crawl, js_bundle, graphql, etc.
    raw_state: Optional[dict[str, Any]] = None  # Page state indicators from _detect_page_state
    modals_found: int = 0  # Count of modals/drawers discovered on this page


class FieldSchema(BaseModel):
    """Schema for a single field in request/response."""
    name: str
    field_type: str  # string, integer, boolean, array, object, enum
    required: bool = False
    enum_values: list[Any] = Field(default_factory=list)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    nested_schema: Optional[dict[str, Any]] = None
    is_hidden: bool = False  # Present in API but not UI


class Endpoint(BaseModel):
    """Represents a discovered API endpoint."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    method: HttpMethod
    url: str
    path_pattern: Optional[str] = None  # /api/users/{id}
    params: dict[str, FieldSchema] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    body_schema: list[FieldSchema] = Field(default_factory=list)
    response_schema: list[FieldSchema] = Field(default_factory=list)
    auth_context: Optional[str] = None  # none, session, bearer, api_key
    sensitivity_label: SensitivityLabel = SensitivityLabel.LOW
    classification: EndpointClassification = EndpointClassification.OTHER
    rate_limited: bool = False
    rate_limit_info: Optional[dict[str, Any]] = None
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = "intercept"
    role_access: dict[str, bool] = Field(default_factory=dict)  # role -> can_access


class RequestRecord(BaseModel):
    """Full capture of an HTTP request/response pair."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    method: HttpMethod
    url: str
    final_url: Optional[str] = None
    redirect_chain: list[dict[str, Any]] = Field(default_factory=list)  # [{status_code, url, location}]
    headers: dict[str, str] = Field(default_factory=dict)
    cookies: dict[str, str] = Field(default_factory=dict)
    body: Optional[str] = None
    body_json: Optional[dict[str, Any]] = None
    response_status: int
    response_content_type: Optional[str] = None
    response_headers: dict[str, str] = Field(default_factory=dict)
    response_body: Optional[str] = None
    response_json: Optional[dict[str, Any]] = None
    response_body_hash: Optional[str] = None
    response_body_preview: Optional[str] = None  # truncated preview for quick triage
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    role_context: Optional[str] = None
    state_context: Optional[str] = None
    duration_ms: Optional[float] = None
    endpoint_id: Optional[str] = None
    warc_ref: Optional[str] = None  # WARC capture ID for evidence (ASRTS)


class CanonicalRequest(BaseModel):
    """Normalized request structure for insertion point extraction (ASRTS)."""
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    method: str
    url_template: str  # path with {id} placeholders
    query_params: list[dict[str, str]] = Field(default_factory=list)  # [{name, value_placeholder}]
    headers: dict[str, str] = Field(default_factory=dict)
    body_ast: Optional[dict[str, Any]] = None  # tree with placeholders
    warc_ref: Optional[str] = None


class InsertionPoint(BaseModel):
    """A single place where user input is accepted (ASRTS)."""
    request_id: str
    location: str  # e.g. path_segment_2, query.q, body.user.id, header.X-Role
    encoding_layers: list[str] = Field(default_factory=list)  # e.g. ["json", "base64"]
    inferred_type: str = "string"  # id, string, token, etc.


class CrawlState(BaseModel):
    """Single state in state-flow (Crawljax-style) crawl (ASRTS §2.3)."""
    state_id: str
    dom_hash: str
    url: str
    warc_ref: Optional[str] = None
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    screenshot_path: Optional[str] = None
    dom_path: Optional[str] = None


class CrawlTransition(BaseModel):
    """Edge: from_state -> to_state via event (ASRTS §2.3)."""
    from_state_id: str
    to_state_id: str
    event_type: str  # click, submit, input
    selector: Optional[str] = None
    payload_preview: Optional[str] = None


class ObjectField(BaseModel):
    """Represents a field in an object model."""
    name: str
    field_type: str
    is_sensitive: bool = False
    is_identifier: bool = False
    is_ownership: bool = False


class ObjectModel(BaseModel):
    """Represents a discovered resource/object type."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    id_format: str  # uuid, integer, slug, custom
    ownership_fields: list[str] = Field(default_factory=list)  # e.g., user_id, org_id
    parent_relationships: dict[str, str] = Field(default_factory=dict)  # field -> parent_type
    readable_fields: list[ObjectField] = Field(default_factory=list)
    writable_fields: list[ObjectField] = Field(default_factory=list)
    sensitive_fields: list[str] = Field(default_factory=list)
    lifecycle_states: list[str] = Field(default_factory=list)
    linked_objects: list[str] = Field(default_factory=list)
    security_criticality: str = "low"  # high, medium, low
    endpoints: list[str] = Field(default_factory=list)  # endpoint IDs


class PermissionEntry(BaseModel):
    """Single permission matrix entry."""
    role: str
    object_type: str
    action: str
    allowed: Optional[bool] = None  # None = unknown
    source: str = "inferred"  # inferred, observed, tested
    evidence: Optional[str] = None


class PermissionMatrix(BaseModel):
    """Full permission matrix for all roles/objects/actions."""
    entries: list[PermissionEntry] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    objects: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    unknown_count: int = 0
    
    def get_permission(self, role: str, obj: str, action: str) -> Optional[bool]:
        for entry in self.entries:
            if entry.role == role and entry.object_type == obj and entry.action == action:
                return entry.allowed
        return None


class WorkflowNode(BaseModel):
    """Node in a workflow state graph."""
    id: str
    state: str
    description: Optional[str] = None
    is_initial: bool = False
    is_terminal: bool = False
    required_role: Optional[str] = None


class WorkflowEdge(BaseModel):
    """Edge/transition in a workflow state graph."""
    from_state: str
    to_state: str
    action: str
    preconditions: list[str] = Field(default_factory=list)
    endpoint_id: Optional[str] = None
    is_reversible: bool = True
    requires_approval: bool = False
    requires_payment: bool = False


class WorkflowGraph(BaseModel):
    """Complete workflow state machine."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    object_type: Optional[str] = None
    suspicious_transitions: list[str] = Field(default_factory=list)


class TestPrecondition(BaseModel):
    """Precondition required for a test."""
    description: str = ""
    setup_steps: list[str] = Field(default_factory=list)
    required_accounts: list[str] = Field(default_factory=list)
    required_data: dict[str, Any] = Field(default_factory=dict)


class TestPlan(BaseModel):
    """Planned security test case."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    category: TestCategory
    name: str
    description: str
    target_endpoint: Optional[str] = None
    target_object: Optional[str] = None
    target_role: Optional[str] = None
    required_state: Optional[str] = None
    preconditions: TestPrecondition = Field(default_factory=TestPrecondition)
    expected_safe_behavior: str
    attack_vector: str
    payloads: list[str] = Field(default_factory=list)
    confidence_score: float = 0.5  # 0-1, based on recon signal strength
    priority: int = 5  # 1-10
    is_destructive: bool = False
    is_noisy: bool = False
    is_state_altering: bool = False
    estimated_requests: int = 1
    rollback_strategy: Optional[str] = None


class ReproductionStep(BaseModel):
    """Single step in reproducing a finding."""
    step_number: int
    action: str
    request: Optional[RequestRecord] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    screenshot_path: Optional[str] = None


class Finding(BaseModel):
    """Security finding from testing phase."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    severity: Severity
    category: TestCategory
    asset: str  # affected endpoint/object
    affected_roles: list[str] = Field(default_factory=list)
    affected_states: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    reproduction_steps: list[ReproductionStep] = Field(default_factory=list)
    request_proof: Optional[RequestRecord] = None
    response_proof: Optional[str] = None
    before_state: Optional[dict[str, Any]] = None
    after_state: Optional[dict[str, Any]] = None
    reliability_score: float = 0.0  # 0-100
    root_cause: Optional[str] = None
    impact_types: list[ImpactType] = Field(default_factory=list)
    cvss_score: Optional[float] = None
    cwe_id: Optional[str] = None
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    test_plan_id: Optional[str] = None
    raw_evidence: dict[str, Any] = Field(default_factory=dict)
    evidence_warc_refs: list[str] = Field(default_factory=list)  # WARC refs for evidence pack (ASRTS)


class VerifiedFinding(Finding):
    """Finding that has passed verification."""
    verification_method: str = ""
    confirmed_impact: str = ""
    exploit_chain: list[str] = Field(default_factory=list)
    breadth: str = ""  # single-object, multi-object, tenant-wide
    alternative_paths: list[str] = Field(default_factory=list)
    timing_sensitivity: Optional[str] = None
    environment_requirements: list[str] = Field(default_factory=list)
    false_positive_ruled_out: bool = False
    cross_role_confirmed: bool = False
    cross_tenant_confirmed: bool = False
    status: FindingStatus = FindingStatus.CONFIRMED
    verified_at: datetime = Field(default_factory=datetime.utcnow)


class PatternCluster(BaseModel):
    """Group of findings with common root cause."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    pattern_name: str
    root_cause: str
    finding_ids: list[str] = Field(default_factory=list)
    affected_endpoints: list[str] = Field(default_factory=list)
    recommended_fix: str
    fix_complexity: str  # low, medium, high


class RemediationItem(BaseModel):
    """Remediation recommendation for a finding."""
    finding_id: str
    priority: int
    fix_description: str
    code_pointers: list[str] = Field(default_factory=list)
    verification_steps: list[str] = Field(default_factory=list)
    estimated_effort: str  # hours, days, weeks
    requires_architecture_change: bool = False


class Report(BaseModel):
    """Complete security assessment report."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    target_url: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    run_id: str
    findings: list[VerifiedFinding] = Field(default_factory=list)
    executive_summary: str = ""
    engineering_pack: str = ""
    pattern_clusters: list[PatternCluster] = Field(default_factory=list)
    remediation_queue: list[RemediationItem] = Field(default_factory=list)
    total_endpoints_tested: int = 0
    total_tests_run: int = 0
    coverage_percentage: float = 0.0
    severity_breakdown: dict[str, int] = Field(default_factory=dict)


class GraphQLOperation(BaseModel):
    """GraphQL operation discovered during recon."""
    name: str
    operation_type: str  # query, mutation, subscription
    fields: list[str] = Field(default_factory=list)
    arguments: dict[str, str] = Field(default_factory=dict)
    requires_auth: bool = True
    role_access: dict[str, bool] = Field(default_factory=dict)


class GraphQLIntel(BaseModel):
    """GraphQL intelligence from discovery."""
    endpoint_url: str
    introspection_enabled: bool = False
    schema_path: Optional[str] = None
    operations: list[GraphQLOperation] = Field(default_factory=list)
    supports_batching: bool = False
    supports_aliases: bool = True
    depth_limit: Optional[int] = None
    cost_limit: Optional[int] = None
    sensitive_fields: list[str] = Field(default_factory=list)


class WebSocketEvent(BaseModel):
    """WebSocket event/message captured."""
    event_type: str  # connect, message, disconnect, error
    direction: str  # inbound, outbound
    channel: Optional[str] = None
    room_id: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WebSocketIntel(BaseModel):
    """WebSocket endpoint intelligence."""
    endpoint_url: str
    auth_mechanism: str  # none, header, query_param, message
    auth_enforced_at: str  # connect, subscribe, per_event
    events_observed: list[WebSocketEvent] = Field(default_factory=list)
    channels_discovered: list[str] = Field(default_factory=list)
    room_id_format: Optional[str] = None
    requires_auth: bool = True


class AsyncFlow(BaseModel):
    """Async/background flow discovered."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    trigger_endpoint: str
    job_id_format: str  # uuid, sequential, random_short
    polling_endpoint: Optional[str] = None
    result_url_pattern: Optional[str] = None
    expiry_seconds: Optional[int] = None
    is_guessable: bool = False
    signed_url_pattern: Optional[str] = None


class SecurityControl(BaseModel):
    """Security control observation."""
    control_type: str  # csp, hsts, cors, csrf, cookie_flags, rate_limit
    present: bool
    value: Optional[str] = None
    is_weak: bool = False
    weakness_reason: Optional[str] = None
    affected_endpoints: list[str] = Field(default_factory=list)


class SecurityControlsReport(BaseModel):
    """Aggregated security controls report."""
    controls: list[SecurityControl] = Field(default_factory=list)
    csp_policy: Optional[str] = None
    cors_origins: list[str] = Field(default_factory=list)
    csrf_mechanism: Optional[str] = None
    token_storage: Optional[str] = None  # localStorage, sessionStorage, httpOnly_cookie
    missing_controls: list[str] = Field(default_factory=list)
    weak_controls: list[str] = Field(default_factory=list)


class SensitiveSurface(BaseModel):
    """Sensitive endpoint/path discovered."""
    path: str
    status_code: int
    response_size: int
    redirect_target: Optional[str] = None
    leaks_metadata: bool = False
    metadata_leaked: list[str] = Field(default_factory=list)
    classification: str  # RESPONDS, REDIRECTS, BLOCKS, LEAKS_METADATA, OPEN


class RoleDiff(BaseModel):
    """Difference between roles for an endpoint."""
    endpoint_id: str
    endpoint_url: str
    roles_with_access: list[str] = Field(default_factory=list)
    roles_without_access: list[str] = Field(default_factory=list)
    field_differences: dict[str, dict[str, list[str]]] = Field(default_factory=dict)  # role -> {extra_fields, missing_fields}
    button_differences: dict[str, list[str]] = Field(default_factory=dict)  # role -> visible_buttons


class StateDiff(BaseModel):
    """Difference between account states."""
    state: str
    available_actions: list[str] = Field(default_factory=list)
    available_endpoints: list[str] = Field(default_factory=list)
    visible_ui_elements: list[str] = Field(default_factory=list)
    transitions_allowed: list[str] = Field(default_factory=list)


class InputSchema(BaseModel):
    """Input schema for an endpoint with mutation inventory."""
    endpoint_id: str
    endpoint_url: str
    fields: list[FieldSchema] = Field(default_factory=list)
    client_validation: dict[str, str] = Field(default_factory=dict)  # field -> validation_rule
    server_accepts_extra: bool = False
    hidden_fields: list[str] = Field(default_factory=list)
    mutation_candidates: list[str] = Field(default_factory=list)


class ComparisonResult(BaseModel):
    """Result of cross-role/state comparison."""
    action: str
    endpoint: str
    role_results: dict[str, dict[str, Any]] = Field(default_factory=dict)
    state_results: dict[str, dict[str, Any]] = Field(default_factory=dict)
    timing_differences: dict[str, float] = Field(default_factory=dict)
    anomalies: list[str] = Field(default_factory=list)


class MasterIntelligence(BaseModel):
    """Aggregated intelligence from all recon phases."""
    meta: BaseMeta = Field(default_factory=BaseMeta)
    routes: list[Route] = Field(default_factory=list)
    endpoints: list[Endpoint] = Field(default_factory=list)
    objects: list[ObjectModel] = Field(default_factory=list)
    permission_matrix: PermissionMatrix = Field(default_factory=PermissionMatrix)
    workflows: list[WorkflowGraph] = Field(default_factory=list)
    graphql_intel: Optional[GraphQLIntel] = None
    websocket_intel: list[WebSocketIntel] = Field(default_factory=list)
    async_flows: list[AsyncFlow] = Field(default_factory=list)
    security_controls: SecurityControlsReport = Field(default_factory=SecurityControlsReport)
    sensitive_surfaces: list[SensitiveSurface] = Field(default_factory=list)
    role_diffs: list[RoleDiff] = Field(default_factory=list)
    state_diffs: list[StateDiff] = Field(default_factory=list)
    input_schemas: list[InputSchema] = Field(default_factory=list)
    hidden_routes: list[Route] = Field(default_factory=list)
    comparison_results: list[ComparisonResult] = Field(default_factory=list)


class LearningLoopEntry(BaseModel):
    """Entry in the learning loop for improving future scans."""
    bug_class: str
    payload: Optional[str] = None
    endpoint_pattern: Optional[str] = None
    success_rate: float = 0.0
    last_successful: Optional[datetime] = None
    notes: str = ""


class LearningLoop(BaseModel):
    """Aggregated learning from successful findings."""
    entries: list[LearningLoopEntry] = Field(default_factory=list)
    high_signal_endpoints: list[str] = Field(default_factory=list)
    effective_payloads: dict[str, list[str]] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
