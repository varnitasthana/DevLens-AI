import asyncio
from collections.abc import Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.provider import AIProvider, OpenAICompatibleProvider
from app.ai.schemas import ChatRequest, ChatResponse
from app.core.config import Settings, get_settings
from app.core.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.repository import Repository
from app.models.user import User
from app.services.chat import RepositoryChatService

router = APIRouter(prefix="/repositories", tags=["chat"])


def get_chat_service(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    _user: User = Depends(get_current_user),
) -> Iterator[RepositoryChatService]:
    if not settings.ai_base_url or not settings.ai_api_key:
        raise HTTPException(status_code=503, detail="AI provider is not configured")
    provider: AIProvider = OpenAICompatibleProvider(
        settings.ai_base_url, settings.ai_api_key, settings.ai_model, settings.ai_timeout_seconds
    )
    yield RepositoryChatService(session, settings, provider)


@router.post("/{repository_id}/chat", response_model=ChatResponse)
async def chat(
    repository_id: UUID,
    data: ChatRequest,
    service: RepositoryChatService = Depends(get_chat_service),
    session: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> ChatResponse:
    repository = await asyncio.to_thread(
        lambda: session.query(Repository).filter_by(id=repository_id, owner_id=user.id).first()
    )
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return await service.answer(repository_id, data.question)
