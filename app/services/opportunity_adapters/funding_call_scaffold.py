import hashlib

from app.schemas.opportunity import OpportunityNormalized
from app.services.opportunity_adapters.base import (
    AdapterCapabilityMetadata,
    AdapterNormalizationError,
    OpportunitySourceAdapter,
)


class FundingCallScaffoldAdapter(OpportunitySourceAdapter):
    """Scaffold adapter for external funding call sources."""

    source_name = "funding_call_scaffold"
    capability = AdapterCapabilityMetadata(
        source_name=source_name,
        supports_incremental_sync=True,
        supports_deadline_detection=True,
        normalization_version="v2",
    )

    def normalize(self, source_record_id: str, payload: dict) -> OpportunityNormalized:
        if not payload.get("title"):
            raise AdapterNormalizationError("missing_title", "payload is missing required title")

        title = payload.get("title", "Untitled opportunity")
        summary = payload.get("summary", "")
        full_text = payload.get("full_text") or summary
        program = payload.get("source_program", "generic_funding_program")

        version_hash = hashlib.sha256(
            f"{source_record_id}:{title}:{summary}:{full_text}:{payload.get('deadline_at')}".encode()
        ).hexdigest()

        return OpportunityNormalized(
            source_program=program,
            source_url=payload.get("source_url", "https://example.org/source"),
            external_id=payload.get("external_id", source_record_id),
            title=title,
            summary=summary,
            full_text=full_text,
            deadline_at=payload.get("deadline_at"),
            call_status=payload.get("call_status", "open"),
            budget_total=payload.get("budget_total"),
            currency=payload.get("currency"),
            eligibility_notes=payload.get("eligibility_notes", []),
            expected_outcomes=payload.get("expected_outcomes", []),
            raw_payload=payload,
            version_hash=version_hash,
            provenance={
                "adapter": self.source_name,
                "source_record_id": source_record_id,
                "normalization_version": self.capability.normalization_version,
            },
            uncertainty_notes=payload.get("uncertainty_notes", []),
        )
