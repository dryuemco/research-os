from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base
from app.domain.common.enums import CodingTaskState
from app.domain.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin

JSONType = JSON().with_variant(JSONB, "postgresql")


class TaskGraph(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "task_graphs"

    project_ref: Mapped[str] = mapped_column(String(255), index=True)
    source_version_ref: Mapped[str] = mapped_column(String(255), index=True)
    graph_json: Mapped[dict] = mapped_column(JSONType)


class CodingTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "coding_tasks"

    task_graph_id: Mapped[str] = mapped_column(ForeignKey("task_graphs.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    acceptance_criteria: Mapped[list[str]] = mapped_column(JSONType)
    context_refs: Mapped[list[str]] = mapped_column(JSONType)
    provider_policy: Mapped[dict] = mapped_column(JSONType)
    recommended_models: Mapped[list[str]] = mapped_column(JSONType)
    estimated_cost_band: Mapped[str] = mapped_column(String(32))
    status: Mapped[CodingTaskState] = mapped_column(
        Enum(CodingTaskState), default=CodingTaskState.CREATED, index=True
    )
