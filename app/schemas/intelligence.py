from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PartnerProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    partner_name: str
    legal_name: str | None = None
    country_code: str | None = None
    geography_notes: str | None = None
    organization_type: str = "research_org"
    capability_tags: list[str] = Field(default_factory=list)
    program_participation: list[str] = Field(default_factory=list)
    role_suitability: dict[str, float] = Field(default_factory=dict)
    source_metadata: dict = Field(default_factory=dict)
    intelligence_notes: str | None = None


class PartnerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    partner_name: str
    legal_name: str | None
    country_code: str | None
    organization_type: str
    capability_tags: list[str]
    program_participation: list[str]
    role_suitability: dict
    source_metadata: dict
    intelligence_notes: str | None
    active: bool
    created_at: datetime


class PartnerFitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required_capabilities: list[str] = Field(default_factory=list)
    preferred_countries: list[str] = Field(default_factory=list)
    target_programme: str | None = None
    desired_roles: list[str] = Field(default_factory=lambda: ["coordinator", "beneficiary"])
    limit: int = 5


class PartnerFitResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    partner: PartnerProfileResponse
    fit_score: float
    role_score: float
    capability_overlap_score: float
    geography_score: float
    complementarity_score: float
    rationale: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)


class QualityIssueCategory(StrEnum):
    RELEVANCE = "relevance"
    CLARITY = "clarity"
    NOVELTY = "novelty"
    FEASIBILITY = "feasibility"
    COMPLIANCE = "compliance"
    COHERENCE = "coherence"
    IMPACT = "impact"
    IMPLEMENTATION = "implementation"


class QualityIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: QualityIssueCategory
    severity: str
    blocker: bool
    issue_text: str
    reviewers: list[str] = Field(default_factory=list)
    priority_score: float


class ProposalQualitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    round_number: int | None = None
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    overall_score: float
    blocker_count: int
    disagreement_count: int
    persistent_red_team_blocker: bool
    top_issues: list[QualityIssue] = Field(default_factory=list)
    next_action_recommendation: str
    rationale: list[str] = Field(default_factory=list)
