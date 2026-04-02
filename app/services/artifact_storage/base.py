from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StoredArtifactRef:
    backend: str
    locator: str
    checksum: str
    size_bytes: int


class ArtifactStorage:
    backend_name: str

    def store(
        self,
        package_id: str,
        file_name: str,
        content_bytes: bytes,
        checksum: str,
    ) -> StoredArtifactRef:
        raise NotImplementedError

    def read_bytes(self, locator: str) -> bytes:
        raise NotImplementedError

    def verify(self, locator: str, expected_checksum: str) -> bool:
        raise NotImplementedError
