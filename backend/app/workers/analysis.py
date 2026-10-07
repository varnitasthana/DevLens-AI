from pathlib import Path
from uuid import UUID

from app.core.config import get_settings
from app.db.session import session_factory
from app.models.repository import Repository
from app.models.analysis import Analysis
from app.services.analysis import StaticAnalysisService
from app.services.storage import StorageService
from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="devlens.analyze_repository",
    autoretry_for=(TimeoutError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
    time_limit=600,
    soft_time_limit=540,
)
def analyze_repository_task(
    task,
    analysis_id: str,
    repository_id: str,
    storage_key: str,
) -> None:
    settings = get_settings()
    storage = StorageService(settings)
    local_path: Path | None = None
    try:
        with session_factory() as session:
            repository = session.get(Repository, UUID(repository_id))
            if repository is None:
                raise ValueError("Repository not found")
            local_path = storage.download_to_temp(storage_key)
            StaticAnalysisService(session, settings).analyze_existing(
                repository, UUID(analysis_id), local_path
            )
    finally:
        if local_path is not None:
            local_path.unlink(missing_ok=True)
        storage.cleanup(storage_key)


@celery_app.task(name="devlens.mark_analysis_failed")
def mark_analysis_failed(analysis_id: str) -> None:
    with session_factory() as session:
        analysis = session.get(Analysis, UUID(analysis_id))
        if analysis is not None and analysis.status not in {"COMPLETED", "FAILED"}:
            analysis.status = "FAILED"
            session.commit()
