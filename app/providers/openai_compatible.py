from __future__ import annotations

import time

import httpx

from app.domain.common.enums import ProviderErrorType
from app.providers.base import (
    ProviderCapabilityMetadata,
    ProviderClient,
    ProviderExecutionContext,
    ProviderExecutionError,
    ProviderRequest,
    ProviderResponse,
)


class OpenAICompatibleProviderClient(ProviderClient):
    provider_name = "openai-compatible"

    def __init__(self, *, base_url: str, api_key: str | None) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.capabilities = ProviderCapabilityMetadata(
            provider_name=self.provider_name,
            supports_structured_output=True,
            supports_sensitive_data=False,
            local_only=False,
            max_context_tokens=128000,
        )

    def generate(
        self,
        request: ProviderRequest,
        context: ProviderExecutionContext,
    ) -> ProviderResponse:
        if not self._api_key:
            raise ProviderExecutionError(
                ProviderErrorType.AUTHENTICATION,
                "openai compatible api key is not configured",
                False,
            )
        start = time.perf_counter()
        payload = {
            "model": request.model_name,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": 0.2,
        }
        try:
            with httpx.Client(timeout=request.timeout_seconds) as client:
                response = client.post(
                    f"{self._base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=payload,
                )
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as exc:
            raise ProviderExecutionError(ProviderErrorType.TIMEOUT, str(exc), True) from exc
        except httpx.HTTPStatusError as exc:
            retryable = exc.response.status_code >= 500
            error_type = (
                ProviderErrorType.QUOTA_EXCEEDED
                if exc.response.status_code == 429
                else ProviderErrorType.PROVIDER_UNAVAILABLE
            )
            raise ProviderExecutionError(error_type, str(exc), retryable) from exc
        except httpx.HTTPError as exc:
            raise ProviderExecutionError(
                ProviderErrorType.PROVIDER_UNAVAILABLE,
                str(exc),
                True,
            ) from exc

        latency_ms = int((time.perf_counter() - start) * 1000)
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return ProviderResponse(
            provider_name=self.provider_name,
            model_name=request.model_name,
            content=content,
            raw_payload=data,
            latency_ms=latency_ms,
            usage=usage,
            cost_estimate=None,
        )

    def structured_generate(
        self,
        request: ProviderRequest,
        context: ProviderExecutionContext,
        schema: dict,
    ) -> ProviderResponse:
        return self.generate(request, context)
