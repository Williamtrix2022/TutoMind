import jwt
import pytest
from pydantic import TypeAdapter

from app.schemas import LoginResponse
from tests.conftest import TEST_SECRET

LOGIN = "/api/v1/auth/login"
PASSWORD = "demo12345"


def login(api, email="u1@tutomind.demo", password=PASSWORD, **extra):
    return api.post(LOGIN, json={"email": email, "password": password, **extra})


def test_valid_credentials_return_a_contract_valid_session(api, make_user):
    make_user("t1", role="teacher", email="docente@tutomind.demo")

    response = login(api, email="docente@tutomind.demo")

    assert response.status_code == 200
    body = response.json()
    TypeAdapter(LoginResponse).validate_python(body)  # matches the contract model
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 3600
    assert body["user"] == {
        "id": "t1",
        "name": "Usuario t1",
        "email": "docente@tutomind.demo",
        "role": "teacher",
    }


def test_response_never_leaks_the_password_hash(api, make_user):
    make_user()

    assert "password" not in login(api).text.lower()


def test_token_carries_subject_role_and_expiry(api, make_user):
    make_user("s1", role="student")

    body = login(api, email="s1@tutomind.demo").json()

    claims = jwt.decode(body["access_token"], TEST_SECRET, algorithms=["HS256"])
    assert claims["sub"] == "s1" and claims["role"] == "student"
    assert claims["exp"] - claims["iat"] == 3600


def test_email_is_case_insensitive(api, make_user):
    make_user(email="ana@tutomind.demo")

    assert login(api, email="ANA@Tutomind.DEMO").status_code == 200


def test_wrong_password_is_401_invalid_credentials(api, make_user):
    make_user()

    response = login(api, password="incorrecta")

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"
    assert response.json()["message"] == "Correo o contraseña incorrectos."


def test_unknown_email_is_indistinguishable_from_wrong_password(api, make_user):
    make_user()

    wrong_password = login(api, password="incorrecta")
    unknown_user = login(api, email="nadie@tutomind.demo")

    assert unknown_user.status_code == wrong_password.status_code == 401
    assert unknown_user.json() == wrong_password.json()


def test_unknown_email_still_pays_the_hashing_cost(api, monkeypatch):
    """Otherwise response time would reveal which emails are registered."""
    calls = []
    import app.api.auth as auth_module

    real = auth_module.verify_password
    monkeypatch.setattr(auth_module, "verify_password", lambda *a: calls.append(a) or real(*a))

    login(api, email="nadie@tutomind.demo")

    assert len(calls) == 1


def test_requested_role_must_match_the_account(api, make_user):
    """`role` is demo-only: asking for another role than the account has must not grant it."""
    make_user(role="student")

    response = login(api, role="teacher")

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


def test_matching_requested_role_is_accepted(api, make_user):
    make_user(role="teacher")

    assert login(api, role="teacher").status_code == 200


@pytest.mark.parametrize("password", ["", "1234567"])
def test_short_password_is_422_and_is_not_echoed(api, password):
    response = login(api, password=password)

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_request"
    if password:
        assert password not in response.text


def test_invalid_email_is_422(api):
    assert login(api, email="not-an-email").status_code == 422


def test_missing_body_is_422(api):
    assert api.post(LOGIN).status_code == 422
