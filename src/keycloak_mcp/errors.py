"""Raw passthrough of Keycloak HTTP errors (FR-7, IR-5). No per-status branching."""

from typing import Any


class KeycloakApiError(Exception):
    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"Keycloak API error {status_code}: {body!r}")
