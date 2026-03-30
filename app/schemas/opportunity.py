from pydantic import BaseModel, ConfigDict, Field


class OpportunityNormalized(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_program: str
    source_url: str
    external_id: str
    title: str
    summary: str
    full_text: str
    deadline_at: str | None = None
    call_status: str
    budget_total: float | None = None
    currency: str | None = None
    eligibility_notes: list[str] = Field(default_factory=list)
    expected_outcomes: list[str] = Field(default_factory=list)
    raw_payload: dict = Field(default_factory=dict)
    version_hash: str
