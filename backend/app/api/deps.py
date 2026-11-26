"""Authentication and authorization dependencies.

401 = the session is not valid (the frontend logs the user out).
403 = valid session, but the role is not allowed.
"""

from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.core.security import TokenError, decode_access_token
from app.db.models import User
from app.db.session import get_session

_bearer = HTTPBearer(auto_error=False)


def _unauthorized() -> ApiError:
    return ApiError(
        401,
        "unauthorized",
        "Sesión inválida o expirada.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None:
        raise _unauthorized()
    try:
        claims = decode_access_token(credentials.credentials, settings)
    except TokenError:
        raise _unauthorized() from None
    user = session.get(User, claims.user_id)
    if user is None:
        raise _unauthorized()
    return user


def require_role(*roles: str) -> Callable[[User], User]:
    """Dependency factory. The role is read from the database, never trusted from the token."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ApiError(403, "forbidden", "No tienes permiso para esta acción.")
        return user

    return dependency
