import asyncio
from collections.abc import Iterator

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_dashboard_service(session: Session = Depends(get_db_session)) -> Iterator[DashboardService]:
    yield DashboardService(session)


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardResponse:
    return await asyncio.to_thread(service.summary)
