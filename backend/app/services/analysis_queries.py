from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.analysis import Analysis
from app.models.finding import Finding


class AnalysisQueryService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, analysis_id: UUID) -> Analysis:
        analysis = self.session.scalar(
            select(Analysis)
            .options(selectinload(Analysis.findings))
            .where(Analysis.id == analysis_id)
        )
        if analysis is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
        return analysis

    def findings(
        self,
        analysis_id: UUID,
        severity: str | None = None,
        category: str | None = None,
        source: str | None = None,
        file: str | None = None,
    ) -> list[Finding]:
        if self.session.scalar(select(Analysis.id).where(Analysis.id == analysis_id)) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
        query = select(Finding).where(Finding.analysis_id == analysis_id)
        if severity:
            query = query.where(Finding.severity == severity)
        if category:
            query = query.where(Finding.category == category)
        if source:
            query = query.where(Finding.source == source)
        if file:
            query = query.where(Finding.file == file)
        return list(self.session.scalars(query.order_by(Finding.file, Finding.line)).all())
