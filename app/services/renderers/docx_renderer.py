from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy.orm import Session

from app.domain.common.enums import ExportArtifactFormat, ExportArtifactType
from app.schemas.export import (
    RenderedArtifact,
    RendererName,
    RenderRequest,
    RenderResult,
)
from app.services.renderers.base import RendererCapabilities
from app.services.renderers.content_builder import build_export_content


class DocxExportRenderer:
    renderer_name = RendererName.DOCX_V1
    capabilities = RendererCapabilities(
        renderer_name=renderer_name,
        supports_formats=[ExportArtifactFormat.DOCX, ExportArtifactFormat.JSON],
    )

    def __init__(self, db: Session) -> None:
        self.db = db

    def render(self, request: RenderRequest) -> RenderResult:
        content = build_export_content(self.db, request)
        proposal = content["proposal"]
        sections = content["sections"]

        narrative_blocks = [f"{proposal.name}", f"State: {proposal.state.value}"]
        for section in sections:
            narrative_blocks.append(section.section_key)
            narrative_blocks.append(section.draft_text or "")

        artifacts: list[RenderedArtifact] = [
            self._docx_artifact(
                artifact_type=ExportArtifactType.PROPOSAL_NARRATIVE,
                file_name="proposal_narrative.docx",
                paragraphs=narrative_blocks,
                metadata_json={"section_count": len(sections)},
            )
        ]

        if request.render_policy.include_reviewer_logs:
            reviewer_lines = ["Reviewer Log"]
            for comment in content["reviewer_comments"]:
                reviewer_lines.append(
                    f"[{comment.severity}] {comment.reviewer_role}: {comment.comment_text}"
                )
            artifacts.append(
                self._docx_artifact(
                    artifact_type=ExportArtifactType.REVIEWER_LOG,
                    file_name="reviewer_log.docx",
                    paragraphs=reviewer_lines,
                    metadata_json={"comment_count": len(content['reviewer_comments'])},
                )
            )

        if request.render_policy.include_reusable_evidence:
            evidence_lines = ["Reusable Evidence"]
            for block in content["reusable_blocks"]:
                evidence_lines.append(block.title)
                evidence_lines.append(f"Status: {block.approval_status.value}")
                evidence_lines.append(block.body_text or "")
            artifacts.append(
                self._docx_artifact(
                    artifact_type=ExportArtifactType.REUSABLE_EVIDENCE,
                    file_name="reusable_evidence.docx",
                    paragraphs=evidence_lines,
                    metadata_json={"block_count": len(content['reusable_blocks'])},
                )
            )

        if request.render_policy.include_decomposition:
            decomposition_lines = ["Decomposition Summary"]
            execution_plan = content["execution_plan"]
            if execution_plan:
                decomposition_lines.append(
                    f"Plan: {execution_plan.plan_name} ({execution_plan.state.value})"
                )
            for ticket in content["tickets"]:
                decomposition_lines.append(f"{ticket.task_code}: {ticket.title}")
            artifacts.append(
                self._docx_artifact(
                    artifact_type=ExportArtifactType.DECOMPOSITION_SUMMARY,
                    file_name="decomposition_summary.docx",
                    paragraphs=decomposition_lines,
                    metadata_json={"ticket_count": len(content['tickets'])},
                )
            )

        return RenderResult(
            renderer_name=self.renderer_name,
            artifacts=artifacts,
            unresolved_items=[],
        )

    def _docx_artifact(
        self,
        artifact_type: ExportArtifactType,
        file_name: str,
        paragraphs: list[str],
        metadata_json: dict,
    ) -> RenderedArtifact:
        return RenderedArtifact(
            artifact_type=artifact_type,
            artifact_format=ExportArtifactFormat.DOCX,
            file_name=file_name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            content_bytes=_build_docx(paragraphs),
            content_text=None,
            metadata_json=metadata_json,
        )


def _build_docx(paragraphs: list[str]) -> bytes:
    doc_content_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
    )
    relationship_type = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    )
    content_types = f"""<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>
  <Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/>
  <Default Extension='xml' ContentType='application/xml'/>
  <Override PartName='/word/document.xml' ContentType='{doc_content_type}'/>
</Types>"""

    rels = f"""<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>
  <Relationship Id='rId1' Type='{relationship_type}' Target='word/document.xml'/>
</Relationships>"""

    doc_rels = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'/>"""

    body = "".join(
        f"<w:p><w:r><w:t>{escape(text)}</w:t></w:r></w:p>"
        for text in paragraphs
        if text is not None
    )
    document = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"
        f"<w:body>{body}</w:body></w:document>"
    )

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/_rels/document.xml.rels", doc_rels)
        archive.writestr("word/document.xml", document)
    return buffer.getvalue()
