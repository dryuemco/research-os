from app.schemas.memory import RetrievalBackendMode, RetrievalPolicy, RetrievalQuery
from app.services.retrieval_service import RetrievalService


def test_retrieval_backend_contract_stable(db_session):
    service = RetrievalService(db_session)
    result = service.retrieve(RetrievalQuery(query_text="nothing", limit=3))
    assert isinstance(result, list)


def test_retrieval_backend_capabilities_exposed(db_session):
    service = RetrievalService(db_session)
    capabilities = service.backend_capabilities()
    assert any(item["backend_name"] == "lexical" for item in capabilities)
    assert any(item["backend_name"] == "vector_ready" for item in capabilities)


def test_explicit_lexical_policy_mode(db_session):
    service = RetrievalService(db_session)
    result = service.retrieve(
        RetrievalQuery(
            query_text="nothing",
            limit=3,
            policy=RetrievalPolicy(backend_mode=RetrievalBackendMode.LEXICAL),
        )
    )
    assert isinstance(result, list)
