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
        owner_id,
    ) -> Repository:
        repository = Repository(
            name=name,
            source_url=source_url,
            default_branch=default_branch,
            description=description,
            owner_id=owner_id,
        )
        self.session.add(repository)
        self.session.flush()
        self.session.refresh(repository)
        return repository

    def list(self, owner_id) -> list[Repository]:
        result = self.session.scalars(
            select(Repository).where(Repository.owner_id == owner_id).order_by(Repository.created_at.desc())
        )
        return list(result.all())

    def get(self, repository_id: UUID, owner_id) -> Repository | None:
        return self.session.scalar(select(Repository).where(Repository.id == repository_id, Repository.owner_id == owner_id))

    def delete(self, repository: Repository) -> None:
        self.session.delete(repository)

    def update(self, repository: Repository, values: dict[str, object]) -> Repository:
        for field, value in values.items():
            setattr(repository, field, value)
        self.session.flush()
        self.session.refresh(repository)
        return repository
