from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base
from app.domain.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin

JSONType = JSON().with_variant(JSONB, "postgresql")


class PartnerProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "partner_profiles"

    partner_name: Mapped[str] = mapped_column(String(255), index=True)
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(8), index=True, nullable=True)
    geography_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    organization_type: Mapped[str] = mapped_column(String(64), default="research_org")
    capability_tags: Mapped[list[str]] = mapped_column(JSONType, default=list)
    program_participation: Mapped[list[str]] = mapped_column(JSONType, default=list)
    role_suitability: Mapped[dict] = mapped_column(JSONType, default=dict)
    source_metadata: Mapped[dict] = mapped_column(JSONType, default=dict)
    intelligence_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
