from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.domain.common.enums import OpportunityState
from app.domain.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin

JSONType = JSON().with_variant(JSONB, "postgresql")


class InterestProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interest_profiles"

    user_id: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(255))
    parameters_json: Mapped[dict] = mapped_column(JSONType)
    active_version: Mapped[int] = mapped_column(Integer, default=1)


class Opportunity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "opportunities"

    source_program: Mapped[str] = mapped_column(String(100), index=True)
    source_url: Mapped[str] = mapped_column(String(1024))
    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512))
    summary: Mapped[str] = mapped_column(Text)
    deadline_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    call_status: Mapped[str] = mapped_column(String(64), default="discovered")
    budget_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    state: Mapped[OpportunityState] = mapped_column(
        Enum(OpportunityState), default=OpportunityState.DISCOVERED, index=True
    )
    current_version_hash: Mapped[str] = mapped_column(String(128), index=True)
    raw_payload: Mapped[dict] = mapped_column(JSONType)

    versions: Mapped[list["OpportunityVersion"]] = relationship(back_populates="opportunity")


class OpportunityVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "opportunity_versions"

    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"))
    version_hash: Mapped[str] = mapped_column(String(128), index=True)
    full_text: Mapped[str] = mapped_column(Text)
    eligibility_notes: Mapped[list[str]] = mapped_column(JSONType)
    expected_outcomes: Mapped[list[str]] = mapped_column(JSONType)
    raw_payload: Mapped[dict] = mapped_column(JSONType)
    provenance: Mapped[dict] = mapped_column(JSONType, default=dict)
    uncertainty_notes: Mapped[list[str]] = mapped_column(JSONType, default=list)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True)

    opportunity: Mapped[Opportunity] = relationship(back_populates="versions")


class OpportunityIngestionSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "opportunity_ingestion_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "source_name", "source_record_id", "payload_hash", name="uq_ingestion_snapshot"
        ),
    )

    source_name: Mapped[str] = mapped_column(String(100), index=True)
    source_record_id: Mapped[str] = mapped_column(String(255), index=True)
    payload_hash: Mapped[str] = mapped_column(String(128), index=True)
    payload: Mapped[dict] = mapped_column(JSONType)


class MatchResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "match_results"

    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"))
    profile_id: Mapped[str] = mapped_column(ForeignKey("interest_profiles.id", ondelete="CASCADE"))
    scoring_policy_id: Mapped[str] = mapped_column(String(255))
    hard_filter_pass: Mapped[bool] = mapped_column(Boolean, default=False)
    hard_filter_reasons: Mapped[list[str]] = mapped_column(JSONType)
    scores: Mapped[dict] = mapped_column(JSONType)
    total_score: Mapped[float] = mapped_column(Float)
    explanations: Mapped[list[str]] = mapped_column(JSONType)
    rationale: Mapped[dict] = mapped_column(JSONType, default=dict)
    recommendation: Mapped[str] = mapped_column(String(64), default="reject")
    recommended_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    red_flags: Mapped[list[str]] = mapped_column(JSONType)
