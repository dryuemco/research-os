from app.domain.opportunity_discovery.models import Opportunity
from app.domain.proposal_factory.models import Proposal, ReviewComment, ReviewRound
from app.services.proposal_quality_service import ProposalQualityService


def _seed_review_data(db_session):
    opp = Opportunity(
        source_program="horizon",
        source_url="https://example.com/call",
        external_id="q-call-1",
        title="Quality Call",
        summary="Summary",
        current_version_hash="v1",
        raw_payload={},
    )
    db_session.add(opp)
    db_session.flush()

    proposal = Proposal(
        opportunity_id=opp.id,
        owner_id="owner-q",
        name="Proposal Q",
        template_type="ria",
        mandatory_sections=["impact"],
        compliance_rules=[],
        human_approved_for_export=False,
    )
    db_session.add(proposal)
    db_session.flush()

    round_model = ReviewRound(
        proposal_id=proposal.id,
        round_number=1,
        reviewer_roles=["scientific", "red_team"],
    )
    db_session.add(round_model)
    db_session.flush()

    db_session.add_all(
        [
            ReviewComment(
                review_round_id=round_model.id,
                reviewer_role="scientific",
                severity="major",
                blocker=False,
                comment_text="Impact logic needs clearer KPI alignment",
                metadata_json={},
            ),
            ReviewComment(
                review_round_id=round_model.id,
                reviewer_role="red_team",
                severity="critical",
                blocker=True,
                comment_text="Compliance eligibility assumptions are not evidenced",
                metadata_json={},
            ),
        ]
    )
    db_session.commit()
    return proposal.id


def test_proposal_quality_summary_prioritizes_blockers(db_session):
    proposal_id = _seed_review_data(db_session)
    summary = ProposalQualityService(db_session).summarize(proposal_id)

    assert summary.blocker_count >= 1
    assert summary.top_issues
    assert summary.next_action_recommendation in {"revise", "escalate", "accept_for_export"}
    assert summary.persistent_red_team_blocker is True
