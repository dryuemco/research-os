from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.common.enums import (
    NotificationType,
    OperationalJobStatus,
    OperationalJobType,
    OpportunityState,
)
from app.domain.operations.models import MatchingRun, OperationalJobConfig, OperationalJobRun
from app.domain.opportunity_discovery.models import InterestProfile, Opportunity
from app.schemas.audit import AuditEventSchema
from app.schemas.matching import MatchRequest
from app.schemas.opportunity import OpportunityIngestRequest
from app.services.audit_service import AuditService
from app.services.matching_service import MatchingService
from app.services.notification_service import NotificationService
from app.services.opportunity_adapters.base import AdapterFetchError
from app.services.opportunity_ingestion_service import IngestionOutcome, OpportunityIngestionService
from app.services.source_registry_service import SourceRegistryService


class OperationalLoopService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)
        self.notifications = NotificationService(db)
        self.registry = SourceRegistryService()

    def ensure_default_jobs(self) -> list[OperationalJobConfig]:
        defaults = [
            {
                "job_key": "source_ingestion_default",
                "job_type": OperationalJobType.SOURCE_INGESTION,
                "source_name": "funding_call_scaffold",
                "interval_minutes": 60,
            },
            {
                "job_key": "matching_default",
                "job_type": OperationalJobType.MATCHING,
                "interval_minutes": 60,
            },
        ]
        created: list[OperationalJobConfig] = []
        for item in defaults:
            existing = self.db.scalar(
                select(OperationalJobConfig).where(OperationalJobConfig.job_key == item["job_key"])
            )
            if existing:
                created.append(existing)
                continue
            model = OperationalJobConfig(
                job_key=item["job_key"],
                job_type=item["job_type"],
                source_name=item.get("source_name"),
                interval_minutes=item["interval_minutes"],
                enabled=True,
                next_run_at=datetime.now(UTC),
            )
            self.db.add(model)
            self.db.flush()
            created.append(model)
        return created

    def run_due_jobs(self) -> list[OperationalJobRun]:
        now = datetime.now(UTC)
        configs = self.db.scalars(
            select(OperationalJobConfig).where(
                OperationalJobConfig.enabled.is_(True),
                OperationalJobConfig.next_run_at.is_not(None),
                OperationalJobConfig.next_run_at <= now,
            )
        ).all()
        runs: list[OperationalJobRun] = []
        for config in configs:
            run = self.trigger_job_config(config, trigger_source="scheduler")
            config.last_triggered_at = now
            config.next_run_at = now + timedelta(minutes=config.interval_minutes)
            self.db.add(config)
            runs.append(run)
        return runs

    def trigger_job_config(
        self, config: OperationalJobConfig, trigger_source: str
    ) -> OperationalJobRun:
        if config.job_type == OperationalJobType.SOURCE_INGESTION:
            return self.run_ingestion_job(
                source_name=config.source_name or "funding_call_scaffold",
                trigger_source=trigger_source,
                run_matching_after=True,
                job_config_id=config.id,
            )
        profile = config.profile_id or self._default_profile_id()
        if not profile:
            raise ValueError("No profile available for matching job")
        return self.run_matching_job(
            profile_id=profile,
            scoring_policy_id="default-v1",
            trigger_source=trigger_source,
            job_config_id=config.id,
        )

    def run_ingestion_job(
        self,
        *,
        source_name: str,
        trigger_source: str,
        run_matching_after: bool,
        records: list[dict] | None = None,
        fetch_filters: dict | None = None,
        job_config_id: str | None = None,
    ) -> OperationalJobRun:
        run = OperationalJobRun(
            job_config_id=job_config_id,
            job_type=OperationalJobType.SOURCE_INGESTION,
            status=OperationalJobStatus.RUNNING,
            trigger_source=trigger_source,
            source_name=source_name,
            started_at=datetime.now(UTC),
        )
        self.db.add(run)
        self.db.flush()
        self._audit_job_event(run, "operational_job_started")

        ingestion = OpportunityIngestionService(self.db)
        adapter = self.registry.get(source_name)
        try:
            if records is None:
                raw_records = [
                    {"source_record_id": r.source_record_id, "payload": r.payload}
                    for r in adapter.fetch_records(**(fetch_filters or {}))
                ]
            else:
                raw_records = records

            created = updated = unchanged = failed = 0
            errors: list[dict] = []
            outcomes: list[IngestionOutcome] = []
            for item in raw_records:
                try:
                    _, outcome = ingestion.ingest_dev_payload_with_result(
                        OpportunityIngestRequest(
                            source_name=source_name,
                            source_record_id=item["source_record_id"],
                            payload=item["payload"],
                        )
                    )
                    outcomes.append(outcome)
                    if outcome.outcome == "created":
                        created += 1
                    elif outcome.outcome == "updated":
                        updated += 1
                    else:
                        unchanged += 1
                except Exception as exc:  # pragma: no cover
                    failed += 1
                    error_item = {
                        "message": str(exc),
                        "source_record_id": item.get("source_record_id"),
                    }
                    errors.append(error_item)
                    run.error_summary = error_item
            run.result_summary = {
                "total_records": len(raw_records),
                "created_count": created,
                "updated_count": updated,
                "unchanged_count": unchanged,
                "failed_count": failed,
                "errors": errors,
            }
            run.status = (
                OperationalJobStatus.SUCCEEDED
                if failed == 0
                else OperationalJobStatus.FAILED
            )
            run.finished_at = datetime.now(UTC)
            self.db.add(run)
            self.db.flush()
            self._audit_job_event(run, "operational_job_finished")

            if run.status == OperationalJobStatus.FAILED:
                self.notifications.create(
                    notification_type=NotificationType.JOB_FAILED,
                    recipient_user_id="ops-admin",
                    related_entity_type="operational_job_run",
                    related_entity_id=run.id,
                    payload_json=run.error_summary or {"message": "unknown"},
                )

            for outcome in outcomes:
                if outcome.outcome == "updated":
                    self.notifications.create(
                        notification_type=NotificationType.OPPORTUNITY_CHANGED,
                        recipient_user_id="ops-admin",
                        related_entity_type="opportunity",
                        related_entity_id=outcome.opportunity_id,
                        payload_json={
                            "source_name": outcome.source_name,
                            "changed_fields": outcome.changed_fields,
                        },
                    )

            if run_matching_after and (created + updated) > 0:
                profile_id = self._default_profile_id()
                if profile_id:
                    self.run_matching_job(
                        profile_id=profile_id,
                        scoring_policy_id="default-v1",
                        trigger_source="post_ingestion",
                        job_config_id=None,
                    )
        except Exception as exc:
            run.status = OperationalJobStatus.FAILED
            run.finished_at = datetime.now(UTC)
            if isinstance(exc, AdapterFetchError):
                run.error_summary = {
                    "error_code": exc.code,
                    "message": str(exc),
                    "diagnostics": exc.diagnostics,
                }
            else:
                run.error_summary = {"message": str(exc)}
            run.result_summary = {
                "total_records": 0,
                "created_count": 0,
                "updated_count": 0,
                "unchanged_count": 0,
                "failed_count": 1,
                "errors": [run.error_summary],
            }
            self.db.add(run)
            self.db.flush()
            self._audit_job_event(run, "operational_job_failed")
            raise

        return run

    def run_matching_job(
        self,
        *,
        profile_id: str,
        scoring_policy_id: str,
        trigger_source: str,
        opportunity_ids: list[str] | None = None,
        job_config_id: str | None = None,
    ) -> OperationalJobRun:
        run = OperationalJobRun(
            job_config_id=job_config_id,
            job_type=OperationalJobType.MATCHING,
            status=OperationalJobStatus.RUNNING,
            trigger_source=trigger_source,
            profile_id=profile_id,
            started_at=datetime.now(UTC),
        )
        self.db.add(run)
        self.db.flush()
        self._audit_job_event(run, "operational_job_started")

        if opportunity_ids is None:
            opportunity_ids = [
                item.id
                for item in self.db.scalars(
                    select(Opportunity).where(
                        Opportunity.state.in_(
                            [
                                OpportunityState.NORMALIZED,
                                OpportunityState.SCORED,
                                OpportunityState.SHORTLISTED,
                            ]
                        )
                    )
                ).all()
            ]

        try:
            results = MatchingService(self.db).run_match(
                MatchRequest(
                    user_id="system",
                    profile_id=profile_id,
                    opportunity_ids=opportunity_ids,
                    scoring_policy_id=scoring_policy_id,
                )
            )
            recommendations = sum(1 for r in results if r.recommendation == "pursue")
            red_flags = sum(len(r.red_flags) for r in results)
            run.result_summary = {
                "matches_created": len(results),
                "recommendations_count": recommendations,
                "red_flags_count": red_flags,
                "opportunities_scanned": len(opportunity_ids),
            }
            run.status = OperationalJobStatus.SUCCEEDED
            run.finished_at = datetime.now(UTC)
            self.db.add(run)

            matching_run = MatchingRun(
                operational_job_run_id=run.id,
                profile_id=profile_id,
                scoring_policy_id=scoring_policy_id,
                status=OperationalJobStatus.SUCCEEDED,
                opportunities_scanned=len(opportunity_ids),
                matches_created=len(results),
                recommendations_count=recommendations,
                red_flags_count=red_flags,
                summary_json=run.result_summary,
            )
            self.db.add(matching_run)
            self.db.flush()
            self._audit_job_event(run, "operational_job_finished")

            for item in results:
                if item.recommendation == "pursue":
                    self.notifications.create(
                        notification_type=NotificationType.NEW_MATCH,
                        recipient_user_id="ops-admin",
                        related_entity_type="opportunity",
                        related_entity_id=item.opportunity_id,
                        payload_json={
                            "profile_id": profile_id,
                            "total_score": item.total_score,
                            "recommendation": item.recommendation,
                            "red_flags": item.red_flags,
                        },
                    )
        except Exception as exc:
            run.status = OperationalJobStatus.FAILED
            run.finished_at = datetime.now(UTC)
            run.error_summary = {"message": str(exc)}
            self.db.add(run)
            self.db.flush()
            self._audit_job_event(run, "operational_job_failed")
            self.notifications.create(
                notification_type=NotificationType.JOB_FAILED,
                recipient_user_id="ops-admin",
                related_entity_type="operational_job_run",
                related_entity_id=run.id,
                payload_json=run.error_summary,
            )
            raise
        return run

    def list_job_runs(self, limit: int = 50) -> list[OperationalJobRun]:
        return self.db.scalars(
            select(OperationalJobRun).order_by(OperationalJobRun.created_at.desc()).limit(limit)
        ).all()

    def list_matching_runs(self, limit: int = 50) -> list[MatchingRun]:
        return self.db.scalars(
            select(MatchingRun).order_by(MatchingRun.created_at.desc()).limit(limit)
        ).all()

    def _default_profile_id(self) -> str | None:
        profile = self.db.scalar(select(InterestProfile).order_by(InterestProfile.created_at.asc()))
        return profile.id if profile else None

    def _audit_job_event(self, run: OperationalJobRun, event_type: str) -> None:
        self.audit.emit(
            AuditEventSchema(
                event_type=event_type,
                entity_type="operational_job_run",
                entity_id=run.id,
                actor_type="system",
                actor_id="operational_loop",
                payload={
                    "job_type": run.job_type.value,
                    "status": run.status.value,
                    "trigger_source": run.trigger_source,
                    "source_name": run.source_name,
                    "profile_id": run.profile_id,
                },
            )
        )
