from __future__ import annotations

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
        content_text: str,
        checksum: str,
    ) -> StoredArtifactRef:
        package_dir = self.root / package_id
        package_dir.mkdir(parents=True, exist_ok=True)
        path = package_dir / file_name
        path.write_text(content_text, encoding="utf-8")
        return StoredArtifactRef(backend=self.backend_name, locator=str(path), checksum=checksum)

    def read(self, locator: str) -> str:
        return Path(locator).read_text(encoding="utf-8")
