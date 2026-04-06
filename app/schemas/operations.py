from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.common.enums import (
    NotificationStatus,
    NotificationType,
    OperationalJobStatus,
    OperationalJobType,
)


class SourceRecordInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_record_id: str
    payload: dict


class TriggerIngestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str
    trigger_source: str = "manual"
    records: list[SourceRecordInput] = Field(default_factory=list)
    run_matching_after: bool = True


class TriggerLiveIngestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    programmes: list[str] = Field(default_factory=lambda: ["horizon", "erasmus+"])
    limit: int = Field(default=50, ge=1, le=100)
    run_matching_after: bool = True


class TriggerMatchingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_id: str
    scoring_policy_id: str = "default-v1"
    opportunity_ids: list[str] | None = None
    trigger_source: str = "manual"


class OperationalJobRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_type: OperationalJobType
    status: OperationalJobStatus
    trigger_source: str
    source_name: str | None
    profile_id: str | None
    result_summary: dict
    error_summary: dict
    created_at: datetime


class MatchingRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    scoring_policy_id: str
    status: OperationalJobStatus
    opportunities_scanned: int
    matches_created: int
    recommendations_count: int
    red_flags_count: int
    summary_json: dict
    created_at: datetime


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    notification_type: NotificationType
    status: NotificationStatus
    recipient_user_id: str
    related_entity_type: str | None
    related_entity_id: str | None
    payload_json: dict
    created_at: datetime
    read_at: datetime | None


class MarkNotificationReadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str


class DemoBootstrapRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm: bool = False
    reset_demo_state: bool = False
    create_demo_proposal: bool = True
    fixture_path: str | None = None
