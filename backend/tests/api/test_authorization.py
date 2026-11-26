"""Bearer-token authentication and role authorization (401 vs 403, as the contract states)."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, require_role
from app.core.security import create_access_token
from app.db.models import User
from app.main import create_app


@pytest.fixture
def guarded(api):
    """The real app plus two throwaway routes that exercise the dependencies."""
    router = APIRouter()

    @router.get("/_t/any")
    def any_user(user: User = Depends(get_current_user)):
        return {"id": user.id, "role": user.role}

    @router.get("/_t/teacher")
    def teacher_only(user: User = Depends(require_role("teacher"))):
        return {"id": user.id}

    api.app.include_router(router)
    return api


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def token_for(user_id: str, role: str, settings, **kwargs) -> str:
    return create_access_token(user_id, role, settings, **kwargs)[0]


def test_missing_header_is_401_with_challenge(guarded):
    response = guarded.get("/_t/any")

    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("header", ["Basic abc", "Bearer", "Bearer not-a-jwt", "token abc"])
def test_malformed_credentials_are_401(guarded, header):
    response = guarded.get("/_t/any", headers={"Authorization": header})

    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_valid_token_authenticates(guarded, make_user, settings):
    make_user("s1")

    response = guarded.get("/_t/any", headers=bearer(token_for("s1", "student", settings)))

    assert response.status_code == 200
    assert response.json() == {"id": "s1", "role": "student"}


def test_expired_token_is_401(guarded, make_user, settings):
    make_user("s1")
    long_ago = datetime.now(UTC) - timedelta(hours=5)

    token = token_for("s1", "student", settings, now=long_ago)

    assert guarded.get("/_t/any", headers=bearer(token)).status_code == 401


def test_token_signed_with_another_secret_is_401(guarded, make_user, settings):
    make_user("s1")
    other = settings.model_copy(update={"jwt_secret": "another-secret-" + "y" * 32})

    token = token_for("s1", "student", other)

    assert guarded.get("/_t/any", headers=bearer(token)).status_code == 401


def test_unsigned_token_alg_none_is_401(guarded, make_user):
    make_user("s1")
    claims = {"sub": "s1", "role": "teacher", "exp": datetime.now(UTC) + timedelta(hours=1)}
    token = jwt.encode(claims, key=None, algorithm="none")

    assert guarded.get("/_t/teacher", headers=bearer(token)).status_code == 401


def test_token_of_a_deleted_user_is_401(guarded, settings):
    token = token_for("ghost", "student", settings)

    assert guarded.get("/_t/any", headers=bearer(token)).status_code == 401


def test_student_on_teacher_route_is_403(guarded, make_user, settings):
    make_user("s1", role="student")

    response = guarded.get("/_t/teacher", headers=bearer(token_for("s1", "student", settings)))

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_teacher_on_teacher_route_is_allowed(guarded, make_user, settings):
    make_user("t1", role="teacher")

    response = guarded.get("/_t/teacher", headers=bearer(token_for("t1", "teacher", settings)))

    assert response.status_code == 200


def test_role_comes_from_the_database_not_from_the_token(guarded, make_user, settings):
    """A validly signed token that claims `teacher` must not elevate a student account."""
    make_user("s1", role="student")
    forged_claim = token_for("s1", "teacher", settings)

    assert guarded.get("/_t/teacher", headers=bearer(forged_claim)).status_code == 403


def test_app_factory_still_works_without_overrides():
    assert create_app().title == "TutoMind API"
