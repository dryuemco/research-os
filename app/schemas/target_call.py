from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.common.enums import TargetCallStatus


class TargetCallCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    programme: str = Field(min_length=1)
    call_url: str | None = None
    call_identifier: str | None = None
    deadline_at: datetime | None = None
    raw_call_text: str | None = None
    summary: str | None = None
    status: TargetCallStatus = TargetCallStatus.DRAFT

    @model_validator(mode="after")
    def validate_source_present(self) -> "TargetCallCreateRequest":
        if not self.call_url and not self.raw_call_text:
            raise ValueError("Either call_url or raw_call_text must be provided")
        return self


class TargetCallUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1)
    programme: str | None = Field(default=None, min_length=1)
    call_url: str | None = None
    call_identifier: str | None = None
    deadline_at: datetime | None = None
    raw_call_text: str | None = None
    summary: str | None = None
    status: TargetCallStatus | None = None

    @model_validator(mode="after")
    def validate_non_empty(self) -> "TargetCallUpdateRequest":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self


class TargetCallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    programme: str
    call_url: str | None
    call_identifier: str | None
    deadline_at: datetime | None
    raw_call_text: str | None
    summary: str | None
    status: TargetCallStatus
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime
