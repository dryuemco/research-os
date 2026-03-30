from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class ProviderRequest:
    task_type: str
    prompt: str
    model_name: str
    metadata: dict


@dataclass(slots=True)
class ProviderResponse:
    provider_name: str
    model_name: str
    content: str
    raw_payload: dict
    latency_ms: int


class ProviderClient(Protocol):
    """Provider-agnostic contract for future model adapters."""

    provider_name: str

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        ...
