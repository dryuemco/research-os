from __future__ import annotations

import hashlib
from datetime import UTC, datetime

import httpx

from app.core.config import get_settings
from app.schemas.opportunity import OpportunityNormalized
from app.services.opportunity_adapters.base import (
    AdapterCapabilityMetadata,
    AdapterFetchError,
    AdapterNormalizationError,
    OpportunitySourceAdapter,
    SourceAdapterRecord,
)

DEFAULT_PROGRAMMES = ["horizon", "erasmus+"]


class EUFundingTendersAdapter(OpportunitySourceAdapter):
    """Live adapter for Funding & Tenders opportunities."""

    source_name = "eu_funding_tenders"
    capability = AdapterCapabilityMetadata(
        source_name=source_name,
        supports_incremental_sync=True,
        supports_deadline_detection=True,
        normalization_version="v1",
    )

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self._transport = transport

    def fetch_records(
        self,
        *,
        programmes: list[str] | None = None,
        limit: int = 50,
        include_closed: bool = False,
    ) -> list[SourceAdapterRecord]:
        settings = get_settings()
        records = self._fetch_live_payload(
            url=self._canonicalize_url(settings.eu_funding_api_url),
            timeout_seconds=settings.eu_funding_timeout_seconds,
            programmes=programmes or DEFAULT_PROGRAMMES,
            limit=limit,
            include_closed=include_closed,
        )
        return [
            SourceAdapterRecord(source_record_id=item["source_record_id"], payload=item["payload"])
            for item in records
        ]


    def _canonicalize_url(self, url: str) -> str:
        normalized = url.rstrip("/")
        legacy = "https://ec.europa.eu/info/funding-tenders/opportunities/data/topicSearch"
        canonical = "https://ec.europa.eu/info/funding-tenders/opportunities/data-api/topic/search"
        if normalized == legacy:
            return canonical
        return normalized

    def _fetch_live_payload(
        self,
        *,
        url: str,
        timeout_seconds: int,
        programmes: list[str],
        limit: int,
        include_closed: bool,
    ) -> list[dict]:
        query = self._build_query(programmes=programmes, include_closed=include_closed)
        params = {
            "query": query,
            "page": 0,
            "size": max(1, min(limit, 100)),
            "sort": "deadlineDate asc",
        }
        headers = {"accept": "application/json"}

        client_args: dict = {"timeout": timeout_seconds, "follow_redirects": True}
        if self._transport is not None:
            client_args["transport"] = self._transport

        with httpx.Client(**client_args) as client:
            try:
                response = client.get(url, params=params, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise self._to_fetch_error(exc) from exc
            except httpx.HTTPError as exc:
                raise AdapterFetchError(
                    code="source_blocked",
                    message=f"EU Funding API request failed: {exc}",
                    diagnostics={
                        "category": "network_error",
                        "method": "GET",
                        "requested_url": str(exc.request.url) if exc.request else url,
                    },
                ) from exc

            try:
                raw = response.json()
            except ValueError as exc:
                raise AdapterFetchError(
                    code="parsing_failure",
                    message="EU Funding API returned a non-JSON payload",
                    diagnostics={
                        "category": "parsing_failure",
                        "status_code": response.status_code,
                        "final_url": str(response.url),
                        "content_type": response.headers.get("content-type"),
                    },
                ) from exc

        return self._extract_records(raw)


    def _to_fetch_error(self, exc: httpx.HTTPStatusError) -> AdapterFetchError:
        response = exc.response
        request = exc.request
        body_preview = (response.text or "")[:300].lower()
        status_code = response.status_code

        if status_code in {401, 403}:
            if "robots" in body_preview:
                code = "robots_blocked"
                category = "robots_blocked"
            else:
                code = "unauthorized"
                category = "unauthorized"
        elif status_code in {301, 302, 307, 308, 404, 405, 410}:
            code = "endpoint_changed"
            category = "endpoint_changed"
        else:
            code = "source_blocked"
            category = "source_blocked"

        return AdapterFetchError(
            code=code,
            message=f"EU Funding API returned HTTP {status_code}",
            diagnostics={
                "category": category,
                "status_code": status_code,
                "method": request.method if request else "GET",
                "requested_url": str(request.url) if request else None,
                "final_url": str(response.url),
                "redirected": bool(response.history),
                "redirect_count": len(response.history),
                "location": response.headers.get("location"),
            },
        )

    def _build_query(self, *, programmes: list[str], include_closed: bool) -> str:
        normalized = [item.strip().lower() for item in programmes if item.strip()]
        clauses = []
        if normalized:
            program_tokens = " OR ".join(f'programme:"{item}"' for item in normalized)
            clauses.append(f"({program_tokens})")
        if not include_closed:
            clauses.append('(status:"OPEN" OR status:"Open")')
        return " AND ".join(clauses) if clauses else "*"

    def _extract_records(self, payload: dict | list) -> list[dict]:
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict):
            items = (
                payload.get("results")
                or payload.get("items")
                or payload.get("content")
                or payload.get("topics")
                or []
            )
        else:
            items = []

        records: list[dict] = []
        for row in items:
            if not isinstance(row, dict):
                continue
            source_record_id = str(
                row.get("identifier")
                or row.get("topicId")
                or row.get("id")
                or row.get("code")
                or ""
            ).strip()
            if not source_record_id:
                continue
            records.append({"source_record_id": source_record_id, "payload": row})
        return records

    def normalize(self, source_record_id: str, payload: dict) -> OpportunityNormalized:
        title = self._as_text(payload.get("title") or payload.get("name") or payload.get("topic"))
        if not title:
            raise AdapterNormalizationError("missing_title", "payload is missing required title")

        summary = self._as_text(
            payload.get("summary") or payload.get("description") or payload.get("objective") or ""
        )
        full_text = self._as_text(payload.get("fullText") or payload.get("content") or summary)

        deadline = self._extract_deadline(payload)
        source_url = self._extract_url(payload, source_record_id)
        source_program = self._infer_programme(payload)
        call_status = self._extract_status(payload)

        canonical = f"{source_record_id}:{title}:{summary}:{deadline}:{call_status}"
        version_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        return OpportunityNormalized(
            source_program=source_program,
            source_url=source_url,
            external_id=str(payload.get("externalId") or source_record_id),
            title=title,
            summary=summary,
            full_text=full_text,
            deadline_at=deadline,
            call_status=call_status,
            budget_total=self._extract_budget(payload),
            currency=self._as_text(payload.get("currency") or "EUR") or "EUR",
            eligibility_notes=self._as_list(
                payload.get("eligibility") or payload.get("eligibilityNotes")
            ),
            expected_outcomes=self._as_list(
                payload.get("expectedOutcomes") or payload.get("outcomes")
            ),
            raw_payload=payload,
            version_hash=version_hash,
            provenance={
                "adapter": self.source_name,
                "source_record_id": source_record_id,
                "normalization_version": self.capability.normalization_version,
                "fetched_at": datetime.now(UTC).isoformat(),
            },
            uncertainty_notes=[],
        )

    def healthcheck(self) -> dict:
        settings = get_settings()
        return {
            "status": "ok",
            "source_name": self.source_name,
            "api_url": settings.eu_funding_api_url,
        }

    def _as_text(self, value) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            for key in ("en", "value", "text", "label"):
                if key in value and isinstance(value[key], str):
                    return value[key].strip()
            return ""
        return str(value).strip()

    def _as_list(self, value) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [self._as_text(item) for item in value if self._as_text(item)]
        return [self._as_text(value)] if self._as_text(value) else []

    def _extract_url(self, payload: dict, source_record_id: str) -> str:
        direct = self._as_text(payload.get("url") or payload.get("link"))
        if direct:
            return direct
        return (
            "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/"
            f"opportunities/topic-details/{source_record_id}"
        )

    def _extract_status(self, payload: dict) -> str:
        status = self._as_text(payload.get("status") or payload.get("callStatus") or "open")
        return status.lower() if status else "open"

    def _extract_budget(self, payload: dict) -> float | None:
        for key in ("budget", "budgetTotal", "totalBudget", "euContribution"):
            value = payload.get(key)
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return None

    def _extract_deadline(self, payload: dict) -> str | None:
        for key in ("deadline", "deadlineDate", "submissionDeadline", "deadline_at"):
            value = self._as_text(payload.get(key))
            if value:
                return value
        return None

    def _infer_programme(self, payload: dict) -> str:
        raw = " ".join(
            [
                self._as_text(payload.get("programme")),
                self._as_text(payload.get("program")),
                self._as_text(payload.get("frameworkProgramme")),
                self._as_text(payload.get("programmeName")),
            ]
        ).lower()
        if "erasmus" in raw:
            return "erasmus+"
        if "horizon" in raw:
            return "horizon"
        return "eu_funding"
