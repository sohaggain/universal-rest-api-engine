# Architecture

## Component Responsibilities

| Component | File | Responsibility |
|---|---|---|
| `RestClient` | `client.py` | Orchestrates a request: builds the URL, merges headers, applies auth, runs the retry-wrapped execute call, maps the raw response to `ApiResponse` or a typed exception |
| `AuthStrategy` | `auth.py` | Mutates outgoing request kwargs to add credentials. Each concrete strategy is independent and swappable |
| `ClientConfig` | `config.py` | Immutable-by-convention configuration: base URL, timeouts, retry policy, TLS verification |
| Retry helper | `retry.py` | Pure function wrapping any callable with exponential-backoff retry on a defined set of exceptions |
| Exceptions | `exceptions.py` | Typed error hierarchy so callers can branch on failure type without string-matching |
| `ApiResponse` | `models.py` | Normalized response shape decoupled from `requests.Response`, so the HTTP library could be swapped later without changing the public interface |
| Logger | `logger.py` | Attaches a `NullHandler` by default (library convention); host apps opt in to logging output |

## Design Decisions & Rationale

**Why a synchronous client, not async?**
Most of the automation contexts this is built for (n8n custom nodes, single-agent tool calls, batch sync jobs) are not high-concurrency. A sync client is simpler to reason about, test, and debug. An async variant is listed as a future improvement rather than built speculatively.

**Why retry 4xx never, but 429/5xx always?**
A 4xx (except 429) means the request itself was invalid — retrying an invalid request wastes time and can trigger rate limiting or account lockouts on the target API. 429 and 5xx are treated as transient/server-side and are safe to retry with backoff.

**Why exponential backoff with jitter instead of fixed delay?**
Fixed delays across many concurrent callers create a "thundering herd" retry spike against a recovering API. Jitter spreads retries out in time.

**Why idempotency keys are optional, not automatic?**
Only the caller knows whether the target API supports and honors an `Idempotency-Key` header. Forcing one on every request could break APIs that reject unrecognized headers.

## What This Does Not Do

- It does not implement business logic for any specific API (CRM, payments, etc.) — that belongs in a thin wrapper built on top of `RestClient`.
- It does not manage OAuth2 authorization-code flows (user-interactive login) — only client-credentials (machine-to-machine).
- It does not persist logs or metrics anywhere — it emits them via the standard `logging` module for the host application to route.
