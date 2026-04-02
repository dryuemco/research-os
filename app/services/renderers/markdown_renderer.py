from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.common.enums import ExportArtifactFormat, ExportArtifactType
from app.domain.execution_orchestrator.models import EngineeringTicket, ExecutionPlan
from app.domain.institutional_memory.models import ReusableEvidenceBlock
from app.domain.proposal_factory.models import (
    Proposal,
    ProposalSection,
    ReviewComment,
    ReviewRound,
)
from app.schemas.export import RenderedArtifact, RendererName, RenderRequest, RenderResult
from app.services.renderers.base import RendererCapabilities


class MarkdownExportRenderer:
    renderer_name = RendererName.MARKDOWN_V1
    capabilities = RendererCapabilities(
        renderer_name=renderer_name,
        supports_formats=[ExportArtifactFormat.MARKDOWN, ExportArtifactFormat.JSON],
    )

    def __init__(self, db: Session) -> None:
        self.db = db

    def render(self, request: RenderRequest) -> RenderResult:
        proposal = self.db.get(Proposal, request.proposal_id)
        if proposal is None:
            raise ValueError("Proposal not found")

        sections = self.db.scalars(
            select(ProposalSection).where(ProposalSection.proposal_id == proposal.id)
        ).all()
        section_lines = [f"# {proposal.name}\n", f"State: {proposal.state.value}\n"]
        for section in sections:
            section_lines.append(f"## {section.section_key}\n{section.draft_text}\n")
        narrative = "\n".join(section_lines)

        artifacts: list[RenderedArtifact] = [
            self._artifact(
                artifact_type=ExportArtifactType.PROPOSAL_NARRATIVE,
                file_name="proposal_narrative.md",
                content_text=narrative,
                metadata_json={"section_count": len(sections)},
            )
        ]

        if request.render_policy.include_reviewer_logs:
            rounds = self.db.scalars(
                select(ReviewRound).where(ReviewRound.proposal_id == proposal.id)
            ).all()
            comments = self.db.scalars(
                select(ReviewComment).where(
                    ReviewComment.review_round_id.in_([r.id for r in rounds])
                )
            ).all()
            comment_lines = ["# Reviewer Log\n"]
            for comment in comments:
                comment_lines.append(
                    f"- [{comment.severity}] {comment.reviewer_role}: {comment.comment_text}"
                )
            artifacts.append(
                self._artifact(
                    artifact_type=ExportArtifactType.REVIEWER_LOG,
                    file_name="reviewer_log.md",
                    content_text="\n".join(comment_lines),
                    metadata_json={"comment_count": len(comments)},
                )
            )

        if request.render_policy.include_reusable_evidence:
            blocks = self.db.scalars(select(ReusableEvidenceBlock)).all()
            evidence_lines = ["# Reusable Evidence\n"]
            for block in blocks:
                evidence_lines.append(
                    f"## {block.title}\nStatus: {block.approval_status.value}\n{block.body_text}\n"
                )
            artifacts.append(
                self._artifact(
                    artifact_type=ExportArtifactType.REUSABLE_EVIDENCE,
                    file_name="reusable_evidence.md",
                    content_text="\n".join(evidence_lines),
                    metadata_json={"block_count": len(blocks)},
                )
            )

        if request.render_policy.include_decomposition:
            plan = self.db.scalar(
                select(ExecutionPlan).where(ExecutionPlan.proposal_id == proposal.id)
            )
            tickets = []
            if plan:
                tickets = self.db.scalars(
                    select(EngineeringTicket).where(EngineeringTicket.execution_plan_id == plan.id)
                ).all()
            task_lines = ["# Decomposition Summary\n"]
            if plan:
                task_lines.append(f"Plan: {plan.plan_name} ({plan.state.value})\n")
            for ticket in tickets:
                task_lines.append(f"- {ticket.task_code}: {ticket.title}")
            artifacts.append(
                self._artifact(
                    artifact_type=ExportArtifactType.DECOMPOSITION_SUMMARY,
                    file_name="decomposition_summary.md",
                    content_text="\n".join(task_lines),
                    metadata_json={"ticket_count": len(tickets)},
                )
            )

        return RenderResult(
            renderer_name=self.renderer_name,
            artifacts=artifacts,
            unresolved_items=[],
        )

    def _artifact(
        self,
        artifact_type: ExportArtifactType,
        file_name: str,
        content_text: str,
        metadata_json: dict,
    ) -> RenderedArtifact:
        return RenderedArtifact(
            artifact_type=artifact_type,
            artifact_format=ExportArtifactFormat.MARKDOWN,
            file_name=file_name,
            media_type="text/markdown",
            content_bytes=content_text.encode("utf-8"),
            content_text=content_text,
            metadata_json=metadata_json,
        )
