# Codebase Concerns

**Analysis Date:** 2026-10-02

## Risk Table

| Severity | Area | Evidence path | Mitigation hint |
|----------|------|---------------|-----------------|
| **Critical** | `clinical_trials` connector performs **no PII scrubbing** — persists verbatim `study` object and `brief_summary` to `raw_signals_bronze`, unlike all 7 other connectors | `backend/app/connectors/clinical_trials.py:239-276` (no `PIIPHIScrubber` import), vs `backend/app/connectors/pubmed.py:193-219` | Import and apply `PIIPHIScrubber.scrub()` to `brief_summary` and to free-text fields inside `study`; either scrub or stop persisting the whole verbatim object |
| **High** | `pii_scrubbed: True` is a **hardcoded literal** in 7 connectors — the scrubber's actual `has_pii` return value is discarded (`scrubbed, _, _ = ...`) | `backend/app/connectors/pubmed.py:219`, `newsapi.py:237`, `fda.py:240`, `ema.py:173`, `biopharma_dive.py:164`, `fierce_pharma.py:163`, `et_pharma.py:163` | Bind the real value: `scrubbed, has_pii, _ = ...` then set `"pii_scrubbed": not has_pii` (or expose match counts). The UI badge in `frontend/components/common/EvidenceDrawer.tsx:218` currently renders a constant |
| **High** | `GrokProvider` gates on classification but **never runs `PIIPHIScrubber` on evidence**, unlike `GeminiProvider` which scrubs and raises on detection — asymmetric privacy enforcement on the same egress path | `backend/app/providers/grok.py:152-168` vs `backend/app/providers/gemini.py:245-251` | Add the identical scrub-and-raise loop to `GrokProvider.generate_intelligence()`; add a `test_privacy_boundary.py` case asserting Grok rejects a PII-bearing `PUBLIC` payload |
| **High** | Plaintext demo credentials ship in source with usable defaults; the production guard does **not** check them | `backend/app/core/config.py:35-49` (8 × `DEMO_PASSWORD_*`), guard at `config.py:140-149` (checks only `SECRET_KEY`, `DEMO_MODE`, wildcard CORS) | Extend `validate_production_settings()` to reject default `DEMO_PASSWORD_*` values, `DEMO_MODE` already covered, and localhost `DATABASE_URL`/`REDIS_URL` when `is_production` |
| **High** | Model/algorithm **misattribution** — `DegradedProvider` reports `model="facebook/bart-large-cnn"` while performing string truncation, and the red-team engine is documented as BART zero-shot NLI but is a 19-rule keyword registry | `backend/app/providers/degraded.py:41-50` (no model is loaded), `backend/app/services/redteam.py:6-28` (`REDTEAM_RULES` A–S, `confidence_type="nli_heuristic"`) | Rename to an honest label (e.g. `model="truncation_v1"`, `mode="extractive_truncation"`) or implement the real model. Fabricated model identity contradicts the no-fabricated-telemetry rule |
| **Medium** | `run.py` **always binds `$PORT` even when `alembic upgrade head` fails**, so a misconfigured deploy serves traffic against an unmigrated schema while `/api/v1/health` reports healthy | `backend/run.py:14-30` (`check=False`, warning only) | Surface migration state through `/api/v1/health/ready` (fail readiness, not liveness) so Render drains the instance instead of silently serving a stale schema |
| **Medium** | Persistence failures are swallowed — `except Exception` + `logger.warning` inside upsert loops means a run can report `status="completed"` with a non-zero `signals_created` while rows were never written | `backend/app/workflows/runner.py` (development, signal, confluence loops), `backend/app/connectors/base.py:397-429` | Catch `SQLAlchemyError`/`IntegrityError` specifically and append to `state["errors"]`; the runner already has an `errors` channel feeding `pipeline_runs.errors_count` |
| **Medium** | In-memory rate limiting is **per-process** — `_rate_buckets` / `_auth_rate_buckets` are module-level dicts, so limits do not hold across concurrent Render instances | `backend/app/api/deps.py:_rate_buckets`, `_auth_rate_buckets` | Move to Redis (already optional and used for locks) with a Postgres fallback; document the limitation if multi-instance is not intended |
| **Medium** | Unbounded memory growth in the rate-limit buckets — keys are never evicted, so every distinct client IP accumulates a list for the process lifetime | `backend/app/api/deps.py` (`_rate_buckets[client]` assignment on every request) | Prune empty/stale keys on write, or bound the dict (e.g. `cachetools.TTLCache`) |
| **Medium** | Documentation materially misstates the stack | `README.md` claims `sentence-transformers` (actual: `fastembed`), `BART-Large-MNLI` zero-shot NLI (actual: rule registry), `186 tests` (actual: 219 test functions) | Regenerate the README claims from CI output, or drop numbers that are not auto-derived |
| **Medium** | `metaradar.tsx` (2,612 lines) is the **only file exempted** from the banned-class style gate, so it is the one place raw `slate-*`/hex colors can accumulate | `scripts/check-banned-classes.mjs` (`if (filePath.endsWith('metaradar.tsx')) continue`) | Extract the shell into `frontend/components/shell/` sub-components and delete the exemption |
| **Medium** | Third-party branding residue survived the "purge all Novo Nordisk" commit | `docs/NN GBS Hackathon 2026 — Kick-off.pptx` still present and still contains "Novo Nordisk"; `README.md` retains 3 hackathon references (commits `e3b93ff` claimed the purge) | Delete/rewrite the deck and README section; add a CI `grep` gate so the purge is enforceable rather than one-off |
| **Medium** | Dual PII label conventions for the same condition — `CONFIDENTIAL` from the scrubber vs `PATIENT_IDENTIFIABLE` at the Athena boundary | `backend/app/services/pii.py:71` (`classify_payload` → `CONFIDENTIAL`), `backend/app/api/v1/endpoints/signals.py:1654` (`PATIENT_IDENTIFIABLE`) | Both are correctly blocked today, but converge on one blocked label so a future allow-list edit cannot open the other |
| **Medium** | Un-promoted bronze rows can accumulate forever — a row whose silver persistence fails permanently is retried on every run and never promoted | `backend/app/workflows/runner.py` (promotion filters `failed_signal_ids`; deliberate, per the inline comment) | Add an attempt counter and a dead-letter state after N failures, or a retention job keyed on `RAW_SIGNAL_RETENTION_DAYS` (already defined but not enforced) |
| **Medium** | Optional dependency not declared — `GemmaProvider` opportunistically uses `llama-cpp-python`, which is absent from `requirements.txt` | `backend/app/providers/gemma.py:1-50`, `backend/requirements.txt` | Declare it as an optional extra (`pip install metaradar[gguf]`) or document the Ollama-only path as the supported one |
| **Medium** | No Python linter, formatter, or static type checker — backend has zero automated static analysis | no `ruff`/`black`/`mypy` config; `backend/requirements.txt` | Add `ruff` (lint + format) and run it in CI alongside pytest; the codebase already reads as if it were formatted |
| **Medium** | Engineered standards exist in two mirrored copies that can drift | `docs/rules/*` and `.agents/rules/*` (11 identical filenames) | Keep one canonical directory and symlink/reference the other, or add a CI diff check |
| **Low** | Generated contract duplication — the canonical TypeScript contract is a string template inside a Python script, and CI only diffs the emitted file | `scripts/export_openapi.py:117-124`, `frontend/types/api.ts` | Acceptable as a deliberate drift gate; note it in onboarding so contributors do not edit `frontend/types/api.ts` directly |
| **Low** | Vestigial empty test directory | `backend/tests/` (contains only `__pycache__`) | Delete it to remove an ambiguous second test root |
| **Low** | Repository directory is named `novonordisk` while all project content is MetaRadar | local path `.../Documents/novonordisk/` | Rename the checkout to avoid confusion in docs and operator runbooks |

