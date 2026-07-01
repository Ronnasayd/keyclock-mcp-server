"""FastMCP app bootstrap: load settings, parse spec once, register generated tools."""

import json
from pathlib import Path

import httpx
from fastmcp import FastMCP

from keycloak_mcp.auth.client_credentials import ClientCredentialsAuthManager
from keycloak_mcp.auth.manager import AuthManager
from keycloak_mcp.auth.password import PasswordAuthManager
from keycloak_mcp.config import Settings
from keycloak_mcp.http.client import HttpClient
from keycloak_mcp.openapi.models import Operation
from keycloak_mcp.openapi.parser import parse_spec
from keycloak_mcp.tools.generator import GenerationReport, generate_tools

VENDORED_SPEC_PATH = (
    Path(__file__).resolve().parent.parent.parent / "spec" / "keycloak-openapi.json"
)


def load_operations(spec_path: Path = VENDORED_SPEC_PATH) -> list[Operation]:
    spec = json.loads(spec_path.read_text())
    return parse_spec(spec)


def build_auth_manager(
    settings: Settings, http_client: httpx.AsyncClient
) -> AuthManager:
    if settings.auth_method == "client_credentials":
        return ClientCredentialsAuthManager(settings, http_client)
    return PasswordAuthManager(settings, http_client)


def build_server(
    settings: Settings, operations: list[Operation] | None = None
) -> tuple[FastMCP, GenerationReport]:
    operations = operations if operations is not None else load_operations()

    auth_http_client = httpx.AsyncClient(base_url=settings.keycloak_base_url)
    admin_http_client = HttpClient(
        httpx.AsyncClient(base_url=settings.keycloak_base_url)
    )
    auth_manager = build_auth_manager(settings, auth_http_client)

    tools, report = generate_tools(
        operations,
        auth_manager,
        admin_http_client,
        default_realm=settings.default_realm,
    )

    mcp = FastMCP(name="keycloak-mcp-server", tools=tools)
    return mcp, report


def main() -> None:
    settings = Settings()
    mcp, _ = build_server(settings)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
