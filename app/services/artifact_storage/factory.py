from app.core.config import get_settings
from app.services.artifact_storage.base import ArtifactStorage
from app.services.artifact_storage.db_fallback import DatabaseFallbackArtifactStorage
from app.services.artifact_storage.local_fs import LocalFilesystemArtifactStorage


def build_artifact_storage() -> ArtifactStorage:
    settings = get_settings()
    if settings.artifact_storage_backend == "local_fs":
        return LocalFilesystemArtifactStorage(settings.artifact_storage_root)
    return DatabaseFallbackArtifactStorage()
