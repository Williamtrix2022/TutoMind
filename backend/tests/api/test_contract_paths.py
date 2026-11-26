"""Every operation the app exposes must match docs/openapi.json (the contract is authoritative).

Operations not implemented yet are skipped (with a reason) so the pending list stays visible.
"""

import pytest

from app.main import create_app
from tests.contract import load_contract

CONTRACT = load_contract()
GENERATED = create_app().openapi()
METHODS = {"get", "post", "put", "patch", "delete"}
OPERATIONS = [
    (path, method)
    for path, item in CONTRACT["paths"].items()
    for method in item
    if method in METHODS
]


def schema_name(node: dict) -> str | None:
    ref = (node.get("schema") or {}).get("$ref")
    return ref.rsplit("/", 1)[-1] if ref else None


def request_schema(operation: dict) -> str | None:
    content = operation.get("requestBody", {}).get("content", {})
    return schema_name(next(iter(content.values()), {}))


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
    assert request_schema(actual) == request_schema(expected)
    assert response_schemas(actual, GENERATED) == response_schemas(expected, CONTRACT)
