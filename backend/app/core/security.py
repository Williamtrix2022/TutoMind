"""Access tokens: signed JWT (HS256) with `sub`, `role`, `iat` and `exp`."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import Settings

ALGORITHM = "HS256"


class TokenError(Exception):
    """The token is missing a claim, expired, forged or otherwise unusable."""


@dataclass(frozen=True)
class TokenClaims:
    user_id: str
    role: str


def create_access_token(
    user_id: str, role: str, settings: Settings, now: datetime | None = None
) -> tuple[str, int]:
    """Return `(token, expires_in_seconds)`. `now` is injectable for tests."""
    issued_at = now or datetime.now(UTC)
    lifetime = settings.access_token_expires_seconds
    payload = {
        "sub": user_id,
        "role": role,
        "iat": issued_at,
        "exp": issued_at + timedelta(seconds=lifetime),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM), lifetime


def decode_access_token(token: str, settings: Settings) -> TokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[ALGORITHM],  # never trust the header's alg (blocks "none")
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as error:
        raise TokenError(str(error)) from error
    return TokenClaims(user_id=payload["sub"], role=str(payload.get("role", "")))
