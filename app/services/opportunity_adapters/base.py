from abc import ABC, abstractmethod
from dataclasses import dataclass

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

    def healthcheck(self) -> dict:
        return {"status": "ok", "source_name": self.source_name}
