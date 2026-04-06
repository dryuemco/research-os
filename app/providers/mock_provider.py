from __future__ import annotations

import time

from app.domain.common.enums import ProviderErrorType
from app.providers.base import (
    ProviderCapabilityMetadata,
    ProviderClient,
    ProviderExecutionContext,
    ProviderExecutionError,
    ProviderRequest,
    ProviderResponse,
)


class MockProviderClient(ProviderClient):
    provider_name = "mock-local"
    capabilities = ProviderCapabilityMetadata(
        provider_name=provider_name,
        supports_structured_output=True,
        supports_sensitive_data=True,
        local_only=True,
        max_context_tokens=64000,
    )

    def generate(
        self,
        request: ProviderRequest,
        context: ProviderExecutionContext,
    ) -> ProviderResponse:
        start = time.perf_counter()
        if request.metadata.get("force_error") == "quota":
            raise ProviderExecutionError(ProviderErrorType.QUOTA_EXCEEDED, "quota exceeded", True)
        if request.metadata.get("force_error") == "invalid_response":
            raise ProviderExecutionError(
                ProviderErrorType.INVALID_RESPONSE,
                "invalid provider response",
                False,
            )

        content = f"[mock:{request.task_type}] {request.prompt[:160]}"
        latency_ms = int((time.perf_counter() - start) * 1000)
        return ProviderResponse(
            provider_name=self.provider_name,
            model_name=request.model_name,
            content=content,
            raw_payload={"echo": True},
            latency_ms=latency_ms,
            usage={"prompt_tokens": len(request.prompt.split()), "completion_tokens": 64},
            cost_estimate=0.0,
        )

    def structured_generate(
        self,
        request: ProviderRequest,
        context: ProviderExecutionContext,
        schema: dict,
    ) -> ProviderResponse:
        return self.generate(request, context)
