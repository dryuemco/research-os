from pydantic import BaseModel, ConfigDict, Field


class ProposalSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    opportunity_id: str
    template_type: str
    section_order: list[str]
    page_limit: int | None = None
    mandatory_sections: list[str] = Field(default_factory=list)
    compliance_rules: list[dict] = Field(default_factory=list)


class ProposalSectionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    section_key: str
    draft_text: str
    model_provider: str
    model_name: str
    prompt_version: str
    round_number: int
    status: str


class ReviewScorecard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    round_number: int
    reviewer_role: str
    scores: dict = Field(default_factory=dict)
    major_issues: list[str] = Field(default_factory=list)
    minor_issues: list[str] = Field(default_factory=list)
    must_fix: list[str] = Field(default_factory=list)
    decision_hint: str