## Tech Debt

**Verbatim upstream payload persistence (`raw_payload`):**
- Issue: `RawSignalPayload.raw_payload` stores the untouched upstream response — for `clinical_trials` that is the entire API v2 `study` object (`backend/app/connectors/clinical_trials.py:266`), and for `pubmed` a full XML fragment (`pubmed.py:222`).
- Files: `backend/app/connectors/base.py` (`RawSignalPayload`), `backend/app/models/__init__.py:RawSignalBronze.raw_payload`
- Impact: bronze growth is unbounded and proportional to upstream payload size, and every unscrubbed field becomes a PII exposure surface. `RAW_SIGNAL_RETENTION_DAYS=30` is defined in `backend/app/core/config.py` but **no enforcement job exists**.
- Fix approach: implement the retention sweep, and move PII scrubbing to the bronze write boundary (`check_and_persist_bronze` in `backend/app/services/deduplication.py`) so every connector inherits it by construction rather than by convention.

**Compatibility shims accumulating:**
- Issue: `IntelligenceState = MetaRadarState` (`backend/app/workflows/state.py`), `hash_session_token = hash_token` (`backend/app/core/security.py`), `getOverview = fetchOverview` and many `fetchX/getX` aliases (`frontend/lib/api.ts`), plus legacy `ScoreBreakdown` fields (`impact`, `urgency`, `evidence_strength`, `strategic_relevance`, `routing_relevance`, `total_score`) in `frontend/types/api.ts`.
- Files: as listed above
- Impact: two names for one concept invites divergent edits, and the legacy score fields can be read by components that should use the 4-factor model.
- Fix approach: sweep aliases with `grep -rn` for each symbol, migrate callers, delete the alias. Do it per-symbol in small commits.

