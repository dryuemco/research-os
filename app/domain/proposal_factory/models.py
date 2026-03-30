from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base
from app.domain.common.enums import ProposalState
from app.domain.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin

JSONType = JSON().with_variant(JSONB, "postgresql")


class Proposal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "proposals"

    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id", ondelete="RESTRICT"))
    owner_id: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(255), default="Proposal Workspace")
    template_type: Mapped[str] = mapped_column(String(100))
    page_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state: Mapped[ProposalState] = mapped_column(
        Enum(ProposalState), default=ProposalState.CREATED, index=True
    )
    latest_version_number: Mapped[int] = mapped_column(Integer, default=0)
    mandatory_sections: Mapped[list[str]] = mapped_column(JSONType)
    compliance_rules: Mapped[list[dict]] = mapped_column(JSONType)
    unresolved_issues_json: Mapped[list[dict]] = mapped_column(JSONType, default=list)
    stage_metadata: Mapped[dict] = mapped_column(JSONType, default=dict)
    human_approved_for_export: Mapped[bool] = mapped_column(Boolean, default=False)


class ProposalVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "proposal_versions"

    proposal_id: Mapped[str] = mapped_column(
        ForeignKey("proposals.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer)
    concept_note_json: Mapped[dict] = mapped_column(JSONType)
    section_plan_json: Mapped[list[dict]] = mapped_column(JSONType, default=list)
    status: Mapped[str] = mapped_column(String(64), default="draft")


class ProposalSection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "proposal_sections"

    proposal_id: Mapped[str] = mapped_column(
        ForeignKey("proposals.id", ondelete="CASCADE"), index=True
    )
    section_key: Mapped[str] = mapped_column(String(128), index=True)
    draft_text: Mapped[str] = mapped_column(Text)
    model_provider: Mapped[str] = mapped_column(String(64))
    model_name: Mapped[str] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(64))
    source_request_json: Mapped[dict] = mapped_column(JSONType, default=dict)
    round_number: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(64), default="drafted")
    review_status: Mapped[str] = mapped_column(String(64), default="pending")
    compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class ReviewRound(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "review_rounds"

    proposal_id: Mapped[str] = mapped_column(
        ForeignKey("proposals.id", ondelete="CASCADE"), index=True
    )
    round_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(64), default="created")
    reviewer_roles: Mapped[list[str]] = mapped_column(JSONType)
    convergence_decision: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stop_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ReviewComment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "review_comments"

    review_round_id: Mapped[str] = mapped_column(
        ForeignKey("review_rounds.id", ondelete="CASCADE"), index=True
    )
    reviewer_role: Mapped[str] = mapped_column(String(128))
    severity: Mapped[str] = mapped_column(String(32))
    blocker: Mapped[bool] = mapped_column(Boolean, default=False)
    issue_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    comment_text: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONType)
