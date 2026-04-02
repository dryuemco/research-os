from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.domain.common.enums import ExportArtifactFormat
from app.schemas.export import RenderRequest, RenderResult


class RendererCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    renderer_name: str
    supports_formats: list[ExportArtifactFormat] = Field(default_factory=list)
    can_include_reviewer_logs: bool = True
    can_include_decomposition: bool = True
    can_include_reusable_evidence: bool = True


class ExportRenderer(Protocol):
    renderer_name: str
    capabilities: RendererCapabilities

    def render(self, request: RenderRequest) -> RenderResult:
        ...
