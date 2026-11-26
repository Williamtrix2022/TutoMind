ORIGIN = "http://localhost:3000"


def test_preflight_allows_the_frontend_origin(client):
    response = client.options(
        "/health",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_simple_request_carries_cors_header(client):
    response = client.get("/health", headers={"Origin": ORIGIN})

    assert response.headers["access-control-allow-origin"] == ORIGIN


def test_unknown_origin_gets_no_cors_header(client):
    response = client.get("/health", headers={"Origin": "http://evil.example"})

    assert "access-control-allow-origin" not in response.headers
