from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.execution_orchestrator.models import EngineeringTicket, ExecutionPlan
from app.domain.institutional_memory.models import ReusableEvidenceBlock
from app.domain.proposal_factory.models import Proposal, ProposalSection, ReviewComment, ReviewRound
from app.schemas.export import RenderRequest


def build_export_content(db: Session, request: RenderRequest) -> dict:
    proposal = db.get(Proposal, request.proposal_id)
    if proposal is None:
        raise ValueError("Proposal not found")

    sections = db.scalars(
        select(ProposalSection).where(ProposalSection.proposal_id == proposal.id)
    ).all()
    if request.render_policy.section_keys:
        allowed = set(request.render_policy.section_keys)
        sections = [s for s in sections if s.section_key in allowed]

    reviewer_comments: list[ReviewComment] = []
    if request.render_policy.include_reviewer_logs:
        rounds = db.scalars(select(ReviewRound).where(ReviewRound.proposal_id == proposal.id)).all()
        review_round_ids = [r.id for r in rounds]
        if review_round_ids:
            reviewer_comments = db.scalars(
                select(ReviewComment).where(ReviewComment.review_round_id.in_(review_round_ids))
            ).all()

    reusable_blocks: list[ReusableEvidenceBlock] = []
    if request.render_policy.include_reusable_evidence:
        reusable_blocks = db.scalars(select(ReusableEvidenceBlock)).all()

    execution_plan = None
    tickets: list[EngineeringTicket] = []
    if request.render_policy.include_decomposition:
        execution_plan = db.scalar(
            select(ExecutionPlan).where(ExecutionPlan.proposal_id == proposal.id)
        )
        if execution_plan:
            tickets = db.scalars(
                select(EngineeringTicket).where(
                    EngineeringTicket.execution_plan_id == execution_plan.id
                )
            ).all()

    return {
        "proposal": proposal,
        "sections": sections,
        "reviewer_comments": reviewer_comments,
        "reusable_blocks": reusable_blocks,
        "execution_plan": execution_plan,
        "tickets": tickets,
    }
