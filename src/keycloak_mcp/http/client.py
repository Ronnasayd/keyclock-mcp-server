"""Thin async httpx wrapper for the Keycloak Admin REST API. No retry (IR-2)."""

import logging

import httpx

from keycloak_mcp.errors import JsonValue, KeycloakApiError
from keycloak_mcp.logging_config import log_http_call
from keycloak_mcp.openapi.models import Operation

logger = logging.getLogger(__name__)


class HttpClient:
    """Thin async wrapper that issues Keycloak Admin REST API requests."""

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        """Store the underlying httpx client used to issue requests."""
        self._http_client = http_client

    async def call(
        self,
        operation: Operation,
        token: str,
        path_params: dict[str, str] | None = None,
        query_params: dict[str, str | int | float | bool | None] | None = None,
        body: JsonValue = None,
    ) -> JsonValue:
        """Call `operation` against Keycloak; raise `KeycloakApiError` on failure."""
        url = operation.path.format(**(path_params or {}))
        response = await self._http_client.request(
            operation.method,
            url,
            params=query_params,
            json=body,
            headers={"Authorization": f"Bearer {token}"},
        )
        log_http_call(logger, operation.method, operation.path, response.status_code)
        if response.status_code >= 300:
            raise KeycloakApiError(response.status_code, _safe_body(response))
        return _safe_body(response)


def _safe_body(response: httpx.Response) -> JsonValue:
    """Parse the response body as JSON, falling back to raw text or None."""
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return response.text
