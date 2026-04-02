from __future__ import annotations

from app.services.opportunity_adapters import DEFAULT_ADAPTERS


class SourceRegistryService:
    def __init__(self) -> None:
        self.adapters = DEFAULT_ADAPTERS

    def list_sources(self) -> list[dict]:
        return [
            {
                "source_name": adapter.source_name,
                "capability": {
                    "supports_incremental_sync": adapter.capability.supports_incremental_sync,
                    "supports_deadline_detection": adapter.capability.supports_deadline_detection,
                    "normalization_version": adapter.capability.normalization_version,
                },
                "health": adapter.healthcheck(),
            }
            for adapter in self.adapters.values()
        ]

    def get(self, source_name: str):
        adapter = self.adapters.get(source_name)
        if adapter is None:
            raise ValueError(f"No source adapter registered for '{source_name}'")
        return adapter
