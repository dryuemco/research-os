from app.providers.base import ProviderClient


class ProviderRegistry:
    """In-memory provider registry for adapter lookup.

    This keeps the core routing layer independent from specific vendors.
    A database-backed registry can be added later without changing callers.
    """

    def __init__(self) -> None:
        self._providers: dict[str, ProviderClient] = {}

    def register(self, provider: ProviderClient) -> None:
        self._providers[provider.provider_name] = provider

    def get(self, provider_name: str) -> ProviderClient:
        if provider_name not in self._providers:
            raise KeyError(f"Provider '{provider_name}' is not registered")
        return self._providers[provider_name]
