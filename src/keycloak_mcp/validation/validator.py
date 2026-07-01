"""jsonschema validation of tool input against an operation's schema (FR-6)."""

from typing import Any

import jsonschema

from keycloak_mcp.openapi.models import Operation


class InputValidationError(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def build_input_schema(operation: Operation) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param in operation.params:
        properties[param.name] = param.schema
        if param.required:
            required.append(param.name)

    if operation.request_body is not None:
        properties["body"] = operation.request_body.schema
        if operation.request_body.required:
            required.append("body")

    return {"type": "object", "properties": properties, "required": required}


def validate_input(operation: Operation, args: dict[str, Any]) -> None:
    schema = build_input_schema(operation)
    validator = jsonschema.Draft7Validator(schema)
    errors = [error.message for error in validator.iter_errors(args)]
    if errors:
        raise InputValidationError(errors)
