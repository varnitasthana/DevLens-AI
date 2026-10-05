import asyncio
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.core.config import Settings, get_settings
from app.models.repository import Repository
from app.schemas.repository import RepositoryCreate, RepositoryResponse, RepositoryUpdate
from app.schemas.ingestion import IngestionResponse
from app.services.ingestion import IngestionService
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


@router.patch("/{repository_id}", response_model=RepositoryResponse)
async def update_repository(
    repository_id: UUID,
    data: RepositoryUpdate,
    service: RepositoryService = Depends(get_repository_service),
) -> RepositoryResponse:
    repository = await asyncio.to_thread(service.update, repository_id, data)
    return RepositoryResponse.model_validate(repository)


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repository_id: UUID,
    service: RepositoryService = Depends(get_repository_service),
) -> Response:
    await asyncio.to_thread(service.delete, repository_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{repository_id}/ingest", response_model=IngestionResponse)
async def ingest_repository(
    repository_id: UUID,
    upload: UploadFile = File(...),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> IngestionResponse:
    if not upload.filename or not upload.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP uploads are supported")
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix="devlens-upload-", suffix=".zip", delete=False) as target:
            temporary_path = target.name
            size = 0
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_archive_size_bytes:
                    raise HTTPException(
                        status_code=413, detail="The archive exceeds the configured upload limit"
                    )
                target.write(chunk)
        repository = await asyncio.to_thread(session.get, Repository, repository_id)
        if repository is None:
            raise HTTPException(status_code=404, detail="Repository not found")
        files = await asyncio.to_thread(
            IngestionService(session, settings).ingest_zip,
            repository,
            Path(temporary_path),
        )
        return IngestionResponse(
            repository_id=repository_id,
            file_count=len(files),
            files=[file.path for file in files],
        )
    finally:
        await upload.close()
        if temporary_path:
            os.unlink(temporary_path)
