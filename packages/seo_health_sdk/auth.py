"""Authentication handling for the SEO Health SDK."""

from datetime import datetime, timedelta
from typing import Optional

import httpx


class TokenAuth(httpx.Auth):
    """HTTPX authentication class for Bearer token authentication."""

    def __init__(self, token: Optional[str] = None, api_key: Optional[str] = None):
        self._token = token
        self._api_key = api_key
        self._token_expires_at: Optional[datetime] = None

    @property
    def token(self) -> Optional[str]:
        """Get the current token."""
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        """Set a new token."""
        self._token = value

    @property
    def api_key(self) -> Optional[str]:
        """Get the API key."""
        return self._api_key

    @api_key.setter
    def api_key(self, value: str) -> None:
        """Set the API key."""
        self._api_key = value

    def set_token_expiry(self, expires_in: int) -> None:
        """Set token expiration time."""
        self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    def is_token_expired(self) -> bool:
        """Check if the token is expired."""
        if self._token_expires_at is None:
            return False
        return datetime.utcnow() >= self._token_expires_at - timedelta(seconds=30)

    def auth_flow(self, request: httpx.Request):
        """Add authentication headers to request."""
        if self._api_key:
            request.headers["X-API-Key"] = self._api_key
        elif self._token:
            request.headers["Authorization"] = f"Bearer {self._token}"
        yield request


class RefreshableTokenAuth(TokenAuth):
    """Token authentication with auto-refresh capability."""

    def __init__(
        self,
        token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        api_key: Optional[str] = None,
        refresh_url: Optional[str] = None,
    ):
        super().__init__(token, api_key)
        self._refresh_token = refresh_token
        self._refresh_url = refresh_url

    @property
    def refresh_token(self) -> Optional[str]:
        """Get the refresh token."""
        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, value: str) -> None:
        """Set a new refresh token."""
        self._refresh_token = value

    def can_refresh(self) -> bool:
        """Check if token refresh is possible."""
        return bool(self._refresh_token and self._refresh_url)

    def sync_refresh(self, client: httpx.Client) -> bool:
        """Synchronously refresh the token."""
        if not self.can_refresh():
            return False

        response = client.post(
            self._refresh_url,
            json={"refresh_token": self._refresh_token},
        )

        if response.status_code == 200:
            data = response.json()
            self._token = data.get("access_token")
            if "refresh_token" in data:
                self._refresh_token = data["refresh_token"]
            if "expires_in" in data:
                self.set_token_expiry(data["expires_in"])
            return True
        return False

    async def async_refresh(self, client: httpx.AsyncClient) -> bool:
        """Asynchronously refresh the token."""
        if not self.can_refresh():
            return False

        response = await client.post(
            self._refresh_url,
            json={"refresh_token": self._refresh_token},
        )

        if response.status_code == 200:
            data = response.json()
            self._token = data.get("access_token")
            if "refresh_token" in data:
                self._refresh_token = data["refresh_token"]
            if "expires_in" in data:
                self.set_token_expiry(data["expires_in"])
            return True
        return False


__all__ = [
    "TokenAuth",
    "RefreshableTokenAuth",
]
