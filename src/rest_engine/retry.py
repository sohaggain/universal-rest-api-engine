"""Retry-with-exponential-backoff for transient HTTP failures.

Kept as a small, dependency-free utility (no `tenacity`) so the failure
policy is easy to audit: what gets retried, how many times, and how long
we wait between attempts.
"""

from __future__ import annotations

import random
import time
from typing import Callable, Iterable, TypeVar

import requests

from .exceptions import ApiServerError, RetryExhaustedError
from .logger import logger

T = TypeVar("T")


def is_retryable_status(status_code: int, retry_on_status: Iterable[int]) -> bool:
    return status_code in retry_on_status


def call_with_retry(
    func: Callable[[], T],
    max_retries: int,
    backoff_factor: float,
    retryable_exceptions: tuple = (requests.ConnectionError, requests.Timeout, ApiServerError),
) -> T:
    """Call `func` and retry on network errors, timeouts, or 5xx/429 responses.

    Uses exponential backoff with jitter: backoff_factor * (2 ** attempt) + jitter.
    Attempt 0 is the first (non-retry) call, so max_retries=3 means up to 4
    total attempts.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except retryable_exceptions as exc:  # noqa: PERF203 - clarity over micro-opt
            last_exception = exc
            if attempt == max_retries:
                break
            sleep_seconds = backoff_factor * (2**attempt) + random.uniform(0, 0.25)
            logger.warning(
                "Retryable error on attempt %s/%s: %s — retrying in %.2fs",
                attempt + 1,
                max_retries + 1,
                exc,
                sleep_seconds,
            )
            time.sleep(sleep_seconds)

    raise RetryExhaustedError(
        f"All {max_retries + 1} attempts failed. Last error: {last_exception}",
        last_exception=last_exception,
    )
