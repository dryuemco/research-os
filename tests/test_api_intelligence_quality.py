from app.domain.common.enums import ApprovalStatus, MemoryCategory
from app.domain.opportunity_discovery.models import Opportunity
from app.domain.proposal_factory.models import Proposal, ReviewComment, ReviewRound
from app.schemas.memory import (
    DocumentSourceCreate,
    MemoryDocumentCreate,
    ReusableBlockCreate,
    ReusableBlockUpdate,
)
from app.services.memory_service import MemoryService


def _seed_memory_and_proposal(db_session):
    memory = MemoryService(db_session)
    source = memory.create_source(
        DocumentSourceCreate(
            source_name="api-intel",
            source_uri="internal://intel",
            source_type="internal",
        )
    )
    doc = memory.create_document(
        MemoryDocumentCreate(
            title="Intel Doc",
            category=MemoryCategory.IMPACT_EVIDENCE,
            source_id=source.id,
            content_text="Impact and AI evidence.",
        )
    )
    block = memory.create_block(
        ReusableBlockCreate(
            document_id=doc.id,
            block_key="intel_block",
            category=MemoryCategory.IMPACT_EVIDENCE,
            title="Impact Evidence",
            body_text="Impact KPI and AI evidence for evaluation",
            tags=["impact", "ai"],
        )
    )
    memory.update_block(
        block.id,
        ReusableBlockUpdate(
            approval_status=ApprovalStatus.APPROVED,
            approved_by="ops-admin",
        ),
    )

    opp = Opportunity(
        source_program="horizon",
        source_url="https://example.com/intel-call",
        external_id="intel-call-1",
        title="Intel Call",
        summary="summary",
        current_version_hash="v1",
        raw_payload={},
    )
    db_session.add(opp)
    db_session.flush()

    proposal = Proposal(
        opportunity_id=opp.id,
        owner_id="owner-intel",
        name="Intel Proposal",
        template_type="ria",
        mandatory_sections=["impact"],
        compliance_rules=[],
        human_approved_for_export=False,
    )
    db_session.add(proposal)
    db_session.flush()

    rr = ReviewRound(proposal_id=proposal.id, round_number=1, reviewer_roles=["red_team"])
    db_session.add(rr)
    db_session.flush()
    db_session.add(
        ReviewComment(
            review_round_id=rr.id,
            reviewer_role="red_team",
            severity="critical",
            blocker=True,
            comment_text="Compliance issue and unclear impact logic",
            metadata_json={},
        )
    )
    db_session.commit()
    return proposal.id


def test_intelligence_endpoints_smoke(client, db_session):
    proposal_id = _seed_memory_and_proposal(db_session)

    partner = client.post(
        "/intelligence/partners",
        json={
            "partner_name": "Gamma Tech",
            "country_code": "FR",
            "capability_tags": ["ai", "impact"],
            "role_suitability": {"coordinator": 0.6},
        },
    )
    assert partner.status_code == 200

    fit = client.post(
        "/intelligence/partners/fit",
        json={"required_capabilities": ["ai"], "preferred_countries": ["FR"], "limit": 3},
    )
    assert fit.status_code == 200
    assert fit.json()

    retrieval = client.post(
        "/intelligence/retrieval/preview",
        json={"query_text": "impact ai", "limit": 5},
    )
    assert retrieval.status_code == 200

    quality = client.get(f"/intelligence/proposal-quality/{proposal_id}")
    assert quality.status_code == 200
    assert "overall_score" in quality.json()