**Docstring/implementation drift on pipeline node count:**
- Issue: `PipelineRunner` docstrings say "10-node" while the graph wires 11 nodes, and `MetaRadarState`'s docstring also says "10-node".
- Files: `backend/app/workflows/runner.py:31-60`, `backend/app/workflows/state.py:26-30`
- Impact: planner/executor agents keying off these comments will reason about the wrong graph.
- Fix approach: correct the docstrings to 11 and reference `backend/app/workflows/graph.py` as the source of truth.

**Duplicated `sys.path` bootstrap in 36 test modules:**
- Issue: every test file repeats `base_dir = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(base_dir / "backend"))`.
- Files: all `tests/test_*.py`
- Impact: pure repetition; `pytest.ini` already sets `pythonpath = backend .`, so the preamble is redundant when run via pytest.
- Fix approach: rely on `pytest.ini` and remove the preamble, or centralize in `tests/conftest.py`.

## Known Bugs

**Score/priority derivation can silently mismatch between writer and reader:**
- Symptoms: `PipelineRunner` persists `priority` from `score_breakdown["priority_level"]` when available, otherwise from `sig["priority"]`, otherwise `"MEDIUM"`. `frontend/lib/mappers.ts` derives `scoring_status` from the presence of `score_breakdown` instead.
- Files: `backend/app/workflows/runner.py` (priority resolution block), `frontend/lib/mappers.ts:161`, `backend/app/api/v1/endpoints/signals.py:70-79`
- Trigger: a signal persisted with a `score_breakdown` that lacks `priority_level` but carries a legacy numeric `priority`.
- Workaround: none needed in the demo path; the deterministic scorer always emits `priority_level`.
- Note: `tests/test_provenance.py:89,125` pins the `computed`/`not_computed` behaviour, so this is guarded for the covered path only.

**Onboarding docs and reality diverge on how to run the frontend:**
- Symptoms: `README.md` shows `npm`/`pnpm` interchangeably, but the project is pnpm-locked (`frontend/packageManager: pnpm@9.15.5`) while `netlify.toml` sets `--frozen-lockfile=false`.
- Files: `README.md`, `frontend/package.json:6`, `netlify.toml:7-9`
- Trigger: a contributor running `npm install` in `frontend/` produces a divergent tree.
- Workaround: always use `pnpm`.

## Security Considerations

**Privacy gate coverage is uneven across egress paths:**
- Risk: the gate is only as strong as its weakest provider. `GeminiProvider` scrubs evidence and raises on PII; `GrokProvider` does not scrub at all (`backend/app/providers/grok.py:152-168`). Both are enabled by the same `AI_PROVIDER`/`ENABLE_GROK_FALLBACK` settings.
- Files: `backend/app/providers/factory.py`, `gemini.py`, `grok.py`, `backend/app/services/pii.py`
- Current mitigation: classification allow-list (`PUBLIC`/`SYNTHETIC` only) is enforced in both providers, so `CONFIDENTIAL`/`PATIENT_IDENTIFIABLE` payloads are blocked. But a mislabeled payload — the exact failure the scrubber exists to catch — reaches xAI unredacted.
- Recommendations: replicate the scrub-and-raise loop in `GrokProvider`; add a shared `_assert_scrubbed(evidence)` helper in `backend/app/providers/base.py` so no future provider can skip it; extend `tests/test_privacy_boundary.py` with a Grok PII-bearing `PUBLIC` case.

