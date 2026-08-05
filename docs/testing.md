# Testing

## Strategy

| Level | Location | What it covers | Network required |
|---|---|---|---|
| Unit | `tests/unit/` | Auth strategies, retry backoff behavior, request/response mapping, error classification, config validation | No (HTTP layer mocked via `unittest.mock`) |
| Integration | `tests/integration/` | Real GET/POST/DELETE against a public test API, marked `integration` | Yes |

## Commands

```bash
# Fast local loop — no network needed
pytest tests/unit -m "not integration" -v

# With coverage
pytest tests/unit -m "not integration" --cov=rest_engine --cov-report=term-missing

# Integration suite (requires outbound network access)
pytest tests/integration -m integration
```

## Verified Results (this run)

```
17 passed in 1.95s
Coverage: 78% overall
  auth.py     60%  (OAuth2 token-fetch path not covered by unit tests — see below)
  client.py   84%
  config.py   76%
  exceptions  100%
  logger.py   45%  (configure_default_logging() is a dev convenience, not exercised in CI)
  models.py   100%
  retry.py    96%
```

## Known Coverage Gaps

- `OAuth2ClientCredentials._fetch_token()` makes a real HTTP call and is not covered by a unit test in this version — it should be tested with a mocked `requests.post` before being used against a production OAuth2 provider.
- `configure_default_logging()` is a local-dev convenience and intentionally untested (no behavior beyond stdlib logging configuration).

## What Is Explicitly Tested

- All 5 HTTP verbs delegate to `request()` with the correct method
- 4xx responses raise `ApiClientError` and do **not** trigger a retry (single call)
- 5xx/429 responses trigger retries up to `max_retries`, then raise `RetryExhaustedError`
- A transient failure followed by a success returns the successful `ApiResponse`
- Unsupported HTTP methods raise `ConfigurationError` before any network call
- Each `AuthStrategy` correctly mutates request kwargs (headers/params/auth tuple)
- Empty/invalid credentials raise `AuthenticationError` at construction time, not at request time
