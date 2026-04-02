from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.domain.common.enums import Permission
from app.domain.institutional_memory.models import MemoryDocument, ReusableEvidenceBlock
from app.schemas.export import (
    ExportArtifactResponse,
    ExportPackageResponse,
    ExportStateTransitionRequest,
    RenderRequest,
)
from app.schemas.memory import (
    DocumentSourceCreate,
    MemoryDocumentCreate,
    MemoryDocumentResponse,
    RetrievalContextAssembly,
    RetrievalQuery,
    ReusableBlockCreate,
    ReusableBlockResponse,
    ReusableBlockUpdate,
)
from app.security.auth import CurrentUser, require_permissions
from app.services.context_assembly_service import ContextAssemblyService
from app.services.export_errors import (
    ArtifactAccessDeniedError,
    ArtifactIntegrityError,
    ArtifactNotFoundError,
    ArtifactStorageError,
    RendererSelectionError,
    RenderExecutionError,
)
from app.services.export_package_service import ExportPackageService, InvalidExportTransitionError
from app.services.memory_service import MemoryService
from app.services.retrieval_service import RetrievalService

router = APIRouter()


@router.post("/sources")
def create_source(
    request: DocumentSourceCreate,
    db: Annotated[Session, Depends(get_db_session)],
) -> dict:
    source = MemoryService(db).create_source(request)
    db.commit()
    return {"source_id": source.id}


@router.post("/documents", response_model=MemoryDocumentResponse)
def create_document(
    request: MemoryDocumentCreate,
    db: Annotated[Session, Depends(get_db_session)],
) -> MemoryDocumentResponse:
    try:
        document = MemoryService(db).create_document(request)
        db.commit()
    except (ValueError, RendererSelectionError, RenderExecutionError, ArtifactStorageError) as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MemoryDocumentResponse.model_validate(document)


@router.get("/documents", response_model=list[MemoryDocumentResponse])
def list_documents(
    db: Annotated[Session, Depends(get_db_session)],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[MemoryDocumentResponse]:
    items = db.scalars(
        select(MemoryDocument).order_by(MemoryDocument.created_at.desc()).offset(offset).limit(limit)
    ).all()
    return [MemoryDocumentResponse.model_validate(item) for item in items]


@router.post("/blocks", response_model=ReusableBlockResponse)
def create_block(
    request: ReusableBlockCreate,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.MEMORY_BLOCK_MUTATE))],
) -> ReusableBlockResponse:
    try:
        block = MemoryService(db).create_block(request)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReusableBlockResponse.model_validate(block)


@router.get("/blocks", response_model=list[ReusableBlockResponse])
def list_blocks(
    db: Annotated[Session, Depends(get_db_session)],
    approved_only: bool = Query(default=False),
) -> list[ReusableBlockResponse]:
    blocks = MemoryService(db).list_blocks(approved_only=approved_only)
    return [ReusableBlockResponse.model_validate(item) for item in blocks]


@router.get("/blocks/{block_id}", response_model=ReusableBlockResponse)
def get_block(
    block_id: str,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.MEMORY_BLOCK_MUTATE))],
) -> ReusableBlockResponse:
    block = db.get(ReusableEvidenceBlock, block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Reusable block not found")
    return ReusableBlockResponse.model_validate(block)


@router.put("/blocks/{block_id}", response_model=ReusableBlockResponse)
def update_block(
    block_id: str,
    request: ReusableBlockUpdate,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.MEMORY_BLOCK_MUTATE))],
) -> ReusableBlockResponse:
    try:
        block = MemoryService(db).update_block(block_id, request)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReusableBlockResponse.model_validate(block)


@router.post("/retrieval/preview", response_model=RetrievalContextAssembly)
def retrieval_preview(
    request: RetrievalQuery,
    db: Annotated[Session, Depends(get_db_session)],
    purpose: str = Query(default="concept_note"),
) -> RetrievalContextAssembly:
    retrieval = RetrievalService(db)
    context_service = ContextAssemblyService(retrieval)
    if purpose == "section_draft":
        return context_service.assemble_for_section_draft(request)
    if purpose == "decomposition":
        return context_service.assemble_for_decomposition(request)
    return context_service.assemble_for_concept_note(request)


@router.post("/exports/generate", response_model=ExportPackageResponse)
def generate_export_package(
    request: RenderRequest,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.EXPORT_GENERATE))],
    actor_id: str = Query(default="operator"),
) -> ExportPackageResponse:
    service = ExportPackageService(db)
    try:
        package = service.generate_package(request, actor_id=actor_id)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ExportPackageResponse.model_validate(package)


@router.get("/exports", response_model=list[ExportPackageResponse])
def list_export_packages(
    db: Annotated[Session, Depends(get_db_session)],
    proposal_id: str | None = Query(default=None),
) -> list[ExportPackageResponse]:
    packages = ExportPackageService(db).list_packages(proposal_id=proposal_id)
    return [ExportPackageResponse.model_validate(item) for item in packages]


@router.get("/exports/{package_id}", response_model=ExportPackageResponse)
def get_export_package(
    package_id: str,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.EXPORT_APPROVE))],
) -> ExportPackageResponse:
    try:
        package = ExportPackageService(db).get_package(package_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExportPackageResponse.model_validate(package)


@router.post("/exports/{package_id}/transition", response_model=ExportPackageResponse)
def transition_export_package(
    package_id: str,
    request: ExportStateTransitionRequest,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.EXPORT_APPROVE))],
) -> ExportPackageResponse:
    service = ExportPackageService(db)
    try:
        package = service.transition_status(package_id, request)
        db.commit()
    except (ValueError, InvalidExportTransitionError) as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ExportPackageResponse.model_validate(package)


@router.get("/exports/{package_id}/artifacts", response_model=list[ExportArtifactResponse])
def list_export_artifacts(
    package_id: str,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.EXPORT_DOWNLOAD))],
) -> list[ExportArtifactResponse]:
    items = ExportPackageService(db).list_artifacts(package_id)
    return [ExportArtifactResponse.model_validate(item) for item in items]


@router.post("/exports/artifacts/{artifact_id}/download-token")
def create_download_token(
    artifact_id: str,
    db: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[CurrentUser, Depends(require_permissions(Permission.EXPORT_DOWNLOAD))],
) -> dict:
    try:
        token = ExportPackageService(db).create_download_token(
            artifact_id=artifact_id,
            actor_id=current_user.user_id,
        )
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"token": token}


@router.get("/exports/artifacts/{artifact_id}/download")
def download_export_artifact(
    artifact_id: str,
    db: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[CurrentUser, Depends(require_permissions(Permission.EXPORT_DOWNLOAD))],
    token: str | None = Query(default=None),
) -> Response:
    service = ExportPackageService(db)
    try:
        if token:
            service.validate_download_token(
                token, actor_id=current_user.user_id, artifact_id=artifact_id
            )
        artifact, payload = service.read_artifact_bytes(artifact_id)
        service.audit_download(artifact, actor_id=current_user.user_id)
        db.commit()
    except ArtifactNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ArtifactAccessDeniedError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (ArtifactStorageError, ArtifactIntegrityError) as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return Response(
        content=payload,
        media_type=artifact.media_type,
        headers={"Content-Disposition": f'attachment; filename="{artifact.file_name}"'},
    )


@router.get("/exports/{package_id}/submission-pack")
def get_submission_pack(
    package_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> dict:
    try:
        return ExportPackageService(db).build_submission_pack(package_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
