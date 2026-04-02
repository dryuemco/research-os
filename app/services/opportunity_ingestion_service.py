import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.common.enums import OpportunityState
from app.domain.opportunity_discovery.models import (
    Opportunity,
    OpportunityIngestionSnapshot,
    OpportunityVersion,
)
from app.schemas.audit import AuditEventSchema
from app.schemas.opportunity import OpportunityIngestRequest, OpportunityNormalized
from app.services.audit_service import AuditService
from app.services.opportunity_adapters import DEFAULT_ADAPTERS
from app.services.opportunity_adapters.base import AdapterNormalizationError
from app.services.opportunity_state_service import OpportunityStateService


class OpportunityIngestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)
        self.state_service = OpportunityStateService(db)
        self.adapters = DEFAULT_ADAPTERS

    def ingest_dev_payload(self, request: OpportunityIngestRequest) -> Opportunity:
        adapter = self.adapters.get(request.source_name)
        if adapter is None:
            raise ValueError(f"No adapter registered for source '{request.source_name}'")
        try:
            normalized = adapter.normalize(request.source_record_id, request.payload)
        except AdapterNormalizationError as exc:
            self.audit.emit(
                AuditEventSchema(
                    event_type="opportunity_ingestion_failed",
                    entity_type="opportunity_source",
                    entity_id=f"{request.source_name}:{request.source_record_id}",
                    actor_type="system",
                    actor_id="ingestion_pipeline",
                    payload={"error_code": exc.code, "message": str(exc)},
                )
            )
            self.db.flush()
            raise

        return self._persist_ingested(
            source_name=request.source_name,
            source_record_id=request.source_record_id,
            payload=request.payload,
            normalized=normalized,
        )

    def _persist_ingested(
        self,
        *,
        source_name: str,
        source_record_id: str,
        payload: dict,
        normalized: OpportunityNormalized,
    ) -> Opportunity:
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload_hash = hashlib.sha256(canonical_payload.encode()).hexdigest()

        existing_snapshot = self.db.scalar(
            select(OpportunityIngestionSnapshot.id).where(
                OpportunityIngestionSnapshot.source_name == source_name,
                OpportunityIngestionSnapshot.source_record_id == source_record_id,
                OpportunityIngestionSnapshot.payload_hash == payload_hash,
            )
        )
        if existing_snapshot is None:
            snapshot = OpportunityIngestionSnapshot(
                source_name=source_name,
                source_record_id=source_record_id,
                payload_hash=payload_hash,
                payload=payload,
            )
            self.db.add(snapshot)
            self.db.flush()

        opportunity = self.db.scalar(
            select(Opportunity).where(Opportunity.external_id == normalized.external_id)
        )

        if opportunity is None:
            opportunity = Opportunity(
                source_program=normalized.source_program,
                source_url=normalized.source_url,
                external_id=normalized.external_id,
                title=normalized.title,
                summary=normalized.summary,
                deadline_at=normalized.deadline_at,
                call_status=normalized.call_status,
                budget_total=normalized.budget_total,
                currency=normalized.currency,
                state=OpportunityState.DISCOVERED,
                current_version_hash=normalized.version_hash,
                raw_payload=normalized.raw_payload,
            )
            self.db.add(opportunity)
            self.db.flush()
            self.audit.emit(
                AuditEventSchema(
                    event_type="opportunity_ingested",
                    entity_type="opportunity",
                    entity_id=opportunity.id,
                    actor_type="system",
                    actor_id="ingestion_pipeline",
                    payload={"source": source_name, "source_record_id": source_record_id},
                )
            )

        has_latest_version = self.db.scalar(
            select(OpportunityVersion.id).where(
                OpportunityVersion.opportunity_id == opportunity.id,
                OpportunityVersion.is_latest.is_(True),
            )
        )

        if (
            opportunity.current_version_hash != normalized.version_hash
            or has_latest_version is None
        ):
            self.db.query(OpportunityVersion).filter(
                OpportunityVersion.opportunity_id == opportunity.id,
                OpportunityVersion.is_latest.is_(True),
            ).update({"is_latest": False})

            opportunity.current_version_hash = normalized.version_hash
            opportunity.title = normalized.title
            opportunity.summary = normalized.summary
            opportunity.deadline_at = normalized.deadline_at
            opportunity.call_status = normalized.call_status
            opportunity.budget_total = normalized.budget_total
            opportunity.currency = normalized.currency
            opportunity.raw_payload = normalized.raw_payload
            self.db.add(opportunity)

            self.db.add(
                OpportunityVersion(
                    opportunity_id=opportunity.id,
                    version_hash=normalized.version_hash,
                    full_text=normalized.full_text,
                    eligibility_notes=normalized.eligibility_notes,
                    expected_outcomes=normalized.expected_outcomes,
                    raw_payload=normalized.raw_payload,
                    provenance=normalized.provenance,
                    uncertainty_notes=normalized.uncertainty_notes,
                    is_latest=True,
                )
            )
            self.audit.emit(
                AuditEventSchema(
                    event_type="opportunity_version_created",
                    entity_type="opportunity",
                    entity_id=opportunity.id,
                    actor_type="system",
                    actor_id="ingestion_pipeline",
                    payload={"version_hash": normalized.version_hash, "payload_hash": payload_hash},
                )
            )

        if opportunity.state == OpportunityState.DISCOVERED:
            self.state_service.transition_state(
                opportunity,
                OpportunityState.NORMALIZED,
                actor_type="system",
                actor_id="ingestion_pipeline",
                reason="normalization complete",
            )

        self.db.flush()
        return opportunity