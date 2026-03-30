import pytest
from sqlalchemy import text

from app.domain.common.enums import DecompositionState, OpportunityState, ProposalState
from app.domain.opportunity_discovery.models import Opportunity
from app.schemas.execution import (
    AcceptanceCriteriaBlock,
    DecompositionRequest,
    PlanningPolicy,
    ProposalContextSummary,
    TaskOutput,
    ValidationPlanBlock,
)
from app.schemas.proposal import ProposalWorkspaceCreateRequest
from app.services.decomposition_service import (
    DecompositionService,
    InvalidDecompositionTransitionError,
)
from app.services.proposal_service import ProposalService


def _proposal_workspace(db_session):
    opportunity = Opportunity(
        source_program="Horizon Europe",
        source_url="https://example.com/call",
        external_id="opp-decompose",
        title="Example",
        summary="Summary",
        deadline_at=None,
        call_status="open",
        budget_total=1000,
        currency="EUR",
        state=OpportunityState.APPROVED,
        current_version_hash="hash-1",
        raw_payload={},
    )
    db_session.add(opportunity)
    db_session.flush()

    proposal = ProposalService(db_session).create_workspace(
        ProposalWorkspaceCreateRequest(
            opportunity_id=opportunity.id,
            owner_id="user-1",
            name="Exec Workspace",
            template_type="generic",
        )
    )
    ProposalService(db_session).transition_state(
        proposal,
        ProposalState.STRATEGY_PENDING,
        actor_type="user",
        actor_id="user-1",
    )
    return proposal


def test_decomposition_transition_requires_human_approval(db_session):
    proposal = _proposal_workspace(db_session)
    service = DecompositionService(db_session)
    plan = service.create_decomposition(
        DecompositionRequest(
            proposal_id=proposal.id,
            plan_name="Plan A",
            context=ProposalContextSummary(
                proposal_id=proposal.id,
                title="Title",
                concept_summary="Summary",
            ),
            policy=PlanningPolicy(
                task_granularity="medium",
                decomposition_depth=2,
                ticket_detail_level="engineering",
                provider_sensitivity_classification="restricted",
                repository_risk_tier="medium",
                human_approval_threshold="all_high_risk",
            ),
        )
    )
    service.transition_state(
        plan, DecompositionState.UNDER_REVIEW, actor_type="user", actor_id="u1"
    )
    with pytest.raises(InvalidDecompositionTransitionError):
        service.transition_state(
            plan, DecompositionState.APPROVED, actor_type="system", actor_id="svc"
        )


def test_ticket_and_handoff_generation(db_session):
    proposal = _proposal_workspace(db_session)
    service = DecompositionService(db_session)
    plan = service.create_decomposition(
        DecompositionRequest(
            proposal_id=proposal.id,
            plan_name="Plan B",
            context=ProposalContextSummary(
                proposal_id=proposal.id,
                title="Title",
                concept_summary="Summary",
            ),
            policy=PlanningPolicy(
                task_granularity="fine",
                decomposition_depth=3,
                ticket_detail_level="engineering",
                provider_sensitivity_classification="restricted",
                repository_risk_tier="high",
                human_approval_threshold="all",
            ),
        )
    )

    tasks = [
        TaskOutput(
            task_code="TASK-1",
            work_package_ref="WP-1",
            title="Implement endpoint",
            description="Build endpoint",
            priority="high",
            owner_role="backend",
            required_capabilities=["fastapi"],
            required_context=["ctx-1"],
            acceptance_criteria=AcceptanceCriteriaBlock(criteria=["endpoint returns 200"]),
            validation_plan=ValidationPlanBlock(checks=["pytest"], evidence_required=["test log"]),
            estimated_complexity="medium",
            blocked=False,
        )
    ]

    graph = service.generate_task_graph(plan.id, tasks)
    assert graph.graph_json["nodes"] == ["TASK-1"]

    tickets = service.generate_engineering_tickets(
        plan.id, tasks, repository_target={"repository": "rpos/api"}
    )
    assert tickets[0].branch_suggestion.startswith("feat/")

    handoff = service.generate_coding_handoff_pack(plan.id)
    assert len(handoff.work_units) == 1

    events = db_session.execute(text("SELECT count(*) FROM audit_events")).scalar_one()
    assert events >= 4
