from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.common.enums import ExportArtifactType, ExportPackageStatus
from app.domain.institutional_memory.models import ExportArtifact, ExportPackage
from app.domain.proposal_factory.models import Proposal, ProposalVersion
from app.schemas.audit import AuditEventSchema
from app.schemas.export import (
    ExportStateTransitionRequest,
    RenderRequest,
)
from app.services.audit_service import AuditService
from app.services.renderers.markdown_renderer import MarkdownExportRenderer

_ALLOWED_TRANSITIONS: dict[ExportPackageStatus, set[ExportPackageStatus]] = {
    ExportPackageStatus.DRAFT: {ExportPackageStatus.READY_FOR_REVIEW, ExportPackageStatus.FAILED},
    ExportPackageStatus.READY_FOR_REVIEW: {
        ExportPackageStatus.APPROVED,
        ExportPackageStatus.SUPERSEDED,
        ExportPackageStatus.ARCHIVED,
        ExportPackageStatus.FAILED,
    },
    ExportPackageStatus.APPROVED: {ExportPackageStatus.SUPERSEDED, ExportPackageStatus.ARCHIVED},
    ExportPackageStatus.SUPERSEDED: {ExportPackageStatus.ARCHIVED},
    ExportPackageStatus.ARCHIVED: set(),
    ExportPackageStatus.FAILED: {ExportPackageStatus.DRAFT, ExportPackageStatus.ARCHIVED},
}


class InvalidExportTransitionError(ValueError):
    pass


class ExportPackageService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)
        self.renderer = MarkdownExportRenderer(db)

    def generate_package(self, request: RenderRequest, actor_id: str) -> ExportPackage:
        proposal = self.db.get(Proposal, request.proposal_id)
        if proposal is None:
            raise ValueError("Proposal workspace not found")

        proposal_version = self._resolve_proposal_version(proposal.id, request.proposal_version_id)

        result = self.renderer.render(request)
        package = ExportPackage(
            proposal_id=proposal.id,
            proposal_version_id=proposal_version.id if proposal_version else None,
            package_name=f"submission-pack-{proposal.id[:8]}",
            status=ExportPackageStatus.DRAFT,
            package_manifest={
                "renderer": self.renderer.renderer_name,
                "artifact_count": len(result.artifacts),
            },
            unresolved_items=result.unresolved_items,
            generated_by=actor_id,
        )
        self.db.add(package)
        self.db.flush()

        self._persist_artifacts(package.id, result.artifacts)
        self.transition_status(
            package.id,
            ExportStateTransitionRequest(
                target_status=ExportPackageStatus.READY_FOR_REVIEW,
                actor_id=actor_id,
                reason="initial_render_completed",
            ),
        )
        self._emit_event(
            package.id,
            "export_package_generated",
            {
                "proposal_id": proposal.id,
                "proposal_version_id": proposal_version.id if proposal_version else None,
                "artifact_count": len(result.artifacts),
            },
            actor_id,
        )
        self.db.flush()
        return package

    def transition_status(
        self,
        package_id: str,
        request: ExportStateTransitionRequest,
    ) -> ExportPackage:
        package = self.get_package(package_id)
        if request.target_status not in _ALLOWED_TRANSITIONS[package.status]:
            raise InvalidExportTransitionError(
                f"Cannot transition export package from {package.status} to {request.target_status}"
            )

        if request.target_status == ExportPackageStatus.APPROVED:
            proposal = self.db.get(Proposal, package.proposal_id)
            if proposal is None or not proposal.human_approved_for_export:
                raise InvalidExportTransitionError(
                    "Proposal must be human-approved before export package approval"
                )
            package.approval_actor_id = request.actor_id

        previous = package.status
        package.status = request.target_status
        self.db.add(package)
        self._emit_event(
            package.id,
            "export_package_status_changed",
            {
                "from_status": previous.value,
                "to_status": request.target_status.value,
                "reason": request.reason,
            },
            request.actor_id,
        )
        self.db.flush()
        return package

    def get_package(self, package_id: str) -> ExportPackage:
        package = self.db.get(ExportPackage, package_id)
        if package is None:
            raise ValueError("Export package not found")
        return package

    def list_packages(self, proposal_id: str | None = None) -> list[ExportPackage]:
        stmt = select(ExportPackage).order_by(ExportPackage.created_at.desc())
        if proposal_id:
            stmt = stmt.where(ExportPackage.proposal_id == proposal_id)
        return self.db.scalars(stmt).all()

    def list_artifacts(self, package_id: str) -> list[ExportArtifact]:
        return self.db.scalars(
            select(ExportArtifact)
            .where(ExportArtifact.export_package_id == package_id)
            .order_by(ExportArtifact.created_at.asc())
        ).all()

    def get_artifact(self, artifact_id: str) -> ExportArtifact:
        artifact = self.db.get(ExportArtifact, artifact_id)
        if artifact is None:
            raise ValueError("Export artifact not found")
        return artifact

    def build_submission_pack(self, package_id: str) -> dict:
        package = self.get_package(package_id)
        artifacts = self.list_artifacts(package.id)
        manifest = {
            "package_id": package.id,
            "proposal_id": package.proposal_id,
            "proposal_version_id": package.proposal_version_id,
            "status": package.status.value,
            "artifacts": [
                {
                    "artifact_id": artifact.id,
                    "artifact_type": artifact.artifact_type.value,
                    "file_name": artifact.file_name,
                    "checksum": artifact.checksum,
                    "media_type": artifact.media_type,
                }
                for artifact in artifacts
            ],
            "generation_context": package.package_manifest,
        }
        # include machine-readable manifest artifact in submission pack view
        return manifest

    def _resolve_proposal_version(
        self, proposal_id: str, proposal_version_id: str | None
    ) -> ProposalVersion | None:
        if proposal_version_id:
            version = self.db.get(ProposalVersion, proposal_version_id)
            if version is None:
                raise ValueError("Proposal version not found")
            return version

        return self.db.scalar(
            select(ProposalVersion)
            .where(ProposalVersion.proposal_id == proposal_id)
            .order_by(ProposalVersion.version_number.desc())
        )

    def _persist_artifacts(self, package_id: str, rendered_artifacts: list) -> None:
        for artifact in rendered_artifacts:
            checksum = hashlib.sha256(artifact.content_text.encode()).hexdigest()
            model = ExportArtifact(
                export_package_id=package_id,
                artifact_type=artifact.artifact_type,
                file_name=artifact.file_name,
                media_type=artifact.media_type,
                content_text=artifact.content_text,
                checksum=checksum,
                metadata_json=artifact.metadata_json,
            )
            self.db.add(model)

        # include export manifest artifact
        manifest_text = "# Export Manifest\nThis artifact is generated with the package metadata."
        manifest_checksum = hashlib.sha256(manifest_text.encode()).hexdigest()
        self.db.add(
            ExportArtifact(
                export_package_id=package_id,
                artifact_type=ExportArtifactType.EXPORT_MANIFEST,
                file_name="export_manifest.md",
                media_type="text/markdown",
                content_text=manifest_text,
                checksum=manifest_checksum,
                metadata_json={},
            )
        )

    def _emit_event(self, package_id: str, event_type: str, payload: dict, actor_id: str) -> None:
        self.audit.emit(
            AuditEventSchema(
                event_type=event_type,
                entity_type="export_package",
                entity_id=package_id,
                actor_type="user",
                actor_id=actor_id,
                payload=payload,
            )
        )
