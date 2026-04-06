from app.schemas.intelligence import PartnerFitRequest, PartnerProfileCreate
from app.services.partner_intelligence_service import PartnerIntelligenceService


def test_partner_fit_scoring_and_rationale(db_session):
    service = PartnerIntelligenceService(db_session)
    service.create_partner(
        PartnerProfileCreate(
            partner_name="Alpha Lab",
            country_code="DE",
            capability_tags=["ai", "climate", "kpi"],
            role_suitability={"coordinator": 0.8, "beneficiary": 0.9},
            program_participation=["horizon"],
        )
    )
    service.create_partner(
        PartnerProfileCreate(
            partner_name="Beta NGO",
            country_code="IT",
            capability_tags=["community", "outreach"],
            role_suitability={"beneficiary": 0.7},
            program_participation=["erasmus+"],
        )
    )
    db_session.commit()

    result = service.fit_preview(
        PartnerFitRequest(
            required_capabilities=["ai", "climate"],
            preferred_countries=["DE"],
            desired_roles=["coordinator"],
        )
    )
    assert result
    assert result[0].partner.partner_name == "Alpha Lab"
    assert result[0].rationale
