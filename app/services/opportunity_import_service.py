from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.services.operational_loop_service import OperationalLoopService


class OpportunityImportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.operational = OperationalLoopService(db)

    def import_fixture(
        self,
        *,
        fixture_path: str,
        run_matching_after: bool,
    ) -> dict:
        payload = self._read_fixture(fixture_path)
        source_name = payload.get("source_name", "funding_call_scaffold")
        records = payload.get("records")
        if not isinstance(records, list) or not records:
            raise ValueError("Fixture file must contain non-empty records[]")

        run = self.operational.run_ingestion_job(
            source_name=source_name,
            trigger_source="opportunities_ingest_dev_fixture",
            run_matching_after=run_matching_after,
            records=records,
        )
        return {
            "job_run_id": run.id,
            "job_status": run.status.value,
            "result_summary": run.result_summary,
            "fixture_path": fixture_path,
            "source_name": source_name,
        }

    def ingest_live_eu_funding(
        self,
        *,
        programmes: list[str],
        limit: int,
        run_matching_after: bool,
    ) -> dict:
        normalized_programmes = [item.strip().lower() for item in programmes if item.strip()]
        run = self.operational.run_ingestion_job(
            source_name="eu_funding_tenders",
            trigger_source="live_eu_funding_ingestion",
            run_matching_after=run_matching_after,
            records=None,
            fetch_filters={
                "programmes": normalized_programmes,
                "limit": limit,
                "include_closed": False,
            },
        )
        return {
            "job_run_id": run.id,
            "job_status": run.status.value,
            "source_name": "eu_funding_tenders",
            "programmes": normalized_programmes,
            "result_summary": run.result_summary,
        }

    def _read_fixture(self, fixture_path: str) -> dict:
        try:
            return json.loads(Path(fixture_path).read_text(encoding="utf-8"))
        except OSError as exc:
            raise ValueError(f"Fixture path is not readable: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Fixture JSON is invalid: {exc}") from exc
