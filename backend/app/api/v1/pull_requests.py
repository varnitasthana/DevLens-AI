import asyncio
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.schemas.dashboard import PullRequestReviewRequest, PullRequestReviewResponse
from app.services.github import HttpGitHubClient
from app.services.pull_request_review import PullRequestReviewService
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/pull-requests", tags=["pull-requests"])


def get_pull_request_review_service(
    settings: Settings = Depends(get_settings),
) -> Iterator[PullRequestReviewService]:
    yield PullRequestReviewService(HttpGitHubClient(settings.github_token), settings)


@router.post("/review", response_model=PullRequestReviewResponse)
async def review_pull_request(
    request: PullRequestReviewRequest,
    service: PullRequestReviewService = Depends(get_pull_request_review_service),
    user: User = Depends(get_current_user),
) -> PullRequestReviewResponse:
    if request.github_url:
        return await asyncio.to_thread(service.review_github_pr, request.github_url)
    if request.diff:
        return service.review_diff(request.diff)
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Either a diff or a GitHub pull request URL must be provided",
    )
