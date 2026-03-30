import pytest
from pydantic import ValidationError

from app.schemas.execution import DecompositionRequest, PlanningPolicy, ProposalContextSummary


def test_decomposition_request_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        DecompositionRequest(
            proposal_id="p1",
            plan_name="plan",
            context=ProposalContextSummary(proposal_id="p1", title="t", concept_summary="s"),
            policy=PlanningPolicy(
                task_granularity="medium",
                decomposition_depth=2,
                ticket_detail_level="engineering",
                provider_sensitivity_classification="restricted",
                repository_risk_tier="medium",
                human_approval_threshold="all",
            ),
            unexpected=True,
        )
