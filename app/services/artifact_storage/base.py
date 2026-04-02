from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StoredArtifactRef:
    backend: str
    locator: str
    checksum: str


class ArtifactStorage:
    backend_name: str

    def store(
        self,
        package_id: str,
        file_name: str,
        content_text: str,
        checksum: str,
    ) -> StoredArtifactRef:
        raise NotImplementedError

    def read(self, locator: str) -> str:
        raise NotImplementedError
