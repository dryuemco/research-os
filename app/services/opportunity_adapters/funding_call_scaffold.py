import hashlib

from app.schemas.opportunity import OpportunityNormalized
from app.services.opportunity_adapters.base import OpportunitySourceAdapter


class FundingCallScaffoldAdapter(OpportunitySourceAdapter):
    """Scaffold adapter for external funding call sources.

    The adapter intentionally keeps only generic, source-agnostic behavior.
    Program-specific parsing can be layered later without changing core ingestion.
    """

    source_name = "funding_call_scaffold"

    def normalize(self, source_record_id: str, payload: dict) -> OpportunityNormalized:
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
            provenance={"adapter": self.source_name, "source_record_id": source_record_id},
            uncertainty_notes=payload.get("uncertainty_notes", []),
        )
