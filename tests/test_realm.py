import pytest

from keycloak_mcp.openapi.models import Operation, Param
from keycloak_mcp.openapi.realm import resolve_realm
from keycloak_mcp.validation.validator import InputValidationError, validate_input


def make_operation(required: bool) -> Operation:
    return Operation(
        operation_id="op",
        method="get",
        path="/admin/realms/{realm}/users",
        params=[
            Param(
                name="realm",
                location="path",
                required=required,
                schema={"type": "string"},
            )
        ],
    )


def test_required_realm_missing_rejected_by_validator():
    operation = make_operation(required=True)
    with pytest.raises(InputValidationError):
        validate_input(operation, {})


def test_optional_realm_falls_back_to_default():
    operation = make_operation(required=False)
    resolved = resolve_realm(operation, {}, default_realm="main")
    assert resolved == {"realm": "main"}


def test_optional_realm_explicit_value_not_overridden():
    operation = make_operation(required=False)
    resolved = resolve_realm(operation, {"realm": "other"}, default_realm="main")
    assert resolved == {"realm": "other"}


def test_no_default_realm_leaves_args_unchanged():
    operation = make_operation(required=False)
    resolved = resolve_realm(operation, {}, default_realm=None)
    assert resolved == {}
