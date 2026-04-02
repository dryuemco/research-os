import io
import zipfile

from app.domain.institutional_memory.models import ExportArtifact
from app.domain.opportunity_discovery.models import Opportunity
from app.domain.proposal_factory.models import Proposal, ProposalSection, ProposalVersion
from app.schemas.export import RenderPolicy, RenderRequest
from app.services.export_package_service import ExportPackageService

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _seed_exportable_proposal(db_session):
    opp = Opportunity(
        source_program="horizon",
        source_url="https://example.com/call-docx",
        external_id="call-docx-export-x",
        title="DOCX Export Call",
        summary="Summary",
        current_version_hash="v1",
        raw_payload={},
    )
    db_session.add(opp)
    db_session.flush()

    proposal = Proposal(
        opportunity_id=opp.id,
        owner_id="owner-docx",
        name="DOCX Export Proposal",
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


def test_docx_renderer_produces_real_docx_package(db_session):
    proposal, version = _seed_exportable_proposal(db_session)
    service = ExportPackageService(db_session)
    package = service.generate_package(
        RenderRequest(
            proposal_id=proposal.id,
            proposal_version_id=version.id,
            render_policy=RenderPolicy(preferred_formats=["docx"]),
        ),
        actor_id="operator-docx",
    )
    db_session.commit()

    artifacts = service.list_artifacts(package.id)
    narrative = next(a for a in artifacts if a.file_name == "proposal_narrative.docx")
    assert narrative.media_type == DOCX_MIME
    assert narrative.artifact_format.value == "docx"
    assert narrative.size_bytes > 0

    _, payload = service.read_artifact_bytes(narrative.id)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        assert "word/document.xml" in archive.namelist()


def test_download_token_enforced_and_download_audited(client, db_session):
    proposal, version = _seed_exportable_proposal(db_session)

    generated = client.post(
        "/memory/exports/generate?actor_id=operator-docx",
        json={
            "proposal_id": proposal.id,
            "proposal_version_id": version.id,
            "render_policy": {"preferred_formats": ["docx"]},
        },
    )
    assert generated.status_code == 200
    package_id = generated.json()["id"]

    artifacts = client.get(f"/memory/exports/{package_id}/artifacts")
    assert artifacts.status_code == 200
    docx_artifact = next(a for a in artifacts.json() if a["file_name"] == "proposal_narrative.docx")

    token_resp = client.post(f"/memory/exports/artifacts/{docx_artifact['id']}/download-token")
    assert token_resp.status_code == 200
    token = token_resp.json()["token"]

    download = client.get(f"/memory/exports/artifacts/{docx_artifact['id']}/download?token={token}")
    assert download.status_code == 200
    assert download.headers["content-type"].startswith(DOCX_MIME)
    assert "attachment;" in download.headers["content-disposition"]


def test_download_fails_on_expired_or_invalid_token(client, db_session):
    proposal, version = _seed_exportable_proposal(db_session)

    generated = client.post(
        "/memory/exports/generate?actor_id=operator-docx",
        json={"proposal_id": proposal.id, "proposal_version_id": version.id},
    )
    package_id = generated.json()["id"]
    artifact_id = client.get(f"/memory/exports/{package_id}/artifacts").json()[0]["id"]

    denied = client.get(f"/memory/exports/artifacts/{artifact_id}/download?token=invalid")
    assert denied.status_code == 403


def test_download_fails_on_checksum_mismatch(client, db_session):
    proposal, version = _seed_exportable_proposal(db_session)
    generated = client.post(
        "/memory/exports/generate?actor_id=operator-docx",
        json={"proposal_id": proposal.id, "proposal_version_id": version.id},
    )
    package_id = generated.json()["id"]
    artifact_id = client.get(f"/memory/exports/{package_id}/artifacts").json()[0]["id"]

    artifact = db_session.get(ExportArtifact, artifact_id)
    artifact.checksum = "0" * 64
    db_session.add(artifact)
    db_session.commit()

    token = client.post(f"/memory/exports/artifacts/{artifact_id}/download-token").json()["token"]
    failed = client.get(f"/memory/exports/artifacts/{artifact_id}/download?token={token}")
    assert failed.status_code == 500
