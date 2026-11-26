from datetime import UTC, datetime, timedelta

import jwt
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import TokenError, create_access_token, decode_access_token
from tests.conftest import TEST_SECRET


def test_round_trip(settings):
    token, expires_in = create_access_token("u1", "teacher", settings)

    claims = decode_access_token(token, settings)

    assert expires_in == 3600
    assert claims.user_id == "u1" and claims.role == "teacher"


def test_expired_token_raises(settings):
    token, _ = create_access_token(
        "u1", "student", settings, now=datetime.now(UTC) - timedelta(days=1)
    )

    with pytest.raises(TokenError):
        decode_access_token(token, settings)


def test_token_without_subject_raises(settings):
    token = jwt.encode(
        {"exp": datetime.now(UTC) + timedelta(hours=1)}, TEST_SECRET, algorithm="HS256"
    )

    with pytest.raises(TokenError):
        decode_access_token(token, settings)


def test_default_secret_is_rejected_outside_development():
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(_env_file=None, environment="production")


def test_default_secret_is_fine_in_development():
    assert Settings(_env_file=None, environment="development").jwt_secret


def test_short_secret_is_rejected_in_production():
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(_env_file=None, environment="production", jwt_secret="short")
