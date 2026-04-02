import pytest

from app.domain.common.enums import ExportPackageStatus
from app.domain.opportunity_discovery.models import Opportunity
from app.domain.proposal_factory.models import (
    Proposal,
    ProposalSection,
    ProposalVersion,
    ReviewComment,
    ReviewRound,
)
from app.schemas.export import ExportStateTransitionRequest, RenderRequest
from app.services.export_package_service import ExportPackageService, InvalidExportTransitionError


def _seed_proposal_with_content(db_session):
    opp = Opportunity(
        source_program="horizon",
        source_url="https://example.com/call-x",
        external_id="call-export-x",
        title="Export Call",
        summary="Summary",
        current_version_hash="v1",
        raw_payload={},
    )
    db_session.add(opp)
    db_session.flush()

    proposal = Proposal(
        opportunity_id=opp.id,
        owner_id="owner-1",
        name="Exportable Proposal",
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
        concept_note_json={"summary": "concept"},
        section_plan_json=[],
    )
    db_session.add(version)

    db_session.add(
        ProposalSection(
            proposal_id=proposal.id,
            section_key="impact",
            draft_text="Impact text",
            model_provider="mock-local",
            model_name="writer-medium",
            prompt_version="v1",
            source_request_json={},
            status="drafted",
        )
    )
    round_model = ReviewRound(
        proposal_id=proposal.id,
        round_number=1,
        reviewer_roles=["scientific"],
    )
    db_session.add(round_model)
    db_session.flush()
    db_session.add(
        ReviewComment(
            review_round_id=round_model.id,
            reviewer_role="scientific",
            severity="major",
            blocker=False,
            comment_text="Needs more measurable KPI",
            metadata_json={},
        )
    )
    db_session.commit()
    return proposal, version


def test_generate_export_package_with_artifacts(db_session):
    proposal, version = _seed_proposal_with_content(db_session)
    service = ExportPackageService(db_session)
    package = service.generate_package(
        RenderRequest(proposal_id=proposal.id, proposal_version_id=version.id),
        actor_id="operator-1",
    )
    db_session.commit()

    assert package.status == ExportPackageStatus.READY_FOR_REVIEW
    artifacts = service.list_artifacts(package.id)
    assert artifacts
    assert any(item.file_name == "proposal_narrative.md" for item in artifacts)
    assert any(item.file_name == "reviewer_log.md" for item in artifacts)


def test_export_transition_requires_human_approval_on_proposal(db_session):
    proposal, version = _seed_proposal_with_content(db_session)
    proposal.human_approved_for_export = False
    db_session.add(proposal)
    db_session.commit()

    service = ExportPackageService(db_session)
    package = service.generate_package(
        RenderRequest(proposal_id=proposal.id, proposal_version_id=version.id),
        actor_id="operator-1",
    )
    db_session.commit()

    with pytest.raises(InvalidExportTransitionError):
        service.transition_status(
            package.id,
            ExportStateTransitionRequest(
                target_status=ExportPackageStatus.APPROVED,
                actor_id="reviewer-1",
            ),
        )


def test_submission_pack_contains_manifest_and_artifacts(db_session):
    proposal, version = _seed_proposal_with_content(db_session)
    service = ExportPackageService(db_session)
    package = service.generate_package(
        RenderRequest(proposal_id=proposal.id, proposal_version_id=version.id),
        actor_id="operator-1",
    )
    db_session.commit()

    pack = service.build_submission_pack(package.id)
    assert pack["proposal_id"] == proposal.id
    assert pack["artifacts"]
    assert any(a["artifact_type"] == "export_manifest" for a in pack["artifacts"])


def test_read_artifact_content_falls_back_to_db_text_when_storage_file_missing(db_session):
    proposal, version = _seed_proposal_with_content(db_session)
    service = ExportPackageService(db_session)
    package = service.generate_package(
        RenderRequest(proposal_id=proposal.id, proposal_version_id=version.id),
        actor_id="operator-1",
    )
    db_session.commit()

    artifact = next(
        a for a in service.list_artifacts(package.id) if a.file_name == "proposal_narrative.md"
    )
    artifact.storage_locator = "missing/path/proposal_narrative.md"
    db_session.add(artifact)
    db_session.commit()

    content = service.read_artifact_content(artifact.id)
    assert "Exportable Proposal" in content
