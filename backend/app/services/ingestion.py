import hashlib
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile

IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "venv",
}
LANGUAGE_BY_EXTENSION = {
    ".css": "css",
    ".go": "go",
    ".html": "html",
    ".java": "java",
    ".js": "javascript",
    ".json": "json",
    ".md": "markdown",
    ".py": "python",
    ".rs": "rust",
    ".sql": "sql",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".yaml": "yaml",
    ".yml": "yaml",
}


@dataclass(frozen=True)
class DiscoveredFile:
    path: str
    size_bytes: int
    language: str
    sha256: str
    content: str


class IngestionService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    def ingest_zip(self, repository: Repository, archive_path: Path) -> list[RepositoryFile]:
        extraction_dir = Path(tempfile.mkdtemp(prefix="devlens-ingestion-"))
        try:
            discovered = self._extract_and_scan(archive_path, extraction_dir)
            self.session.query(RepositoryFile).filter(
                RepositoryFile.repository_id == repository.id
            ).delete(synchronize_session=False)
            files = [
                RepositoryFile(
                    repository_id=repository.id,
                    path=item.path,
                    size_bytes=item.size_bytes,
                    language=item.language,
                    is_binary=False,
                    sha256=item.sha256,
                    content=item.content,
                )
                for item in discovered
            ]
            self.session.add_all(files)
            self.session.commit()
            return files
        except HTTPException:
            self.session.rollback()
            raise
        except Exception as exc:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The archive could not be ingested",
            ) from exc
        finally:
            shutil.rmtree(extraction_dir, ignore_errors=True)

    def _extract_and_scan(self, archive_path: Path, extraction_dir: Path) -> list[DiscoveredFile]:
        total_size = 0
        file_count = 0
        try:
            archive = zipfile.ZipFile(archive_path)
        except zipfile.BadZipFile as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="The upload is not a valid ZIP archive"
            ) from exc

        with archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                relative_path = self._safe_archive_path(member.filename)
                if relative_path is None or self._is_ignored(relative_path):
                    continue
                file_count += 1
                if file_count > self.settings.max_file_count:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="The archive contains too many files",
                    )
                if member.file_size > self.settings.max_file_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds the {self.settings.max_file_size_bytes}-byte limit",
                    )
                total_size += member.file_size
                if total_size > self.settings.max_repository_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="The repository exceeds the configured size limit",
                    )
                destination = extraction_dir / Path(*relative_path.parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, destination.open("wb") as target:
                    shutil.copyfileobj(source, target, length=1024 * 1024)

        return self._discover_files(extraction_dir)

    def _discover_files(self, root: Path) -> list[DiscoveredFile]:
        discovered: list[DiscoveredFile] = []
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative_path = path.relative_to(root)
            if self._is_ignored(PurePosixPath(relative_path.as_posix())):
                continue
            language = LANGUAGE_BY_EXTENSION.get(path.suffix.lower())
            if language is None or self._is_binary(path):
                continue
            digest = hashlib.sha256()
            with path.open("rb") as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
            discovered.append(
                DiscoveredFile(
                    path=relative_path.as_posix(),
                    size_bytes=path.stat().st_size,
                    language=language,
                    sha256=digest.hexdigest(),
                    content=path.read_text(encoding="utf-8", errors="replace"),
                )
            )
        return sorted(discovered, key=lambda item: item.path)

    @staticmethod
    def _safe_archive_path(name: str) -> PurePosixPath | None:
        if not name or "\x00" in name or "\\" in name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Archive contains an unsafe path",
            )
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Archive contains an unsafe path",
            )
        return path

    @staticmethod
    def _is_ignored(path: PurePosixPath) -> bool:
        return any(part in IGNORED_DIRECTORIES for part in path.parts)

    @staticmethod
    def _is_binary(path: Path) -> bool:
        with path.open("rb") as source:
            return b"\x00" in source.read(8192)
