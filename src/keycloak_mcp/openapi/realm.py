"""Realm param resolution (FR-5): required/optional per op, DEFAULT_REALM fallback."""

from typing import Any

from keycloak_mcp.openapi.models import Operation

REALM_PARAM_NAME = "realm"


def resolve_realm(
    operation: Operation, args: dict[str, Any], default_realm: str | None
) -> dict[str, Any]:
    """Fill in `default_realm` for the optional, unset realm param of `operation`."""
    realm_param = next(
        (param for param in operation.params if param.name == REALM_PARAM_NAME), None
    )
    if realm_param is None or realm_param.required or REALM_PARAM_NAME in args:
        return args
    if default_realm is None:
        return args
    return {**args, REALM_PARAM_NAME: default_realm}
