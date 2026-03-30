from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.common.enums import OpportunityState
from app.domain.opportunity_discovery.models import InterestProfile, MatchResult, Opportunity
from app.schemas.audit import AuditEventSchema
from app.schemas.matching import InterestProfileParameters, MatchRequest, MatchResultSchema
from app.services.audit_service import AuditService
from app.services.opportunity_state_service import OpportunityStateService


@dataclass
class ScoringPolicy:
    policy_id: str

    def score(
        self, *, profile: InterestProfileParameters, opportunity: Opportunity
    ) -> MatchResultSchema:
        text = f"{opportunity.title} {opportunity.summary}".lower()
        hard_filter_reasons: list[str] = []

        if profile.allowed_programs and opportunity.source_program not in profile.allowed_programs:
            hard_filter_reasons.append("program_not_allowed")
        if opportunity.source_program in profile.blocked_programs:
            hard_filter_reasons.append("program_blocked")
        if profile.min_budget_total and (opportunity.budget_total or 0) < profile.min_budget_total:
            hard_filter_reasons.append("budget_below_minimum")
        for keyword in profile.required_keywords:
            if keyword.lower() not in text:
                hard_filter_reasons.append(f"missing_required_keyword:{keyword}")

        hard_filter_pass = len(hard_filter_reasons) == 0

        preferred_hits = sum(1 for k in profile.preferred_keywords if k.lower() in text)
        keyword_score = (preferred_hits / max(len(profile.preferred_keywords), 1)) * 100

        budget_score = 100.0
        if profile.min_budget_total and opportunity.budget_total:
            budget_score = min(100.0, (opportunity.budget_total / profile.min_budget_total) * 100)

        weights = profile.weights
        total_score = keyword_score * weights.get(
            "keyword_overlap", 0.6
        ) + budget_score * weights.get("budget_fit", 0.4)

        red_flags: list[str] = []
        if opportunity.deadline_at:
            try:
                deadline = datetime.fromisoformat(opportunity.deadline_at)
                days_left = (deadline - datetime.now(UTC)).days
                if (
                    profile.max_days_to_deadline is not None
                    and days_left > profile.max_days_to_deadline
                ):
                    hard_filter_reasons.append("deadline_too_far")
                    hard_filter_pass = False
                if days_left <= 14:
                    red_flags.append("deadline_soon")
            except ValueError:
                red_flags.append("deadline_unparseable")

        recommendation = "reject"
        if hard_filter_pass and total_score >= 70:
            recommendation = "pursue"
        elif hard_filter_pass and total_score >= 50:
            recommendation = "monitor"

        explanations = [
            f"keyword_score={keyword_score:.1f}",
            f"budget_score={budget_score:.1f}",
            f"weighted_total={total_score:.1f}",
        ]

        return MatchResultSchema(
            opportunity_id=opportunity.id,
            hard_filter_pass=hard_filter_pass,
            hard_filter_reasons=hard_filter_reasons,
            scores={"keyword_overlap": keyword_score, "budget_fit": budget_score},
            total_score=total_score,
            explanations=explanations,
            rationale={
                "preferred_keyword_hits": preferred_hits,
                "weights": weights,
                "score_drivers": ["keyword_overlap", "budget_fit"],
            },
            recommendation=recommendation,
            recommended_role=profile.target_roles[0] if profile.target_roles else None,
            red_flags=red_flags,
        )


class MatchingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.state_service = OpportunityStateService(db)
        self.audit = AuditService(db)

    def _get_policy(self, policy_id: str) -> ScoringPolicy:
        return ScoringPolicy(policy_id=policy_id)

    def run_match(self, request: MatchRequest) -> list[MatchResult]:
        profile = self.db.get(InterestProfile, request.profile_id)
        if profile is None:
            raise ValueError("Interest profile not found")

        profile_parameters = InterestProfileParameters.model_validate(profile.parameters_json)
        opportunities = self.db.scalars(
            select(Opportunity).where(Opportunity.id.in_(request.opportunity_ids))
        ).all()
        policy = self._get_policy(request.scoring_policy_id)

        persisted_results: list[MatchResult] = []
        for opportunity in opportunities:
            result = policy.score(profile=profile_parameters, opportunity=opportunity)
            persisted = MatchResult(
                opportunity_id=result.opportunity_id,
                profile_id=request.profile_id,
                scoring_policy_id=request.scoring_policy_id,
                hard_filter_pass=result.hard_filter_pass,
                hard_filter_reasons=result.hard_filter_reasons,
                scores=result.scores,
                total_score=result.total_score,
                explanations=result.explanations,
                rationale=result.rationale,
                recommendation=result.recommendation,
                recommended_role=result.recommended_role,
                red_flags=result.red_flags,
            )
            self.db.add(persisted)
            self.db.flush()
            persisted_results.append(persisted)

            self.audit.emit(
                AuditEventSchema(
                    event_type="opportunity_matched",
                    entity_type="match_result",
                    entity_id=persisted.id,
                    actor_type="system",
                    actor_id="matching_engine",
                    payload={
                        "opportunity_id": opportunity.id,
                        "policy_id": request.scoring_policy_id,
                        "recommendation": result.recommendation,
                    },
                )
            )

            if opportunity.state == OpportunityState.NORMALIZED:
                self.state_service.transition_state(
                    opportunity,
                    OpportunityState.SCORED,
                    actor_type="system",
                    actor_id="matching_engine",
                    reason=f"policy={request.scoring_policy_id}",
                )
                if result.recommendation == "pursue":
                    self.state_service.transition_state(
                        opportunity,
                        OpportunityState.SHORTLISTED,
                        actor_type="system",
                        actor_id="matching_engine",
                        reason="high score recommendation",
                    )

        return persisted_results

    def list_matches(self, profile_id: str | None = None) -> list[MatchResult]:
        stmt = select(MatchResult)
        if profile_id:
            stmt = stmt.where(MatchResult.profile_id == profile_id)
        return self.db.scalars(stmt.order_by(MatchResult.created_at.desc())).all()
