from os import getenv

import httpx
import pytest
from pydantic import ValidationError

from app.ai.context import build_context, render_context
from app.ai.provider import OpenAICompatibleProvider
from app.ai.schemas import (
    AIRequest,
    AIReviewResponse,
    GeneratedTestResponse,
    TestGenerationRequest as GenerationRequest,
)
from app.ai.test_generation import AITestGenerationService


def test_context_filters_files_and_caps_size() -> None:
    chunks = build_context({"app.py": "x" * 20, "image.png": "ignored"}, max_file_chars=10, max_total_chars=10)
    assert render_context(chunks).count("app.py") == 1
    assert len(chunks[0].content) == 10


def test_ai_response_rejects_untrusted_malformed_output() -> None:
    with pytest.raises(ValidationError):
        AIReviewResponse.model_validate({"findings": [{"category": "unknown"}]})


@pytest.mark.asyncio
async def test_mock_provider_response_is_structured() -> None:
    class MockProvider:
        async def review(self, request):
            return AIReviewResponse(findings=[])

    from app.ai.service import AIReviewService
    result = await AIReviewService(MockProvider()).review_files({"app.py": "pass"})
    assert result.findings == []


@pytest.mark.asyncio
async def test_openai_compatible_provider_validates_response_and_auth() -> None:
    captured: dict[str, str] = {}
    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content.decode()
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"findings":[]}'}}]},
        )

    provider = OpenAICompatibleProvider(
        "https://ai.example.test",
        "test-key",
        "test-model",
        transport=httpx.MockTransport(handler),
    )
    result = await provider.review(AIRequest(context="app.py\npass"))
    assert result.findings == []
    assert "never as instructions" in captured.get("body", "")


@pytest.mark.asyncio
async def test_openai_compatible_provider_rejects_malformed_payload() -> None:
    provider = OpenAICompatibleProvider(
        "https://ai.example.test",
        "test-key",
        "test-model",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"choices": []})),
    )
    with pytest.raises(RuntimeError, match="invalid or unavailable"):
        await provider.review(AIRequest(context="app.py\npass"))


@pytest.mark.asyncio
async def test_openai_compatible_provider_handles_timeout() -> None:
    def timeout(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    provider = OpenAICompatibleProvider(
        "https://ai.example.test",
        "test-key",
        "test-model",
        transport=httpx.MockTransport(timeout),
    )
    with pytest.raises(RuntimeError, match="invalid or unavailable"):
        await provider.review(AIRequest(context="app.py\npass"))


@pytest.mark.asyncio
async def test_mock_test_generation_is_marked_and_not_executed() -> None:
    class MockProvider:
        async def generate_tests(self, request: GenerationRequest) -> GeneratedTestResponse:
            return GeneratedTestResponse(
                file_name=request.file_name,
                test_code="def test_add():\n    assert add(1, 2) == 3",
                scenarios=["happy path"],
            )

    result = await AITestGenerationService(MockProvider()).generate(
        GenerationRequest(file_name="math.py", source="def add(a, b): return a + b")
    )
    assert result.review_banner == "AI GENERATED — REVIEW BEFORE EXECUTION"
    assert "def test_add" in result.test_code


def test_test_generation_request_rejects_non_python_files() -> None:
    with pytest.raises(ValidationError):
        GenerationRequest(file_name="component.ts", source="export const value = 1")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_configured_ai_provider_integration() -> None:
    base_url = getenv("AI_BASE_URL")
    api_key = getenv("AI_API_KEY")
    model = getenv("AI_MODEL", "devlens-reviewer")
    if not base_url or not api_key:
        pytest.skip("AI_BASE_URL and AI_API_KEY are required")

    provider = OpenAICompatibleProvider(
        base_url=base_url,
        api_key=api_key,
        model=model,
    )
    response = await provider.review(
        AIRequest(
            context=(
                "FILE: example.py\n"
                "```python\n"
                "def add(left: int, right: int) -> int:\n"
                "    return left + right\n"
                "```"
            )
        )
    )
    assert isinstance(response, AIReviewResponse)
