"""Resource Owner Password Credentials (ROPC) grant token fetch (FR-4). No refresh (IR-1)."""

import httpx

from keycloak_mcp.config import Settings

TOKEN_PATH = "/realms/{realm}/protocol/openid-connect/token"


class PasswordAuthManager:
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http_client = http_client

    async def get_token(self) -> str:
        realm = self._settings.default_realm or "master"
        response = await self._http_client.post(
            TOKEN_PATH.format(realm=realm),
            data={
                "grant_type": "password",
                "client_id": self._settings.client_id,
                "username": self._settings.admin_username,
                "password": self._settings.admin_password,
            },
        )
        response.raise_for_status()
        return str(response.json()["access_token"])
