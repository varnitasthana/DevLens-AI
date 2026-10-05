import pytest
from pydantic import ValidationError

from app.ai.context import build_context, render_context
from app.ai.schemas import AIReviewResponse


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
