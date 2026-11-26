import uuid

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def new_id() -> str:
    """Opaque string id; the contract types every id as a string."""
    return uuid.uuid4().hex
