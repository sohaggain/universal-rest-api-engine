import pytest

from rest_engine.exceptions import ApiServerError, RetryExhaustedError
from rest_engine.retry import call_with_retry


def test_succeeds_on_first_try():
    calls = {"count": 0}

    def func():
        calls["count"] += 1
        return "ok"

    result = call_with_retry(func, max_retries=3, backoff_factor=0.01)
    assert result == "ok"
    assert calls["count"] == 1


def test_succeeds_after_transient_failures():
    calls = {"count": 0}

    def func():
        calls["count"] += 1
        if calls["count"] < 3:
            raise ApiServerError("boom", status_code=503)
        return "ok"

    result = call_with_retry(func, max_retries=3, backoff_factor=0.01)
    assert result == "ok"
    assert calls["count"] == 3


def test_raises_retry_exhausted_after_max_attempts():
    calls = {"count": 0}

    def func():
        calls["count"] += 1
        raise ApiServerError("always fails", status_code=500)

    with pytest.raises(RetryExhaustedError):
        call_with_retry(func, max_retries=2, backoff_factor=0.01)

    assert calls["count"] == 3  # initial attempt + 2 retries


def test_non_retryable_exception_propagates_immediately():
    calls = {"count": 0}

    def func():
        calls["count"] += 1
        raise ValueError("not retryable")

    with pytest.raises(ValueError):
        call_with_retry(func, max_retries=3, backoff_factor=0.01)

    assert calls["count"] == 1
