from app.domain.opportunity_discovery.models import Opportunity
from app.domain.proposal_factory.models import Proposal, ProposalSection, ProposalVersion
from app.schemas.export import RenderPolicy
from app.services.renderers.selector import ExportRendererSelector


def _seed(db_session):
    opp = Opportunity(
        source_program="horizon",
        source_url="https://example.com/call-r",
        external_id="call-r",
        title="Call",
        summary="Summary",
        current_version_hash="v1",
        raw_payload={},
    )
    db_session.add(opp)
    db_session.flush()

    proposal = Proposal(
        opportunity_id=opp.id,
        owner_id="owner-1",
        name="Proposal",
        template_type="ria",
        mandatory_sections=["impact"],
        compliance_rules=[],
        human_approved_for_export=True,
    )
    db_session.add(proposal)
    db_session.flush()
    db_session.add(
        ProposalVersion(
            proposal_id=proposal.id,
            version_number=1,
            concept_note_json={"summary": "x"},
            section_plan_json=[],
        )
    )
    db_session.add(
        ProposalSection(
            proposal_id=proposal.id,
            section_key="impact",
            draft_text="Impact",
            model_provider="mock-local",
            model_name="writer",
            prompt_version="v1",
            source_request_json={},
            status="drafted",
        )
    )
    db_session.commit()


def test_renderer_selector_prefers_docx_when_requested(db_session):
    _seed(db_session)
    renderer = ExportRendererSelector(db_session).resolve(RenderPolicy(preferred_formats=["docx"]))
    assert renderer.renderer_name == "docx-v1"


def test_renderer_selector_falls_back_to_markdown(db_session):
    _seed(db_session)
    renderer = ExportRendererSelector(db_session).resolve(
        RenderPolicy(preferred_formats=["pdf", "markdown"])
    )
    assert renderer.renderer_name == "markdown-v1"
