from collections import Counter
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.finding import Finding
from app.models.repository import Repository
from app.schemas.dashboard import DashboardResponse


class DashboardService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def summary(self) -> DashboardResponse:
        repositories = self.session.scalar(select(func.count(Repository.id))) or 0
        total_analyses = self.session.scalar(select(func.count(Analysis.id))) or 0
        latest = self.session.scalar(select(Analysis).order_by(Analysis.created_at.desc()).limit(1))
        findings = list(self.session.scalars(select(Finding)).all())
        severities = Counter(finding.severity for finding in findings)
        sources = Counter(finding.source for finding in findings)
        return DashboardResponse(
            repositories=repositories,
            total_analyses=total_analyses,
            latest_analysis_id=latest.id if latest else None,
            latest_analysis_status=latest.status if latest else None,
            latest_analysis_at=latest.created_at if latest else None,
            findings_total=len(findings),
            findings_by_severity=dict(severities),
            findings_by_source=dict(sources),
            security_findings=sum(finding.category == "security" for finding in findings),
            files_analyzed=sum(analysis.files_analyzed for analysis in self.session.scalars(select(Analysis)).all()),
        )
