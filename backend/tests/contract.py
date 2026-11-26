"""Helpers to compare Pydantic models against `docs/openapi.json`, the single source of truth."""

import json
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "docs" / "openapi.json"

_IGNORED = {
    "title",
    "description",
    "examples",
    "example",
    "$defs",
    "discriminator",
    "contentMediaType",
}
# Keywords the contract states explicitly: the model must reproduce them exactly.
_CONSTRAINTS = (
    "minimum",
    "maximum",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
    "format",
    "const",
    "additionalProperties",
    "default",
)


def load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def canon(node: dict[str, Any], defs: dict[str, Any]) -> dict[str, Any]:
    """Inline every $ref and normalise the JSON Schema so both sides are comparable."""
    if "$ref" in node:
        resolved = defs[node["$ref"].rsplit("/", 1)[-1]]
        siblings = {k: v for k, v in node.items() if k != "$ref"}
        return canon({**resolved, **siblings}, defs)

    node = {k: v for k, v in node.items() if k not in _IGNORED}

    if "anyOf" in node:
        branches = [canon(b, defs) for b in node.pop("anyOf")]
        nullable = any(b.get("type") == ["null"] for b in branches)
        others = [b for b in branches if b.get("type") != ["null"]]
        if all(set(b) == {"type"} for b in others):  # e.g. number | string
            types = {t for b in others for t in b["type"]} | ({"null"} if nullable else set())
            return {**node, "type": sorted(types)}
        assert len(others) == 1, f"unsupported anyOf: {branches}"
        merged = others[0]
        if nullable:
            merged = {**merged, "type": sorted({*merged.get("type", []), "null"})}
        return {**node, **merged}

    if "const" in node:
        node.pop("type", None)
    elif "type" in node:
        node["type"] = sorted(node["type"] if isinstance(node["type"], list) else [node["type"]])

    if "properties" in node:
        node["properties"] = {k: canon(v, defs) for k, v in node["properties"].items()}
    if "items" in node:
        node["items"] = canon(node["items"], defs)
    if "oneOf" in node:
        node["oneOf"] = [canon(b, defs) for b in node["oneOf"]]
    return node


def _tag(variant: dict[str, Any]) -> str:
    return variant["properties"]["type"]["const"]


def compare(
    contract: dict[str, Any], model: dict[str, Any], path: str, optional: bool = False
) -> list[str]:
    """Return the list of differences. The contract is authoritative."""
    errors: list[str] = []

    if "type" in contract:
        model_types = list(model.get("type", []))
        # An optional field whose Python default is None is simply "may be omitted":
        # the contract does not call it nullable, so drop the implicit null.
        if optional and "null" in model_types and "null" not in contract["type"]:
            model_types.remove("null")
        if model_types != contract["type"]:
            errors.append(f"{path}: type {model_types} != contract {contract['type']}")

    if "enum" in contract and set(model.get("enum", [])) != set(contract["enum"]):
        errors.append(f"{path}: enum {model.get('enum')} != contract {contract['enum']}")

    for key in _CONSTRAINTS:
        if key in contract and model.get(key) != contract[key]:
            errors.append(f"{path}: {key}={model.get(key)!r} != contract {contract[key]!r}")

    if "properties" in contract:
        required_c = set(contract.get("required", []))
        required_m = set(model.get("required", []))
        if required_c != required_m:
            errors.append(f"{path}: required {sorted(required_m)} != contract {sorted(required_c)}")
        names_c, names_m = set(contract["properties"]), set(model.get("properties", {}))
        if names_c != names_m:
            errors.append(f"{path}: properties {sorted(names_m)} != contract {sorted(names_c)}")
        for name in names_c & names_m:
            errors += compare(
                contract["properties"][name],
                model["properties"][name],
                f"{path}.{name}",
                optional=name not in required_c,
            )

    if "items" in contract:
        errors += compare(contract["items"], model.get("items", {}), f"{path}[]")

    if "oneOf" in contract:
        by_tag_c = {_tag(b): b for b in contract["oneOf"]}
        by_tag_m = {_tag(b): b for b in model.get("oneOf", [])}
        if set(by_tag_c) != set(by_tag_m):
            errors.append(f"{path}: variants {sorted(by_tag_m)} != contract {sorted(by_tag_c)}")
        for tag in set(by_tag_c) & set(by_tag_m):
            errors += compare(by_tag_c[tag], by_tag_m[tag], f"{path}<{tag}>")

    return errors
