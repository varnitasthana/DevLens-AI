from typing import TYPE_CHECKING
from uuid import UUID

from datetime import datetime

from sqlalchemy import Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedModel

if TYPE_CHECKING:
    from app.models.repository import Repository
    from app.models.finding import Finding


class Analysis(TimestampedModel):
    __tablename__ = "analyses"
    __table_args__ = (Index("ix_analyses_repository_id", "repository_id"),)

    repository_id: Mapped[UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="QUEUED")
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    files_analyzed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    analyzer_source: Mapped[str] = mapped_column(String(32), nullable=False, default="static")
    repository: Mapped["Repository"] = relationship(back_populates="analyses")
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
