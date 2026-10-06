import asyncio
from collections.abc import Iterator

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.schemas.dashboard import GitHubImportRequest, GitHubImportResponse
from app.services.github import GitHubImportService, HttpGitHubClient
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/github", tags=["github"])


def get_github_import_service(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> Iterator[GitHubImportService]:
    yield GitHubImportService(session, HttpGitHubClient(settings.github_token), settings)


@router.post("/repositories/import", response_model=GitHubImportResponse, status_code=201)
async def import_github_repository(
    request: GitHubImportRequest,
    service: GitHubImportService = Depends(get_github_import_service),
    user: User = Depends(get_current_user),
) -> GitHubImportResponse:
    return await asyncio.to_thread(service.import_repository, request, user.id)
