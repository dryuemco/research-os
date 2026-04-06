from app.domain.opportunity_discovery.models import Opportunity
from app.domain.proposal_factory.models import Proposal, ProposalSection, ProposalVersion


def _seed_proposal(db_session):
    opp = Opportunity(
        source_program="horizon",
        source_url="https://example.com/call-auth",
        external_id="call-auth-1",
        title="Auth Call",
        summary="Summary",
        current_version_hash="v1",
        raw_payload={},
    )
    db_session.add(opp)
    db_session.flush()
    proposal = Proposal(
        opportunity_id=opp.id,
        owner_id="owner",
        name="Protected Proposal",
        template_type="ria",
        mandatory_sections=["impact"],
        compliance_rules=[],
        human_approved_for_export=True,
    )
    db_session.add(proposal)
    db_session.flush()
    version = ProposalVersion(
        proposal_id=proposal.id,
        version_number=1,
        concept_note_json={"x": 1},
        section_plan_json=[],
    )
    db_session.add(version)
    db_session.add(
        ProposalSection(
            proposal_id=proposal.id,
            section_key="impact",
            draft_text="x",
            model_provider="mock-local",
            model_name="writer-medium",
            prompt_version="v1",
            source_request_json={},
            status="drafted",
        )
    )
    db_session.commit()
    return proposal, version


def test_permission_denied_for_export_approve(client, db_session):
    proposal, version = _seed_proposal(db_session)
    gen = client.post(
        "/memory/exports/generate?actor_id=admin-user",
        json={"proposal_id": proposal.id, "proposal_version_id": version.id},
    )
    assert gen.status_code == 200
    package_id = gen.json()["id"]

    denied = client.post(
        f"/memory/exports/{package_id}/transition",
        headers={
            "X-Internal-Api-Key": "dev-internal-key",
            "X-User-Id": "writer-1",
            "X-User-Role": "grant_writer",
        },
        json={"target_status": "approved", "actor_id": "writer-1"},
    )
    assert denied.status_code == 403


def test_permission_allowed_for_admin_export_approve(client, db_session):
    proposal, version = _seed_proposal(db_session)
    gen = client.post(
        "/memory/exports/generate?actor_id=admin-user",
        json={"proposal_id": proposal.id, "proposal_version_id": version.id},
    )
    package_id = gen.json()["id"]
    allowed = client.post(
        f"/memory/exports/{package_id}/transition",
        json={"target_status": "approved", "actor_id": "admin-user"},
    )
    assert allowed.status_code == 200
