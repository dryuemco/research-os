from pydantic import BaseModel, ConfigDict, Field


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
    recommended_role: str | None = None
    red_flags: list[str] = Field(default_factory=list)
