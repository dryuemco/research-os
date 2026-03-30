from abc import ABC, abstractmethod

from app.schemas.opportunity import OpportunityNormalized


class OpportunitySourceAdapter(ABC):
    source_name: str

    @abstractmethod
    def normalize(self, source_record_id: str, payload: dict) -> OpportunityNormalized:
        """Normalize provider payload into contract-compliant opportunity data."""
