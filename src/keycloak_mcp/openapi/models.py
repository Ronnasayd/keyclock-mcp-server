"""Parsed OpenAPI operation representations (Design §1)."""

from dataclasses import dataclass, field
from typing import Any, Literal

ParamLocation = Literal["path", "query", "header"]


@dataclass
class Param:
    """A path, query, or header parameter for an operation."""

    name: str
    location: ParamLocation
    required: bool
    schema: dict[str, Any] = field(default_factory=dict)
    description: str | None = None


@dataclass
class RequestBodySchema:
    """The request body schema for an operation."""

    required: bool
    content_type: str
    schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class Operation:
    """A single parsed OpenAPI operation, ready to become an MCP tool."""

    operation_id: str
    method: str
    path: str
    params: list[Param] = field(default_factory=list)
    request_body: RequestBodySchema | None = None
    response_schema: dict[str, Any] = field(default_factory=dict)
    operation_id_synthesized: bool = False
    summary: str | None = None
    description: str | None = None
