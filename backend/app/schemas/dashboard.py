from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DashboardResponse(BaseModel):
    repositories: int
    total_analyses: int
    latest_analysis_id: UUID | None
    latest_analysis_status: str | None
    latest_analysis_at: datetime | None
    findings_total: int
    findings_by_severity: dict[str, int]
    findings_by_source: dict[str, int]
    security_findings: int
    files_analyzed: int


class GitHubImportRequest(BaseModel):
    url: str
    branch: str | None = None


class GitHubImportResponse(BaseModel):
    id: UUID
    name: str
    source_url: str
    default_branch: str
    file_count: int
    status: str


class PullRequestReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diff: str | None = None
    github_url: str | None = None
    repository: str | None = None
    pull_request: int | None = None


class PullRequestReviewResponse(BaseModel):
    summary: str
    issues: list[dict[str, str]]
    testing_recommendations: list[str]
