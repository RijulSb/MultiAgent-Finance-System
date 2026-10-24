# Finance Agent Hardening Plan and Windows Test Setup

## 1. Current risk assessment

The project now has the intended architecture, but runtime verification is still pending because Python is not installed on the active Windows device.

The two highest-priority hardening areas are:

1. Confirming that the installed Agno version supports the configured output schema and expose actual specialist execution metadata.
2. Preventing model-generated prose from introducing unsupported or numerically incorrect market claims.

The deterministic API fields must remain Python-owned regardless of model behavior.

## 2. Agno output-schema hardening plan

### Step 1: Install the pinned environment before changing framework code

Do not infer Agno API compatibility from source inspection alone. Install the pinned versions and run a smoke check first.

```powershell
cd C:\Users\USER\Desktop\MULTI_FINANCE_AGENT
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pip show agno groq pydantic
```

Record the exact installed versions:

```powershell
python -m pip freeze | Out-File .work\installed-freeze.txt -Encoding utf8
```

### Step 2: Verify the Team constructor contract

Confirm that the pinned Agno version accepts:

```python
Team(
    name="Financial Insights Team",
    mode="coordinate",
    model=model,
    members=[market, news, reviewer],
    output_schema=SynthesisResponse,
)
```

If the installed version rejects `output_schema`, do not silently fall back to free-form output. Treat the configuration as unsupported and return a safe startup/configuration error. The PRD explicitly requires tool gathering and schema-constrained synthesis to be separated when the provider supports that mode.

### Step 3: Use a strict synthesis schema

Keep the leader output limited to fields that can be deterministically validated:

```python
class SynthesisResponse(BaseModel):
    summary: str = Field(max_length=2_000)
    reported_developments: list[Claim] = Field(max_length=5)
    interpretations: list[Claim] = Field(max_length=5)
    warnings: list[str] = Field(max_length=20)
```

Recommended additional constraints:

- `summary` must be qualitative and must not introduce new numeric market values.
- Every reported or interpretive claim must contain at least one evidence ID.
- Every evidence ID must exist in the request-local registry.
- No user-provided source IDs are accepted.
- No additional fields are accepted: use `ConfigDict(extra="forbid")` on synthesis models.
- Do not include hidden reasoning, chain-of-thought, or unconstrained explanation fields.

### Step 4: Separate tool gathering from synthesis

Use two distinct phases:

1. **Evidence phase:** the Agno team delegates to Market Analyst, News Researcher, and Evidence Reviewer through scoped tools.
2. **Synthesis phase:** a separate schema-constrained model request receives only a compact evidence package and produces `SynthesisResponse`.

Count both phases in the aggregate model budget. Do not pass full provider histories or unrestricted external text into synthesis.

### Step 5: Add a bounded repair path

If schema parsing fails:

1. Check the remaining model, token, provider, and deadline budgets.
2. Permit one repair request with the validation error category only.
3. Parse the repair response against the same schema.
4. If it fails again, return `partial` or `unavailable` without using free-form output.

Never loop indefinitely and never repair by asking the model to reveal reasoning.

## 3. Agno execution-receipt hardening plan

### Receipt requirement

A full `ok` report requires verified framework participation by:

- Market Analyst.
- News Researcher.
- Evidence Reviewer.

Application counters such as “delegation requested” are not receipts.

### Receipt adapter

Implement one narrow adapter around the pinned Agno response shape:

```text
Agno response/event metadata
        ↓
receipt adapter
        ↓
SpecialistReceipt(agent, status, framework_source)
        ↓
status policy
```

The adapter should inspect documented framework fields such as member responses, run messages, or event records. It must not infer execution from model prose alone.

### Receipt validation rules

- Require exactly one observed receipt for each required specialist, or a documented framework event proving invocation.
- Mark missing or failed members explicitly.
- Preserve the framework source field used to establish the receipt.
- Set report status to `partial` when any required receipt is missing.
- Set report status to `ok` only after synthesis, evidence review, and all receipts pass.
- Add fixture tests for complete, missing, duplicate, and failed receipt payloads.

### Receipt compatibility test

Run a mocked Agno response fixture first. Then run one controlled provider smoke test with valid credentials. Compare the actual response shape with the adapter assumptions and update the adapter deliberately if the pinned framework version differs.

## 4. Numeric prose validation plan

### Principle

Python owns all numeric API fields. The model may summarize evidence but cannot alter calculated values.

### Preferred design: structured metrics, qualitative summary

Keep these fields outside synthesis and attach them after synthesis from `MarketReport`:

- Latest close.
- Five-session change.
- Twenty-session change.
- Session dates.
- Observation counts.
- Currency and return basis.

Require the leader `summary` to be qualitative. This is safer than allowing arbitrary numbers in prose.

### If numeric prose is allowed

Implement a numeric validator with these stages:

