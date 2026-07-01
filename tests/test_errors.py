from keycloak_mcp.errors import KeycloakApiError


def test_403_raw_passthrough():
    error = KeycloakApiError(
        403, {"error": "Forbidden", "error_description": "no access"}
    )
    assert error.status_code == 403
    assert error.body == {"error": "Forbidden", "error_description": "no access"}


def test_500_raw_passthrough():
    error = KeycloakApiError(500, {"error": "Internal Server Error"})
    assert error.status_code == 500
    assert error.body == {"error": "Internal Server Error"}


def test_no_message_rewriting_between_statuses():
    error_403 = KeycloakApiError(403, {"detail": "x"})
    error_500 = KeycloakApiError(500, {"detail": "x"})
    assert type(error_403) is type(error_500)
    assert error_403.body == error_500.body
