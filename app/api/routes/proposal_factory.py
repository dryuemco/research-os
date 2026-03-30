from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.domain.proposal_factory.models import Proposal
from app.schemas.proposal import (
    ConceptNoteInputContext,
    ConvergenceResult,
    ProposalWorkspaceCreateRequest,
    ProposalWorkspaceResponse,
    ReviewerFeedback,
    ReviewRoundCreateRequest,
    ReviewRoundResponse,
    SectionDraftRequest,
    SectionDraftResult,
)
from app.schemas.provider import (
    QuotaPolicyEvaluationDecision,
    QuotaPolicyEvaluationRequest,
)
from app.schemas.routing import ModelRoutingDecision, ModelRoutingRequest
from app.services.model_routing_service import ModelRoutingService
from app.services.prompt_registry_service import PromptRegistryService
from app.services.proposal_factory_service import ProposalFactoryService
from app.services.proposal_service import ProposalService
from app.services.quota_policy_service import QuotaPolicyService

router = APIRouter()


def _factory(db: Session) -> ProposalFactoryService:
    prompt_registry = PromptRegistryService(prompt_root=Path("prompts"))
    return ProposalFactoryService(db, prompt_registry)


@router.post("/workspaces", response_model=ProposalWorkspaceResponse)
def create_workspace(
    request: ProposalWorkspaceCreateRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> ProposalWorkspaceResponse:
    service = ProposalService(db)
    try:
        workspace = service.create_workspace(request)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProposalWorkspaceResponse.model_validate(workspace)


@router.get("/workspaces/{proposal_id}", response_model=ProposalWorkspaceResponse)
def get_workspace(
    proposal_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> ProposalWorkspaceResponse:
    proposal = db.get(Proposal, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return ProposalWorkspaceResponse.model_validate(proposal)


@router.post("/concept-note")
def create_concept_note(
    request: ConceptNoteInputContext,
    db: Annotated[Session, Depends(get_db_session)],
) -> dict:
    try:
        version = _factory(db).create_concept_note(request)
        db.commit()
    except (ValueError, FileNotFoundError) as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"proposal_version_id": version.id, "version_number": version.version_number}


@router.post("/sections/draft", response_model=SectionDraftResult)
def create_section_draft(
    request: SectionDraftRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> SectionDraftResult:
    try:
        section = _factory(db).create_section_draft(request)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SectionDraftResult(
        proposal_id=section.proposal_id,
        section_key=section.section_key,
        draft_text=section.draft_text,
        model_provider=section.model_provider,
        model_name=section.model_name,
        prompt_version=section.prompt_version,
        round_number=section.round_number,
        status=section.status,
    )


@router.post("/review-rounds", response_model=ReviewRoundResponse)
def create_review_round(
    request: ReviewRoundCreateRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> ReviewRoundResponse:
    try:
        round_model = _factory(db).create_review_round(request)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReviewRoundResponse.model_validate(round_model)


@router.post("/review-feedback")
def add_review_feedback(
    request: ReviewerFeedback,
    db: Annotated[Session, Depends(get_db_session)],
) -> dict:
    try:
        comment = _factory(db).add_reviewer_feedback(request)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"review_comment_id": comment.id}


@router.get("/workspaces/{proposal_id}/convergence", response_model=ConvergenceResult)
def convergence_preview(
    proposal_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> ConvergenceResult:
    try:
        result = _factory(db).evaluate_convergence(
            proposal_id,
            max_rounds=3,
            blocker_threshold=1,
            compliance_threshold=0.7,
            reviewer_agreement_threshold=0.6,
            minimal_improvement_threshold=0.0,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.post("/routing-preview", response_model=ModelRoutingDecision)
def routing_preview(request: ModelRoutingRequest) -> ModelRoutingDecision:
    service = ModelRoutingService.from_config()
    return service.decide(request)


@router.post("/quota-preview", response_model=QuotaPolicyEvaluationDecision)
def quota_preview(
    request: QuotaPolicyEvaluationRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> QuotaPolicyEvaluationDecision:
    service = QuotaPolicyService(db)
    decision = service.evaluate(request)
    db.commit()
    return decision
