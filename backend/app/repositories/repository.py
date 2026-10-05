from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.repository import Repository


class RepositoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        name: str,
        source_url: str,
        default_branch: str,
        description: str | None,
    ) -> Repository:
        repository = Repository(
            name=name,
            source_url=source_url,
            default_branch=default_branch,
            description=description,
        )
        self.session.add(repository)
        self.session.flush()
        self.session.refresh(repository)
        return repository

    def list(self) -> list[Repository]:
        result = self.session.scalars(
            select(Repository).order_by(Repository.created_at.desc())
        )
        return list(result.all())

    def get(self, repository_id: UUID) -> Repository | None:
        return self.session.get(Repository, repository_id)

    def delete(self, repository: Repository) -> None:
        self.session.delete(repository)
