# Market Brief Multi-Agent Finance Agent

A bounded, read-only financial research API built from the Market Brief PRD. The prototype accepts one supported US-listed symbol, computes recent daily-session performance deterministically, and exposes an evidence-linked FastAPI response. When Groq and Agno are configured, the application also constructs a coordinate-mode Agno team with a Market Analyst, News Researcher, and Evidence Reviewer.

This is an educational/personal research prototype. It is not a trading platform, investment adviser, price-forecasting system, or source of personalized investment advice.

## Batch 1 deliverables

- `market_agent.py`: the single authored application source. It contains typed API contracts, authentication, idempotency persistence, deterministic return calculations, evidence hashing, budget guards, health/analyze endpoints, and the Agno team boundary.
- `requirements.txt`: pinned initial dependency set from the PRD. Framework APIs and model/tool compatibility still require verification in the target environment.
- `README.md`: setup and design notes.

Later batches should add deterministic fixture tests, bounded news/provider adapters, complete Agno tool wiring and synthesis validation, and security/reliability smoke coverage without splitting application logic into multiple authored runtime modules.

## Run locally

Use Python 3.11 or newer, create a virtual environment, install the manifest, and configure credentials through environment variables only:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:APP_API_KEY = "replace-with-a-local-secret"
$env:GROQ_API_KEY = "replace-with-your-groq-key"  # optional for deterministic-only tests
$env:GROQ_MODEL = "openai/gpt-oss-20b"
uvicorn market_agent:app --host 127.0.0.1 --port 8000 --workers 1
```

The application uses a local SQLite file named `market_agent.sqlite3` by default. Set `MARKET_AGENT_DB` to change it. `SUPPORTED_SYMBOLS` can replace the small default allowlist during local testing.

Example request:

```powershell
$headers = @{
  "X-API-Key" = $env:APP_API_KEY
  "Idempotency-Key" = "demo-msft-20261021"
}
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/analyze `
  -Headers $headers -ContentType "application/json" `
  -Body '{"symbol":"MSFT","news_days":7}'
```

## Design constraints

The server owns authentication, symbol and body validation, rate/budget boundaries, SQLite idempotency, evidence registration, deterministic numeric fields, and final status policy. External provider text is data, never an instruction. No user-supplied URLs, shell commands, broker operations, portfolio holdings, or arbitrary prompts are accepted.

Returns use one consistent adjusted-close basis and preserve the actual metric dates and observation count. A five-session change requires six valid closes; a twenty-session change requires twenty-one. Missing data is represented as `null` with a warning instead of being forward-filled or invented. The latest quoted close is kept separate from the adjusted series when available.

The current first batch intentionally reports news and model synthesis as explicit limitations unless their providers are fully configured. It does not claim that an observed news item caused a price movement. The PRD requires real specialist participation for a successful full report; later batches must add the restricted tools and evidence-review gates before changing the success policy.

## API surface

- `GET /health` is liveness-only and performs no provider call.
- `GET /docs` exposes local FastAPI documentation.
- `POST /analyze` requires `X-API-Key` and a validated `Idempotency-Key`. The request is limited to `symbol` and `news_days`.

The response includes status (`ok`, `partial`, or `unavailable`), deterministic market fields, warnings, source registry entries, review state, and execution metadata. Internal exceptions and credentials are not returned to clients.

## Safety and deployment note

The default single-key authentication and in-process limits are suitable only for a local prototype. Public deployment requires HTTPS, protected documentation, a proper identity model, shared rate limiting, market-data licensing, provider review, and additional operational/security testing.
