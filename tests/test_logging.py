import httpx
import respx

from keycloak_mcp.http.client import HttpClient
from keycloak_mcp.logging_config import JsonFormatter
from keycloak_mcp.openapi.models import Operation

BASE_URL = "https://kc.example.com"
SECRET_TOKEN = "super-secret-token-xyz"
SECRET_PASSWORD = "hunter2"


@respx.mock
async def test_http_call_logs_no_pii_or_secrets(caplog):
    respx.post(f"{BASE_URL}/admin/realms/main/users").mock(
        return_value=httpx.Response(
            201, json={"username": "alice", "password": SECRET_PASSWORD}
        )
    )
    client = HttpClient(httpx.AsyncClient(base_url=BASE_URL))
    operation = Operation(
        operation_id="createUser", method="post", path="/admin/realms/main/users"
    )

    with caplog.at_level("INFO"):
        await client.call(
            operation, token=SECRET_TOKEN, body={"password": SECRET_PASSWORD}
        )

    for record in caplog.records:
        formatted = JsonFormatter().format(record)
        assert SECRET_TOKEN not in formatted
        assert SECRET_PASSWORD not in formatted
        assert "alice" not in formatted


@respx.mock
async def test_log_record_contains_method_path_status(caplog):
    respx.get(f"{BASE_URL}/admin/realms/main").mock(
        return_value=httpx.Response(200, json={})
    )
    client = HttpClient(httpx.AsyncClient(base_url=BASE_URL))
    operation = Operation(
        operation_id="getRealm", method="get", path="/admin/realms/main"
    )

    with caplog.at_level("INFO"):
        await client.call(operation, token=SECRET_TOKEN)

    record = next(r for r in caplog.records if hasattr(r, "structured_fields"))
    assert record.structured_fields == {
        "method": "get",
        "path": "/admin/realms/main",
        "status": 200,
    }
