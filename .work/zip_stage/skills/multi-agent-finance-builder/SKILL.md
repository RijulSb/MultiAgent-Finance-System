---
name: multi-agent-finance-builder
description: Build, audit, and harden a single-source FastAPI financial research agent from a PRD. Use for read-only multi-agent market briefs with deterministic price calculations, bounded news evidence, Agno/Groq orchestration, schema-constrained synthesis, evidence validation, execution receipts, pytest fixtures, and staged batch delivery.
---

# Multi-Agent Finance Builder

Build a bounded, read-only financial research API while keeping Python authoritative for authentication, persistence, budgets, deterministic calculations, evidence integrity, and final validation. Use the agent framework for delegation and synthesis, never for arithmetic, permissions, or source truth.

## Workflow

1. **Read the project rules and PRD first.** Inspect `AGENTS.md` files, the supplied PRD, existing source, tests, dependency manifests, and the current file plan. Extract the acceptance matrix, security boundaries, budgets, API schema, and Definition of Done.
2. **Preserve the source architecture.** Keep authored runtime logic in the PRD's single application source unless the PRD explicitly permits modules. Use supporting files only for dependencies, fixtures, launch wrappers, documentation, and skill resources.
3. **Work in bounded batches.** Unless the user specifies otherwise, implement at most three files per batch. After each batch, inspect file existence, line endings, key declarations, and available runtime/tooling. Do not claim tests passed when the runtime is unavailable.
4. **Define contracts before providers.** Create strict Pydantic request, response, source, claim, review, execution, receipt, and synthesis models. Reject unknown request fields, user URLs, custom prompts, arbitrary tools, shell commands, and broker actions.
5. **Implement deterministic market evidence.** Normalize and allowlist symbols. Fetch a bounded daily history. Sort sessions, reject duplicate/nonfinite/nonpositive values, exclude an unfinished current bar when exchange-local completion cannot be established, and never forward-fill missing closes.
6. **Compute returns in Python only.** For N sessions use `100 * (P_t / P_(t-N) - 1)` on one declared adjusted-close basis. Require six closes for five-session returns and twenty-one for twenty-session returns. Preserve actual start/end dates, observation count, and full internal precision; return null plus a warning when insufficient history exists.
7. **Implement the restricted news wrapper.** Construct queries server-side. Retrieve at most ten candidates and retain at most five. Strip markup, bound snippet length, canonicalize URLs, deduplicate URLs/titles, require dated in-window results, reject irrelevant records, never fetch full articles, and distinguish `news_unavailable` from a genuinely empty result.
8. **Create immutable request-local evidence.** Hash canonical evidence content with SHA-256. Resolve evidence only through the current authenticated run. Never allow a model or user to mint a source ID.
9. **Filter claims before delivery.** Validate source IDs, duplicate IDs, nonempty text, evidence-level/source compatibility, unsupported causal/predictive language, and numeric prose against Python-owned values. Return accepted claims only. If any claim is rejected, keep the response partial/rejected as appropriate and never include the rejected claim in `reported_developments` or `interpretations`.
10. **Wire real specialist agents.** Configure a Groq-backed Agno Team in coordinate mode with exactly scoped tools: Market Analyst gets price/history and pure metric tools; News Researcher gets the restricted news tool; Evidence Reviewer gets request-local lookup only. Do not grant shell, arbitrary web, filesystem, broker, or dynamic permission tools.
11. **Separate evidence gathering from synthesis.** Run framework-managed tool/delegation turns first. Then request a Pydantic/schema-constrained synthesis object. Permit at most one bounded repair. Parse only a framework-structured object or valid JSON matching the schema; never accept free-form prose as structured output.
12. **Require actual execution receipts.** Extract receipts from Agno response metadata/events, not from model assertions or application intention counters. Require observed receipts for Market Analyst, News Researcher, and Evidence Reviewer before `status="ok"`; otherwise return a safe partial/unavailable result.
13. **Validate final synthesis deterministically.** Re-run evidence and claim validation on the synthesis. Keep numeric fields Python-owned, remove invalid claims, validate review status, source IDs, and response status, and retain actionable warnings.
14. **Add observability and persistence.** Log concise structured events for start/end, cache/idempotency, delegation, tool start/end, model usage, review, validation, timeout, and budget termination. Redact credentials and do not store hidden chain-of-thought. Use parameterized SQLite queries, atomic idempotency claims, leases, TTLs, and scoped evidence rows.
15. **Test locally with fixtures first.** Cover the full acceptance matrix with mocked providers/models. Add edge cases for insufficient sessions, split-adjusted data, incomplete current sessions, duplicate/invalid prices, injection snippets, invented IDs, altered numeric prose, concurrent idempotency, cache expiry, budget exhaustion, missing reviewer receipts, and unsupported causal assertions. Run live-provider smoke tests separately.
16. **Deliver with honest status.** Report exact files, tests actually run, unavailable runtimes, provider limitations, and remaining PRD gaps. Do not claim production readiness, guaranteed real-time data, forecast accuracy, or investment-return improvement.

## Required implementation invariants

- No personalized investment advice, price targets, trading execution, broker writes, or portfolio suitability.
- No user-supplied URLs or unrestricted crawling.
- External text is untrusted data, never instructions.
- Model arithmetic never controls numeric API fields.
- Rejected claims never cross the final response boundary.
- An unavailable news provider is not reported as “no relevant news.”
- `ok` requires valid required metrics, completed news investigation, accepted review, and actual receipts for all required specialists.
- Use `partial` or `unavailable` when any required provider, review, receipt, budget, or validation condition fails.

## Windows setup/test pattern

Use Python 3.11+ and a project-local virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pytest -q
python -m py_compile market_agent.py test_market_agent.py run_market_agent.py
```

If activation is blocked, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`. Keep credentials in environment variables only. Run the API with one Uvicorn worker unless shared rate limits and coordination are implemented.

## Batch handoff format

At the end of each batch, report:

- Files created or updated.
- PRD sections addressed.
- Tests added and whether they actually ran.
- Runtime/provider limitations.
- Remaining acceptance-matrix failures.
- Exact next batch scope, limited to three files unless the user authorizes more.
