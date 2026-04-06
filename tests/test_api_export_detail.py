from app.domain.opportunity_discovery.models import Opportunity
from app.domain.proposal_factory.models import Proposal, ProposalSection, ProposalVersion


def _seed_exportable_proposal(db_session):
    opp = Opportunity(
        source_program="horizon",
        source_url="https://example.com/call-api",
        external_id="call-api-export-x",
        title="API Export Call",
        summary="Summary",
        current_version_hash="v1",
        raw_payload={},
    )
    db_session.add(opp)
    db_session.flush()

    proposal = Proposal(
        opportunity_id=opp.id,
        owner_id="owner-2",
        name="API Export Proposal",
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
        concept_note_json={"summary": "x"},
        section_plan_json=[],
    )
    db_session.add(version)
    db_session.add(
        ProposalSection(
            proposal_id=proposal.id,
            section_key="impact",
            draft_text="Impact draft",
            model_provider="mock-local",
            model_name="writer-medium",
            prompt_version="v1",
            source_request_json={},
            status="drafted",
        )
    )
    db_session.commit()
    return proposal, version


def test_export_generation_and_detail_endpoints(client, db_session):
    proposal, version = _seed_exportable_proposal(db_session)

    generated = client.post(
        "/memory/exports/generate?actor_id=operator-1",
        json={"proposal_id": proposal.id, "proposal_version_id": version.id},
    )
    assert generated.status_code == 200
    package_id = generated.json()["id"]

    detail = client.get(f"/memory/exports/{package_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "ready_for_review"

    transition = client.post(
        f"/memory/exports/{package_id}/transition",
        json={"target_status": "approved", "actor_id": "reviewer-1"},
    )
    assert transition.status_code == 200

    artifacts = client.get(f"/memory/exports/{package_id}/artifacts")
    assert artifacts.status_code == 200
    assert artifacts.json()

    artifact_id = artifacts.json()[0]["id"]
    download = client.get(f"/memory/exports/artifacts/{artifact_id}/download")
    assert download.status_code == 200
    assert download.text

    pack = client.get(f"/memory/exports/{package_id}/submission-pack")
    assert pack.status_code == 200
    assert pack.json()["artifacts"]
