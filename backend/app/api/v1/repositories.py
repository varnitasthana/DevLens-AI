import asyncio
from collections.abc import Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas.repository import RepositoryCreate, RepositoryResponse
from app.services.repository import RepositoryService

router = APIRouter(prefix="/repositories", tags=["repositories"])


def get_repository_service(
    session: Session = Depends(get_db_session),
) -> Iterator[RepositoryService]:
    yield RepositoryService(session)


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository(
    data: RepositoryCreate,
    service: RepositoryService = Depends(get_repository_service),
) -> RepositoryResponse:
    return RepositoryResponse.model_validate(await asyncio.to_thread(service.create, data))


@router.get("", response_model=list[RepositoryResponse])
async def list_repositories(
    service: RepositoryService = Depends(get_repository_service),
) -> list[RepositoryResponse]:
    repositories = await asyncio.to_thread(service.list)
    return [RepositoryResponse.model_validate(item) for item in repositories]


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: UUID,
    service: RepositoryService = Depends(get_repository_service),
) -> RepositoryResponse:
    repository = await asyncio.to_thread(service.get, repository_id)
    return RepositoryResponse.model_validate(repository)


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repository_id: UUID,
    service: RepositoryService = Depends(get_repository_service),
) -> Response:
    await asyncio.to_thread(service.delete, repository_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
