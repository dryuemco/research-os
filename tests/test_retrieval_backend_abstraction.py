from app.schemas.memory import RetrievalQuery
from app.services.retrieval_service import RetrievalService


def test_retrieval_backend_contract_stable(db_session):
    service = RetrievalService(db_session)
    result = service.retrieve(RetrievalQuery(query_text="nothing", limit=3))
    assert isinstance(result, list)


def test_unknown_backend_falls_back_to_lexical(monkeypatch, db_session):
    monkeypatch.setenv("RETRIEVAL_BACKEND", "unknown")
    from app.core.config import get_settings

    get_settings.cache_clear()
    service = RetrievalService(db_session)
    assert service.backend.backend_name == "lexical"