**Unscrubbed clinical-trial text enters the system at the source:**
- Risk: `clinical_trials` is the highest-volume connector and the only one that never scrubs. Trial `brief_summary` and the verbatim `study` object can contain site contact names, emails, and investigator names.
- Files: `backend/app/connectors/clinical_trials.py:239-276`
- Current mitigation: none at the connector. Downstream `node_validate` does not re-scrub either — `PIIPHIScrubber` is invoked by connectors and by the provider boundary, not by the pipeline.
- Recommendations: scrub at `check_and_persist_bronze()` so it is structurally impossible to bypass; add an ingestion test asserting no email-shaped string survives in `raw_signals_bronze` for the `clinical_trials` source.

**Production guard is narrower than the risk surface:**
- Risk: `validate_production_settings()` checks three conditions. A production deploy with default demo passwords, or a `DATABASE_URL` still pointing at localhost, passes the guard.
- Files: `backend/app/core/config.py:140-149`
- Current mitigation: the guard does run at startup (`backend/app/main.py:lifespan`) and Render supplies `APP_ENV=production`, `DEMO_MODE=false`, and a generated `SECRET_KEY`.
- Recommendations: also reject any `DEMO_PASSWORD_*` equal to its default, reject `localhost`/`127.0.0.1` in `DATABASE_URL`/`REDIS_URL`, and require `CORS_ORIGINS` to be non-empty under production.

**Audit trail exists but has no external anchoring:**
- Risk: `audit_log` is append-only (ORM events + a PostgreSQL trigger), but a database-level actor with DDL rights could drop the trigger. There is no hash chain, WORM export, or external sink.
- Files: `backend/app/models/__init__.py` (`block_audit_log_update`/`block_audit_log_delete`), `backend/alembic/versions/014_auditlog_user_correlation.py`
- Current mitigation: strong in-database immutability; `tests/test_security.py` (16 cases) exercises it.
- Recommendations: out of scope for a prototype, but note it in `docs/9_RISK_AND_GUARDRAILS.md` — the README currently implies a stronger guarantee than a single trigger provides.

**Demo mode is on by default in source:**
- Risk: `DEMO_MODE: bool = True` and `DEMO_AUTO_SEED_USERS: bool = True` are the defaults, so a forgotten env var enables `/auth/demo-login` and seeds 8 users with known passwords.
- Files: `backend/app/core/config.py:35-49`
- Current mitigation: the production guard raises if `DEMO_MODE` is true under production.
- Recommendations: flip the defaults to `False` so safety is opt-out rather than opt-in.

## Performance Bottlenecks

**Synchronous migration subprocess on the request-serving path:**
- Problem: `backend/run.py` blocks startup on `subprocess.run([... "alembic", "upgrade", "head"])`, and on Render's free tier this competes with the 60 s health-check window.
- Files: `backend/run.py:14-30`
- Cause: migrations are coupled to process start rather than a release/deploy step (`render.yaml` previously used `preDeployCommand`, removed in commit `0f5b0b9` for free-tier compatibility).
- Improvement path: move migrations to CI/CD or a one-shot job, or make the start path async and gate readiness on completion.

**Embedding inference is CPU-bound and serialized:**
- Problem: `fastembed` ONNX inference runs on the default executor; `PipelineRunner` awaits `embedding_service.embed_signal()` per signal, sequentially.
- Files: `backend/app/services/embeddings.py`, `backend/app/workflows/runner.py` (per-signal embedding loop)
- Cause: one `run_in_executor` call per signal rather than batched `embed(texts, batch_size=32)`; the service exposes batching, the runner does not use it.
- Improvement path: collect signal texts and call the batched path once per run; the `batch_size` parameter already exists in `_embed_sync`.

