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
