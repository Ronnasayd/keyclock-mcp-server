"""Settings loaded from environment (FR-4, Specs §5)."""

from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server configuration loaded from `MCP_KEYCLOAK_*` environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="MCP_KEYCLOAK_", extra="ignore", populate_by_name=True
    )

    keycloak_base_url: str = Field(validation_alias="MCP_KEYCLOAK_BASE_URL")
    auth_method: Literal["client_credentials", "password"]
    client_id: str | None = None
    client_secret: str | None = None
    admin_username: str | None = None
    admin_password: str | None = None
    default_realm: str | None = None
    read_only: bool = False

    @model_validator(mode="after")
    def validate_auth_fields(self) -> "Settings":
        """Ensure the fields required by `auth_method` are present."""
        if self.auth_method == "client_credentials":
            self._require_fields(
                client_id=self.client_id, client_secret=self.client_secret
            )
        else:
            self._require_fields(
                client_id=self.client_id,
                admin_username=self.admin_username,
                admin_password=self.admin_password,
            )
        return self

    def _require_fields(self, **fields: str | None) -> None:
        missing = [name for name, value in fields.items() if not value]
        if missing:
            raise ValueError(
                f"auth_method={self.auth_method!r} requires fields: "
                f"{', '.join(missing)}"
            )
