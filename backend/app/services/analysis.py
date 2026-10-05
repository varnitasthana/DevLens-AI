import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.analyzers.base import Analyzer, NormalizedFinding
from app.analyzers.javascript import JavaScriptAnalyzer
from app.analyzers.python import PythonAnalyzer
from app.models.analysis import Analysis
from app.models.finding import Finding
from app.models.repository import Repository
from app.core.config import Settings


class StaticAnalysisService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.analyzers: dict[str, Analyzer] = {
            "python": PythonAnalyzer(),
            "javascript": JavaScriptAnalyzer(),
            "typescript": JavaScriptAnalyzer(),
        }

    def analyze_zip(self, repository: Repository, archive_path: Path) -> tuple[Analysis, list[Finding]]:
        workspace = Path(tempfile.mkdtemp(prefix="devlens-analysis-"))
        try:
            with zipfile.ZipFile(archive_path) as archive:
                total_size = 0
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    relative = PurePosixPath(member.filename)
                    if relative.is_absolute() or ".." in relative.parts or "\\" in member.filename:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archive contains an unsafe path")
                    if member.file_size > self.settings.max_file_size_bytes:
                        raise HTTPException(status_code=413, detail="File exceeds the configured limit")
                    total_size += member.file_size
                    if total_size > self.settings.max_repository_size_bytes:
                        raise HTTPException(status_code=413, detail="The repository exceeds the configured size limit")
                    destination = workspace.joinpath(*relative.parts)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(member) as source, destination.open("wb") as target:
                        shutil.copyfileobj(source, target, length=1024 * 1024)
            normalized: list[NormalizedFinding] = []
            for path in workspace.rglob("*"):
                if not path.is_file():
                    continue
                language = self._language(path)
                analyzer = self.analyzers.get(language or "")
                if analyzer:
                    normalized.extend(analyzer.analyze(path, path.relative_to(workspace).as_posix()))
            analysis = Analysis(repository_id=repository.id, status="completed")
            analysis.findings = [Finding(**finding.__dict__) for finding in normalized]
            self.session.add(analysis)
            self.session.commit()
            return analysis, list(analysis.findings)
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    @staticmethod
    def _language(path: Path) -> str | None:
        return {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
        }.get(path.suffix.lower())
