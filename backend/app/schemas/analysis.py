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
    findings: list[FindingResponse]
