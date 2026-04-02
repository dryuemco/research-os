from app.services.artifact_storage.local_fs import LocalFilesystemArtifactStorage


def test_local_filesystem_storage_roundtrip(tmp_path):
    storage = LocalFilesystemArtifactStorage(str(tmp_path))
    payload = b"hello world"
    ref = storage.store(
        package_id="pkg-1",
        file_name="artifact.md",
        content_bytes=payload,
        checksum="abc",
    )
    assert ref.backend == "local_fs"
    assert storage.read_bytes(ref.locator) == payload
    assert ref.size_bytes == len(payload)
