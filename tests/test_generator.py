import httpx
import pytest
import respx

from keycloak_mcp.auth.client_credentials import ClientCredentialsAuthManager
from keycloak_mcp.config import Settings
from keycloak_mcp.http.client import HttpClient
from keycloak_mcp.openapi.models import Operation, Param, RequestBodySchema
from keycloak_mcp.tools.generator import generate_tools

BASE_URL = "https://kc.example.com"


def make_settings() -> Settings:
    return Settings(
        keycloak_base_url=BASE_URL,
        auth_method="client_credentials",
        client_id="my-client",
        client_secret="s3cr3t",
    )


def make_operations() -> list[Operation]:
    good_ops = [
        Operation(
            operation_id=f"getThing{i}",
            method="get",
            path=f"/admin/realms/{{realm}}/thing{i}",
            params=[
                Param(
                    name="realm",
                    location="path",
                    required=True,
                    schema={"type": "string"},
                )
            ],
        )
        for i in range(4)
    ]
    with_body = Operation(
        operation_id="createThing",
        method="post",
        path="/admin/realms/{realm}/things",
        params=[
            Param(
                name="realm", location="path", required=True, schema={"type": "string"}
            )
        ],
        request_body=RequestBodySchema(
            required=True, content_type="application/json", schema={"type": "object"}
        ),
    )
    malformed = Operation(operation_id="", method="get", path="/broken")
    return [*good_ops, with_body, malformed]


def test_tool_description_uses_summary_only():
    op = Operation(
        operation_id="getThing", method="get", path="/thing", summary="Get thing"
    )
    http_client = HttpClient(httpx.AsyncClient(base_url=BASE_URL))
    auth_manager = ClientCredentialsAuthManager(
        make_settings(), httpx.AsyncClient(base_url=BASE_URL)
    )
    tools, _ = generate_tools([op], auth_manager, http_client)
    assert tools[0].description == "Get thing"


def test_tool_description_uses_description_only():
    op = Operation(
        operation_id="getThing",
        method="get",
        path="/thing",
        description="Fetches a thing.",
    )
    http_client = HttpClient(httpx.AsyncClient(base_url=BASE_URL))
    auth_manager = ClientCredentialsAuthManager(
        make_settings(), httpx.AsyncClient(base_url=BASE_URL)
    )
    tools, _ = generate_tools([op], auth_manager, http_client)
    assert tools[0].description == "Fetches a thing."


def test_tool_description_concatenates_summary_and_description():
    op = Operation(
        operation_id="getThing",
        method="get",
        path="/thing",
        summary="Get thing",
        description="Fetches a thing.",
    )
    http_client = HttpClient(httpx.AsyncClient(base_url=BASE_URL))
    auth_manager = ClientCredentialsAuthManager(
        make_settings(), httpx.AsyncClient(base_url=BASE_URL)
    )
    tools, _ = generate_tools([op], auth_manager, http_client)
    assert tools[0].description == "Get thing\n\nFetches a thing."


def test_tool_description_none_when_neither_present():
    op = Operation(operation_id="getThing", method="get", path="/thing")
    http_client = HttpClient(httpx.AsyncClient(base_url=BASE_URL))
    auth_manager = ClientCredentialsAuthManager(
        make_settings(), httpx.AsyncClient(base_url=BASE_URL)
    )
    tools, _ = generate_tools([op], auth_manager, http_client)
    assert tools[0].description is None


def test_generation_produces_correct_tool_count_and_skips_malformed():
    http_client = HttpClient(httpx.AsyncClient(base_url=BASE_URL))
    auth_manager = ClientCredentialsAuthManager(
        make_settings(), httpx.AsyncClient(base_url=BASE_URL)
    )

    tools, report = generate_tools(make_operations(), auth_manager, http_client)

    assert len(tools) == 5
    assert "createThing" in report.succeeded
    assert "" in report.failed


@respx.mock
async def test_generated_tool_calls_http_and_returns_result():
    respx.post(f"{BASE_URL}/realms/master/protocol/openid-connect/token").mock(
        return_value=httpx.Response(200, json={"access_token": "tok"})
    )
    respx.get(f"{BASE_URL}/admin/realms/main/thing0").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    http_client = HttpClient(httpx.AsyncClient(base_url=BASE_URL))
    auth_manager = ClientCredentialsAuthManager(
        make_settings(), httpx.AsyncClient(base_url=BASE_URL)
    )

    tools, _ = generate_tools(make_operations(), auth_manager, http_client)
    tool = next(t for t in tools if t.name == "getThing0")
    result = await tool.run({"realm": "main"})

    assert result.is_error is not True


@respx.mock
async def test_invalid_input_never_reaches_http_client():
    route = respx.get(f"{BASE_URL}/admin/realms/main/thing0").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    http_client = HttpClient(httpx.AsyncClient(base_url=BASE_URL))
    auth_manager = ClientCredentialsAuthManager(
        make_settings(), httpx.AsyncClient(base_url=BASE_URL)
    )

    tools, _ = generate_tools(make_operations(), auth_manager, http_client)
    tool = next(t for t in tools if t.name == "getThing0")

    with pytest.raises(Exception):
        await tool.run({})

    assert route.call_count == 0
