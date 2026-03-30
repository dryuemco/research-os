from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProviderQuotaSnapshotSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_name: str
    account_ref: str
    model_name: str
    window_start: datetime
    window_end: datetime
    requests_used: int
    tokens_used: int
    spend_used: float
    status: str
