from fastapi import APIRouter

from app.schemas.dashboard import PullRequestReviewRequest, PullRequestReviewResponse
from app.services.pull_request_review import PullRequestReviewService

router = APIRouter(prefix="/pull-requests", tags=["pull-requests"])


@router.post("/review", response_model=PullRequestReviewResponse)
async def review_pull_request(
    request: PullRequestReviewRequest,
) -> PullRequestReviewResponse:
    return PullRequestReviewService().review_diff(request.diff)
