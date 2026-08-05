import pytest

from rest_engine.auth import ApiKeyAuth, BasicAuth, BearerTokenAuth, NoAuth
from rest_engine.exceptions import AuthenticationError


def test_no_auth_does_not_modify_request():
    kwargs = {"headers": {}}
    result = NoAuth().apply(dict(kwargs))
    assert result == kwargs


def test_api_key_auth_header():
    auth = ApiKeyAuth(key="secret123", name="X-API-Key", location="header")
    kwargs = auth.apply({})
    assert kwargs["headers"]["X-API-Key"] == "secret123"


def test_api_key_auth_query():
    auth = ApiKeyAuth(key="secret123", name="api_key", location="query")
    kwargs = auth.apply({})
    assert kwargs["params"]["api_key"] == "secret123"


def test_api_key_auth_rejects_empty_key():
    with pytest.raises(AuthenticationError):
        ApiKeyAuth(key="")


def test_bearer_token_auth_sets_header():
    auth = BearerTokenAuth(token="abc.def.ghi")
    kwargs = auth.apply({})
    assert kwargs["headers"]["Authorization"] == "Bearer abc.def.ghi"


def test_basic_auth_sets_tuple():
    auth = BasicAuth(username="user", password="pass")
    kwargs = auth.apply({})
    assert kwargs["auth"] == ("user", "pass")


def test_basic_auth_requires_username():
    with pytest.raises(AuthenticationError):
        BasicAuth(username="", password="pass")
