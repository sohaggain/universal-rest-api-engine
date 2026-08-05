"""Configuration for RestClient.

Configuration is intentionally explicit and code-first: values can be
passed directly, or sourced from environment variables via `ClientConfig.from_env()`.
Nothing here reads secrets implicitly from disk or hardcodes credentials.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ClientConfig:
    base_url: str
    default_headers: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 15.0
    connect_timeout_seconds: float = 5.0
    max_retries: int = 3
    backoff_factor: float = 0.5  # exponential: 0.5, 1, 2, 4 ...
    retry_on_status: tuple = (429, 500, 502, 503, 504)
    verify_ssl: bool = True
    user_agent: str = "universal-rest-api-engine/0.1.0"

    def __post_init__(self) -> None:
        if not self.base_url:
            raise ValueError("base_url is required")
        self.base_url = self.base_url.rstrip("/")
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")

    @classmethod
    def from_env(cls, prefix: str = "REST_ENGINE_") -> "ClientConfig":
        """Build a ClientConfig from environment variables.

        Recognized variables (with default prefix REST_ENGINE_):
            REST_ENGINE_BASE_URL (required)
            REST_ENGINE_TIMEOUT_SECONDS
            REST_ENGINE_MAX_RETRIES
            REST_ENGINE_BACKOFF_FACTOR
            REST_ENGINE_VERIFY_SSL
        """
        base_url = os.environ.get(f"{prefix}BASE_URL")
        if not base_url:
            raise ValueError(f"{prefix}BASE_URL environment variable is required")

        return cls(
            base_url=base_url,
            timeout_seconds=float(os.environ.get(f"{prefix}TIMEOUT_SECONDS", 15.0)),
            max_retries=int(os.environ.get(f"{prefix}MAX_RETRIES", 3)),
            backoff_factor=float(os.environ.get(f"{prefix}BACKOFF_FACTOR", 0.5)),
            verify_ssl=os.environ.get(f"{prefix}VERIFY_SSL", "true").lower() != "false",
        )
