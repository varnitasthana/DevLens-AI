from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedModel

if TYPE_CHECKING:
    from app.models.analysis import Analysis
    from app.models.repository_file import RepositoryFile
    from app.models.user import User


class Repository(TimestampedModel):
    __tablename__ = "repositories"
    __table_args__ = (
        UniqueConstraint("source_url", name="uq_repositories_source_url"),
        Index("ix_repositories_name", "name"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    default_branch: Mapped[str] = mapped_column(
        String(255), nullable=False, default="main", server_default="main"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    owner: Mapped["User | None"] = relationship(back_populates="repositories")
    files: Mapped[list["RepositoryFile"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
            return f"Repository(id={self.id!r}, name={self.name!r})"
