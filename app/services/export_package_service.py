from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.institutional_memory.models import ExportPackage, ReusableEvidenceBlock
from app.domain.proposal_factory.models import Proposal, ProposalSection, ReviewComment, ReviewRound
from app.schemas.audit import AuditEventSchema
from app.schemas.memory import ExportPackagePreviewRequest, ExportPackagePreviewResponse
from app.services.audit_service import AuditService


class ExportPackageService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def preview(self, request: ExportPackagePreviewRequest) -> ExportPackagePreviewResponse:
        proposal = self.db.get(Proposal, request.proposal_id)
        if proposal is None:
            raise ValueError("Proposal workspace not found")

        sections = self.db.scalars(
            select(ProposalSection).where(ProposalSection.proposal_id == request.proposal_id)
        ).all()
        rounds = self.db.scalars(
            select(ReviewRound).where(ReviewRound.proposal_id == request.proposal_id)
        ).all()

        package_items: list[dict] = [
            {
                "type": "proposal_workspace",
                "proposal_id": proposal.id,
                "state": proposal.state.value,
            },
            {
                "type": "proposal_artifact_manifest",
                "section_count": len(sections),
                "sections": [
                    {"section_key": section.section_key, "status": section.status}
                    for section in sections
                ],
            },
        ]

        if request.include_reviewer_logs:
            comments = self.db.scalars(
                select(ReviewComment).where(
                    ReviewComment.review_round_id.in_([r.id for r in rounds])
                )
            ).all()
            package_items.append(
                {
                    "type": "reviewer_log_manifest",
                    "round_count": len(rounds),
                    "comment_count": len(comments),
                }
            )

        if request.include_reusable_evidence:
            blocks = self.db.scalars(select(ReusableEvidenceBlock)).all()
            package_items.append(
                {
                    "type": "reusable_evidence_manifest",
                    "block_count": len(blocks),
                    "approved_block_count": len(
                        [b for b in blocks if b.approval_status.value == "approved"]
                    ),
                }
            )

        if request.include_decomposition:
            package_items.append({"type": "decomposition_manifest", "status": "pending_link"})

        unresolved_items: list[dict] = []
        if not proposal.human_approved_for_export:
            unresolved_items.append(
                {
                    "code": "human_approval_required",
                    "detail": "Proposal must be human-approved before final export",
                }
            )

        preview = ExportPackagePreviewResponse(
            package_name=f"proposal-export-{proposal.id[:8]}",
            proposal_id=proposal.id,
            package_items=package_items,
            unresolved_items=unresolved_items,
            metadata={"renderer": "future_docx_pdf", "ready_for_render": not unresolved_items},
        )
        return preview

    def persist_preview(self, request: ExportPackagePreviewRequest) -> ExportPackage:
        preview = self.preview(request)
        package = ExportPackage(
            proposal_id=request.proposal_id,
            package_name=preview.package_name,
            package_manifest={"items": preview.package_items, "metadata": preview.metadata},
            unresolved_items=preview.unresolved_items,
        )
        self.db.add(package)
        self.db.flush()
        self.audit.emit(
            AuditEventSchema(
                event_type="export_package_generated",
                entity_type="export_package",
                entity_id=package.id,
                actor_type="system",
                actor_id="export_package_service",
                payload={
                    "proposal_id": request.proposal_id,
                    "item_count": len(preview.package_items),
                },
            )
        )
        self.db.flush()
        return package
