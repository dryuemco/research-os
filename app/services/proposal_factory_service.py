from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.common.enums import ProposalState
from app.domain.proposal_factory.models import (
    Proposal,
    ProposalSection,
    ProposalVersion,
    ReviewComment,
    ReviewRound,
)
from app.schemas.audit import AuditEventSchema
from app.schemas.proposal import (
    ConceptNoteInputContext,
    ConceptNoteOutput,
    ConvergenceResult,
    ReviewerFeedback,
    ReviewRoundCreateRequest,
    SectionDraftRequest,
)
from app.services.audit_service import AuditService
from app.services.prompt_registry_service import PromptRegistryService
from app.services.proposal_service import ProposalService


class ProposalFactoryService:
    def __init__(self, db: Session, prompt_registry: PromptRegistryService) -> None:
        self.db = db
        self.prompt_registry = prompt_registry
        self.audit = AuditService(db)
        self.proposal_service = ProposalService(db)

    def create_concept_note(self, request: ConceptNoteInputContext) -> ProposalVersion:
        proposal = self._get_proposal(request.proposal_id)
        if proposal.state == ProposalState.CREATED:
            self.proposal_service.transition_state(
                proposal,
                ProposalState.STRATEGY_PENDING,
                actor_type="user",
                actor_id=proposal.owner_id,
                reason="concept note requested",
            )

        _ = self.prompt_registry.get_prompt("call_parser")
        concept_note = ConceptNoteOutput(
            summary=request.problem_statement,
            strategic_fit="Pending provider execution",
            impact_thesis="Pending provider execution",
            implementation_outline="Pending provider execution",
            risks=request.constraints,
            assumptions=["Generated via stubbed proposal factory"],
        )

        version_number = proposal.latest_version_number + 1
        version = ProposalVersion(
            proposal_id=proposal.id,
            version_number=version_number,
            concept_note_json=concept_note.model_dump(mode="json"),
            section_plan_json=[],
            status="concept_note_ready",
        )
        self.db.add(version)

        proposal.latest_version_number = version_number
        self.proposal_service.transition_state(
            proposal,
            ProposalState.CONCEPT_NOTE_READY,
            actor_type="system",
            actor_id="proposal_factory",
            reason="concept note version persisted",
        )

        self.audit.emit(
            AuditEventSchema(
                event_type="concept_note_created",
                entity_type="proposal_version",
                entity_id=version.id,
                actor_type="system",
                actor_id="proposal_factory",
                payload={"proposal_id": proposal.id, "version_number": version_number},
            )
        )
        self.db.flush()
        return version

    def create_section_draft(self, request: SectionDraftRequest) -> ProposalSection:
        proposal = self._get_proposal(request.proposal_id)
        if proposal.state == ProposalState.CONCEPT_NOTE_READY:
            self.proposal_service.transition_state(
                proposal,
                ProposalState.DRAFTING,
                actor_type="system",
                actor_id="proposal_factory",
                reason="section drafting started",
            )

        section = ProposalSection(
            proposal_id=proposal.id,
            section_key=request.section_key,
            draft_text="[stub] draft pending provider execution",
            model_provider="stub",
            model_name=request.writer_policy_id,
            prompt_version="v1",
            source_request_json=request.model_dump(mode="json"),
            round_number=request.round_number,
            status="stubbed",
            review_status="pending",
        )
        self.db.add(section)
        self.db.flush()

        self.audit.emit(
            AuditEventSchema(
                event_type="section_draft_created",
                entity_type="proposal_section",
                entity_id=section.id,
                actor_type="system",
                actor_id="proposal_factory",
                payload={"proposal_id": proposal.id, "section_key": request.section_key},
            )
        )
        self.db.flush()
        return section

    def create_review_round(self, request: ReviewRoundCreateRequest) -> ReviewRound:
        proposal = self._get_proposal(request.proposal_id)
        if proposal.state in {ProposalState.DRAFTING, ProposalState.REVISION_PENDING}:
            self.proposal_service.transition_state(
                proposal,
                ProposalState.IN_REVIEW,
                actor_type="system",
                actor_id="proposal_factory",
                reason="review round created",
            )

        next_round = self.db.scalar(
            select(func.coalesce(func.max(ReviewRound.round_number), 0)).where(
                ReviewRound.proposal_id == request.proposal_id
            )
        )
        round_model = ReviewRound(
            proposal_id=request.proposal_id,
            round_number=(next_round or 0) + 1,
            status="created",
            reviewer_roles=request.reviewer_roles,
        )
        self.db.add(round_model)
        self.db.flush()

        self.audit.emit(
            AuditEventSchema(
                event_type="review_round_created",
                entity_type="review_round",
                entity_id=round_model.id,
                actor_type="system",
                actor_id="proposal_factory",
                payload={
                    "proposal_id": request.proposal_id,
                    "round_number": round_model.round_number,
                },
            )
        )
        self.db.flush()
        return round_model

    def add_reviewer_feedback(self, feedback: ReviewerFeedback) -> ReviewComment:
        round_model = self.db.get(ReviewRound, feedback.review_round_id)
        if round_model is None:
            raise ValueError("Review round not found")

        comment = ReviewComment(
            review_round_id=feedback.review_round_id,
            reviewer_role=feedback.reviewer_role,
            severity=feedback.severity,
            blocker=feedback.blocker,
            issue_code=feedback.issue_code,
            comment_text=feedback.comment_text,
            metadata_json={"scores": feedback.scores, "must_fix": feedback.must_fix},
        )
        self.db.add(comment)
        self.db.flush()
        self.audit.emit(
            AuditEventSchema(
                event_type="review_comment_added",
                entity_type="review_comment",
                entity_id=comment.id,
                actor_type="user",
                actor_id=feedback.reviewer_role,
                payload={"review_round_id": feedback.review_round_id, "blocker": feedback.blocker},
            )
        )
        self.db.flush()
        return comment

    def evaluate_convergence(
        self,
        proposal_id: str,
        *,
        max_rounds: int,
        blocker_threshold: int,
        compliance_threshold: float,
        reviewer_agreement_threshold: float,
        minimal_improvement_threshold: float,
    ) -> ConvergenceResult:
        review_rounds = self.db.scalars(
            select(ReviewRound)
            .where(ReviewRound.proposal_id == proposal_id)
            .order_by(ReviewRound.round_number.asc())
        ).all()
        if not review_rounds:
            return ConvergenceResult(
                should_stop=False,
                decision="repeat",
                reason="no_review_rounds",
                unresolved_issues=[],
            )

        latest_round = review_rounds[-1]
        comments = self.db.scalars(
            select(ReviewComment).where(ReviewComment.review_round_id == latest_round.id)
        ).all()
        blocker_count = sum(1 for comment in comments if comment.blocker)
        compliance_scores = [
            comment.metadata_json.get("scores", {}).get("compliance", 0.0) for comment in comments
        ]
        compliance_average = sum(compliance_scores) / max(len(compliance_scores), 1)
        approvals = sum(
            1
            for comment in comments
            if comment.metadata_json.get("scores", {}).get("overall", 0.0) >= compliance_threshold
        )
        agreement_ratio = approvals / max(len(comments), 1)

        unresolved = [
            {
                "issue_code": comment.issue_code or "unspecified",
                "role": comment.reviewer_role,
                "details": comment.comment_text,
                "blocker": comment.blocker,
            }
            for comment in comments
            if comment.blocker
        ]

        if latest_round.round_number >= max_rounds:
            return ConvergenceResult(
                should_stop=True,
                decision="escalate",
                reason="max_rounds_reached",
                unresolved_issues=unresolved,
            )

        if blocker_count >= blocker_threshold:
            has_red_team_blocker = any(
                comment.blocker and comment.reviewer_role == "red_team" for comment in comments
            )
            if has_red_team_blocker:
                return ConvergenceResult(
                    should_stop=True,
                    decision="escalate",
                    reason="persistent_red_team_blocker",
                    unresolved_issues=unresolved,
                )

            return ConvergenceResult(
                should_stop=False,
                decision="repeat",
                reason="blocker_threshold_not_met",
                unresolved_issues=unresolved,
            )

        if compliance_average < compliance_threshold:
            return ConvergenceResult(
                should_stop=False,
                decision="repeat",
                reason="compliance_below_threshold",
                unresolved_issues=unresolved,
            )

        if agreement_ratio < reviewer_agreement_threshold:
            return ConvergenceResult(
                should_stop=False,
                decision="repeat",
                reason="reviewer_agreement_below_threshold",
                unresolved_issues=unresolved,
            )

        if minimal_improvement_threshold > 0 and len(review_rounds) > 1:
            return ConvergenceResult(
                should_stop=False,
                decision="repeat",
                reason="improvement_signal_required",
                unresolved_issues=unresolved,
            )

        proposal = self._get_proposal(proposal_id)
        self.proposal_service.transition_state(
            proposal,
            ProposalState.APPROVED_FOR_EXPORT,
            actor_type="user",
            actor_id=proposal.owner_id,
            reason="convergence thresholds met",
        )

        return ConvergenceResult(
            should_stop=True,
            decision="stop",
            reason="converged",
            unresolved_issues=unresolved,
        )

    def _get_proposal(self, proposal_id: str) -> Proposal:
        proposal = self.db.get(Proposal, proposal_id)
        if proposal is None:
            raise ValueError("Proposal not found")
        return proposal
