from keycloak_mcp.openapi.deref import resolve_refs


def test_simple_ref_is_inlined():
    root = {"components": {"schemas": {"Foo": {"type": "string"}}}}
    schema = {"$ref": "#/components/schemas/Foo"}
    assert resolve_refs(schema, root) == {"type": "string"}


def test_nested_ref_is_inlined():
    root = {
        "components": {
            "schemas": {
                "Foo": {
                    "type": "object",
                    "properties": {"bar": {"$ref": "#/components/schemas/Bar"}},
                },
                "Bar": {"type": "integer"},
            }
        }
    }
    schema = {"$ref": "#/components/schemas/Foo"}
    assert resolve_refs(schema, root) == {
        "type": "object",
        "properties": {"bar": {"type": "integer"}},
    }


def test_self_referential_cycle_does_not_recurse_infinitely():
    root = {
        "components": {
            "schemas": {
                "Foo": {
                    "type": "object",
                    "properties": {"self": {"$ref": "#/components/schemas/Foo"}},
                }
            }
        }
    }
    schema = {"$ref": "#/components/schemas/Foo"}
    result = resolve_refs(schema, root)
    assert result == {"type": "object", "properties": {"self": True}}


def test_missing_component_left_unresolved():
    root = {"components": {"schemas": {}}}
    schema = {"$ref": "#/components/schemas/Missing"}
    assert resolve_refs(schema, root) == schema
