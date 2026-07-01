"""client_credentials grant token fetch (FR-4). No refresh (IR-1)."""

import httpx

from keycloak_mcp.config import Settings

TOKEN_PATH = "/realms/{realm}/protocol/openid-connect/token"


class ClientCredentialsAuthManager:
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http_client = http_client

    async def get_token(self) -> str:
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
