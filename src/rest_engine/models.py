"""Response models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ApiResponse:
    """Normalized representation of an API response.

    Wrapping `requests.Response` keeps the public interface of RestClient
    stable even if the underlying HTTP library is swapped out later.
    """

    status_code: int
    url: str
    headers: Dict[str, str]
    elapsed_ms: float
    json_body: Optional[Any] = None
    text_body: Optional[str] = None
    request_id: Optional[str] = None  # correlation id set by the caller, for log tracing

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300
