from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.domain.common.enums import ProviderErrorType


@dataclass(slots=True)
class ProviderCapabilityMetadata:
    provider_name: str
    supports_structured_output: bool
    supports_sensitive_data: bool
    local_only: bool = False
    max_context_tokens: int | None = None


@dataclass(slots=True)
class ProviderRequest:
    task_type: str
    purpose: str
    prompt: str
    model_name: str
    timeout_seconds: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProviderResponse:
    provider_name: str
    model_name: str
    content: str
    raw_payload: dict[str, Any]
    latency_ms: int
    usage: dict[str, Any] = field(default_factory=dict)
    cost_estimate: float | None = None


@dataclass(slots=True)
class ProviderExecutionContext:
    run_id: str
    attempt_number: int
    approved_providers: list[str]
    sensitive_data: bool
    local_only: bool


class ProviderExecutionError(Exception):
    def __init__(self, error_type: ProviderErrorType, message: str, retryable: bool) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.retryable = retryable


class ProviderClient(Protocol):
    provider_name: str
    capabilities: ProviderCapabilityMetadata

    def generate(
        self,
        request: ProviderRequest,
        context: ProviderExecutionContext,
    ) -> ProviderResponse:
        ...

    def structured_generate(
        self,
        request: ProviderRequest,
        context: ProviderExecutionContext,
        schema: dict[str, Any],
    ) -> ProviderResponse:
        ...
