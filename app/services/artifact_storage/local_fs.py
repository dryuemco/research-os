from __future__ import annotations

import hashlib
from pathlib import Path

from app.services.artifact_storage.base import ArtifactStorage, StoredArtifactRef


class LocalFilesystemArtifactStorage(ArtifactStorage):
    backend_name = "local_fs"

    def __init__(self, root_path: str) -> None:
        self.root = Path(root_path)
        self.root.mkdir(parents=True, exist_ok=True)

    def store(
        self,
        package_id: str,
        file_name: str,
        content_bytes: bytes,
        checksum: str,
    ) -> StoredArtifactRef:
        package_dir = self.root / package_id
        package_dir.mkdir(parents=True, exist_ok=True)
        path = package_dir / file_name
        path.write_bytes(content_bytes)
        locator = str(path.relative_to(self.root))
        return StoredArtifactRef(
            backend=self.backend_name,
            locator=locator,
            checksum=checksum,
            size_bytes=len(content_bytes),
        )

    def read_bytes(self, locator: str) -> bytes:
        path = self._resolve(locator)
        return path.read_bytes()

    def verify(self, locator: str, expected_checksum: str) -> bool:
        payload = self.read_bytes(locator)
        actual = hashlib.sha256(payload).hexdigest()
        return actual == expected_checksum

    def _resolve(self, locator: str) -> Path:
        path = (self.root / locator).resolve()
        root_resolved = self.root.resolve()
        if root_resolved not in path.parents and path != root_resolved:
            raise ValueError("Invalid storage locator")
        return path
