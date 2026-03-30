from app.domain.common.enums import OpportunityState
from app.domain.opportunity_discovery.models import Opportunity


def _approved_workspace(client, db_session):
    opp = Opportunity(
        source_program="Horizon Europe",
        source_url="https://example.com",
        external_id="opp-api-decompose",
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
    db_session.add(opp)
    db_session.flush()

    resp = client.post(
        "/proposal-factory/workspaces",
        json={
            "opportunity_id": opp.id,
            "owner_id": "user-1",
            "name": "Workspace",
            "template_type": "generic",
        },
    )
    return resp.json()["id"]


def test_decomposition_api_smoke(client, db_session):
    proposal_id = _approved_workspace(client, db_session)
    create = client.post(
        "/decomposition",
        json={
            "proposal_id": proposal_id,
            "plan_name": "Plan API",
            "context": {
                "proposal_id": proposal_id,
                "title": "Execution",
                "concept_summary": "Build modules",
                "key_constraints": [],
            },
            "policy": {
                "task_granularity": "medium",
                "decomposition_depth": 2,
                "ticket_detail_level": "engineering",
                "provider_sensitivity_classification": "restricted",
                "repository_risk_tier": "medium",
                "human_approval_threshold": "all",
            },
        },
    )
    assert create.status_code == 200
    plan_id = create.json()["id"]

    get_resp = client.get(f"/decomposition/{plan_id}")
    assert get_resp.status_code == 200

    task_graph = client.post(
        f"/decomposition/{plan_id}/task-graph",
        json=[
            {
                "task_code": "TASK-1",
                "work_package_ref": "WP-1",
                "title": "Task",
                "description": "Desc",
                "priority": "high",
                "owner_role": "backend",
                "required_capabilities": ["python"],
                "required_context": ["ctx"],
                "acceptance_criteria": {"criteria": ["done"]},
                "validation_plan": {"checks": ["pytest"], "evidence_required": ["log"]},
                "estimated_complexity": "medium",
                "blocked": False,
            }
        ],
    )
    assert task_graph.status_code == 200

    tickets = client.post(
        f"/decomposition/{plan_id}/tickets",
        json=[
            {
                "task_code": "TASK-1",
                "work_package_ref": "WP-1",
                "title": "Task",
                "description": "Desc",
                "priority": "high",
                "owner_role": "backend",
                "required_capabilities": ["python"],
                "required_context": ["ctx"],
                "acceptance_criteria": {"criteria": ["done"]},
                "validation_plan": {"checks": ["pytest"], "evidence_required": ["log"]},
                "estimated_complexity": "medium",
                "blocked": False,
            }
        ],
    )
    assert tickets.status_code == 200

    handoff = client.post(f"/decomposition/{plan_id}/handoff")
    assert handoff.status_code == 200
