from dataclasses import dataclass
from uuid import UUID

from app.ai.context import ContextChunk, render_context
from app.ai.provider import AIProvider
from app.ai.schemas import ChatResponse
from app.core.config import Settings
from app.models.repository_file import RepositoryFile


@dataclass(frozen=True)
class RetrievedChunk:
    file: str
    content: str


class RepositoryChatService:
    def __init__(self, session, settings: Settings, provider: AIProvider) -> None:
        self.session = session
        self.settings = settings
        self.provider = provider

    async def answer(self, repository_id: UUID, question: str) -> ChatResponse:
        terms = {term.lower() for term in question.split() if len(term) > 2}
        files = self.session.query(RepositoryFile).filter(
            RepositoryFile.repository_id == repository_id,
            RepositoryFile.content.is_not(None),
        ).all()
        ranked = sorted(
            files,
            key=lambda item: sum(term in (item.content or "").lower() for term in terms),
            reverse=True,
        )
        selected = [
            RetrievedChunk(item.path, (item.content or "")[: self.settings.chat_max_context_chars])
            for item in ranked[: self.settings.chat_max_files]
            if terms and any(term in (item.content or "").lower() for term in terms)
        ]
        if not selected:
            return ChatResponse(
                answer="I could not find relevant repository content for that question.",
                citations=[],
            )
        context = render_context(
            [ContextChunk(item.file, item.content) for item in selected]
        )[: self.settings.chat_max_context_chars]
        result = await self.provider.chat(question, context)
        allowed = {item.file for item in selected}
        citations = [
            citation for citation in result.citations if citation.file in allowed
        ]
        return result.model_copy(update={"citations": citations})
