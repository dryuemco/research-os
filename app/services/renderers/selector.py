from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.common.enums import ExportArtifactFormat
from app.schemas.export import RenderPolicy
from app.services.export_errors import RendererSelectionError
from app.services.renderers.docx_renderer import DocxExportRenderer
from app.services.renderers.markdown_renderer import MarkdownExportRenderer


class ExportRendererSelector:
    def __init__(self, db: Session) -> None:
        self.renderers = {
            ExportArtifactFormat.MARKDOWN: MarkdownExportRenderer(db),
            ExportArtifactFormat.DOCX: DocxExportRenderer(db),
        }

    def resolve(self, policy: RenderPolicy):
        for preferred in policy.preferred_formats:
            renderer = self.renderers.get(preferred)
            if renderer:
                return renderer
        preferred_values = [fmt.value for fmt in policy.preferred_formats]
        raise RendererSelectionError(
            f"No renderer available for preferred formats: {preferred_values}"
        )
