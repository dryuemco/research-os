from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.common.enums import OpportunityState


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
    provenance: dict = Field(default_factory=dict)
    uncertainty_notes: list[str] = Field(default_factory=list)


class OpportunityIngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str
    source_record_id: str
    payload: dict


class OpportunityDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    actor_type: str = "user"
    actor_id: str
    reason: str | None = None


class OpportunityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_program: str
    source_url: str
    external_id: str
    title: str
    summary: str
    deadline_at: str | None
    call_status: str
    budget_total: float | None
    currency: str | None
    state: OpportunityState
    current_version_hash: str
    created_at: datetime
    updated_at: datetime
