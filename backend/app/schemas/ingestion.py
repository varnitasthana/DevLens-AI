from pydantic import BaseModel, ConfigDict
from uuid import UUID


class IngestionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_id: UUID
    file_count: int
    files: list[str]
