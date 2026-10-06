import asyncio
from collections.abc import Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas.analysis import AnalysisResponse, FindingResponse
from app.services.analysis_queries import AnalysisQueryService
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/analyses", tags=["analyses"])


def get_analysis_query_service(
    session: Session = Depends(get_db_session),
) -> Iterator[AnalysisQueryService]:
    yield AnalysisQueryService(session)


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: UUID,
    service: AnalysisQueryService = Depends(get_analysis_query_service),
    user: User = Depends(get_current_user),
) -> AnalysisResponse:
    analysis = await asyncio.to_thread(service.get, analysis_id, user.id)
    return AnalysisResponse.model_validate(analysis)


@router.get("/{analysis_id}/findings", response_model=list[FindingResponse])
async def get_analysis_findings(
    analysis_id: UUID,
    severity: str | None = Query(default=None),
    category: str | None = Query(default=None),
    source: str | None = Query(default=None),
    file: str | None = Query(default=None),
    service: AnalysisQueryService = Depends(get_analysis_query_service),
    user: User = Depends(get_current_user),
) -> list[FindingResponse]:
    findings = await asyncio.to_thread(
        service.findings,
        analysis_id,
        severity,
        category,
        source,
        file,
        user.id,
    )
    return [FindingResponse.model_validate(finding) for finding in findings]
