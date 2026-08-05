"""
Universal REST API Automation Engine
=====================================

A production-oriented, reusable Python client for calling any REST API:
GET / POST / PUT / PATCH / DELETE, pluggable authentication, automatic
retries with backoff, timeouts, structured logging, and typed responses.
"""

from .client import RestClient
from .auth import (
    AuthStrategy,
    NoAuth,
    ApiKeyAuth,
    BearerTokenAuth,
    BasicAuth,
    OAuth2ClientCredentials,
)
from .config import ClientConfig
from .exceptions import (
    RestEngineError,
    RequestTimeoutError,
    RetryExhaustedError,
    ApiClientError,
    ApiServerError,
    AuthenticationError,
)
from .models import ApiResponse

__all__ = [
    "RestClient",
    "AuthStrategy",
    "NoAuth",
    "ApiKeyAuth",
    "BearerTokenAuth",
    "BasicAuth",
    "OAuth2ClientCredentials",
    "ClientConfig",
    "RestEngineError",
    "RequestTimeoutError",
    "RetryExhaustedError",
    "ApiClientError",
    "ApiServerError",
    "AuthenticationError",
    "ApiResponse",
]

__version__ = "0.1.0"
