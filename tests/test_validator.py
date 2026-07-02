import pytest

from keycloak_mcp.openapi.models import Operation, Param, RequestBodySchema
from keycloak_mcp.validation.validator import (
    InputValidationError,
    build_input_schema,
    validate_input,
)


def make_operation() -> Operation:
    return Operation(
        operation_id="createUser",
        method="post",
        path="/admin/realms/{realm}/users",
        params=[
            Param(
                name="realm", location="path", required=True, schema={"type": "string"}
            )
        ],
        request_body=RequestBodySchema(
            required=True,
            content_type="application/json",
            schema={"type": "object", "properties": {"username": {"type": "string"}}},
        ),
    )


def test_valid_input_passes():
    validate_input(make_operation(), {"realm": "main", "body": {"username": "alice"}})


def test_missing_required_realm_rejected():
    with pytest.raises(InputValidationError):
        validate_input(make_operation(), {"body": {"username": "alice"}})


def test_missing_required_body_rejected():
    with pytest.raises(InputValidationError):
        validate_input(make_operation(), {"realm": "main"})


def test_param_description_merged_into_schema():
    operation = Operation(
        operation_id="getRealm",
        method="get",
        path="/admin/realms/{realm}",
        params=[
            Param(
                name="realm",
                location="path",
                required=True,
                schema={"type": "string"},
                description="Realm name.",
            )
        ],
    )
    schema = build_input_schema(operation)
    assert schema["properties"]["realm"]["description"] == "Realm name."


def test_existing_schema_description_not_overwritten():
    operation = Operation(
        operation_id="getRealm",
        method="get",
        path="/admin/realms/{realm}",
        params=[
            Param(
                name="realm",
                location="path",
                required=True,
                schema={"type": "string", "description": "From $ref schema."},
                description="Realm name.",
            )
        ],
    )
    schema = build_input_schema(operation)
    assert schema["properties"]["realm"]["description"] == "From $ref schema."
