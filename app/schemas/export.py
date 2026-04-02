from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.common.enums import ExportArtifactType, ExportPackageStatus


class RenderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    proposal_version_id: str | None = None
    export_package_id: str | None = None
    include_reviewer_logs: bool = True
    include_decomposition: bool = True
    include_reusable_evidence: bool = True


class RenderedArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_type: ExportArtifactType
    file_name: str
    media_type: str
    content_text: str
    metadata_json: dict = Field(default_factory=dict)


class RenderResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    file_name: str
    media_type: str
    checksum: str
    storage_backend: str
    storage_locator: str | None
    created_at: datetime


class ExportStateTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_status: ExportPackageStatus
    actor_id: str
    reason: str | None = None
