def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_is_not_part_of_the_public_contract(client):
    schema = client.get("/openapi.json").json()

    assert "/health" not in schema["paths"]
