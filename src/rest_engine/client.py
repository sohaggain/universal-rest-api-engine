"""Universal REST API client.

Design goals:
    - One client, any REST API: GET/POST/PUT/PATCH/DELETE
    - Pluggable auth (see auth.py)
    - Automatic retry with backoff on transient failures (see retry.py)
    - Explicit timeouts (connect + read)
    - Structured logging with request correlation
    - Typed, predictable error handling (see exceptions.py)
    - No hidden global state, no hardcoded credentials
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional

import requests

from .auth import AuthStrategy, NoAuth
from .config import ClientConfig
from .exceptions import (
    ApiClientError,
    ApiServerError,
    ConfigurationError,
    RequestTimeoutError,
)
from .logger import logger
from .models import ApiResponse
from .retry import call_with_retry

_ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


class RestClient:
    """A reusable, production-oriented HTTP client for any REST API.

    Example:
        config = ClientConfig(base_url="https://api.example.com")
        auth = BearerTokenAuth(token="...")
        client = RestClient(config=config, auth=auth)

        response = client.get("/users", params={"page": 1})
        response = client.post("/users", json={"name": "Ada"})
    """

    def __init__(
        self,
        config: ClientConfig,
        auth: Optional[AuthStrategy] = None,
        session: Optional[requests.Session] = None,
    ):
        if config is None:
            raise ConfigurationError("ClientConfig is required")
        self.config = config
        self.auth = auth or NoAuth()
        self.session = session or requests.Session()

    # -- Public HTTP verbs ------------------------------------------------

    def get(self, path: str, **kwargs) -> ApiResponse:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> ApiResponse:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> ApiResponse:
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs) -> ApiResponse:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs) -> ApiResponse:
        return self.request("DELETE", path, **kwargs)

    # -- Core request path --------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        idempotency_key: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> ApiResponse:
        method = method.upper()
        if method not in _ALLOWED_METHODS:
            raise ConfigurationError(f"Unsupported HTTP method: {method}")

        url = self._build_url(path)
        request_id = str(uuid.uuid4())

        merged_headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "application/json",
            "X-Request-ID": request_id,
            **self.config.default_headers,
            **(headers or {}),
        }

        # Idempotency key lets safe retries of POST/PATCH avoid duplicate
        # side effects on APIs that support it (e.g. payment/CRM APIs).
        if idempotency_key:
            merged_headers.setdefault("Idempotency-Key", idempotency_key)

        request_kwargs: Dict[str, Any] = {
            "method": method,
            "url": url,
            "params": params,
            "json": json,
            "data": data,
            "headers": merged_headers,
            "timeout": (
                self.config.connect_timeout_seconds,
                timeout_seconds or self.config.timeout_seconds,
            ),
            "verify": self.config.verify_ssl,
        }

        request_kwargs = self.auth.apply(request_kwargs)

        def _do_request() -> ApiResponse:
            return self._execute(request_kwargs, request_id)

        logger.info("[%s] %s %s starting", request_id, method, url)
        start = time.monotonic()

        response = call_with_retry(
            _do_request,
            max_retries=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
        )

        elapsed = (time.monotonic() - start) * 1000
        logger.info(
            "[%s] %s %s finished in %.1fms with status %s",
            request_id,
            method,
            url,
            elapsed,
            response.status_code,
        )
        return response

    # -- Internals ------------------------------------------------------

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.config.base_url}/{path.lstrip('/')}"

    def _execute(self, request_kwargs: Dict[str, Any], request_id: str) -> ApiResponse:
        try:
            raw_response = self.session.request(**request_kwargs)
        except requests.Timeout as exc:
            raise RequestTimeoutError(
                f"Request to {request_kwargs['url']} timed out"
            ) from exc

        api_response = self._to_api_response(raw_response, request_id)

        if self.config.retry_on_status and raw_response.status_code in self.config.retry_on_status:
            # Raising here lets call_with_retry() catch it and retry.
            raise ApiServerError(
                f"Retryable status {raw_response.status_code} from {raw_response.url}",
                status_code=raw_response.status_code,
                response_body=api_response.json_body or api_response.text_body,
            )

        if 400 <= raw_response.status_code < 500:
            raise ApiClientError(
                f"Client error {raw_response.status_code} from {raw_response.url}",
                status_code=raw_response.status_code,
                response_body=api_response.json_body or api_response.text_body,
            )

        if raw_response.status_code >= 500:
            raise ApiServerError(
                f"Server error {raw_response.status_code} from {raw_response.url}",
                status_code=raw_response.status_code,
                response_body=api_response.json_body or api_response.text_body,
            )

        return api_response

    @staticmethod
    def _to_api_response(raw_response: requests.Response, request_id: str) -> ApiResponse:
        json_body = None
        text_body = None
        content_type = raw_response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            try:
                json_body = raw_response.json()
            except ValueError:
                text_body = raw_response.text
        else:
            text_body = raw_response.text

        return ApiResponse(
            status_code=raw_response.status_code,
            url=raw_response.url,
            headers=dict(raw_response.headers),
            elapsed_ms=raw_response.elapsed.total_seconds() * 1000,
            json_body=json_body,
            text_body=text_body,
            request_id=request_id,
        )
