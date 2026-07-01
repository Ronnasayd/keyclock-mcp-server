import pytest

from keycloak_mcp.openapi.models import Operation, Param, RequestBodySchema
from keycloak_mcp.validation.validator import InputValidationError, validate_input


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
