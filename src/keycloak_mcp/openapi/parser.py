"""Parse a vendored OpenAPI spec into a list of Operation (FR-1)."""

import logging
import re
from typing import Any

from keycloak_mcp.openapi.deref import resolve_refs
from keycloak_mcp.openapi.models import Operation, Param, RequestBodySchema

HTTP_METHODS = {"get", "post", "put", "delete", "patch"}
_SLUG_NON_ALNUM = re.compile(r"[^a-zA-Z0-9]+")

logger = logging.getLogger(__name__)


def _resolve_schema(raw_schema: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    resolved = resolve_refs(raw_schema, spec)
    return resolved if isinstance(resolved, dict) else raw_schema


def parse_spec(spec: dict[str, Any]) -> list[Operation]:
    operations: list[Operation] = []
    for path, path_item in spec.get("paths", {}).items():
        for method, raw_operation in path_item.items():
            if method not in HTTP_METHODS:
                continue
            operation = _parse_operation(path, method, raw_operation, spec)
            if operation is not None:
                operations.append(operation)
    return operations


def _parse_operation(
    path: str, method: str, raw_operation: Any, spec: dict[str, Any]
) -> Operation | None:
    try:
        return Operation(
            operation_id=_resolve_operation_id(path, method, raw_operation),
            operation_id_synthesized="operationId" not in raw_operation
            or not raw_operation["operationId"],
            method=method,
            path=path,
            params=_parse_params(raw_operation.get("parameters", []), spec),
            request_body=_parse_request_body(raw_operation.get("requestBody"), spec),
            response_schema=raw_operation.get("responses", {}),
        )
    except (AttributeError, TypeError, KeyError) as exc:
        logger.warning("skip malformed operation %s %s: %s", method, path, exc)
        return None


def _resolve_operation_id(path: str, method: str, raw_operation: dict[str, Any]) -> str:
    operation_id = raw_operation.get("operationId")
    if operation_id:
        return str(operation_id)
    slug = _SLUG_NON_ALNUM.sub("_", path).strip("_")
    synthesized = f"{method}_{slug}"
    logger.warning("synthesized operationId %r for %s %s", synthesized, method, path)
    return synthesized


def _parse_params(raw_params: Any, spec: dict[str, Any]) -> list[Param]:
    return [
        Param(
            name=raw_param["name"],
            location=raw_param["in"],
            required=raw_param.get("required", False),
            schema=_resolve_schema(raw_param.get("schema", {}), spec),
        )
        for raw_param in raw_params
    ]


def _parse_request_body(
    raw_body: dict[str, Any] | None, spec: dict[str, Any]
) -> RequestBodySchema | None:
    if not raw_body:
        return None
    content = raw_body.get("content", {})
    content_type, media = next(iter(content.items()))
    return RequestBodySchema(
        required=raw_body.get("required", False),
        content_type=content_type,
        schema=_resolve_schema(media.get("schema", {}), spec),
    )
