import httpx
import pytest
import respx

from keycloak_mcp.auth.client_credentials import ClientCredentialsAuthManager
from keycloak_mcp.auth.password import PasswordAuthManager
from keycloak_mcp.config import Settings

BASE_URL = "https://kc.example.com"


@pytest.fixture
def http_client():
    return httpx.AsyncClient(base_url=BASE_URL)


@respx.mock
async def test_client_credentials_returns_token(http_client):
    respx.post(f"{BASE_URL}/realms/master/protocol/openid-connect/token").mock(
        return_value=httpx.Response(200, json={"access_token": "abc123"})
    )
    settings = Settings(
        keycloak_base_url=BASE_URL,
        auth_method="client_credentials",
        client_id="my-client",
        client_secret="s3cr3t",
    )
    manager = ClientCredentialsAuthManager(settings, http_client)
    token = await manager.get_token()
    assert token == "abc123"


def test_client_credentials_has_no_refresh_method(http_client):
    settings = Settings(
        keycloak_base_url=BASE_URL,
        auth_method="client_credentials",
        client_id="my-client",
        client_secret="s3cr3t",
    )
    manager = ClientCredentialsAuthManager(settings, http_client)
    assert not hasattr(manager, "refresh_token")
    assert not hasattr(manager, "refresh")


@respx.mock
async def test_password_grant_returns_token(http_client):
    respx.post(f"{BASE_URL}/realms/master/protocol/openid-connect/token").mock(
        return_value=httpx.Response(200, json={"access_token": "xyz789"})
    )
    settings = Settings(
        keycloak_base_url=BASE_URL,
        auth_method="password",
        client_id="my-client",
        admin_username="admin",
        admin_password="admin-pass",
    )
    manager = PasswordAuthManager(settings, http_client)
    token = await manager.get_token()
    assert token == "xyz789"
