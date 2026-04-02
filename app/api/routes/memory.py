from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.domain.institutional_memory.models import MemoryDocument, ReusableEvidenceBlock
from app.schemas.memory import (
    DocumentSourceCreate,
    ExportPackagePreviewRequest,
    ExportPackagePreviewResponse,
    MemoryDocumentCreate,
    MemoryDocumentResponse,
    RetrievalContextAssembly,
    RetrievalQuery,
    ReusableBlockCreate,
    ReusableBlockResponse,
    ReusableBlockUpdate,
)
from app.services.context_assembly_service import ContextAssemblyService
from app.services.export_package_service import ExportPackageService
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
    except ValueError as exc:
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


@router.post("/export/preview", response_model=ExportPackagePreviewResponse)
def export_preview(
    request: ExportPackagePreviewRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> ExportPackagePreviewResponse:
    try:
        response = ExportPackageService(db).preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return response


@router.post("/export/packages")
def create_export_package(
    request: ExportPackagePreviewRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> dict:
    try:
        package = ExportPackageService(db).persist_preview(request)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"package_id": package.id, "package_name": package.package_name}
