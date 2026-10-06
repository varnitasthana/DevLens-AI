from app.ai.provider import AIProvider
from app.ai.schemas import GeneratedTestResponse, TestGenerationRequest


class AITestGenerationService:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def generate(self, request: TestGenerationRequest) -> GeneratedTestResponse:
        return await self.provider.generate_tests(request)
