from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
import requests

from rest_engine.client import RestClient
from rest_engine.config import ClientConfig
from rest_engine.exceptions import ApiClientError, ApiServerError, RetryExhaustedError


def make_response(status_code=200, json_body=None, content_type="application/json"):
    response = MagicMock(spec=list(vars(requests.Response()).keys()) + ["json", "text"])
    response.status_code = status_code
    response.url = "https://api.example.com/resource"
    response.headers = {"Content-Type": content_type}
    response.elapsed = timedelta(milliseconds=123)
    response.json.return_value = json_body or {}
    response.text = "" if json_body is not None else "plain text body"
    return response


@pytest.fixture
def client():
    config = ClientConfig(base_url="https://api.example.com", max_retries=2, backoff_factor=0.01)
    return RestClient(config=config)


def test_get_success(client):
    ok_response = make_response(200, {"id": 1, "name": "Ada"})
    with patch.object(client.session, "request", return_value=ok_response) as mock_request:
        result = client.get("/users/1")

    assert result.ok
    assert result.status_code == 200
    assert result.json_body == {"id": 1, "name": "Ada"}
    mock_request.assert_called_once()
    assert mock_request.call_args.kwargs["method"] == "GET"


def test_post_sends_json_body(client):
    ok_response = make_response(201, {"id": 2})
    with patch.object(client.session, "request", return_value=ok_response) as mock_request:
        result = client.post("/users", json={"name": "Grace"})

    assert result.status_code == 201
    assert mock_request.call_args.kwargs["json"] == {"name": "Grace"}


def test_4xx_raises_api_client_error_without_retry(client):
    bad_response = make_response(404, {"error": "not found"})
    with patch.object(client.session, "request", return_value=bad_response) as mock_request:
        with pytest.raises(ApiClientError) as exc_info:
            client.get("/users/999")

    assert exc_info.value.status_code == 404
    mock_request.assert_called_once()  # 4xx (non-retryable) should not retry


def test_5xx_retries_then_raises_retry_exhausted(client):
    error_response = make_response(500, {"error": "server error"})
    with patch.object(client.session, "request", return_value=error_response) as mock_request:
        with pytest.raises(RetryExhaustedError):
            client.get("/flaky")

    # max_retries=2 -> 3 total attempts
    assert mock_request.call_count == 3


def test_retry_then_success(client):
    error_response = make_response(503, {"error": "unavailable"})
    ok_response = make_response(200, {"status": "recovered"})
    with patch.object(
        client.session, "request", side_effect=[error_response, ok_response]
    ) as mock_request:
        result = client.get("/flaky")

    assert result.ok
    assert result.json_body == {"status": "recovered"}
    assert mock_request.call_count == 2


def test_unsupported_method_raises_configuration_error(client):
    from rest_engine.exceptions import ConfigurationError

    with pytest.raises(ConfigurationError):
        client.request("TRACE", "/anything")
