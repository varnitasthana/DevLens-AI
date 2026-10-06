from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("A valid email address is required")
        return value.lower()
class LoginRequest(RegisterRequest):
    pass
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    is_active: bool
    created_at: datetime
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
