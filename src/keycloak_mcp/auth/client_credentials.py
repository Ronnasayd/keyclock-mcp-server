"""client_credentials grant token fetch (FR-4). No refresh (IR-1)."""

import httpx

from keycloak_mcp.config import Settings

TOKEN_PATH = "/realms/{realm}/protocol/openid-connect/token"  # noqa: S105


class ClientCredentialsAuthManager:
    """Fetches access tokens via the OAuth2 client_credentials grant."""

    def __init__(self, settings: Settings, http_client: httpx.AsyncClient) -> None:
        """Store settings and the HTTP client used to reach the token endpoint."""
        self._settings = settings
        self._http_client = http_client

    async def get_token(self) -> str:
        """Return a fresh access token; no refresh/caching (IR-1)."""
        realm = self._settings.default_realm or "master"
        response = await self._http_client.post(
            TOKEN_PATH.format(realm=realm),
            data={
                "grant_type": "client_credentials",
                "client_id": self._settings.client_id,
                "client_secret": self._settings.client_secret,
            },
        )
        response.raise_for_status()
        return str(response.json()["access_token"])
