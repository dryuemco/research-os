from sqlalchemy import DateTime, Enum, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base
from app.domain.common.enums import ProviderStatus
from app.domain.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin

JSONType = JSON().with_variant(JSONB, "postgresql")


class ProviderAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "provider_accounts"

    provider_name: Mapped[str] = mapped_column(String(64), index=True)
    account_ref: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[ProviderStatus] = mapped_column(
        Enum(ProviderStatus), default=ProviderStatus.ACTIVE, index=True
    )
    config_json: Mapped[dict] = mapped_column(JSONType)


class ProviderQuotaSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "provider_quota_snapshots"

    provider_name: Mapped[str] = mapped_column(String(64), index=True)
    account_ref: Mapped[str] = mapped_column(String(255), index=True)
    model_name: Mapped[str] = mapped_column(String(128), index=True)
    window_start: Mapped[str] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[str] = mapped_column(DateTime(timezone=True))
    requests_used: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    spend_used: Mapped[float] = mapped_column(Numeric(12, 4), default=0)
    status: Mapped[str] = mapped_column(String(64))
    raw_payload: Mapped[dict] = mapped_column(JSONType)
