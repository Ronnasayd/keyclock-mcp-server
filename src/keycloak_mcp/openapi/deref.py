"""Inline `$ref` pointers against `components.schemas` (fixes PointerToNowhere)."""

JsonDict = dict[str, "JsonValue"]
JsonValue = JsonDict | list["JsonValue"] | str | int | float | bool | None

_REF_PREFIX = "#/components/schemas/"


def _lookup_component(root: JsonDict, name: str) -> JsonValue:
    components = root.get("components")
    if not isinstance(components, dict):
        return None
    schemas = components.get("schemas")
    if not isinstance(schemas, dict):
        return None
    return schemas.get(name)


def resolve_refs(
    schema: JsonValue, root: JsonDict, seen: frozenset[str] = frozenset()
) -> JsonValue:
    """Recursively inline `$ref` pointers so schemas are self-contained."""
    if isinstance(schema, list):
        return [resolve_refs(item, root, seen) for item in schema]

    if not isinstance(schema, dict):
        return schema

    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith(_REF_PREFIX):
        if ref in seen:
            return True
        target = _lookup_component(root, ref[len(_REF_PREFIX) :])
        if target is None:
            return schema
        resolved = resolve_refs(target, root, seen | {ref})
        siblings: JsonDict = {
            key: value for key, value in schema.items() if key != "$ref"
        }
        merged_siblings = {
            key: resolve_refs(value, root, seen) for key, value in siblings.items()
        }
        if merged_siblings and isinstance(resolved, dict):
            return {**merged_siblings, **resolved}
        return resolved

    return {key: resolve_refs(value, root, seen) for key, value in schema.items()}
