"""Every error must follow the contract's ErrorResponse: {code, message, details?}."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.errors import ApiError
from app.main import create_app


class Item(BaseModel):
    name: str
    quantity: int


def build_client():
    from fastapi.testclient import TestClient

    app = create_app()
    router = APIRouter()

    @router.post("/_t/validate")
    def validate(item: Item) -> Item:
        return item

    @router.get("/_t/api-error")
    def api_error():
        raise ApiError(409, "conflict", "Ya existe.", details={"field": "email"})

    @router.get("/_t/http-error")
    def http_error():
        raise HTTPException(status_code=403, detail="nope")

    @router.get("/_t/boom")
    def boom():
        raise RuntimeError("secret internal detail")

    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def assert_error_shape(body: dict) -> None:
    assert set(body) <= {"code", "message", "details"}
    assert isinstance(body["code"], str) and body["code"]
    assert isinstance(body["message"], str) and body["message"]


def test_unknown_route_is_a_404_error_response(client):
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert_error_shape(body)
    assert body["code"] == "not_found"


def test_validation_error_is_422_with_details():
    response = build_client().post("/_t/validate", json={"name": "x", "quantity": "abc"})

    assert response.status_code == 422
    body = response.json()
    assert_error_shape(body)
    assert body["code"] == "invalid_request"
    assert body["details"]["errors"], "must list which fields failed"


def test_api_error_keeps_status_code_and_details():
    response = build_client().get("/_t/api-error")

    assert response.status_code == 409
    assert response.json() == {
        "code": "conflict",
        "message": "Ya existe.",
        "details": {"field": "email"},
    }


def test_http_exception_is_mapped_to_error_response():
    response = build_client().get("/_t/http-error")

    assert response.status_code == 403
    body = response.json()
    assert_error_shape(body)
    assert body["code"] == "forbidden"


def test_unhandled_exception_is_500_and_leaks_nothing():
    response = build_client().get("/_t/boom")

    assert response.status_code == 500
    body = response.json()
    assert_error_shape(body)
    assert body["code"] == "internal_error"
    assert "secret internal detail" not in response.text
