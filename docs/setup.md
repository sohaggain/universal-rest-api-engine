# Setup

## Prerequisites

- Python 3.10+
- pip
- (Optional) a target REST API and credentials to test against

## Install

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Configure

```bash
cp .env.example .env
# edit .env with your target API's base URL and credentials
```

`ClientConfig.from_env()` reads `REST_ENGINE_*` variables. Auth credentials (`API_KEY`, `BEARER_TOKEN`, etc.) are read by your own application code and passed into the relevant `AuthStrategy` — this keeps the library from ever needing to know which auth scheme you're using.

## Run the example

```bash
python examples/example_usage.py
```

Note: the bundled example targets a public test API (jsonplaceholder.typicode.com). If your network environment restricts outbound domains (e.g. a sandboxed CI runner), point `ClientConfig.base_url` at an allowed API instead, or run the unit test suite, which does not require network access.

## Run tests

```bash
pytest tests/unit -m "not integration"
```
