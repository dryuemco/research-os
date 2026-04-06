from sqlalchemy.exc import SQLAlchemyError

from app.services.export_package_service import ExportPackageService
from app.services.partner_intelligence_service import PartnerIntelligenceService
from app.services.proposal_quality_service import ProposalQualityService
from app.services.retrieval_service import RetrievalService


def test_dashboard_summary_returns_degraded_payload_on_db_error(client, monkeypatch):
    def boom(*_args, **_kwargs):
        raise SQLAlchemyError("db unavailable")

    from app.services.dashboard_service import DashboardService

    monkeypatch.setattr(DashboardService, "summary", boom)
    response = client.get(
        "/dashboard/summary",
        headers={"Origin": "https://dryuemco.github.io"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["opportunities"] == 0
    assert payload["_status"] == "degraded"
    assert response.headers.get("access-control-allow-origin") == "https://dryuemco.github.io"


def test_memory_exports_returns_empty_list_on_db_error(client, monkeypatch):
    def boom(*_args, **_kwargs):
        raise SQLAlchemyError("db unavailable")

    monkeypatch.setattr(ExportPackageService, "list_packages", boom)
    response = client.get("/memory/exports")

    assert response.status_code == 200
    assert response.json() == []


def test_intelligence_preview_returns_empty_on_db_error(client, monkeypatch):
    def boom(*_args, **_kwargs):
        raise SQLAlchemyError("db unavailable")

    monkeypatch.setattr(RetrievalService, "retrieve", boom)
    response = client.post(
        "/intelligence/retrieval/preview",
        json={"query_text": "health", "limit": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["count"] == 0
    assert payload["status"] == "degraded"


def test_intelligence_partners_and_fit_return_empty_on_db_error(client, monkeypatch):
    def boom(*_args, **_kwargs):
        raise SQLAlchemyError("db unavailable")

    monkeypatch.setattr(PartnerIntelligenceService, "list_partners", boom)

    partners = client.get("/intelligence/partners")
    assert partners.status_code == 200
    assert partners.json() == []

    fit = client.post(
        "/intelligence/partners/fit",
        json={
            "required_capabilities": ["ai"],
            "desired_roles": ["coordinator"],
            "preferred_countries": ["US"],
            "limit": 5,
        },
    )
    assert fit.status_code == 200
    assert fit.json() == []


def test_dashboard_proposal_quality_returns_degraded_on_db_error(client, monkeypatch):
    def boom(*_args, **_kwargs):
        raise SQLAlchemyError("db unavailable")

    monkeypatch.setattr(ProposalQualityService, "summarize", boom)

    response = client.get("/dashboard/intelligence/proposals/any-proposal/quality")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["error"] == "proposal_quality_unavailable"
