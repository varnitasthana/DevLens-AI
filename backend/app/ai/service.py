from app.ai.context import build_context, render_context
from app.ai.provider import AIProvider
from app.ai.schemas import AIRequest, AIReviewResponse


class AIReviewService:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def review_files(self, files: dict[str, str]) -> AIReviewResponse:
        context = render_context(build_context(files))
        if not context:
            return AIReviewResponse(findings=[])
        return await self.provider.review(AIRequest(context=context))
