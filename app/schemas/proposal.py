from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.common.enums import ProposalState


class ProposalWorkspaceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_id: str
    owner_id: str
    name: str
    template_type: str = "generic"
    page_limit: int | None = None
    mandatory_sections: list[str] = Field(default_factory=list)
    compliance_rules: list[dict] = Field(default_factory=list)


class ProposalWorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    owner_id: str
    name: str
    template_type: str
    page_limit: int | None
    state: ProposalState
    latest_version_number: int
    unresolved_issues_json: list[dict]
    human_approved_for_export: bool
    created_at: datetime
    updated_at: datetime


class ConceptNoteInputContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    problem_statement: str
    objectives: list[str] = Field(default_factory=list)
    target_beneficiaries: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class ConceptNoteOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    strategic_fit: str
    impact_thesis: str
    implementation_outline: str
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ProposalSectionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_key: str
    title: str
    objective: str
    max_words: int
    dependencies: list[str] = Field(default_factory=list)


class SectionDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    section_key: str
    context_refs: list[str] = Field(default_factory=list)
    writer_policy_id: str
    round_number: int = 1


class SectionDraftResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    section_key: str
    draft_text: str
    model_provider: str
    model_name: str
    prompt_version: str
    round_number: int
    status: str


class ReviewerFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_round_id: str
    reviewer_role: str
    severity: str
    blocker: bool = False
    issue_code: str | None = None
    comment_text: str
    scores: dict[str, float] = Field(default_factory=dict)
    must_fix: list[str] = Field(default_factory=list)


class UnresolvedIssueLog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_code: str
    role: str
    details: str
    blocker: bool


class ConvergenceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    should_stop: bool
    decision: str
    reason: str
    unresolved_issues: list[UnresolvedIssueLog] = Field(default_factory=list)


class ReviewRoundCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    reviewer_roles: list[str]


class ReviewRoundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    proposal_id: str
    round_number: int
    status: str
    reviewer_roles: list[str]
    convergence_decision: str | None
    stop_reason: str | None


class ProposalSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    opportunity_id: str
    template_type: str
    section_order: list[str]
    page_limit: int | None = None
    mandatory_sections: list[str] = Field(default_factory=list)
    compliance_rules: list[dict] = Field(default_factory=list)
