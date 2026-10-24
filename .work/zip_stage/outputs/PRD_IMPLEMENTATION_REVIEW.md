# Market Brief Multi-Agent Finance Agent
## Full PRD implementation review and local test setup

Review scope: current `market_agent.py`, `test_market_agent.py`, `run_market_agent.py`, the pinned dependency manifest, and the complete Market Brief PRD.

## 1. Executive assessment

The project has a credible deterministic foundation and the intended single-source architecture is present. The current code includes typed FastAPI contracts, strict request fields, authentication, SQLite idempotency records, deterministic price-return calculations, bounded news discovery, per-request evidence registration, scoped Agno tools, a coordinate-mode Team definition, operational logging, and local fixture tests.

It is not yet Definition-of-Done complete. The most important blockers are:

1. Rejected claims are detected by `review_claims()` but are not removed from `reported_developments` before the response is returned.
2. The Agno team output is executed but ignored; no schema-constrained synthesis result is parsed, validated, or attached to the final brief.
3. Required specialist participation is represented by intended delegation counters rather than verified framework execution receipts.
4. The cache table exists but is not used for price evidence, news evidence, or final-report caching.
5. Rate limiting, concurrent-analysis limits, lease recovery, structured error handlers, and the required 429/504 behavior are incomplete.
6. Completed-session handling, exchange-local timezone handling, and current-bar exclusion are not implemented robustly.
7. Python is not installed on the active Windows device, so the test suite has not yet been executed.

The current implementation should therefore be described as a Batch 3 prototype foundation, not as a fully acceptance-tested finance agent.

## 2. Evidence-review validation audit

### Current behavior

`review_claims(registry, claims)` performs these checks:

- Resolves every `source_id` against the request-local `EvidenceRegistry`.
- Reports unknown IDs as review issues.
- Requires an evidence ID for interpretation claims.
- Flags causal or predictive terms including `caused`, `because of`, `led to`, `will make`, `will rise`, and `will fall`.
- Returns `rejected` when any issue exists.

The request-local registry is a good boundary for preventing a reviewer from resolving an arbitrary ID from another request. The Agno reviewer tool also returns an error for an ID that is not present in the current registry.

### Critical defect

In `analyse()`, the code builds `reported` claims, calls `review_claims()`, and appends review issues to warnings. However, it still returns the original `reported` list even when the review is `rejected`.

The PRD explicitly requires rejected claims to be removed before delivery. The current behavior can therefore produce a `partial` response containing a claim that deterministic review rejected.

Required correction:

```python
review = review_claims(registry, reported)
if review.status == "rejected":
    reported = []
    warnings.extend(review.issues)
```

A stronger implementation should return a filtered result from the validator, for example `(accepted_claims, review_result)`, so callers cannot accidentally deliver the unfiltered draft.

### Additional review gaps

The validator should also be extended to:

- Validate that every claim's source IDs are unique.
- Verify that a reported claim references a news source and a calculated claim references market evidence.
- Check that every returned source ID is present in the response `sources` collection.
- Reject empty claim text after normalization.
- Detect numeric prose that disagrees with Python-owned market metrics.
- Reject unsupported causal language rather than merely warning about it.
- Validate interpretation wording and require qualified language such as “may,” “could,” or “is consistent with,” without treating those words as proof.
- Return accepted and rejected claims separately for auditability.

## 3. Deterministic calculation review

The implementation correctly uses:

```text
N-session return (%) = 100 × (P_t / P_(t-N) − 1)
```

where `P` is the adjusted close.

The current tests cover:

- Six valid closes for a five-session return.
- Twenty-one valid closes for a twenty-session return.
- Insufficient history at five and twenty sessions.
- Unsorted bars.
- Flat adjusted prices.
- Adjusted-close versus quoted-close separation.
- Duplicate dates.
- Zero prices.
- NaN prices.

The current implementation also preserves the latest quoted close separately and reports the return basis.

Remaining calculation work from the PRD:

