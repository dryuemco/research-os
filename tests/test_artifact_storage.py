from app.services.artifact_storage.local_fs import LocalFilesystemArtifactStorage


def test_local_filesystem_storage_roundtrip(tmp_path):
    storage = LocalFilesystemArtifactStorage(str(tmp_path))
    ref = storage.store(
        package_id="pkg-1",
        file_name="artifact.md",
        content_text="hello world",
        checksum="abc",
    )
    assert ref.backend == "local_fs"
    assert storage.read(ref.locator) == "hello world"
