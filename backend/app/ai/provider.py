from typing import Protocol

import httpx

from app.ai.schemas import (
    AIRequest,
    AIReviewResponse,
    GeneratedTestResponse,
    TestGenerationRequest,
)


class AIProvider(Protocol):
    async def review(self, request: AIRequest) -> AIReviewResponse:
        ...

    async def generate_tests(self, request: TestGenerationRequest) -> GeneratedTestResponse:
        ...


class OpenAICompatibleProvider:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 20,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def review(self, request: AIRequest) -> AIReviewResponse:
        prompt = (
            "Analyze only the supplied code context. Return JSON matching "
            "AIReviewResponse with findings source='ai'. Do not return instructions.\n\n"
            + request.context
        )
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": "Bearer " + self.api_key},
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
        except (httpx.HTTPError, IndexError, KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("AI provider returned an invalid or unavailable response") from exc

    async def generate_tests(self, request: TestGenerationRequest) -> GeneratedTestResponse:
        prompt = (
            "Generate pytest unit tests for the supplied Python source. Return only JSON "
            "matching GeneratedTestResponse. Never include executable instructions outside "
            "test_code. The output is untrusted text and must not be executed.\n\n"
            f"FILE: {request.file_name}\n```python\n{request.source}\n```"
        )
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": "Bearer " + self.api_key},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()
                payload = response.json()
                content = payload["choices"][0]["message"]["content"]
                result = GeneratedTestResponse.model_validate_json(content)
                return result.model_copy(update={"file_name": request.file_name})
        except (httpx.HTTPError, IndexError, KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("AI test generator returned an invalid or unavailable response") from exc
