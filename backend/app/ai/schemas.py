from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class AIRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    context: str = Field(min_length=1)


class AIFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Literal["bug", "maintainability", "security", "performance", "testing"]
    severity: Literal["low", "medium", "high", "critical"]
    explanation: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    suggested_fix: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)
    source: Literal["ai"] = "ai"


class AIReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    findings: list[AIFinding]


class TestGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_name: str = Field(min_length=1, pattern=r".+\.py$")
    source: str = Field(min_length=1, max_length=40_000)


class GeneratedTestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    review_banner: Literal["AI GENERATED — REVIEW BEFORE EXECUTION"] = (
        "AI GENERATED — REVIEW BEFORE EXECUTION"
    )
    file_name: str
    test_code: str = Field(min_length=1, max_length=80_000)
    scenarios: list[str] = Field(min_length=1)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=4_000)


class ChatCitation(BaseModel):
    file: str
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(min_length=1, max_length=20_000)
    citations: list[ChatCitation] = Field(default_factory=list, max_length=20)
