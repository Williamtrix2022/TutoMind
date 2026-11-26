"""Every operation the app exposes must match docs/openapi.json (the contract is authoritative).

Operations not implemented yet are skipped (with a reason) so the pending list stays visible.
"""

import pytest

from app.main import create_app
from tests.contract import canon, compare, load_contract

CONTRACT = load_contract()
GENERATED = create_app().openapi()
METHODS = {"get", "post", "put", "patch", "delete"}
# Responses the code returns but the contract does not list yet (gaps to fix in a contract PR).
UNDOCUMENTED_OK = {"404", "422"}
OPERATIONS = [
    (path, method)
    for path, item in CONTRACT["paths"].items()
    for method in item
    if method in METHODS
]


def schema_name(node: dict) -> str | None:
    ref = (node.get("schema") or {}).get("$ref")
    return ref.rsplit("/", 1)[-1] if ref else None


def request_body(operation: dict, spec: dict) -> dict | None:
    """Content type + fully resolved schema, so `$ref` and inline bodies compare equal."""
    content = operation.get("requestBody", {}).get("content", {})
    if not content:
        return None
    content_type, media = next(iter(content.items()))
    schemas = spec["components"]["schemas"]
    return {"content_type": content_type, "schema": canon(media["schema"], schemas)}


def response_schemas(operation: dict, contract: dict) -> dict[str, str | None]:
    result = {}
    for status, response in operation["responses"].items():
        if "$ref" in response:
            response = contract["components"]["responses"][response["$ref"].rsplit("/", 1)[-1]]
        content = response.get("content", {})
        result[status] = schema_name(next(iter(content.values()), {}))
    return result


@pytest.mark.parametrize(("path", "method"), OPERATIONS)
def test_operation_matches_the_contract(path, method):
    if method not in GENERATED["paths"].get(path, {}):
        pytest.skip("pendiente de implementar")
    expected = CONTRACT["paths"][path][method]
    actual = GENERATED["paths"][path][method]

    assert actual["operationId"] == expected["operationId"]
    assert actual.get("tags") == expected.get("tags")
    expected_body, actual_body = request_body(expected, CONTRACT), request_body(actual, GENERATED)
    if expected_body is None:
        assert actual_body is None
    else:
        assert actual_body["content_type"] == expected_body["content_type"]
        assert compare(expected_body["schema"], actual_body["schema"], "body") == []

    expected_responses = response_schemas(expected, CONTRACT)
    actual_responses = response_schemas(actual, GENERATED)
    # Only the known gaps may be extra (404 unknown course, 422 validation). Nothing else may differ.
    for status in UNDOCUMENTED_OK:
        if status not in expected_responses:
            actual_responses.pop(status, None)
    assert actual_responses == expected_responses
