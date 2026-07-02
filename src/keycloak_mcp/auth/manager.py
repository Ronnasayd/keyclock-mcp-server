"""AuthManager protocol (FR-4). No refresh logic — see IR-1."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class AuthManager(Protocol):
    """Protocol for fetching access tokens, regardless of grant type."""

    async def get_token(self) -> str:
        """Return a current access token. Callers must reauthenticate on 401."""
        ...
