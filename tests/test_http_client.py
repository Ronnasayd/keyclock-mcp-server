import httpx
import pytest
import respx

from keycloak_mcp.errors import KeycloakApiError
from keycloak_mcp.http.client import HttpClient
from keycloak_mcp.openapi.models import Operation

BASE_URL = "https://kc.example.com"


def make_operation(
    path: str = "/admin/realms/{realm}", method: str = "get"
) -> Operation:
    return Operation(operation_id="getRealm", method=method, path=path)


@respx.mock
async def test_call_builds_request_from_operation_params():
    respx.get(f"{BASE_URL}/admin/realms/main").mock(
        return_value=httpx.Response(200, json={"realm": "main"})
    )
    client = HttpClient(httpx.AsyncClient(base_url=BASE_URL))
    result = await client.call(
        make_operation(), token="tok", path_params={"realm": "main"}
    )
    assert result == {"realm": "main"}


@respx.mock
async def test_non_2xx_raises_keycloak_api_error():
    respx.get(f"{BASE_URL}/admin/realms/main").mock(
        return_value=httpx.Response(403, json={"error": "Forbidden"})
    )
    client = HttpClient(httpx.AsyncClient(base_url=BASE_URL))
    with pytest.raises(KeycloakApiError) as exc_info:
        await client.call(make_operation(), token="tok", path_params={"realm": "main"})
    assert exc_info.value.status_code == 403
    assert exc_info.value.body == {"error": "Forbidden"}


@respx.mock
async def test_network_exception_propagates_without_retry():
    route = respx.get(f"{BASE_URL}/admin/realms/main").mock(
        side_effect=httpx.ConnectError("boom")
    )
    client = HttpClient(httpx.AsyncClient(base_url=BASE_URL))
    with pytest.raises(httpx.ConnectError):
        await client.call(make_operation(), token="tok", path_params={"realm": "main"})
    assert route.call_count == 1