**Per-connector DB session and advisory lock churn:**
- Problem: each worker cycle opens a session for the lock, another inside `IngestionService`, and a third for `next_scheduled_run` persistence (`backend/app/services/scheduler.py`) — three round-trips per connector per interval on 8 connectors.
- Files: `backend/app/services/scheduler.py`
- Cause: convenience rather than correctness; the sessions are correctly closed but not reused.
- Improvement path: consolidate the lock acquisition and telemetry write into the ingestion session where the lock lifetime allows it.

**Whole-study JSONB writes:**
- Problem: `clinical_trials` writes the entire API v2 `study` object per row into `raw_signals_bronze.raw_payload` JSONB.
- Files: `backend/app/connectors/clinical_trials.py:266`
- Cause: verbatim-persistence requirement (D-23) applied without field pruning.
- Improvement path: retain verbatim payloads in object storage and keep a reference plus hashed excerpt in Postgres, or prune to the fields the pipeline actually consumes.

## Fragile Areas

**`backend/app/api/v1/endpoints/signals.py` (1,826 lines):**
- Files: `backend/app/api/v1/endpoints/signals.py`
- Why fragile: the largest module in the repo, mixing signal reads, review-state transitions, approval workflow, audit history, decision-object projection, an executive overview, and three Athena endpoints including SSE. State transitions and RBAC checks are interleaved with query construction.
- Safe modification: add tests to `tests/test_signals_endpoints.py`, `tests/test_review_state_machine.py`, and `tests/test_approval_workflow.py` first (they are thin — 3, 5, and 4 tests respectively against a 1,826-line module). Extract sub-routers before adding features.
- Test coverage: `/athena/stream` (line 1630) has **no test**; the decision-object projection (line 1164) and audit-history endpoint (line 1045) are only indirectly covered.

**`frontend/components/metaradar.tsx` (2,612 lines):**
- Files: `frontend/components/metaradar.tsx`
- Why fragile: owns nav, workspace routing, ⌘K search, ingestion controls, theme, and layout; the style gate exempts it, so it is unconstrained by the project's own color rules.
- Safe modification: extract one workspace at a time; verify with `pnpm exec tsc --noEmit` and a manual pass over the affected section.
- Test coverage: **zero** — no component is tested anywhere in the frontend.

**`ProviderFactory.execute_task` fallback chain:**
- Files: `backend/app/providers/factory.py`
- Why fragile: a single `try/except Exception` per provider means a programming error (e.g. a `TypeError` in response parsing) silently degrades to the next provider instead of surfacing. The Grok step's guard is a compound boolean (`has_grok_key and (ENABLE_GROK_FALLBACK or LLM_PROVIDER in [...] )`) that is easy to misread and change.
- Safe modification: `tests/test_provider_matrix.py` (6 tests) and `tests/test_failure_injection.py` (2 tests) are the guard rails — extend them before editing the chain.
- Test coverage: the chain order is asserted; the *reason* a provider was skipped is not.

**`node_synthesize` provider coupling:**
- Files: `backend/app/workflows/nodes/synthesize.py`
- Why fragile: it is the only node that crosses into the provider layer, and its output shape must satisfy both `ModelMetadataSchema` and the decision-object projection consumed by the frontend.
- Safe modification: run `tests/test_intelligence_nodes.py` (17 tests — the largest module) plus `tests/test_provider_matrix.py`.
- Test coverage: good for the happy path; degraded-mode shape is covered by `tests/test_failure_injection.py`.

## Scaling Limits

**Ingestion concurrency:**
- Current capacity: hard cap of 4 simultaneous connectors (`_global_connector_semaphore = asyncio.Semaphore(4)` in `backend/app/services/scheduler.py`) against 8 connectors, so at most half run concurrently.
- Limit: the cap is a module constant, not a setting, and does not account for Render free-tier CPU (0.1 vCPU class).
- Scaling path: expose as `SCHEDULER_MAX_CONCURRENT_CONNECTORS` and size per deployment tier.

**Pipeline batch size:**
- Current capacity: `batch_size=50` per run, hardcoded at both call sites (`backend/app/services/scheduler.py` and the pipeline endpoint).
- Limit: a single unpromoted backlog larger than 50 drains at one batch per connector cycle (15–60 min), so a cold start against thousands of bronze rows takes many hours.
- Scaling path: make batch size a setting and loop until the backlog is empty, bounded by a wall-clock budget.

