"""Build one FastMCP tool per Operation via metaprogramming (FR-2, Design §3)."""

from dataclasses import dataclass, field
import json
import logging
from typing import Any, ClassVar

from fastmcp.tools import Tool, ToolResult
from mcp.types import TextContent
from pydantic import ConfigDict

from keycloak_mcp.auth.manager import AuthManager
from keycloak_mcp.errors import JsonValue, KeycloakApiError
from keycloak_mcp.http.client import HttpClient
from keycloak_mcp.openapi.models import Operation
from keycloak_mcp.openapi.realm import resolve_realm
from keycloak_mcp.validation.validator import build_input_schema, validate_input

logger = logging.getLogger(__name__)


def _to_text_content(value: JsonValue) -> TextContent:
    return TextContent(type="text", text=json.dumps(value))


@dataclass
class GenerationReport:
    """Tally of tool generation outcomes: succeeded, failed, or blocked."""

    succeeded: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)


class GeneratedTool(Tool):
    """An MCP tool backed by a single OpenAPI operation."""

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    operation: Operation
    auth_manager: AuthManager
    http_client: HttpClient
    default_realm: str | None

    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        """Resolve realm, validate input, call Keycloak, and wrap the result."""
        args = resolve_realm(self.operation, arguments, self.default_realm)
        validate_input(self.operation, args)

        path_params = {
            p.name: args[p.name]
            for p in self.operation.params
            if p.location == "path" and p.name in args
        }
        query_params = {
            p.name: args[p.name]
            for p in self.operation.params
            if p.location == "query" and p.name in args
        }
        body = args.get("body")

        token = await self.auth_manager.get_token()
        try:
            result = await self.http_client.call(
                self.operation,
                token=token,
                path_params=path_params,
                query_params=query_params,
                body=body,
            )
        except KeycloakApiError as error:
            return ToolResult(content=[_to_text_content(error.body)], is_error=True)
        return ToolResult(content=[_to_text_content(result)])


def _build_tool_description(operation: Operation) -> str | None:
    if operation.summary and operation.description:
        return f"{operation.summary}\n\n{operation.description}"
    return operation.description or operation.summary or None


def generate_tools(
    operations: list[Operation],
    auth_manager: AuthManager,
    http_client: HttpClient,
    default_realm: str | None = None,
    read_only: bool = False,
) -> tuple[list[GeneratedTool], GenerationReport]:
    """Build one `GeneratedTool` per operation, skipping malformed/blocked ones."""
    tools: list[GeneratedTool] = []
    report = GenerationReport()

    for operation in operations:
        try:
            if not operation.operation_id:
                raise ValueError("operation_id must not be empty")
            if read_only and operation.method.upper() != "GET":
                report.blocked.append(operation.operation_id)
                continue
            tools.append(
                GeneratedTool(
                    name=operation.operation_id,
                    description=_build_tool_description(operation),
                    parameters=build_input_schema(operation),
                    operation=operation,
                    auth_manager=auth_manager,
                    http_client=http_client,
                    default_realm=default_realm,
                )
            )
            report.succeeded.append(operation.operation_id)
        except Exception:
            logger.exception("skip malformed operation %s", operation.operation_id)
            report.failed.append(operation.operation_id)

    return tools, report
