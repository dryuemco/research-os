from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.proposal_factory.models import ReviewComment, ReviewRound
from app.schemas.intelligence import ProposalQualitySummary, QualityIssue, QualityIssueCategory

_SEVERITY_WEIGHT = {"critical": 1.0, "major": 0.7, "minor": 0.4, "info": 0.2}
_CATEGORY_HINTS = {
    QualityIssueCategory.COMPLIANCE: ["compliance", "eligibility", "mandatory"],
    QualityIssueCategory.IMPACT: ["impact", "kpi", "outcome"],
    QualityIssueCategory.CLARITY: ["clear", "vague", "clarity"],
    QualityIssueCategory.FEASIBILITY: ["feasible", "timeline", "risk"],
    QualityIssueCategory.IMPLEMENTATION: ["implementation", "work package", "deliverable"],
    QualityIssueCategory.RELEVANCE: ["relevance", "fit", "scope"],
    QualityIssueCategory.COHERENCE: ["coherent", "consistency", "alignment"],
    QualityIssueCategory.NOVELTY: ["novel", "innovation", "original"],
}


class ProposalQualityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def summarize(
        self, proposal_id: str, round_number: int | None = None
    ) -> ProposalQualitySummary:
        round_model = self._resolve_round(proposal_id, round_number)
        comments = self.db.scalars(
            select(ReviewComment).where(ReviewComment.review_round_id == round_model.id)
        ).all()

        issues = self._aggregate_issues(comments)
        blocker_count = sum(1 for i in issues if i.blocker)
        disagreements = self._disagreement_count(comments)
        persistent_red_team_blocker = any(
            c.reviewer_role == "red_team" and c.blocker for c in comments
        )

        dimension_scores = self._dimension_scores(issues)
        overall = round(sum(dimension_scores.values()) / max(len(dimension_scores), 1), 4)

        next_action = "revise"
        if blocker_count == 0 and overall >= 0.72:
            next_action = "accept_for_export"
        elif blocker_count > 0 and persistent_red_team_blocker:
            next_action = "escalate"

        rationale = [
            f"issues={len(issues)}",
            f"blockers={blocker_count}",
            f"disagreements={disagreements}",
            f"overall={overall:.2f}",
        ]

        return ProposalQualitySummary(
            proposal_id=proposal_id,
            round_number=round_model.round_number,
            dimension_scores=dimension_scores,
            overall_score=overall,
            blocker_count=blocker_count,
            disagreement_count=disagreements,
            persistent_red_team_blocker=persistent_red_team_blocker,
            top_issues=sorted(issues, key=lambda i: i.priority_score, reverse=True)[:8],
            next_action_recommendation=next_action,
            rationale=rationale,
        )

    def _resolve_round(self, proposal_id: str, round_number: int | None) -> ReviewRound:
        stmt = select(ReviewRound).where(ReviewRound.proposal_id == proposal_id)
        if round_number is not None:
            stmt = stmt.where(ReviewRound.round_number == round_number)
        stmt = stmt.order_by(ReviewRound.round_number.desc())
        round_model = self.db.scalar(stmt)
        if round_model is None:
            raise ValueError("No review round found for proposal")
        return round_model

    def _aggregate_issues(self, comments: list[ReviewComment]) -> list[QualityIssue]:
        grouped: dict[str, list[ReviewComment]] = defaultdict(list)
        for comment in comments:
            key = self._issue_key(comment.comment_text)
            grouped[key].append(comment)

        issues: list[QualityIssue] = []
        for _key, group in grouped.items():
            sample = group[0]
            category = self._classify_category(sample.comment_text)
            severity_weight = max(_SEVERITY_WEIGHT.get(item.severity, 0.3) for item in group)
            blocker = any(item.blocker for item in group)
            reviewer_bonus = min(0.3, len({g.reviewer_role for g in group}) * 0.08)
            priority = round(severity_weight + reviewer_bonus + (0.25 if blocker else 0.0), 4)
            issues.append(
                QualityIssue(
                    category=category,
                    severity=sample.severity,
                    blocker=blocker,
                    issue_text=sample.comment_text,
                    reviewers=[g.reviewer_role for g in group],
                    priority_score=priority,
                )
            )
        return issues

    def _dimension_scores(self, issues: list[QualityIssue]) -> dict[str, float]:
        base = {
            key.value: 1.0
            for key in [
                QualityIssueCategory.RELEVANCE,
                QualityIssueCategory.CLARITY,
                QualityIssueCategory.NOVELTY,
                QualityIssueCategory.FEASIBILITY,
                QualityIssueCategory.COMPLIANCE,
                QualityIssueCategory.COHERENCE,
                QualityIssueCategory.IMPACT,
                QualityIssueCategory.IMPLEMENTATION,
            ]
        }
        for issue in issues:
            penalty = min(0.7, issue.priority_score * 0.4)
            base[issue.category.value] = round(max(0.0, base[issue.category.value] - penalty), 4)
        return base

    def _disagreement_count(self, comments: list[ReviewComment]) -> int:
        disagreement = 0
        by_key: dict[str, set[str]] = defaultdict(set)
        for comment in comments:
            by_key[self._issue_key(comment.comment_text)].add(comment.severity)
        for severities in by_key.values():
            if len(severities) > 1:
                disagreement += 1
        return disagreement

    def _classify_category(self, text: str) -> QualityIssueCategory:
        lowered = text.lower()
        for category, hints in _CATEGORY_HINTS.items():
            if any(h in lowered for h in hints):
                return category
        return QualityIssueCategory.COHERENCE

    def _issue_key(self, text: str) -> str:
        tokens = [t.lower().strip(".,:;!?()[]") for t in text.split() if t.strip()]
        return " ".join(tokens[:8])
