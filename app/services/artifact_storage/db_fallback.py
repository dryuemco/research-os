from __future__ import annotations

from app.services.artifact_storage.base import ArtifactStorage, StoredArtifactRef


class DatabaseFallbackArtifactStorage(ArtifactStorage):
    backend_name = "db_fallback"

    def store(
        self,
        package_id: str,
        file_name: str,
        content_bytes: bytes,
        checksum: str,
    ) -> StoredArtifactRef:
        locator = f"db://{package_id}/{file_name}"
        return StoredArtifactRef(
            backend=self.backend_name,
            locator=locator,
            checksum=checksum,
            size_bytes=len(content_bytes),
        )

    def read_bytes(self, locator: str) -> bytes:
        raise ValueError("DB fallback artifacts should be read from persisted content_text")

    def verify(self, locator: str, expected_checksum: str) -> bool:
        return True
