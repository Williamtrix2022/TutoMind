"""#13: every schema in docs/openapi.json has a Pydantic model that matches it exactly."""

import pytest
from pydantic import TypeAdapter

from app.schemas import CONTRACT_TYPES
from tests.contract import canon, compare, load_contract

CONTRACT_SCHEMAS = load_contract()["components"]["schemas"]


def test_one_model_per_contract_schema():
    assert set(CONTRACT_TYPES) == set(CONTRACT_SCHEMAS)


@pytest.mark.parametrize("name", sorted(CONTRACT_SCHEMAS))
def test_model_matches_contract(name):
    model_schema = TypeAdapter(CONTRACT_TYPES[name]).json_schema()
    model = canon(model_schema, model_schema.get("$defs", {}))
    contract = canon(CONTRACT_SCHEMAS[name], CONTRACT_SCHEMAS)

    assert compare(contract, model, name) == []


def test_comparator_detects_a_drifted_model():
    """Guard the guard: a wrong required set or bound must be reported."""
    contract = canon(CONTRACT_SCHEMAS["FrustrationSignal"], CONTRACT_SCHEMAS)
    drifted = {
        "type": ["object"],
        "required": ["detected"],
        "properties": {
            "detected": {"type": ["boolean"]},
            "score": {"type": ["number"], "minimum": 0, "maximum": 5},
            "adapted_tone": {"type": ["boolean"]},
        },
    }

    errors = compare(contract, drifted, "FrustrationSignal")

    assert any("required" in e for e in errors)
    assert any("maximum" in e for e in errors)