- Exclude an unfinished current exchange-local-date bar.
- Determine completed sessions with exchange-local time and validated session metadata.
- Preserve actual exchange timezone and currency in `MarketReport`.
- Handle yfinance column-shape variations, including MultiIndex output.
- Reject missing adjusted-close values rather than allowing provider conversion errors to become generic failures.
- Add a split-adjusted fixture with an explicit convention test.
- Add a provider fixture containing a current incomplete bar and assert that it is excluded.
- Avoid treating calendar days as sessions in production fixtures; test with actual trading-session dates.
- Preserve full internal precision and round only at the API presentation boundary.

## 4. Current FastAPI and Pydantic review

The following contracts are present:

- `AnalyzeRequest` with `extra="forbid"`.
- Uppercase symbol normalization.
- `news_days` constrained to 1 through 7.
- `Source`, `Claim`, `NewsItem`, `NewsEvidence`, `MarketReport`, `ReviewResult`, `ExecutionMeta`, and `AnalyzeResponse`.
- `GET /health`.
- `POST /analyze`.
- Local `/docs` through FastAPI.

The endpoint requires `X-API-Key` and `Idempotency-Key`, checks the body size header, and stores request state in SQLite.

Remaining API work:

- Add safe custom exception handlers so all errors use the PRD's `{error_code, request_id, message}` shape.
- Avoid exposing raw FastAPI validation details where the PRD requires safe concise errors.
- Add explicit 429 rate-limit responses.
- Add explicit 504 deadline responses.
- Add explicit 503 behavior when no usable report exists.
- Validate `Content-Length` defensively and handle malformed header values.
- Ensure idempotency insertion is atomic under concurrent requests rather than relying only on `INSERT OR REPLACE`.
- Persist failed terminal results as `state='failed'` and replay them for the retention period.
- Implement abandoned in-progress lease recovery.

## 5. Agno orchestration review

Present:

- Three named specialist agents.
- Groq-backed model construction.
- Coordinate-mode Team definition.
- Scoped tools for market data, metric computation, news search, and request-local evidence lookup.
- A bounded `run_team_orchestration()` call.
- A model request budget counter.
- Operational trace events.

Not yet sufficient for the PRD Definition of Done:

- The team result is discarded instead of parsed into a structured final brief.
- There is no schema-constrained synthesis model or repair attempt.
- Tool execution receipts are not collected from actual Agno framework events.
- Delegation counters are incremented by application code and do not prove that each member ran.
- The reviewer is not guaranteed to receive the complete market/news evidence package through the framework.
- The final model output is not checked for invented source IDs or altered numeric fields.
- The model identifier, prompt/schema version, input tokens, output tokens, and cost estimate are not captured.
- The application does not separate tool-gathering turns from schema-constrained synthesis as required by the PRD.

Required next implementation:

1. Define a Pydantic synthesis schema.
2. Run tool-capable specialist turns first.
3. Collect actual framework receipts for Market Analyst, News Researcher, and Evidence Reviewer.
4. Perform a separate constrained synthesis request.
5. Validate all claim IDs, numeric fields, evidence levels, and review status deterministically.
6. Remove or qualify invalid claims before returning the response.
7. Permit at most one bounded structured-output repair.

## 6. Persistence, cache, rate, and budget gaps

The SQLite schema includes `requests`, `cache`, and `evidence`, but only request and evidence records are currently used.

Still required:

- Price-evidence cache with 15-minute TTL.
- News-evidence cache with 15-minute TTL.
- Final-report cache with 5-minute TTL.
- Cache keys containing normalized inputs, model identifier, prompt/schema version, and analysis session.
- Preservation of original `retrieved_at` and `data_as_of` values.
- Seven-day audit metadata retention and cleanup.
- Ten analyses per hour per principal.
- Maximum two concurrent analyses per process.
- Expiring leases for abandoned requests.
- Safe reclaim behavior after lease expiry.
- Explicit retry policy for transient provider failures, limited to one retry.
- Aggregate model token ceilings of 24,000 input and 4,000 output tokens.
- Individual prompt/output bounds.
- Provider-call and model-call counters connected to actual work.
- No additional call after budget exhaustion.

