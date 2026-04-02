from __future__ import annotations

from app.services.artifact_storage.base import ArtifactStorage, StoredArtifactRef


class DatabaseFallbackArtifactStorage(ArtifactStorage):
    backend_name = "db_fallback"

    def store(
        self,
        package_id: str,
        file_name: str,
        content_text: str,
        checksum: str,
    ) -> StoredArtifactRef:
        locator = f"db://{package_id}/{file_name}"
        return StoredArtifactRef(backend=self.backend_name, locator=locator, checksum=checksum)

    def read(self, locator: str) -> str:
        raise ValueError("DB fallback artifacts should be read from persisted content_text")
