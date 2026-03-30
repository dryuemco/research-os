from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditEventSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str
    entity_type: str
    entity_id: str
    actor_type: str
    actor_id: str
    payload: dict = Field(default_factory=dict)
    created_at: datetime | None = None
