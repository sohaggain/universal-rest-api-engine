"""End-to-end usage example against a public test API (jsonplaceholder).

Run:
    python examples/example_usage.py
"""

import logging

from rest_engine import (
    ApiClientError,
    ApiServerError,
    BearerTokenAuth,
    ClientConfig,
    RestClient,
    RetryExhaustedError,
)
from rest_engine.logger import configure_default_logging

configure_default_logging(level=logging.INFO)


def main() -> None:
    config = ClientConfig(
        base_url="https://jsonplaceholder.typicode.com",
        timeout_seconds=10,
        max_retries=3,
    )

    # Swap in real credentials via environment variables in production;
    # NoAuth is used here since this public test API needs no auth.
    client = RestClient(config=config)

    # GET
    response = client.get("/posts/1")
    print("GET /posts/1 ->", response.status_code, response.json_body)

    # POST
    response = client.post(
        "/posts",
        json={"title": "Universal REST Engine", "body": "Demo post", "userId": 1},
    )
    print("POST /posts ->", response.status_code, response.json_body)

    # PUT
    response = client.put(
        "/posts/1",
        json={"id": 1, "title": "Updated title", "body": "Updated body", "userId": 1},
    )
    print("PUT /posts/1 ->", response.status_code, response.json_body)

    # PATCH
    response = client.patch("/posts/1", json={"title": "Patched title"})
    print("PATCH /posts/1 ->", response.status_code, response.json_body)

    # DELETE
    response = client.delete("/posts/1")
    print("DELETE /posts/1 ->", response.status_code)

    # Example error handling
    try:
        client.get("/posts/999999999")
    except ApiClientError as exc:
        print(f"Handled expected client error: {exc.status_code}")
    except ApiServerError as exc:
        print(f"Handled server error: {exc.status_code}")
    except RetryExhaustedError as exc:
        print(f"Retries exhausted: {exc}")


if __name__ == "__main__":
    main()
