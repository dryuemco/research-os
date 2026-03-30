from app.domain.common.enums import OpportunityState
from app.domain.opportunity_discovery.models import Opportunity


def _seed_approved_opportunity(db_session) -> Opportunity:
    opp = Opportunity(
        source_program="Horizon Europe",
        source_url="https://example.com",
        external_id="opp-api-proposal-factory",
        title="Example Call",
        summary="Summary",
        deadline_at=None,
        call_status="open",
        budget_total=10000,
        currency="EUR",
        state=OpportunityState.APPROVED,
        current_version_hash="hash-1",
        raw_payload={},
    )
    db_session.add(opp)
    db_session.flush()
    return opp


def test_proposal_factory_api_smoke(client, db_session) -> None:
    opportunity = _seed_approved_opportunity(db_session)

    workspace_resp = client.post(
        "/proposal-factory/workspaces",
        json={
            "opportunity_id": opportunity.id,
            "owner_id": "user-1",
            "name": "Workspace API",
            "template_type": "generic",
        },
    )
    assert workspace_resp.status_code == 200
    proposal_id = workspace_resp.json()["id"]

    concept_resp = client.post(
        "/proposal-factory/concept-note",
        json={
            "proposal_id": proposal_id,
            "problem_statement": "Need AI health progress",
            "objectives": ["Objective 1"],
        },
    )
    assert concept_resp.status_code == 200

    routing_resp = client.post(
        "/proposal-factory/routing-preview",
        json={
            "task_type": "concept_note",
            "sensitivity": "standard",
            "budget_tier": "medium",
            "approved_providers": ["openai", "anthropic"],
            "local_only": False,
        },
    )
    assert routing_resp.status_code == 200

    quota_resp = client.post(
        "/proposal-factory/quota-preview",
        json={
            "provider_name": "openai",
            "account_ref": "acc-1",
            "model_name": "writer-large",
            "projected_spend": 5,
            "budget_policy": {
                "run_budget_limit": 100,
                "soft_limit_ratio": 0.8,
                "hard_stop_ratio": 1.0,
            },
        },
    )
    assert quota_resp.status_code == 200