1. Extract numeric tokens, percentages, currency values, and session counts from the synthesis text.
2. Build an allowlist of canonical renderings from the Python-owned `MarketReport`, including permitted rounding forms.
3. Compare every detected numeric token with the allowlist.
4. If a number does not correspond to an allowed Python-owned value, remove the sentence or reject the synthesis.
5. Never replace a Python-owned response field with a model value.
6. Add a validation event recording the category of mismatch without storing hidden reasoning.

### Required numeric tests

Add fixtures for:

- Model changes `5.0%` to `50%`.
- Model reports a different latest close.
- Model invents a twenty-session value when it is null.
- Model inserts an unsupported currency amount.
- Model uses a number that is correct but outside the permitted presentation rounding.
- Model writes a causal sentence containing a valid number but unsupported interpretation.

Expected behavior: the numerical API fields remain unchanged and invalid prose is removed, qualified, or causes a safe `partial` response.

## 5. Final status policy

Use this decision order:

1. If required market evidence is unavailable: `unavailable`.
2. If no usable news investigation result exists: `partial` or `unavailable`, never “no news” without evidence.
3. If any claim fails evidence validation: remove it and set `partial` when useful evidence remains.
4. If any specialist receipt is missing: cannot be `ok`.
5. If synthesis parsing or numeric validation fails: return a safe partial report without unvalidated model prose.
6. Only return `ok` when market metrics, news investigation, review, synthesis, and all required receipts pass.

## 6. Complete Windows setup instructions

### A. Install Python

Install Python 3.11 or newer using one of these approaches:

**Python.org installer:**

1. Download the Windows installer for Python 3.11 or 3.12.
2. Enable **Add Python to PATH**.
3. Install the Python Launcher.
4. Open a new PowerShell window.

Verify:

```powershell
py -3.11 --version
python --version
```

If the `py` command is not available, repair the installation and ensure the launcher/PATH options are enabled.

### B. Create the virtual environment

```powershell
cd C:\Users\USER\Desktop\MULTI_FINANCE_AGENT
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Confirm the active interpreter:

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

The executable should point inside:

```text
C:\Users\USER\Desktop\MULTI_FINANCE_AGENT\.venv\Scripts\python.exe
```

### C. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest
```

Verify:

```powershell
python -m pip show agno groq fastapi uvicorn pydantic yfinance ddgs pytest
python -m pip freeze
```

Do not silently change pinned versions if installation fails. Record the failure, identify the compatibility issue, and update `requirements.txt` deliberately after testing.

### D. Configure local variables

For deterministic tests:

```powershell
$env:APP_API_KEY = "local-development-secret-change-me"
$env:MARKET_AGENT_DB = "market_agent_test.sqlite3"
```

For controlled Agno/Groq smoke tests:

```powershell
$env:GROQ_API_KEY = "your-groq-key"
$env:GROQ_MODEL = "openai/gpt-oss-20b"
```

Never place real credentials in source files, test fixtures, prompts, logs, or response bodies.

### E. Run syntax compilation

```powershell
python -m py_compile market_agent.py test_market_agent.py run_market_agent.py
```

### F. Run the complete pytest suite

```powershell
python -m pytest -q
```

Run with full test names and tracebacks:

```powershell
python -m pytest -vv -rA
```

Run the newly added hardening tests:

```powershell
python -m pytest -q test_market_agent.py -k "filter_reviewed_claims or synthesis_validation or specialist_receipts"
```

Stop and fix any failure before running live-provider smoke tests.

### G. Run the local API

```powershell
python run_market_agent.py
```

Open:

```text
http://127.0.0.1:8000/docs
```

### H. Run a controlled authenticated request

In another PowerShell window:

```powershell
$headers = @{
  "X-API-Key" = "local-development-secret-change-me"
  "Idempotency-Key" = "diagnostic-msft-20261021"
}

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/analyze `
  -Headers $headers `
  -ContentType "application/json" `
  -Body '{"symbol":"MSFT","news_days":7}'
```

Confirm that:

- The response contains a request ID.
- Numeric market fields come from deterministic calculation.
- Rejected claims are absent from returned claim lists.
- `execution.specialist_receipts` is present.
- A missing provider or receipt produces `partial`/`unavailable`, not a fabricated `ok` report.

## 7. Acceptance gates after hardening

Before declaring the project complete:

- `pytest` passes all deterministic and integration tests.
- `py_compile` succeeds.
- The pinned Agno Team schema path works in a controlled smoke test.
- Actual framework receipts are observed for all three specialists.
- Numeric prose mutation tests pass.
- Rejected claims never appear in final response lists.
- A malformed schema response becomes a safe partial/unavailable result.
- No secret, stack trace, hidden reasoning, or unsupported source ID appears in output.
- PRD acceptance scenarios A01–A22 are covered or explicitly marked with a justified limitation.
