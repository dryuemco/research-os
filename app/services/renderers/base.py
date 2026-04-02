from __future__ import annotations

from typing import Protocol

from app.schemas.export import RenderRequest, RenderResult


class ExportRenderer(Protocol):
    renderer_name: str

    def render(self, request: RenderRequest) -> RenderResult:
        ...
