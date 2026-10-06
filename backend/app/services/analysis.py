import asyncio
import shutil
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.analyzers.base import Analyzer, NormalizedFinding
from app.analyzers.javascript import JavaScriptAnalyzer
from app.analyzers.python import PythonAnalyzer
from app.ai.provider import OpenAICompatibleProvider
from app.ai.service import AIReviewService
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
        analysis = Analysis(repository_id=repository.id, status="QUEUED")
        self.session.add(analysis)
        self.session.commit()
        analysis.status = "RUNNING"
        analysis.started_at = datetime.now(timezone.utc)
        self.session.commit()
        started = time.perf_counter()
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
            source_files: dict[str, str] = {}
            for path in workspace.rglob("*"):
                if not path.is_file():
                    continue
                language = self._language(path)
                analyzer = self.analyzers.get(language or "")
                if analyzer:
                    relative_path = path.relative_to(workspace).as_posix()
                    normalized.extend(analyzer.analyze(path, relative_path))
                    source_files[relative_path] = path.read_text(encoding="utf-8", errors="replace")
            ai_findings = self._run_ai(source_files)
            normalized.extend(ai_findings)
            analysis.findings = [Finding(**finding.__dict__) for finding in normalized]
            analysis.status = "COMPLETED"
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.duration_ms = (time.perf_counter() - started) * 1000
            analysis.files_analyzed = len(source_files)
            analysis.analyzer_source = "static,ai" if ai_findings else "static"
            self.session.commit()
            return analysis, list(analysis.findings)
        except Exception:
            analysis.status = "FAILED"
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.duration_ms = (time.perf_counter() - started) * 1000
            self.session.commit()
            raise
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def _run_ai(self, files: dict[str, str]) -> list[NormalizedFinding]:
        if not self.settings.ai_base_url or not self.settings.ai_api_key:
            return []
        provider = OpenAICompatibleProvider(
            self.settings.ai_base_url,
            self.settings.ai_api_key,
            self.settings.ai_model,
            self.settings.ai_timeout_seconds,
        )
        response = asyncio.run(AIReviewService(provider).review_files(files))
        return [
            NormalizedFinding(
                file=finding.evidence.split(":", 1)[0] if ":" in finding.evidence else "unknown",
                line=0,
                column=0,
                rule=f"ai.{finding.category}",
                category=finding.category,
                severity=finding.severity,
                message=finding.explanation,
                source="ai",
                evidence=finding.evidence,
                remediation=finding.suggested_fix,
            )
            for finding in response.findings
        ]

    @staticmethod
    def _language(path: Path) -> str | None:
        return {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
        }.get(path.suffix.lower())