**Rate limiter memory:**
- Current capacity: one list entry per client IP, retained for the process lifetime.
- Limit: unbounded dict growth under distributed traffic; no eviction path.
- Scaling path: TTL cache or Redis-backed counters (see the risk table entry).

**Single-instance assumptions:**
- Current capacity: PostgreSQL advisory locks provide correct cross-instance mutual exclusion for the scheduler, and Redis is available when configured.
- Limit: production deliberately sets `REDIS_URL=""` (`render.yaml`), so the lock path falls back to Postgres; rate-limit state and the `SourceScheduler._instance` singleton are process-local, so horizontal scaling would need both revisited.
- Scaling path: keep the scheduler single-instance by design (document it), and move rate limiting to shared storage before adding replicas.

## Dependencies at Risk

**`llama-cpp-python` (undeclared, optional):**
- Risk: `GemmaProvider` imports it opportunistically. It is absent from `backend/requirements.txt`, so the local-GGUF path works on a developer machine and not in CI or on Render.
- Impact: silent capability divergence — the same code path behaves differently per environment with no error until synthesis is attempted.
- Migration plan: declare an optional extra, or drop the GGUF path and standardize on Ollama (`OLLAMA_HOST`) as the single local inference mechanism.

**`fastembed` pinned to a model revision:**
- Risk: `EMBEDDING_MODEL_REVISION` is pinned in `backend/app/core/config.py` and stamped onto every signal row as `embedding_model_version`. Changing the revision invalidates stored vectors.
- Impact: embeddings from two revisions are not comparable, but nothing prevents mixed-revision rows in `signals.embedding`.
- Migration plan: add a backfill gate that refuses to score novelty across mismatched `embedding_model_version` values; `backend/app/services/embeddings_backfill.py` exists and is the natural home.

**`@designcodeio/threeui` and `shadcn` at caret ranges:**
- Risk: `^1.0.0` / `^4.8.0` on UI packages while `next`, `react`, and `typescript` are pinned.
- Impact: a UI-library minor bump can break the star-portal effects (`frontend/components/effects/star-portal/`) with no type signal.
- Migration plan: no tests cover these components; pin exactly (as `typescript` already is) or add a smoke render test.

**No error-tracking dependency at all:**
- Risk: neither Sentry nor any equivalent is present, and the only telemetry is structured stdout.
- Impact: production failures on Render are visible only in log scraping; there is no alerting on `errors_count` or on the scheduler's `consecutive_failures`.
- Migration plan: add `sentry-sdk` with a structlog processor, or wire an alert on the existing `/api/v1/scheduler` and `/api/v1/health/connectors` signals.

## Missing Critical Features

**API contract is hand-maintained rather than generated:**
- Problem: `frontend/types/api.ts` is a TypeScript string literal inside `scripts/export_openapi.py`. CI detects drift but cannot prevent a backend field from being absent from the TS template — it only fails if the emitted file differs from the committed one, which both are derived from the same template.
- Blocks: reliable end-to-end type safety. A new Pydantic field does not appear in the TypeScript contract unless a human edits the Python string.
- Recommendation: generate the TS types from `contracts/openapi.json` (e.g. `openapi-typescript`) and keep the drift gate.

**No frontend test harness:**
- Problem: `pnpm exec tsc --noEmit` + lint + build is the entire frontend suite. There is no Jest, Vitest, Playwright, or Cypress.
- Blocks: any behavioural refactor of `frontend/lib/api.ts` (1,139 lines), `frontend/lib/mappers.ts`, or the workspace components. The 2,612-line shell is untestable by construction.
- Recommendation: add Vitest for pure functions (`mappers.ts`, `errors.ts`) as the first, cheapest step; Playwright for the login→workspace path second.

**No continuous deployment job:**
- Problem: `.github/workflows/ci.yml` has a single `test-and-verify` job. Deployment is Netlify/Render git integration only, with no post-deploy smoke test.
- Blocks: automated rollback and verified releases; `docs/rules/RELEASE_PROCESS.md` describes a process CI does not enforce.
- Recommendation: add a post-deploy step that hits `/api/v1/health/ready` and `/api/v1/health/connectors` and fails the deploy on a bad status.

