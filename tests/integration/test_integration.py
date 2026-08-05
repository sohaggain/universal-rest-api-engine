"""Integration tests that hit a real public test API.

Marked so they can be excluded from fast local/unit runs:
    pytest -m "not integration"

Run explicitly with:
    pytest tests/integration -m integration
"""

import pytest

from rest_engine.client import RestClient
from rest_engine.config import ClientConfig

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    config = ClientConfig(base_url="https://jsonplaceholder.typicode.com", max_retries=2)
    return RestClient(config=config)


def test_get_real_resource(client):
    response = client.get("/posts/1")
    assert response.ok
    assert response.json_body["id"] == 1


def test_post_real_resource(client):
    response = client.post(
        "/posts", json={"title": "test", "body": "content", "userId": 1}
    )
    assert response.status_code == 201
    assert response.json_body["title"] == "test"


def test_delete_real_resource(client):
    response = client.delete("/posts/1")
    assert response.ok
