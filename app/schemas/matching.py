from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InterestProfileParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed_programs: list[str] = Field(default_factory=list)
    blocked_programs: list[str] = Field(default_factory=list)
    required_keywords: list[str] = Field(default_factory=list)
    preferred_keywords: list[str] = Field(default_factory=list)
    min_budget_total: float | None = None
    max_days_to_deadline: int | None = None
    target_roles: list[str] = Field(default_factory=list)
    weights: dict[str, float] = Field(
        default_factory=lambda: {"keyword_overlap": 0.6, "budget_fit": 0.4}
    )


class MatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    profile_id: str
    opportunity_ids: list[str]
    scoring_policy_id: str


class MatchResultSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_id: str
    hard_filter_pass: bool
    hard_filter_reasons: list[str] = Field(default_factory=list)
    scores: dict = Field(default_factory=dict)
    total_score: float
    explanations: list[str] = Field(default_factory=list)
    rationale: dict = Field(default_factory=dict)
    recommendation: str
    recommended_role: str | None = None
    red_flags: list[str] = Field(default_factory=list)


class MatchResultResponse(MatchResultSchema):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    scoring_policy_id: str
    created_at: datetime
