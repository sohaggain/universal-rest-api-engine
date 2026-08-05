"""Pluggable authentication strategies.

Each strategy implements `apply(request_kwargs) -> request_kwargs`, mutating
headers/params/auth as needed. This keeps RestClient decoupled from any
single auth scheme and makes it trivial to add new ones (HMAC signing,
JWT refresh, etc.) without touching the client itself.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import requests

from .exceptions import AuthenticationError


class AuthStrategy(ABC):
    """Base class for all authentication strategies."""

    @abstractmethod
    def apply(self, request_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Mutate and return the kwargs that will be passed to requests.request()."""
        raise NotImplementedError


class NoAuth(AuthStrategy):
    """No authentication — used for public APIs."""

    def apply(self, request_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        return request_kwargs


class ApiKeyAuth(AuthStrategy):
    """API key sent as a header or query parameter.

    Example: ApiKeyAuth(key="secret", location="header", name="X-API-Key")
    """

    def __init__(self, key: str, name: str = "X-API-Key", location: str = "header"):
        if not key:
            raise AuthenticationError("ApiKeyAuth requires a non-empty key")
        if location not in ("header", "query"):
            raise AuthenticationError("location must be 'header' or 'query'")
        self.key = key
        self.name = name
        self.location = location

    def apply(self, request_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        if self.location == "header":
            headers = request_kwargs.setdefault("headers", {})
            headers[self.name] = self.key
        else:
            params = request_kwargs.setdefault("params", {})
            params[self.name] = self.key
        return request_kwargs


class BearerTokenAuth(AuthStrategy):
    """Standard `Authorization: Bearer <token>` header."""

    def __init__(self, token: str):
        if not token:
            raise AuthenticationError("BearerTokenAuth requires a non-empty token")
        self.token = token

    def apply(self, request_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        headers = request_kwargs.setdefault("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"
        return request_kwargs


class BasicAuth(AuthStrategy):
    """HTTP Basic authentication."""

    def __init__(self, username: str, password: str):
        if not username or password is None:
            raise AuthenticationError("BasicAuth requires username and password")
        self.username = username
        self.password = password

    def apply(self, request_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        request_kwargs["auth"] = (self.username, self.password)
        return request_kwargs


class OAuth2ClientCredentials(AuthStrategy):
    """OAuth2 client-credentials grant with automatic token caching + refresh.

    Fetches an access token from `token_url` using client_id/client_secret,
    caches it in memory, and refreshes it a short buffer before expiry.
    """

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: Optional[str] = None,
        expiry_buffer_seconds: int = 30,
    ):
        if not (token_url and client_id and client_secret):
            raise AuthenticationError(
                "OAuth2ClientCredentials requires token_url, client_id, and client_secret"
            )
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.expiry_buffer_seconds = expiry_buffer_seconds
        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0

    def _token_is_valid(self) -> bool:
        return bool(self._access_token) and time.time() < (
            self._expires_at - self.expiry_buffer_seconds
        )

    def _fetch_token(self) -> None:
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.scope:
            payload["scope"] = self.scope

        try:
            response = requests.post(self.token_url, data=payload, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise AuthenticationError(f"OAuth2 token request failed: {exc}") from exc

        data = response.json()
        self._access_token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)
        self._expires_at = time.time() + float(expires_in)

        if not self._access_token:
            raise AuthenticationError("OAuth2 token endpoint did not return access_token")

    def apply(self, request_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        if not self._token_is_valid():
            self._fetch_token()
        headers = request_kwargs.setdefault("headers", {})
        headers["Authorization"] = f"Bearer {self._access_token}"
        return request_kwargs
