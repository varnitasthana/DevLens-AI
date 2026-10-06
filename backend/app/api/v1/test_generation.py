from fastapi import APIRouter, Depends, HTTPException, status

from app.ai.provider import OpenAICompatibleProvider
from app.ai.test_generation import AITestGenerationService
from app.core.config import Settings, get_settings
from app.schemas.test_generation import GeneratedTestResponse, TestGenerationRequest
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/test-generation", tags=["test-generation"])


@router.post("", response_model=GeneratedTestResponse)
async def generate_tests(
    request: TestGenerationRequest,
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_user),
) -> GeneratedTestResponse:
    if not settings.ai_base_url or not settings.ai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI test generation is not configured",
        )
    provider = OpenAICompatibleProvider(
        settings.ai_base_url,
        settings.ai_api_key,
        settings.ai_model,
        settings.ai_timeout_seconds,
    )
    return await AITestGenerationService(provider).generate(request)
