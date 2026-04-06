from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.domain.common.enums import (
    ExportArtifactFormat,
    ExportArtifactType,
    ExportPackageStatus,
)


class RendererName(StrEnum):
    MARKDOWN_V1 = "markdown-v1"
    DOCX_V1 = "docx-v1"


class RenderPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preferred_formats: list[ExportArtifactFormat] = Field(
        default_factory=lambda: [ExportArtifactFormat.MARKDOWN]
    )
    include_reviewer_logs: bool = True
    include_decomposition: bool = True
    include_reusable_evidence: bool = True
    include_evidence_summary: bool = True
    include_delivery_manifest: bool = True
    section_keys: list[str] = Field(default_factory=list)


class RenderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    proposal_version_id: str | None = None
    export_package_id: str | None = None
    render_policy: RenderPolicy = Field(default_factory=RenderPolicy)


class RenderedArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_type: ExportArtifactType
    artifact_format: ExportArtifactFormat = ExportArtifactFormat.MARKDOWN
    file_name: str
    media_type: str
    content_bytes: bytes
    content_text: str | None = None
    metadata_json: dict = Field(default_factory=dict)


class RenderResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    renderer_name: RendererName
    artifacts: list[RenderedArtifact] = Field(default_factory=list)
    unresolved_items: list[dict] = Field(default_factory=list)


class ExportPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    proposal_id: str
    proposal_version_id: str | None
    package_name: str
    status: ExportPackageStatus
    unresolved_items: list[dict]
    approval_actor_id: str | None
    created_at: datetime


class ExportArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    export_package_id: str
    artifact_type: ExportArtifactType
    artifact_format: ExportArtifactFormat
    file_name: str
    media_type: str
    size_bytes: int
    checksum: str
    storage_backend: str
    storage_locator: str | None
    created_at: datetime


class ExportStateTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_status: ExportPackageStatus
    actor_id: str
    reason: str | None = None
