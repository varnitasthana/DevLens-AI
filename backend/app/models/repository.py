from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TimestampedModel


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

    def __repr__(self) -> str:
        return f"Repository(id={self.id!r}, name={self.name!r})"
