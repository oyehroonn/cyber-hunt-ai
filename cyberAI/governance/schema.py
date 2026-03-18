"""
Pydantic schema for ASRTS engagement configuration.

Mirrors the YAML/JSON structure in ASRTS Implementation Plan §2.1.
"""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class TestIdentity(BaseModel):
    """Authorized test identity (role) for crawling and testing."""
    role: str
    credentials: dict[str, Any] = Field(default_factory=dict)
    # credentials.type: "recorded_login" | "form_replay" | "oauth"
    # form_replay: username, password
    # recorded_login: login_sequence_ref
    login_sequence_ref: Optional[str] = None


class RateLimits(BaseModel):
    """Rate limits and backoff for polite crawling."""
    per_host_rps: float = Field(default=10.0, description="Max requests per second per host")
    global_rps: Optional[float] = Field(default=None, description="Max requests per second globally")
    backoff_on_5xx: Literal["none", "linear", "exponential"] = "exponential"


class DataRetention(BaseModel):
    """Data retention and permitted data classes."""
    raw_capture_ttl_days: int = Field(default=90, ge=0)
    structured_ttl_days: int = Field(default=365, ge=0)
    permitted_data_classes: list[str] = Field(
        default_factory=lambda: ["request_response_meta", "finding_evidence", "insertion_point_schema"]
    )


class IncidentContact(BaseModel):
    """Contact for incident response."""
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class EngagementConfig(BaseModel):
    """
    Full engagement configuration: scope, identities, rate limits, retention.
    Loaded from YAML/JSON per engagement; enforced on every request.
    """
    engagement_id: str = Field(default="default", description="Engagement identifier")
    name: str = Field(default="", description="Human-readable engagement name")
    target_domains: list[str] = Field(default_factory=list, description="In-scope base URLs")
    out_of_scope_patterns: list[str] = Field(
        default_factory=list,
        description="Glob/regex patterns for URLs that must never be requested",
    )
    allowed_schemes: list[str] = Field(default_factory=lambda: ["https"], description="Allowed URL schemes")
    test_identities: list[TestIdentity] = Field(default_factory=list)
    rate_limits: RateLimits = Field(default_factory=RateLimits)
    data_retention: DataRetention = Field(default_factory=DataRetention)
    incident_contacts: list[IncidentContact] = Field(default_factory=list)

    def is_empty_scope(self) -> bool:
        """True if no target_domains configured (scope not used)."""
        return not self.target_domains
