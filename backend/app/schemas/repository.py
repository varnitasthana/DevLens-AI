from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class RepositoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    source_url: AnyHttpUrl
    default_branch: str = Field(default="main", min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)


class RepositoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    source_url: AnyHttpUrl | None = None
    default_branch: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)


class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source_url: AnyHttpUrl
    default_branch: str
    description: str | None
    created_at: datetime
    updated_at: datetime
