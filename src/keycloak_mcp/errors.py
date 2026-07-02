"""Raw passthrough of Keycloak HTTP errors (FR-7, IR-5). No per-status branching."""

type JsonValue = (
    dict[str, JsonValue] | list[JsonValue] | str | int | float | bool | None
)


class KeycloakApiError(Exception):
    """Raised with the raw status code and body from a failed Keycloak API call."""

    def __init__(self, status_code: int, body: JsonValue) -> None:
        """Store the HTTP status code and raw response body."""
        self.status_code = status_code
        self.body = body
        super().__init__(f"Keycloak API error {status_code}: {body!r}")
