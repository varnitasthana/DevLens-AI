from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Protocol

from app.core.config import Settings


class StorageBackend(Protocol):
    def upload(self, key: str, source_path: Path) -> str:
        ...

    def download(self, key: str, destination_path: Path) -> None:
        ...

    def delete(self, key: str) -> None:
        ...


class S3StorageBackend(StorageBackend):
    def __init__(self, settings: Settings) -> None:
        import boto3  # type: ignore

        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region or None,
        )
        self._bucket = settings.s3_bucket_name

    def upload(self, key: str, source_path: Path) -> str:
        self._client.upload_file(str(source_path), self._bucket, key)
        return key

    def download(self, key: str, destination_path: Path) -> None:
        self._client.download_file(self._bucket, key, str(destination_path))

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)


class LocalStorageBackend(StorageBackend):
    def __init__(self, settings: Settings) -> None:
        self._base = Path(settings.analysis_upload_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    def upload(self, key: str, source_path: Path) -> str:
        destination = self._base / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        return str(destination)

    def download(self, key: str, destination_path: Path) -> None:
        shutil.copy2(Path(key), destination_path)

    def delete(self, key: str) -> None:
        Path(key).unlink(missing_ok=True)


class StorageService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._backend: StorageBackend | None = None

    @property
    def backend(self) -> StorageBackend:
        if self._backend is None:
            if self._settings.s3_bucket_name:
                self._backend = S3StorageBackend(self._settings)
            else:
                self._backend = LocalStorageBackend(self._settings)
        return self._backend

    def upload_archive(self, source_path: Path) -> str:
        key = f"uploads/{os.urandom(16).hex()}.zip"
        return self.backend.upload(key, source_path)

    def download_to_temp(self, key: str) -> Path:
        temp_file = tempfile.NamedTemporaryFile(
            prefix="devlens-archive-", suffix=".zip", delete=False
        )
        temp_path = Path(temp_file.name)
        temp_file.close()
        self.backend.download(key, temp_path)
        return temp_path

    def cleanup(self, key: str) -> None:
        self.backend.delete(key)


def get_storage_service(settings: Settings | None = None) -> StorageService:
    from app.core.config import get_settings

    return StorageService(settings or get_settings())
