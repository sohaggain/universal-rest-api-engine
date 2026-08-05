"""Exception hierarchy for the REST engine.

Keeping exceptions specific (rather than a single generic Exception)
lets callers decide precisely how to react: retry, alert, fail fast, etc.
"""

from __future__ import annotations

from typing import Any, Optional


class RestEngineError(Exception):
    """Base class for all errors raised by this package."""


class ConfigurationError(RestEngineError):
    """Raised when the client is misconfigured (bad base_url, missing auth, etc.)."""


class AuthenticationError(RestEngineError):
    """Raised when authentication fails (401) or an auth strategy is misconfigured."""


class RequestTimeoutError(RestEngineError):
    """Raised when a request exceeds the configured timeout."""


class RetryExhaustedError(RestEngineError):
    """Raised when all retry attempts have been exhausted without success."""

    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


class ApiClientError(RestEngineError):
    """Raised for 4xx responses (bad request, unauthorized, forbidden, not found, etc.)."""

    def __init__(self, message: str, status_code: int, response_body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class ApiServerError(RestEngineError):
    """Raised for 5xx responses. These are generally safe to retry."""

    def __init__(self, message: str, status_code: int, response_body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
