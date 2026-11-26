from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.core.passwords import hash_password, verify_password
from app.core.security import create_access_token
from app.db.models import User as UserRow
from app.db.session import get_session
from app.schemas import ErrorResponse, LoginRequest, LoginResponse, User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Verified against when the email is unknown, so both failures cost the same time.
_DUMMY_HASH = hash_password("not-a-real-password")


def _invalid_credentials() -> ApiError:
    return ApiError(401, "invalid_credentials", "Correo o contraseña incorrectos.")


@router.post(
    "/login",
    operation_id="login",
    summary="Iniciar sesión",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def login(
    body: LoginRequest,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    row = session.scalar(select(UserRow).where(func.lower(UserRow.email) == body.email.lower()))
    password_ok = verify_password(body.password, row.password_hash if row else _DUMMY_HASH)
    # `role` is demo-only: it can confirm the account's role, never grant another one.
    role_ok = row is not None and (body.role is None or body.role == row.role)
    if row is None or not password_ok or not role_ok:
        raise _invalid_credentials()

    token, expires_in = create_access_token(row.id, row.role, settings)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=User(id=row.id, name=row.name, email=row.email, role=row.role),
    )
