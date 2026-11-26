from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class Role(StrEnum):
    student = "student"
    teacher = "teacher"


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
