import pytest
from pydantic import ValidationError

from app.schemas.matching import InterestProfileParameters
from app.schemas.opportunity import OpportunityNormalized


def test_opportunity_schema_forbids_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        OpportunityNormalized(
            source_program="Horizon Europe",
            source_url="https://example.com",
            external_id="call-1",
            title="Example",
            summary="Summary",
            full_text="Full text",
            call_status="open",
            version_hash="abc123",
            unexpected_field="nope",
        )


def test_interest_profile_schema_requires_typed_weights() -> None:
    with pytest.raises(ValidationError):
        InterestProfileParameters(weights={"keyword_overlap": "high"})