## 7. News-wrapper review

Implemented correctly at a prototype level:

- Server-created query.
- Maximum 10 candidates.
- Maximum 5 retained items.
- Canonical URL normalization.
- Normalized-title deduplication.
- HTML stripping and bounded snippets.
- Publication-window filtering.
- Explicit `news_unavailable` versus empty results.
- No full-article fetching.

Remaining work:

- Add relevance filtering beyond the query itself and symbol presence.
- Add provider timeout handling around the DDGS call.
- Add a typed provider error category for timeout, rate limit, and malformed output.
- Add tests for prompt-injection text in snippets.
- Ensure provider metadata and retrieval time are always preserved.
- Verify the installed DDGS API against the pinned version.

## 8. PRD acceptance matrix status

| ID | Scenario | Current status |
|---|---|---|
| A01 | Six known closes | Covered by fixture tests |
| A02 | Fewer than 21 closes | Covered in calculation tests; API warning path needs integration test |
| A03 | Split-adjusted fixture | Partially covered by adjusted/quoted separation; dedicated split fixture remains |
| A04 | Unfinished current session | Not implemented |
| A05 | Duplicate/invalid prices | Covered |
| A06 | Invalid symbol/unknown fields | Model-level behavior exists; endpoint/provider-call test remains |
| A07 | Irrelevant/undated news | Dated/undated filtering covered; relevance test remains |
| A08 | Search outage | Code returns `news_unavailable`; endpoint integration test remains |
| A09 | Injection in snippet | Not yet tested |
| A10 | Invented source ID | Validator unit test covered |
| A11 | Model alters price | Not implemented; final model-output validation required |
| A12 | Concurrent duplicate key/body | Schema exists; concurrency test and atomic-claim proof remain |
| A13 | Same key/different body | Endpoint branch exists; integration test remains |
| A14 | Provider timeout/quota | Generic safe fallback exists; typed error and status tests remain |
| A15 | Missing reviewer delegation | Not enforced from actual framework receipts |
| A16 | Budget exhaustion | Budget counters exist; no complete call-boundary test |
| A17 | Unsupported causal assertion | Validator detects terms; rejected claims are not yet removed |
| A18 | Unauthorized evidence lookup | Request-local registry exists; cross-request test remains |
| A19 | Expired cache | Cache table exists but cache behavior is not implemented |
| A20 | Tool/output compatibility | Not verified against installed Agno/Groq versions |
| A21 | Public auth/rate limit | Authentication exists; rate limit is not implemented |
| A22 | Agent execution metadata | Operational events exist; actual framework receipts/token usage are not connected |

## 9. Python environment setup on Windows

The active device currently does not have a Python runtime. Install Python 3.11 or newer first.

### Option A: python.org installer

1. Download Python 3.11 or 3.12 for Windows from python.org.
2. During installation, enable **Add Python to PATH** and install the Python Launcher.
3. Open a new PowerShell window.
4. Verify:

```powershell
py -3.11 --version
python --version
```

### Create and activate a virtual environment

From the project directory:

```powershell
cd C:\Users\USER\Desktop\MULTI_FINANCE_AGENT
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
python -m pip install --upgrade pip
```

If PowerShell blocks activation for the current user, use the current-process-only policy change:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Install pinned dependencies

```powershell
python -m pip install -r requirements.txt
python -m pip install pytest
```

The current manifest pins:

- `agno==1.8.4`
- `groq==0.31.0`
- `fastapi==0.116.1`
- `uvicorn[standard]==0.35.0`
- `pydantic==2.11.7`
- `yfinance==0.2.65`
- `ddgs==9.5.5`

