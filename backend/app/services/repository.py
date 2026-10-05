from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.repositories.repository import RepositoryRepository
from app.schemas.repository import RepositoryCreate


class RepositoryService:
    def __init__(self, session: Session) -> None:
        self.repository = RepositoryRepository(session)
        self.session = session

    def create(self, data: RepositoryCreate) -> Repository:
        try:
            repository = self.repository.create(
                name=data.name,
                source_url=str(data.source_url),
                default_branch=data.default_branch,
                description=data.description,
            )
            self.session.commit()
            return repository
        except IntegrityError as exc:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A repository with this source URL already exists",
            ) from exc

    def list(self) -> list[Repository]:
        return self.repository.list()

    def get(self, repository_id: UUID) -> Repository:
        repository = self.repository.get(repository_id)
        if repository is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found",
            )
        return repository

    def delete(self, repository_id: UUID) -> None:
        repository = self.get(repository_id)
        self.repository.delete(repository)
        self.session.commit()
