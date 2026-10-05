import zipfile
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.services.ingestion import IngestionService


def test_scan_discovers_languages_and_ignores_binary_and_directories(tmp_path: Path) -> None:
    archive_path = tmp_path / "repository.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("src/main.py", b"print('ok')")
        archive.writestr("README.md", b"# DevLens")
        archive.writestr("node_modules/package/index.js", b"ignored")
        archive.writestr("image.png", b"\x89PNG\x00binary")
        archive.writestr("notes.xyz", b"unsupported")

    service = IngestionService(None, Settings())
    discovered = service._extract_and_scan(archive_path, tmp_path / "out")

    assert [(item.path, item.language) for item in discovered] == [
        ("README.md", "markdown"),
        ("src/main.py", "python"),
    ]


def test_empty_archive_returns_no_files(tmp_path: Path) -> None:
    archive_path = tmp_path / "empty.zip"
    with zipfile.ZipFile(archive_path, "w"):
        pass

    discovered = IngestionService(None, Settings())._extract_and_scan(
        archive_path, tmp_path / "out"
    )

    assert discovered == []


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.py", b"unsafe")

    with pytest.raises(HTTPException, match="unsafe path"):
        IngestionService(None, Settings())._extract_and_scan(
            archive_path, tmp_path / "out"
        )


def test_nested_directories_are_supported(tmp_path: Path) -> None:
    archive_path = tmp_path / "nested.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("one/two/three/app.ts", b"const ok = true")

    discovered = IngestionService(None, Settings())._extract_and_scan(
        archive_path, tmp_path / "out"
    )

    assert discovered[0].path == "one/two/three/app.ts"


def test_oversized_file_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "large.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("large.py", b"x" * 11)

    settings = Settings(max_file_size_bytes=10)
    with pytest.raises(HTTPException, match="exceeds"):
        IngestionService(None, settings)._extract_and_scan(
            archive_path, tmp_path / "out"
        )