The PRD requires these versions to be verified as a compatible set. If installation reports that a specific version is unavailable or incompatible, do not silently change the manifest; record the failure, test the smallest compatible adjustment, and update the pinned file deliberately.

### Configure local environment variables

PowerShell session configuration:

```powershell
$env:APP_API_KEY = "local-development-secret-change-me"
$env:GROQ_API_KEY = "your-groq-key"       # optional for deterministic tests
$env:GROQ_MODEL = "openai/gpt-oss-20b"
$env:MARKET_AGENT_DB = "market_agent_test.sqlite3"
```

For deterministic unit tests, `GROQ_API_KEY` is not required. Provider-backed smoke tests require valid credentials and appropriate data-provider terms.

### Run pytest

```powershell
python -m pytest -q
```

Run only deterministic fixtures:

```powershell
python -m pytest -q test_market_agent.py
```

Run with detailed output:

```powershell
python -m pytest -q -vv
```

Compile the application without running providers:

```powershell
python -m py_compile market_agent.py test_market_agent.py run_market_agent.py
```

### Run the API locally

```powershell
python run_market_agent.py
```

Then open local documentation at `http://127.0.0.1:8000/docs`.

Example request from another PowerShell window:

```powershell
$headers = @{
  "X-API-Key" = "local-development-secret-change-me"
  "Idempotency-Key" = "demo-msft-20261021"
}

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/analyze `
  -Headers $headers `
  -ContentType "application/json" `
  -Body '{"symbol":"MSFT","news_days":7}'
```

## 10. Recommended remaining implementation order

### Remaining Batch 4: validation and safe delivery

- Filter rejected claims before response construction.
- Add deterministic validation of model-generated numeric prose.
- Add synthesis Pydantic schema and one repair attempt.
- Add cross-request evidence lookup tests.
- Add injection-in-snippet tests.

### Remaining Batch 5: provider and market correctness

- Implement completed-session logic and exchange-local timezone handling.
- Add robust yfinance frame normalization and typed provider errors.
- Add dedicated split-adjusted and incomplete-current-bar fixtures.
- Add DDGS timeout/rate-limit classification and relevance filtering.

### Remaining Batch 6: persistence and reliability

- Implement cache read/write/expiry behavior.
- Add atomic idempotency claims and lease recovery.
- Add failed-request replay semantics.
- Add per-principal hourly rate limits and two-request concurrency guard.
- Add safe exception handlers for 401, 409, 422, 429, 503, and 504.

### Remaining Batch 7: genuine Agno completion

- Verify exact installed Agno coordinate-mode API.
- Verify Groq tool-call and structured-output behavior.
- Capture actual member execution receipts.
- Separate evidence-gathering turns from synthesis.
- Enforce all-three-specialist participation before `status="ok"`.
- Attach validated synthesized summary and interpretations.

### Remaining Batch 8: acceptance and smoke testing

- Run all A01-A22 tests.
- Add a golden request/failure set.
- Run limited live-provider smoke tests separately from fixture tests.
- Confirm no credentials, stack traces, hidden reasoning, or invented citations appear in responses.
- Record dependency versions, model ID, observed token usage, latency, provider failures, and cache behavior.

## 11. Definition-of-done checklist

The project is ready to claim PRD completion only when all of the following are true:

- Python environment installs the pinned dependency set.
- `pytest` passes all deterministic and integration fixtures.
- A real authenticated request enters an Agno coordinate-mode Team.
- Market Analyst, News Researcher, and Evidence Reviewer all produce actual execution receipts.
- The leader returns a schema-constrained brief.
- Python validates source IDs, numeric fields, status policy, and claim safety.
- Rejected claims are removed or explicitly qualified before delivery.
- SQLite prevents duplicate concurrent work.
- Cache TTLs and lease recovery behave as specified.
- Rate limits, deadlines, budgets, and safe error responses are tested.
- No successful report depends on fabricated prices, invented citations, unrestricted browsing, broker actions, or guaranteed-live claims.
