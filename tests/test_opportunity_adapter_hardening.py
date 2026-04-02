import pytest

from app.schemas.opportunity import OpportunityIngestRequest
from app.services.opportunity_adapters.base import AdapterNormalizationError
from app.services.opportunity_ingestion_service import OpportunityIngestionService


def test_adapter_rejects_payload_without_title(db_session):
    service = OpportunityIngestionService(db_session)
    with pytest.raises(AdapterNormalizationError):
        service.ingest_dev_payload(
            OpportunityIngestRequest(
                source_name="funding_call_scaffold",
                source_record_id="src-1",
                payload={"summary": "no title"},
            )
        )
