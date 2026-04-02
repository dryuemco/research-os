from app.core.config import get_settings
from app.providers.base import ProviderClient
from app.providers.mock_provider import MockProviderClient
from app.providers.openai_compatible import OpenAICompatibleProviderClient


class ProviderRegistry:
    """In-memory provider registry for adapter lookup."""

    def __init__(self) -> None:
        self._providers: dict[str, ProviderClient] = {}

    def register(self, provider: ProviderClient) -> None:
        self._providers[provider.provider_name] = provider

    def get(self, provider_name: str) -> ProviderClient:
        if provider_name not in self._providers:
            raise KeyError(f"Provider '{provider_name}' is not registered")
        return self._providers[provider_name]

    def list_provider_names(self) -> list[str]:
        return list(self._providers.keys())


def build_default_provider_registry() -> ProviderRegistry:
    settings = get_settings()
    registry = ProviderRegistry()
    registry.register(MockProviderClient())
    registry.register(
        OpenAICompatibleProviderClient(
            base_url=settings.openai_compatible_base_url,
            api_key=settings.openai_compatible_api_key,
        )
    )
    return registry
