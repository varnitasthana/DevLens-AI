from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    file: str
    line: int
    column: int
    rule: str
    category: str
    severity: str
    message: str
    source: str
    evidence: str | None
    remediation: str | None


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    repository_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: float | None
    files_analyzed: int
    analyzer_source: str
    findings: list[FindingResponse]


class AnalysisSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    repository_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: float | None
    files_analyzed: int
    analyzer_source: str
