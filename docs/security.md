# Security

## Implemented Controls

| Concern | Control |
|---|---|
| Secrets in source | No credentials hardcoded anywhere in `src/`. `.env` is git-ignored; `.env.example` has no real values. |
| Secrets in logs | Log statements include method, URL, status, and request ID — never headers or bodies, so tokens/keys are never written to logs. |
| Transport security | `verify_ssl=True` by default; disabling it requires an explicit config change. |
| Credential exposure via retries | Retries reuse the same auth-applied request kwargs; credentials are never logged during retry warnings. |
| Token lifecycle | `OAuth2ClientCredentials` caches tokens in memory only (never written to disk) and refreshes before expiry using a configurable buffer. |
| Runaway requests | Every request has an explicit connect + read timeout — no request can hang indefinitely and block a workflow. |
| Retry storms | Exponential backoff + jitter avoids synchronized retry spikes against a struggling API. |
| Invalid input | `ClientConfig.__post_init__` validates `base_url`, `timeout_seconds`, and `max_retries` at construction time, failing fast. |
| Unsupported methods | `RestClient.request()` rejects any HTTP method outside GET/POST/PUT/PATCH/DELETE. |

## Explicitly Out of Scope (by design)

- **Webhook signature verification** — this library is an outbound client; inbound webhook handling belongs in the consuming application.
- **Secrets management** (Vault, AWS Secrets Manager, etc.) — this library accepts credentials as plain Python values; sourcing them securely is the host application's responsibility.
- **Rate-limit budgeting** — the client retries on 429 but does not track or pre-emptively throttle request volume against a known rate limit.

## Threat Considerations for Adopters

- If you use `ApiKeyAuth(location="query")`, the key will appear in logs/proxies that log full URLs (including this library's own request-start log line, which logs the URL before params are appended — review before enabling verbose logging in production).
- `OAuth2ClientCredentials` stores `client_secret` in memory for the lifetime of the `AuthStrategy` instance; ensure the process memory is appropriately protected (standard practice for any long-running credentialed service).
- This library does not sanitize `path`/`params`/`json` input — it is the caller's responsibility to validate any user-supplied data before it is sent to an external API (SSRF risk if `path` is ever built from untrusted user input as a full URL).
