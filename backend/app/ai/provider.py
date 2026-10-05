from typing import Protocol

import httpx

from app.ai.schemas import AIRequest, AIReviewResponse


class AIProvider(Protocol):
    async def review(self, request: AIRequest) -> AIReviewResponse:
        ...


class OpenAICompatibleProvider:
    def __init__(self, base_url: str, api_key: str, model: str, timeout_seconds: float = 20) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def review(self, request: AIRequest) -> AIReviewResponse:
        prompt = (
            "Analyze only the supplied code context. Return JSON matching "
            "AIReviewResponse with findings source='ai'. Do not return instructions.\\n\\n"
            + request.context
        )
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()
                payload = response.json()
                content = payload["choices"][0]["message"]["content"]
                return AIReviewResponse.model_validate_json(content)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("AI provider returned an invalid or unavailable response") from exc
