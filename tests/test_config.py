import pytest
from pydantic import ValidationError

from keycloak_mcp.config import Settings


def test_client_credentials_missing_secret_raises():
    with pytest.raises(ValidationError):
        Settings(
            keycloak_base_url="https://kc.example.com",
            auth_method="client_credentials",
            client_id="my-client",
        )


def test_client_credentials_valid_config_loads():
    settings = Settings(
        keycloak_base_url="https://kc.example.com",
        auth_method="client_credentials",
        client_id="my-client",
        client_secret="s3cr3t",
    )
    assert settings.auth_method == "client_credentials"
    assert settings.client_secret == "s3cr3t"


def test_password_mode_missing_credentials_raises():
    with pytest.raises(ValidationError):
        Settings(
            keycloak_base_url="https://kc.example.com",
            auth_method="password",
            client_id="my-client",
        )


def test_password_mode_valid_config_loads():
    settings = Settings(
        keycloak_base_url="https://kc.example.com",
        auth_method="password",
        client_id="my-client",
        admin_username="admin",
        admin_password="admin-pass",
    )
    assert settings.auth_method == "password"
    assert settings.admin_username == "admin"


def test_default_realm_is_optional():
    settings = Settings(
        keycloak_base_url="https://kc.example.com",
        auth_method="password",
        client_id="my-client",
        admin_username="admin",
        admin_password="admin-pass",
    )
    assert settings.default_realm is None
