import time

from keycloak_mcp.config import Settings
from keycloak_mcp.openapi.models import Operation, Param
from keycloak_mcp.server import VENDORED_SPEC_PATH, build_server, load_operations


def make_settings() -> Settings:
    return Settings(
        keycloak_base_url="https://kc.example.com",
        auth_method="client_credentials",
        client_id="my-client",
        client_secret="s3cr3t",
    )


def test_startup_registers_expected_tool_count():
    operations = [
        Operation(
            operation_id=f"op{i}",
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
        for i in range(5)
    ]
    _mcp, report = build_server(make_settings(), operations=operations)
    assert len(report.succeeded) == 5


def test_startup_time_under_2s_with_real_spec():
    operations = load_operations(VENDORED_SPEC_PATH)
    start = time.monotonic()
    build_server(make_settings(), operations=operations)
    elapsed = time.monotonic() - start
    assert elapsed < 2.0
