# Library API Reference

This is a client library, not a hosted API — this document describes the Python
public interface (`from rest_engine import ...`).

## `ClientConfig`

```python
ClientConfig(
    base_url: str,
    default_headers: dict[str, str] = {},
    timeout_seconds: float = 15.0,
    connect_timeout_seconds: float = 5.0,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    retry_on_status: tuple = (429, 500, 502, 503, 504),
    verify_ssl: bool = True,
    user_agent: str = "universal-rest-api-engine/0.1.0",
)
```

`ClientConfig.from_env(prefix="REST_ENGINE_")` builds a config from environment variables (see `.env.example`).

## `RestClient`

```python
client = RestClient(config: ClientConfig, auth: AuthStrategy = NoAuth(), session: requests.Session | None = None)
```

### Methods

All five return an `ApiResponse` or raise a typed exception (see `docs/architecture.md`).

```python
client.get(path, params=None, headers=None, timeout_seconds=None) -> ApiResponse
client.post(path, json=None, data=None, params=None, headers=None, idempotency_key=None, timeout_seconds=None) -> ApiResponse
client.put(path, json=None, data=None, params=None, headers=None, idempotency_key=None, timeout_seconds=None) -> ApiResponse
client.patch(path, json=None, data=None, params=None, headers=None, idempotency_key=None, timeout_seconds=None) -> ApiResponse
client.delete(path, params=None, headers=None, timeout_seconds=None) -> ApiResponse
```

`path` may be a relative path (joined to `config.base_url`) or a full URL (used as-is — useful for following `next` links in paginated responses).

### `ApiResponse`

```python
@dataclass
class ApiResponse:
    status_code: int
    url: str
    headers: dict[str, str]
    elapsed_ms: float
    json_body: Any | None
    text_body: str | None
    request_id: str | None

    @property
    def ok(self) -> bool  # True for 2xx
```

## Example: paginating with a `next` URL

```python
response = client.get("/items")
while response.json_body.get("next"):
    response = client.get(response.json_body["next"])  # full URL passed straight through
```

## Example: idempotent POST

```python
import uuid
key = str(uuid.uuid4())
client.post("/charges", json={"amount": 500}, idempotency_key=key)
# Safe to retry with the same key if the caller times out waiting for the response.
```
