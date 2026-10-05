from typing import TYPE_CHECKING

from uuid import UUID

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedModel

if TYPE_CHECKING:
    from app.models.repository import Repository


class RepositoryFile(TimestampedModel):
    __tablename__ = "repository_files"
    __table_args__ = (
        UniqueConstraint("repository_id", "path", name="uq_repository_files_repository_path"),
        Index("ix_repository_files_repository_id", "repository_id"),
    )

    repository_id: Mapped[UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    path: Mapped[str] = mapped_column(String(4096), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_binary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    repository: Mapped["Repository"] = relationship(back_populates="files")
