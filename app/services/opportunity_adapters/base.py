from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from app.schemas.opportunity import OpportunityNormalized


@dataclass(slots=True)
class AdapterCapabilityMetadata:
    source_name: str
    supports_incremental_sync: bool
    supports_deadline_detection: bool
    normalization_version: str


class AdapterNormalizationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class OpportunitySourceAdapter(ABC):
    source_name: str
    capability: AdapterCapabilityMetadata

    @abstractmethod
    def normalize(self, source_record_id: str, payload: dict) -> OpportunityNormalized:
        """Normalize provider payload into contract-compliant opportunity data."""

    def fetch_records(self) -> list["SourceAdapterRecord"]:
        """Optional pull path for scheduled ingestion runs."""
        return []

    def healthcheck(self) -> dict:
        return {"status": "ok", "source_name": self.source_name}


@dataclass(slots=True)
class SourceAdapterRecord:
    source_record_id: str
    payload: dict
    fetched_at: datetime | None = None


@dataclass(slots=True)
class SourceExecutionResult:
    source_name: str
    total_records: int = 0
    created_count: int = 0
    updated_count: int = 0
    unchanged_count: int = 0
    failed_count: int = 0
    errors: list[dict] = field(default_factory=list)
