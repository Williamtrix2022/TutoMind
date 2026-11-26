from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import Role


class User(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, json_schema_extra={"format": "password"})
    # Demo mode only; in production the role comes from Moodle.
    role: Role | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    expires_in: int
    user: User
