from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.common.enums import (
    ExportArtifactFormat,
    ExportArtifactType,
    ExportPackageStatus,
)
from app.domain.institutional_memory.models import ExportArtifact, ExportPackage
from app.domain.proposal_factory.models import Proposal, ProposalVersion
from app.schemas.audit import AuditEventSchema
from app.schemas.export import ExportStateTransitionRequest, RenderedArtifact, RenderRequest
from app.services.artifact_storage.factory import build_artifact_storage
from app.services.audit_service import AuditService
from app.services.export_errors import (
    ArtifactAccessDeniedError,
    ArtifactIntegrityError,
    ArtifactNotFoundError,
    ArtifactStorageError,
    RenderExecutionError,
)
from app.services.renderers.selector import ExportRendererSelector

logger = logging.getLogger(__name__)

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
        self.storage = build_artifact_storage()
        self.settings = get_settings()

    def generate_package(self, request: RenderRequest, actor_id: str) -> ExportPackage:
        proposal = self.db.get(Proposal, request.proposal_id)
        if proposal is None:
            raise ValueError("Proposal workspace not found")

        proposal_version = self._resolve_proposal_version(proposal.id, request.proposal_version_id)
        renderer = ExportRendererSelector(self.db).resolve(request.render_policy)

        render_started = time.monotonic()
        try:
            result = renderer.render(request)
        except Exception as exc:
            logger.exception("export_render_failed", extra={"proposal_id": proposal.id})
            raise RenderExecutionError(str(exc)) from exc
        duration_ms = int((time.monotonic() - render_started) * 1000)

        package = ExportPackage(
            proposal_id=proposal.id,
            proposal_version_id=proposal_version.id if proposal_version else None,
            package_name=f"submission-pack-{proposal.id[:8]}",
            status=ExportPackageStatus.DRAFT,
            package_manifest={
                "renderer": result.renderer_name,
                "artifact_count": len(result.artifacts),
                "generation_duration_ms": duration_ms,
                "preferred_formats": [f.value for f in request.render_policy.preferred_formats],
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
                "renderer": str(result.renderer_name),
                "generation_duration_ms": duration_ms,
                "storage_backend": self.storage.backend_name,
            },
            actor_id,
        )
        self.db.flush()
        logger.info(
            "export_package_generated",
            extra={
                "package_id": package.id,
                "proposal_id": proposal.id,
                "renderer": str(result.renderer_name),
                "artifact_count": len(result.artifacts),
                "generation_duration_ms": duration_ms,
            },
        )
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
            raise ArtifactNotFoundError("Export artifact not found")
        return artifact

    def create_download_token(self, artifact_id: str, actor_id: str) -> str:
        self.get_artifact(artifact_id)
        expires_at = datetime.now(UTC) + timedelta(
            seconds=self.settings.artifact_download_ttl_seconds
        )
        payload = {
            "artifact_id": artifact_id,
            "actor_id": actor_id,
            "exp": int(expires_at.timestamp()),
        }
        encoded = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
        signature = self._sign(encoded)
        return f"{encoded}.{signature}"

    def validate_download_token(self, token: str, actor_id: str, artifact_id: str) -> None:
        try:
            encoded, provided_sig = token.split(".", maxsplit=1)
        except ValueError as exc:
            raise ArtifactAccessDeniedError("Invalid download token") from exc

        if not hmac.compare_digest(provided_sig, self._sign(encoded)):
            raise ArtifactAccessDeniedError("Invalid download token")

        payload = json.loads(base64.urlsafe_b64decode(encoded.encode("utf-8")).decode("utf-8"))
        if payload.get("artifact_id") != artifact_id or payload.get("actor_id") != actor_id:
            raise ArtifactAccessDeniedError("Download token scope mismatch")
        if int(payload.get("exp", 0)) < int(datetime.now(UTC).timestamp()):
            raise ArtifactAccessDeniedError("Download token expired")

    def read_artifact_bytes(self, artifact_id: str) -> tuple[ExportArtifact, bytes]:
        artifact = self.get_artifact(artifact_id)
        data: bytes
        if artifact.storage_locator and artifact.storage_backend == self.storage.backend_name:
            try:
                if not self.storage.verify(artifact.storage_locator, artifact.checksum):
                    raise ArtifactIntegrityError("Artifact checksum verification failed")
                data = self.storage.read_bytes(artifact.storage_locator)
            except FileNotFoundError:
                data = self._fallback_payload(artifact)
            except ValueError as exc:
                raise ArtifactStorageError(str(exc)) from exc
        else:
            data = self._fallback_payload(artifact)

        if hashlib.sha256(data).hexdigest() != artifact.checksum:
            raise ArtifactIntegrityError("Artifact checksum mismatch")
        return artifact, data

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
                    "artifact_format": artifact.artifact_format.value,
                    "file_name": artifact.file_name,
                    "checksum": artifact.checksum,
                    "media_type": artifact.media_type,
                    "size_bytes": artifact.size_bytes,
                    "storage_backend": artifact.storage_backend,
                }
                for artifact in artifacts
            ],
            "generation_context": package.package_manifest,
        }
        return manifest

    def audit_download(self, artifact: ExportArtifact, actor_id: str) -> None:
        self._emit_event(
            artifact.export_package_id,
            "export_artifact_downloaded",
            {
                "artifact_id": artifact.id,
                "file_name": artifact.file_name,
                "artifact_type": artifact.artifact_type.value,
                "artifact_format": artifact.artifact_format.value,
                "storage_backend": artifact.storage_backend,
                "size_bytes": artifact.size_bytes,
            },
            actor_id,
        )

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

    def _persist_artifacts(
        self, package_id: str, rendered_artifacts: list[RenderedArtifact]
    ) -> None:
        for artifact in rendered_artifacts:
            checksum = hashlib.sha256(artifact.content_bytes).hexdigest()
            try:
                stored = self.storage.store(
                    package_id=package_id,
                    file_name=artifact.file_name,
                    content_bytes=artifact.content_bytes,
                    checksum=checksum,
                )
            except Exception as exc:
                raise ArtifactStorageError(
                    f"Storage write failed for {artifact.file_name}"
                ) from exc

            model = ExportArtifact(
                export_package_id=package_id,
                artifact_type=artifact.artifact_type,
                artifact_format=artifact.artifact_format,
                file_name=artifact.file_name,
                media_type=artifact.media_type,
                content_text=artifact.content_text or "",
                content_base64=base64.b64encode(artifact.content_bytes).decode("utf-8"),
                size_bytes=stored.size_bytes,
                checksum=checksum,
                storage_backend=stored.backend,
                storage_locator=stored.locator,
                metadata_json=artifact.metadata_json,
            )
            self.db.add(model)

        manifest_payload = {
            "package_id": package_id,
            "artifact_count": len(rendered_artifacts),
            "created_at": datetime.now(UTC).isoformat(),
            "storage_backend": self.storage.backend_name,
        }
        manifest_bytes = json.dumps(manifest_payload, indent=2).encode("utf-8")
        manifest_checksum = hashlib.sha256(manifest_bytes).hexdigest()
        manifest_ref = self.storage.store(
            package_id=package_id,
            file_name="delivery_manifest.json",
            content_bytes=manifest_bytes,
            checksum=manifest_checksum,
        )
        self.db.add(
            ExportArtifact(
                export_package_id=package_id,
                artifact_type=ExportArtifactType.DELIVERY_MANIFEST,
                artifact_format=ExportArtifactFormat.JSON,
                file_name="delivery_manifest.json",
                media_type="application/json",
                content_text=manifest_bytes.decode("utf-8"),
                content_base64=base64.b64encode(manifest_bytes).decode("utf-8"),
                size_bytes=manifest_ref.size_bytes,
                checksum=manifest_checksum,
                storage_backend=manifest_ref.backend,
                storage_locator=manifest_ref.locator,
                metadata_json={"kind": "delivery_manifest"},
            )
        )

    def _fallback_payload(self, artifact: ExportArtifact) -> bytes:
        if artifact.content_base64:
            return base64.b64decode(artifact.content_base64.encode("utf-8"))
        if artifact.content_text:
            return artifact.content_text.encode("utf-8")
        raise ArtifactNotFoundError("Artifact payload unavailable")

    def _sign(self, payload: str) -> str:
        return hmac.new(
            self.settings.artifact_download_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

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
