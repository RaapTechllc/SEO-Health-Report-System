"""Main client classes for the SEO Health SDK."""

from typing import Any, Optional

import httpx

from .auth import RefreshableTokenAuth
from .exceptions import raise_for_status
from .models import (
    AuditResponse,
    AuditResult,
    AuditTier,
    Branding,
    BrandingUpdate,
    TokenResponse,
    Webhook,
    WebhookDelivery,
    WebhookEvent,
)


class SEOHealthClient:
    """Synchronous client for the SEO Health Report API."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the SEO Health client.

        Args:
            base_url: Base URL of the API (e.g., "https://api.seohealth.com")
            api_key: API key for authentication (takes precedence over token)
            token: Bearer token for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self._auth = RefreshableTokenAuth(
            token=token,
            api_key=api_key,
            refresh_url=f"{self.base_url}/api/v1/auth/refresh",
        )
        self._client = httpx.Client(
            base_url=self.base_url,
            auth=self._auth,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Make an HTTP request and handle errors."""
        response = self._client.request(method, path, **kwargs)

        if response.status_code >= 400:
            try:
                data = response.json()
            except Exception:
                data = {"detail": response.text}
            raise_for_status(
                response.status_code,
                data,
                dict(response.headers),
            )

        if response.status_code == 204:
            return {}

        return response.json()

    # Auth Methods

    def login(self, email: str, password: str) -> TokenResponse:
        """
        Authenticate with email and password.

        Args:
            email: User email address
            password: User password

        Returns:
            TokenResponse with access token and optional refresh token
        """
        data = self._request(
            "POST",
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        token_response = TokenResponse(**data)
        self._auth.token = token_response.access_token
        if token_response.refresh_token:
            self._auth.refresh_token = token_response.refresh_token
        if token_response.expires_in:
            self._auth.set_token_expiry(token_response.expires_in)
        return token_response

    def register(self, email: str, password: str, name: Optional[str] = None) -> TokenResponse:
        """
        Register a new user account.

        Args:
            email: User email address
            password: User password
            name: Optional user name

        Returns:
            TokenResponse with access token
        """
        payload = {"email": email, "password": password}
        if name:
            payload["name"] = name
        data = self._request("POST", "/api/v1/auth/register", json=payload)
        token_response = TokenResponse(**data)
        self._auth.token = token_response.access_token
        if token_response.refresh_token:
            self._auth.refresh_token = token_response.refresh_token
        return token_response

    def refresh_token(self) -> TokenResponse:
        """
        Refresh the access token using the refresh token.

        Returns:
            TokenResponse with new access token
        """
        data = self._request(
            "POST",
            "/api/v1/auth/refresh",
            json={"refresh_token": self._auth.refresh_token},
        )
        token_response = TokenResponse(**data)
        self._auth.token = token_response.access_token
        if token_response.refresh_token:
            self._auth.refresh_token = token_response.refresh_token
        return token_response

    # Audit Methods

    def create_audit(
        self,
        url: str,
        company_name: str,
        tier: AuditTier = AuditTier.FREE,
        webhook_url: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> AuditResponse:
        """
        Create a new SEO audit.

        Args:
            url: Website URL to audit
            company_name: Company name for the report
            tier: Audit tier (free, premium, enterprise)
            webhook_url: Optional webhook URL for completion notification
            options: Optional additional audit options

        Returns:
            AuditResponse with audit ID and status
        """
        payload = {
            "url": url,
            "company_name": company_name,
            "tier": tier.value,
        }
        if webhook_url:
            payload["webhook_url"] = webhook_url
        if options:
            payload["options"] = options

        data = self._request("POST", "/api/v1/audits", json=payload)
        return AuditResponse(**data)

    def get_audit(self, audit_id: str) -> AuditResult:
        """
        Get an audit by ID.

        Args:
            audit_id: The audit ID

        Returns:
            AuditResult with full audit data
        """
        data = self._request("GET", f"/api/v1/audits/{audit_id}")
        return AuditResult(**data)

    def list_audits(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
    ) -> list[AuditResult]:
        """
        List all audits for the current user.

        Args:
            page: Page number (1-indexed)
            per_page: Number of results per page
            status: Optional status filter

        Returns:
            List of AuditResult objects
        """
        params = {"page": page, "per_page": per_page}
        if status:
            params["status"] = status
        data = self._request("GET", "/api/v1/audits", params=params)
        items = data.get("items", data) if isinstance(data, dict) else data
        return [AuditResult(**item) for item in items]

    def delete_audit(self, audit_id: str) -> None:
        """
        Delete an audit.

        Args:
            audit_id: The audit ID to delete
        """
        self._request("DELETE", f"/api/v1/audits/{audit_id}")

    def get_audit_pdf(self, audit_id: str) -> bytes:
        """
        Download the PDF report for an audit.

        Args:
            audit_id: The audit ID

        Returns:
            PDF file contents as bytes
        """
        response = self._client.get(f"/api/v1/audits/{audit_id}/pdf")
        if response.status_code >= 400:
            try:
                data = response.json()
            except Exception:
                data = {"detail": response.text}
            raise_for_status(response.status_code, data, dict(response.headers))
        return response.content

    def get_audit_html(self, audit_id: str) -> str:
        """
        Get the HTML report for an audit.

        Args:
            audit_id: The audit ID

        Returns:
            HTML report as string
        """
        response = self._client.get(f"/api/v1/audits/{audit_id}/html")
        if response.status_code >= 400:
            try:
                data = response.json()
            except Exception:
                data = {"detail": response.text}
            raise_for_status(response.status_code, data, dict(response.headers))
        return response.text

    # Webhook Methods

    def create_webhook(
        self,
        url: str,
        events: list[WebhookEvent],
        active: bool = True,
    ) -> Webhook:
        """
        Create a new webhook.

        Args:
            url: Webhook endpoint URL
            events: List of events to subscribe to
            active: Whether the webhook is active

        Returns:
            Webhook configuration with secret
        """
        data = self._request(
            "POST",
            "/api/v1/webhooks",
            json={
                "url": url,
                "events": [e.value for e in events],
                "active": active,
            },
        )
        return Webhook(**data)

    def list_webhooks(self) -> list[Webhook]:
        """
        List all webhooks for the current user.

        Returns:
            List of Webhook configurations
        """
        data = self._request("GET", "/api/v1/webhooks")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [Webhook(**item) for item in items]

    def get_webhook(self, webhook_id: str) -> Webhook:
        """
        Get a webhook by ID.

        Args:
            webhook_id: The webhook ID

        Returns:
            Webhook configuration
        """
        data = self._request("GET", f"/api/v1/webhooks/{webhook_id}")
        return Webhook(**data)

    def update_webhook(
        self,
        webhook_id: str,
        url: Optional[str] = None,
        events: Optional[list[WebhookEvent]] = None,
        active: Optional[bool] = None,
    ) -> Webhook:
        """
        Update a webhook.

        Args:
            webhook_id: The webhook ID
            url: New webhook URL
            events: New list of events
            active: New active status

        Returns:
            Updated Webhook configuration
        """
        payload = {}
        if url is not None:
            payload["url"] = url
        if events is not None:
            payload["events"] = [e.value for e in events]
        if active is not None:
            payload["active"] = active

        data = self._request("PATCH", f"/api/v1/webhooks/{webhook_id}", json=payload)
        return Webhook(**data)

    def delete_webhook(self, webhook_id: str) -> None:
        """
        Delete a webhook.

        Args:
            webhook_id: The webhook ID to delete
        """
        self._request("DELETE", f"/api/v1/webhooks/{webhook_id}")

    def list_webhook_deliveries(
        self,
        webhook_id: str,
        page: int = 1,
        per_page: int = 20,
    ) -> list[WebhookDelivery]:
        """
        List delivery attempts for a webhook.

        Args:
            webhook_id: The webhook ID
            page: Page number
            per_page: Results per page

        Returns:
            List of WebhookDelivery records
        """
        data = self._request(
            "GET",
            f"/api/v1/webhooks/{webhook_id}/deliveries",
            params={"page": page, "per_page": per_page},
        )
        items = data.get("items", data) if isinstance(data, dict) else data
        return [WebhookDelivery(**item) for item in items]

    # Branding Methods

    def get_branding(self) -> Branding:
        """
        Get current branding configuration.

        Returns:
            Branding configuration
        """
        data = self._request("GET", "/api/v1/branding")
        return Branding(**data)

    def update_branding(
        self,
        logo_url: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        company_name: Optional[str] = None,
        footer_text: Optional[str] = None,
        custom_css: Optional[str] = None,
    ) -> Branding:
        """
        Update branding configuration.

        Args:
            logo_url: URL to company logo
            primary_color: Primary brand color (hex)
            secondary_color: Secondary brand color (hex)
            company_name: Company name for reports
            footer_text: Custom footer text
            custom_css: Custom CSS for reports

        Returns:
            Updated Branding configuration
        """
        payload = BrandingUpdate(
            logo_url=logo_url,
            primary_color=primary_color,
            secondary_color=secondary_color,
            company_name=company_name,
            footer_text=footer_text,
            custom_css=custom_css,
        ).model_dump(exclude_none=True)

        data = self._request("PATCH", "/api/v1/branding", json=payload)
        return Branding(**data)


class AsyncSEOHealthClient:
    """Asynchronous client for the SEO Health Report API."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the async SEO Health client.

        Args:
            base_url: Base URL of the API (e.g., "https://api.seohealth.com")
            api_key: API key for authentication (takes precedence over token)
            token: Bearer token for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self._auth = RefreshableTokenAuth(
            token=token,
            api_key=api_key,
            refresh_url=f"{self.base_url}/api/v1/auth/refresh",
        )
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=self._auth,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Make an HTTP request and handle errors."""
        response = await self._client.request(method, path, **kwargs)

        if response.status_code >= 400:
            try:
                data = response.json()
            except Exception:
                data = {"detail": response.text}
            raise_for_status(
                response.status_code,
                data,
                dict(response.headers),
            )

        if response.status_code == 204:
            return {}

        return response.json()

    # Auth Methods

    async def login(self, email: str, password: str) -> TokenResponse:
        """
        Authenticate with email and password.

        Args:
            email: User email address
            password: User password

        Returns:
            TokenResponse with access token and optional refresh token
        """
        data = await self._request(
            "POST",
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        token_response = TokenResponse(**data)
        self._auth.token = token_response.access_token
        if token_response.refresh_token:
            self._auth.refresh_token = token_response.refresh_token
        if token_response.expires_in:
            self._auth.set_token_expiry(token_response.expires_in)
        return token_response

    async def register(
        self, email: str, password: str, name: Optional[str] = None
    ) -> TokenResponse:
        """
        Register a new user account.

        Args:
            email: User email address
            password: User password
            name: Optional user name

        Returns:
            TokenResponse with access token
        """
        payload = {"email": email, "password": password}
        if name:
            payload["name"] = name
        data = await self._request("POST", "/api/v1/auth/register", json=payload)
        token_response = TokenResponse(**data)
        self._auth.token = token_response.access_token
        if token_response.refresh_token:
            self._auth.refresh_token = token_response.refresh_token
        return token_response

    async def refresh_token(self) -> TokenResponse:
        """
        Refresh the access token using the refresh token.

        Returns:
            TokenResponse with new access token
        """
        data = await self._request(
            "POST",
            "/api/v1/auth/refresh",
            json={"refresh_token": self._auth.refresh_token},
        )
        token_response = TokenResponse(**data)
        self._auth.token = token_response.access_token
        if token_response.refresh_token:
            self._auth.refresh_token = token_response.refresh_token
        return token_response

    # Audit Methods

    async def create_audit(
        self,
        url: str,
        company_name: str,
        tier: AuditTier = AuditTier.FREE,
        webhook_url: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> AuditResponse:
        """
        Create a new SEO audit.

        Args:
            url: Website URL to audit
            company_name: Company name for the report
            tier: Audit tier (free, premium, enterprise)
            webhook_url: Optional webhook URL for completion notification
            options: Optional additional audit options

        Returns:
            AuditResponse with audit ID and status
        """
        payload = {
            "url": url,
            "company_name": company_name,
            "tier": tier.value,
        }
        if webhook_url:
            payload["webhook_url"] = webhook_url
        if options:
            payload["options"] = options

        data = await self._request("POST", "/api/v1/audits", json=payload)
        return AuditResponse(**data)

    async def get_audit(self, audit_id: str) -> AuditResult:
        """
        Get an audit by ID.

        Args:
            audit_id: The audit ID

        Returns:
            AuditResult with full audit data
        """
        data = await self._request("GET", f"/api/v1/audits/{audit_id}")
        return AuditResult(**data)

    async def list_audits(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
    ) -> list[AuditResult]:
        """
        List all audits for the current user.

        Args:
            page: Page number (1-indexed)
            per_page: Number of results per page
            status: Optional status filter

        Returns:
            List of AuditResult objects
        """
        params = {"page": page, "per_page": per_page}
        if status:
            params["status"] = status
        data = await self._request("GET", "/api/v1/audits", params=params)
        items = data.get("items", data) if isinstance(data, dict) else data
        return [AuditResult(**item) for item in items]

    async def delete_audit(self, audit_id: str) -> None:
        """
        Delete an audit.

        Args:
            audit_id: The audit ID to delete
        """
        await self._request("DELETE", f"/api/v1/audits/{audit_id}")

    async def get_audit_pdf(self, audit_id: str) -> bytes:
        """
        Download the PDF report for an audit.

        Args:
            audit_id: The audit ID

        Returns:
            PDF file contents as bytes
        """
        response = await self._client.get(f"/api/v1/audits/{audit_id}/pdf")
        if response.status_code >= 400:
            try:
                data = response.json()
            except Exception:
                data = {"detail": response.text}
            raise_for_status(response.status_code, data, dict(response.headers))
        return response.content

    async def get_audit_html(self, audit_id: str) -> str:
        """
        Get the HTML report for an audit.

        Args:
            audit_id: The audit ID

        Returns:
            HTML report as string
        """
        response = await self._client.get(f"/api/v1/audits/{audit_id}/html")
        if response.status_code >= 400:
            try:
                data = response.json()
            except Exception:
                data = {"detail": response.text}
            raise_for_status(response.status_code, data, dict(response.headers))
        return response.text

    # Webhook Methods

    async def create_webhook(
        self,
        url: str,
        events: list[WebhookEvent],
        active: bool = True,
    ) -> Webhook:
        """
        Create a new webhook.

        Args:
            url: Webhook endpoint URL
            events: List of events to subscribe to
            active: Whether the webhook is active

        Returns:
            Webhook configuration with secret
        """
        data = await self._request(
            "POST",
            "/api/v1/webhooks",
            json={
                "url": url,
                "events": [e.value for e in events],
                "active": active,
            },
        )
        return Webhook(**data)

    async def list_webhooks(self) -> list[Webhook]:
        """
        List all webhooks for the current user.

        Returns:
            List of Webhook configurations
        """
        data = await self._request("GET", "/api/v1/webhooks")
        items = data.get("items", data) if isinstance(data, dict) else data
        return [Webhook(**item) for item in items]

    async def get_webhook(self, webhook_id: str) -> Webhook:
        """
        Get a webhook by ID.

        Args:
            webhook_id: The webhook ID

        Returns:
            Webhook configuration
        """
        data = await self._request("GET", f"/api/v1/webhooks/{webhook_id}")
        return Webhook(**data)

    async def update_webhook(
        self,
        webhook_id: str,
        url: Optional[str] = None,
        events: Optional[list[WebhookEvent]] = None,
        active: Optional[bool] = None,
    ) -> Webhook:
        """
        Update a webhook.

        Args:
            webhook_id: The webhook ID
            url: New webhook URL
            events: New list of events
            active: New active status

        Returns:
            Updated Webhook configuration
        """
        payload = {}
        if url is not None:
            payload["url"] = url
        if events is not None:
            payload["events"] = [e.value for e in events]
        if active is not None:
            payload["active"] = active

        data = await self._request("PATCH", f"/api/v1/webhooks/{webhook_id}", json=payload)
        return Webhook(**data)

    async def delete_webhook(self, webhook_id: str) -> None:
        """
        Delete a webhook.

        Args:
            webhook_id: The webhook ID to delete
        """
        await self._request("DELETE", f"/api/v1/webhooks/{webhook_id}")

    async def list_webhook_deliveries(
        self,
        webhook_id: str,
        page: int = 1,
        per_page: int = 20,
    ) -> list[WebhookDelivery]:
        """
        List delivery attempts for a webhook.

        Args:
            webhook_id: The webhook ID
            page: Page number
            per_page: Results per page

        Returns:
            List of WebhookDelivery records
        """
        data = await self._request(
            "GET",
            f"/api/v1/webhooks/{webhook_id}/deliveries",
            params={"page": page, "per_page": per_page},
        )
        items = data.get("items", data) if isinstance(data, dict) else data
        return [WebhookDelivery(**item) for item in items]

    # Branding Methods

    async def get_branding(self) -> Branding:
        """
        Get current branding configuration.

        Returns:
            Branding configuration
        """
        data = await self._request("GET", "/api/v1/branding")
        return Branding(**data)

    async def update_branding(
        self,
        logo_url: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        company_name: Optional[str] = None,
        footer_text: Optional[str] = None,
        custom_css: Optional[str] = None,
    ) -> Branding:
        """
        Update branding configuration.

        Args:
            logo_url: URL to company logo
            primary_color: Primary brand color (hex)
            secondary_color: Secondary brand color (hex)
            company_name: Company name for reports
            footer_text: Custom footer text
            custom_css: Custom CSS for reports

        Returns:
            Updated Branding configuration
        """
        payload = BrandingUpdate(
            logo_url=logo_url,
            primary_color=primary_color,
            secondary_color=secondary_color,
            company_name=company_name,
            footer_text=footer_text,
            custom_css=custom_css,
        ).model_dump(exclude_none=True)

        data = await self._request("PATCH", "/api/v1/branding", json=payload)
        return Branding(**data)


__all__ = [
    "SEOHealthClient",
    "AsyncSEOHealthClient",
]
