from typing import TYPE_CHECKING
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import TimestampedModel
if TYPE_CHECKING:
    from app.models.repository import Repository

class User(TimestampedModel):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    repositories: Mapped[list["Repository"]] = relationship(back_populates="owner")