**Retention policy defined but not implemented:**
- Problem: `RAW_SIGNAL_RETENTION_DAYS: int = 30` exists in settings with no consumer.
- Blocks: any defensible data-retention claim; bronze rows persist indefinitely.
- Recommendation: implement a scheduled sweep and reference it from `docs/rules/DATA_AND_PRIVACY_STANDARDS.md`.

**No webhook or notification egress:**
- Problem: `approval_requests` and `is_escalated` signals are surfaced only inside the UI.
- Blocks: the "expected action / routing" promise — a CRITICAL signal escalates only if a human happens to be logged in.
- Recommendation: add an optional egress (email/Slack) behind a feature flag, with the same privacy gate applied.

## Test Coverage Gaps

**Athena SSE streaming route:**
- What's not tested: `POST /api/v1/athena/stream` (`backend/app/api/v1/endpoints/signals.py:1630`) end to end — the streaming contract, mid-stream `error` events, and citation attachment.
- Files: `backend/app/api/v1/endpoints/signals.py:1630-1766`, `frontend/lib/api.ts` (stream reader)
- Risk: the flagship demo surface can regress silently; the documented honest-failure `error` event is untested.
- Priority: **High**

**Frontend mappers and API client:**
- What's not tested: all of `frontend/lib/mappers.ts` and the 1,139-line `frontend/lib/api.ts`.
- Files: `frontend/lib/mappers.ts`, `frontend/lib/api.ts`
- Risk: runtime shape normalization against a hand-maintained contract diverges from the backend with no failing test.
- Priority: **High**

**`backend/run.py` production entrypoint:**
- What's not tested: the migration-failure branch that deliberately still binds the port.
- Files: `backend/run.py`
- Risk: the deploy-time behaviour that matters most on Render free tier is the least exercised code in the repo. `tests/test_launchers.py` covers `setup.py`/`start.py` only.
- Priority: **Medium**

**Scheduler timing, backoff, and quota governor:**
- What's not tested: `_connector_worker_loop` delay math, exponential backoff growth, and the NewsAPI `quota_remaining < 15` preservation branch.
- Files: `backend/app/services/scheduler.py`
- Risk: quota exhaustion or hot-looping in production with no failing test; `SCHEDULER_JITTER_PERCENT` and `SCHEDULER_MAX_BACKOFF_MINUTES` are unverified.
- Priority: **Medium**

**Approval workflow and review state machine:**
- What's not tested: terminal-state locking under concurrent resolution, and approval resolution by a non-leadership role.
- Files: `backend/app/api/v1/endpoints/signals.py:792-1045`, `backend/app/models/__init__.py:ApprovalRequest`
- Risk: `tests/test_approval_workflow.py` has 4 tests and `tests/test_review_state_machine.py` has 5 against a large stateful surface; an illegal transition could be accepted.
- Priority: **Medium**

**PII scrubber targets outside the provider boundary:**
- What's not tested: that `clinical_trials` bronze rows are free of PII (they currently are not — see the risk table), and that the `pii_scrubbed` flag reflects the scrubber's real result.
- Files: `backend/app/connectors/clinical_trials.py`, `backend/app/connectors/*.py` (`pii_scrubbed` literals), `tests/test_ingestion.py:216` (asserts a `True` flag that is hardcoded)
- Risk: `tests/test_ingestion.py:216` currently **passes for the wrong reason** — it asserts a constant. A regression that stops scrubbing entirely would not fail any test.
- Priority: **High**

**Multi-instance / cross-process behaviour:**
- What's not tested: two concurrent schedulers contending for the same advisory lock; per-process rate-limit state.
- Files: `backend/app/services/scheduler.py`, `backend/app/api/deps.py`, `backend/app/db/session.py`
- Risk: duplicate ingestion and ineffective rate limiting if replicas are ever added.
- Priority: **Low**

**Coverage threshold:**
- What's not tested: nothing enforces a floor. `pytest-cov` is installed but no `--cov-fail-under`, no `.coveragerc`, no CI gate.
- Files: `pytest.ini`, `.github/workflows/ci.yml`
- Risk: new untested code lands freely; `backend/app/api/v1/endpoints/signals.py` and the `frontend/` tree are the obvious sinks.
- Priority: **Low**

---

*Concerns audit: 2026-10-02*
