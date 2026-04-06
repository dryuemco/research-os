from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.partner_intelligence.models import PartnerProfile
from app.schemas.intelligence import (
    PartnerFitRequest,
    PartnerFitResult,
    PartnerProfileCreate,
    PartnerProfileResponse,
)


class PartnerIntelligenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_partner(self, request: PartnerProfileCreate) -> PartnerProfile:
        partner = PartnerProfile(**request.model_dump(), active=True)
        self.db.add(partner)
        self.db.flush()
        return partner

    def list_partners(self, active_only: bool = True) -> list[PartnerProfile]:
        stmt = select(PartnerProfile)
        if active_only:
            stmt = stmt.where(PartnerProfile.active.is_(True))
        return self.db.scalars(stmt.order_by(PartnerProfile.created_at.desc())).all()

    def fit_preview(self, request: PartnerFitRequest) -> list[PartnerFitResult]:
        partners = self.list_partners(active_only=True)
        scored: list[PartnerFitResult] = []
        for partner in partners:
            capability_overlap = self._capability_overlap(request.required_capabilities, partner)
            role_score = self._role_score(request.desired_roles, partner)
            geography_score = self._geography_score(request.preferred_countries, partner)
            complementarity_score = max(0.0, 1.0 - (capability_overlap * 0.35))
            fit = round(
                (capability_overlap * 0.45)
                + (role_score * 0.25)
                + (geography_score * 0.15)
                + (complementarity_score * 0.15),
                4,
            )
            rationale = [
                f"capability_overlap={capability_overlap:.2f}",
                f"role_score={role_score:.2f}",
                f"geography_score={geography_score:.2f}",
                f"complementarity={complementarity_score:.2f}",
            ]
            red_flags: list[str] = []
            partner_caps = _normalize(partner.capability_tags)
            missing_caps = [
                cap
                for cap in request.required_capabilities
                if cap.lower() not in partner_caps
            ]
            if missing_caps:
                red_flags.append(f"missing_capabilities:{','.join(missing_caps)}")

            scored.append(
                PartnerFitResult(
                    partner=PartnerProfileResponse.model_validate(partner),
                    fit_score=fit,
                    role_score=round(role_score, 4),
                    capability_overlap_score=round(capability_overlap, 4),
                    geography_score=round(geography_score, 4),
                    complementarity_score=round(complementarity_score, 4),
                    rationale=rationale,
                    red_flags=red_flags,
                )
            )

        scored.sort(key=lambda item: item.fit_score, reverse=True)
        return scored[: request.limit]

    def _capability_overlap(self, required: list[str], partner: PartnerProfile) -> float:
        if not required:
            return 0.6
        p_tags = _normalize(partner.capability_tags)
        hits = sum(1 for item in required if item.lower() in p_tags)
        return hits / max(len(required), 1)

    def _role_score(self, desired_roles: list[str], partner: PartnerProfile) -> float:
        if not desired_roles:
            return 0.5
        return max(float(partner.role_suitability.get(role, 0.0)) for role in desired_roles)

    def _geography_score(self, preferred_countries: list[str], partner: PartnerProfile) -> float:
        if not preferred_countries:
            return 0.5
        if not partner.country_code:
            return 0.0
        preferred = [c.upper() for c in preferred_countries]
        return 1.0 if partner.country_code.upper() in preferred else 0.0


def _normalize(items: list[str]) -> set[str]:
    return {item.lower().strip() for item in items}
