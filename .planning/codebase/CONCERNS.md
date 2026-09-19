# Codebase Concerns

**Analysis Date:** 2026-09-19

## Security Posture

**PII/PHI scrub (`backend/app/services/pii.py`):**
- Risk: Regex-only scrubber covers `email`, `phone`, `ssn`, `mrn`, `patient_dob`, `national_id` — no spaCy NER, no person-name / address / free-text clinical narrative detection. Adversarial or non-English PII passes through.
- Files: `backend/app/services/pii.py`, callers in `backend/app/connectors/*.py` (all 8 connectors), `backend/app/workflows/nodes/validate.py:58-59`, `backend/app/api/v1/endpoints/signals.py:1541,1653`
- Current mitigation: `PIIPHIScrubber.scrub()` applied before persistence in every connector; `classify_payload()` escalates PII hits to `CONFIDENTIAL`; validate node quarantines on low confidence.
- Severity: **High** — sole gate before persistence and external LLM send.
- Recommendations: Add name/entity layer, quarantine-on-`UNKNOWN` default, EV-4 audit scan regression in `tests/test_privacy_boundary.py`.

**Grok privacy gate — PUBLIC/SYNTHETIC only (`backend/app/providers/grok.py:63-74`):**
- Risk: Hosted xAI transmission retains requests ~30 days for abuse auditing (R28). Any classification bug leaks data off-local.
- Files: `backend/app/providers/grok.py:63-96,152-153`, `backend/app/providers/factory.py:46`, `backend/app/providers/base.py` (`DataClassification`)
- Current mitigation: `validate_privacy_gate()` returns True only for `PUBLIC`/`SYNTHETIC`; default parameter is `UNKNOWN` (blocked); missing key raises `GrokUnavailableError` → BART degraded fallback; gate decisions logged via `backend/app/core/logging.py`.
- Severity: **High** (impact) / **Low** (likelihood — default-deny).
- Recommendations: Keep gate synchronous and non-bypassable; never add `INTERNAL` to allow-list; retain `tests/test_privacy_boundary.py` + EV-20 coverage.

**Audit immutability — WORM (`backend/alembic/versions/014_auditlog_user_correlation.py`, `backend/app/models/__init__.py:424-445`):**
- Risk: Defense relies on two layers that must stay in sync: DB trigger `trg_block_audit_log_update_delete` + SQLAlchemy `before_update`/`before_delete` listeners raising `PermissionError`. Direct SQL superuser or bulk `Query.delete()` paths bypass ORM listeners; trigger is the only backstop.
- Files: `backend/alembic/versions/014_auditlog_user_correlation.py:24-35`, `backend/app/models/__init__.py:438-445`, `backend/alembic/versions/001_initial_v51_schema.py:246`
- Current mitigation: Trigger blocks `UPDATE OR DELETE` at DB level; ORM listeners fail fast in app; `user_id`/`correlation_id` indexed for traceability.
- Severity: **Medium**.
- Recommendations: Add migration-drift test asserting trigger exists (`pg_trigger` check); document superuser-break-glass procedure; never claim 21 CFR Part 11/GxP compliance (see `docs/9_RISK_AND_GUARDRAILS.md` §3).

**Password hashing — bcrypt (`backend/app/core/security.py:12-23`):**
- Risk: None structural — `bcrypt.gensalt` + `checkpw` with constant-time session-token compare (`hmac.compare_digest`). Risk is operational: demo passwords in config.
- Files: `backend/app/core/security.py`, `backend/app/services/auth_service.py`, `backend/app/core/config.py:42-49`
- Current mitigation: Salted bcrypt; session tokens SHA-256 indexed, `TimestampSigner`-signed cookies.
- Severity: **Low**.
- Recommendations: Rotate demo passwords out of defaults before any shared deployment; enforce `DEMO_MODE=false` in production.

**Session cookies — HttpOnly / SameSite (`backend/app/api/v1/endpoints/auth.py:45-70`, `backend/app/core/config.py:55-63`):**
- Risk: `SESSION_COOKIE_SECURE=false` default; relies on `effective_session_cookie_secure` auto-enforcing in production. CSRF cookie is intentionally `httponly=False` (JS-readable for `X-CSRF-Token` header) — XSS would expose CSRF token (but not session).
- Files: `backend/app/api/v1/endpoints/auth.py:45-70`, `backend/app/core/config.py:38,60-63`
- Current mitigation: Session cookie `HttpOnly`, `SameSite="lax"`, `Secure` in prod; session-bound HMAC CSRF (`generate_session_bound_csrf`/`verify_session_bound_csrf` in `backend/app/core/security.py:55-74`); `require_csrf` on `/logout` and mutations; `auth_rate_limit` (5/min) + `require_preauth_origin` on login.
- Severity: **Medium** (dev-default `Secure=false` + JS-readable CSRF cookie by design).
- Recommendations: Keep CSP hardened (`backend/app/core/middleware.py:76-98`); never set CSRF cookie `HttpOnly`; verify `Secure` flag in staging with HTTPS.

**Log secret scrubbing (`backend/app/core/redact.py`):**
- Risk: Scrub covers `password/token/secret/api_key/authorization/bearer/jwt` patterns in logs and query-param dumps. Non-matching key names (e.g., `xai_key`, custom headers) could leak.
- Files: `backend/app/core/redact.py`, `backend/app/core/logging.py`
- Current mitigation: `SecretScrubFilter` on stdlib logs + structlog redaction; `_KV_RE`/`_QUOTED_RE` free-text redaction.
- Severity: **Low**.
- Recommendations: Extend `SENSITIVE_KEYS` if new credential var names are added; keep `.env` (present, gitignored) out of repo — `.env.example` contains key names only, all empty.

## Tech Debt

**Oversized endpoint module — `signals.py` (1826 lines):**
- Issue: Single module owns signals CRUD, RBAC scoping, review queue, Ask Athena streaming, audit reads. High merge-conflict and regression surface.
- Files: `backend/app/api/v1/endpoints/signals.py`
- Impact: Slow review, fragile edits, test setup cost.
- Severity: **Medium**
- Fix approach: Split into `signals_crud.py` / `signals_review.py` / `athena.py` routers behind the same prefix; move PII-scrub calls into a shared dependency.

**Demo credential defaults in `config.py`:**
- Issue: Eight `DEMO_PASSWORD_*` plaintext defaults (e.g., `MedAffairs2026!`-pattern) ship in source; `SECRET_KEY` defaults to `dev-secret-change-in-production`; `DATABASE_URL`/`REDIS_URL` localhost defaults.
- Files: `backend/app/core/config.py:28-53`
- Impact: Credential-spray risk if `DEMO_MODE=true` ever reaches a shared host; session forgery if default `SECRET_KEY` used in prod.
- Severity: **High** (if deployed without env override) / **Low** (local-only as-is)
- Fix approach: Fail-fast on boot when `APP_ENV=production` and `SECRET_KEY` is default or `DEMO_MODE=true`; document in `docs/rules/SECURITY_STANDARDS.md`.

**Regex-only PII scrubber (no NER):**
- Issue: See Security Posture. Six patterns only; `docs/9_RISK_AND_GUARDRAILS.md` R14 already flags "spaCy NER contributes but is not a guaranteed scrubber" — currently spaCy is absent entirely.
- Files: `backend/app/services/pii.py`
- Impact: False negatives on names/addresses/clinical narratives.
- Severity: **High**
- Fix approach: Add lightweight NER or deny-list second pass; quarantine-on-`UNKNOWN` classification.

**Contract sync is manual-gated:**
- Issue: TypeScript `frontend/types/api.ts` must mirror FastAPI `backend/app/schemas/`; drift breaks UI deserialization.
- Files: `backend/app/schemas/__init__.py` (656 lines), `frontend/types/api.ts`, `contracts/openapi.json`, `scripts/export_openapi.py`
- Impact: Runtime display bugs on schema change.
- Severity: **Medium**
- Fix approach: Keep CI drift gate `tests/test_contract_drift.py` + `scripts/export_openapi.py` diff check green; split growing `schemas/__init__.py`.

**Synthetic/live coexistence in `signals` gold table:**
- Issue: Benchmark and live rows share one table; provenance depends on `data_mode`/`is_synthetic` flags being set on every write path.
- Files: `backend/app/models/__init__.py`, `frontend/lib/mappers.ts`, `frontend/components/common/DataModeBadge.tsx`
- Impact: Mislabeling shows synthetic as LIVE.
- Severity: **Medium**
- Fix approach: Enforce `data_mode` enum (`live`, `recorded_demo`, `test_fixture`, `benchmark`, `synthetic`) at model + mapper + badge; invariant tests in `tests/test_truthfulness_and_invariants.py`.

**No TODO/FIXME tracking debt:**
- Issue: Grep across `backend/` finds zero `TODO`/`FIXME`/`HACK`/`XXX` markers in app code (only placeholder-string guards in config and historical planning docs). No hidden stub debt detected.
- Severity: **None** — healthy.

## Known Bugs

**None open for hackathon MVP scope:**
- Symptoms: No reproducible crashers filed; failure-injection suite covers provider outage, quota exhaustion, and stale-cache paths.
- Files: `tests/test_failure_injection.py`
- Trigger: N/A
- Workaround: N/A

## Performance Bottlenecks

**Local Gemma 3 4B CPU inference:**
- Problem: ~2–5 tok/s on CPU-only hosts; KV-cache + 2048-token context budgeted tightly for 4 GB VRAM (R30).
- Files: `backend/app/providers/gemma.py` (453 lines), `backend/app/core/config.py:70-76`
- Cause: Transformer matmuls without CUDA/AVX-512 offload.
- Severity: **Medium**
- Improvement path: `LLM_DEVICE=cuda:0` + cuBLAS wheels (~35+ tok/s); reduce `MAX_CONTEXT_TOKENS`/`MAX_OUTPUT_TOKENS`; provider chain degrades Gemma → Grok (privacy-gated) → BART factual.

**NewsAPI quota (100 req/day developer tier):**
- Problem: Aggressive polling exhausts daily quota and starves demo.
- Files: `backend/app/connectors/newsapi.py:21-169`, `backend/app/services/scheduler.py:143-151`, `backend/app/core/domain_config.py:62-69`
- Cause: Third-party tier cap.
- Severity: **Medium**
- Improvement path: Quota governor already pauses auto-polling when `<15` remain and forces 90-min backoff; keep `quota_per_day` in domain config accurate.

## Fragile Areas

**Ingestion backoff / scheduler (`backend/app/services/scheduler.py`, `backend/app/connectors/base.py:130-168`, `backend/app/services/ingestion.py:142`):**
- Files: `backend/app/services/scheduler.py:19,143-151`, `backend/app/connectors/base.py:139-168`, `backend/app/models/__init__.py:64` (`backoff_minutes`)
- Why fragile: Exponential backoff + jitter + advisory locks + per-source `backoff_minutes` interact; mis-tuning either hammers APIs or stalls freshness (R5/R11). Global semaphore (`Semaphore(4)`) is a single choke point.
- Safe modification: Tune intervals only via `backend/app/core/config.py:122-131` (`SCHEDULER_*`); never bypass `_backoff_delay`; preserve quota-gate read-before-fetch in `newsapi.py:74-85`.
- Test coverage: `tests/test_ingestion.py`, `tests/test_failure_injection.py`, `tests/test_connector_health.py`.

**NewsAPI quota gate (read-before-fetch):**
- Files: `backend/app/connectors/newsapi.py:74-85,104-130,155-169`
- Why fragile: Quota state lives in connector cursor JSON (`quota_remaining`, `quota_window_date`); clock-skew or cursor reset re-opens the gate and burns quota.
- Safe modification: Keep `_read_quota` as the single source of truth; handle unparseable `X-RateLimit-Remaining` as today (current code does); never fetch when `quota_remaining <= 0` same-day.
- Test coverage: `tests/test_connector_health.py`, `tests/test_config_errors.py`.

**pgvector index / embedding dimension:**
- Problem: 384-dim `sentence-transformers/all-MiniLM-L6-v2` vectors pinned by revision (`backend/app/core/config.py:97-100`); HNSW/IVFFlat index pressure grows with row count; dimension mismatch breaks search.
- Files: `backend/app/services/embeddings.py:26,70-76`, `backend/app/services/embeddings_backfill.py`, `backend/app/services/vector_query.py`, `backend/app/api/v1/endpoints/search.py`, `backend/app/db/seed.py:764`
- Cause: Single pinned model + unpartitioned vector index.
- Severity: **Low** (thousands of rows) → **Medium** at millions.
- Safe modification: Never change `EMBEDDING_MODEL`/`EMBEDDING_DIMENSION` without full backfill; `_validate_vector` must keep raising (never zero-vector fallback); scaling path is partition by disease domain + date.
- Test coverage: `tests/test_retrieval.py`.

**LangGraph nodes / state reducers (`backend/app/workflows/`):**
- Files: `backend/app/workflows/state.py`, `backend/app/workflows/graph.py`, `backend/app/workflows/runner.py` (432 lines), `backend/app/workflows/nodes/validate.py`, `backend/app/workflows/nodes/embed.py:52-53`
- Why fragile: Reducer choice (`replace_list` vs `operator.add`) determines duplication; 11-node chain amplifies single-node contract breaks; PII scrub + embedding + classification ordering matters.
- Safe modification: Follow reducer specs in `ARCHITECTURE.md`; keep scrub-before-persist ordering; validate node must run before embed.
- Test coverage: `tests/test_intelligence_nodes.py`, `tests/test_signal_routing_workflow.py`, `tests/test_confluence_semantics.py`.

## Scaling Limits

**PostgreSQL vector indexing:**
- Current capacity: Thousands of 384-dim embeddings, HNSW/IVFFlat via `pgvector>=0.2.5`.
- Limit: Memory pressure past millions of rows without partitioning.
- Scaling path: Partition by disease domain + date ranges; move embeddings to dedicated vector store if needed.

**Scheduler concurrency:**
- Current capacity: `_global_connector_semaphore = asyncio.Semaphore(4)` serializes connector bursts.
- Limit: 8-connector fan-out queues behind 4 slots; adding connectors linearly slows cycles.
- Scaling path: Per-tier semaphores; separate cadence for slow sources (PubMed/CT.gov hourly vs News 15-min).

## Dependencies at Risk

**`llama-cpp-python` platform builds:**
- Risk: C++ extension needs compilation on non-standard arch; local inference setup fails without prebuilt wheels.
- Impact: Gemma provider unavailable → chain falls to Grok/BART.
- Files: `backend/app/providers/gemma.py`, `setup.py`, `backend/requirements.txt`
- Migration plan: Prebuilt wheel repo + Ollama sidecar fallback (`OLLAMA_HOST`, `OLLAMA_MODEL=gemma3:4b` in `backend/app/core/config.py:93-94`).

**Unpinned `>=` dependency floors (`backend/requirements.txt`):**
- Risk: All floors are `>=` (`fastapi>=0.110.0`, `langgraph>=0.2.0`, `pgvector>=0.2.5`, …); fresh installs can pull breaking minors.
- Impact: CI green today, install drift tomorrow.
- Migration plan: Generate `requirements.lock` / pip freeze snapshot for reproducible builds; pin `langgraph` and `pgvector` first (API-churn prone).

## Missing Critical Features

- None for hackathon MVP: 7 stakeholder workspaces, Ask Athena streaming, 8 connectors, medallion pipeline, LangGraph workflow, and online calibration are implemented and test-covered.

## Test Coverage Gaps

**Covered (34 test files, incl.):** `tests/test_auth.py`, `tests/test_rbac.py`, `tests/test_security.py`, `tests/test_privacy_boundary.py`, `tests/test_login_credentials.py`, `tests/test_approval_workflow.py`, `tests/test_failure_injection.py`, `tests/test_contract_drift.py`, `tests/test_truthfulness_and_invariants.py`, `tests/test_provenance.py`, `tests/test_provider_matrix.py`, `tests/test_providers_live.py`.
- What's not tested: NER-grade PII adversarial cases (regex-only suite passes by construction); superuser-bypass of audit trigger (DB-level negative test absent); migration-drift assertion that `trg_block_audit_log_update_delete` exists post-migrate; frontend XSS/CSRF cookie-flag assertion in production-mode config.
- Files: `backend/app/services/pii.py`, `backend/alembic/versions/014_auditlog_user_correlation.py`, `backend/app/core/config.py:55-63`
- Risk: Silent scrub miss or trigger loss after migration squash goes unnoticed.
- Priority: **High** (PII adversarial + trigger-existence tests), **Medium** (prod-config cookie-flag test).

## Environment Configuration (key names only — zero secrets)

- `.env` present in workspace (gitignored); `.env.example` key names only, all secret values empty.
- Required: `DATABASE_URL`, `REDIS_URL` (env-driven per `docs/rules/SECURITY_STANDARDS.md`).
- Conditionally required: `NEWSAPI_KEY` (NewsAPI has no anonymous tier → `CONFIGURATION_ERROR` via `configuration_error_for()` in `backend/app/core/config.py:137-148`); `XAI_API_KEY` only when `ENABLE_GROK_FALLBACK=true`.
- Optional/rate-lift: `NCBI_API_KEY`, `OPENFDA_API_KEY`; `GROK_API_KEY` accepted as alias; `NEWS_API_KEY` accepted as alias.
- Never committed: `.env`, credentials files, `*.pem`/`*.key`, keystores — none quoted in this document.

## Recommended Next Hardening Steps

1. **PII second layer (High):** Add name/address NER or deny-list pass in `backend/app/services/pii.py`; default `classify_payload()` `UNKNOWN` → quarantine, never `PUBLIC`; add adversarial EV-4 cases to `tests/test_privacy_boundary.py`.
2. **Production boot guard (High):** Refuse startup when `APP_ENV=production` with default `SECRET_KEY` or `DEMO_MODE=true` (`backend/app/core/config.py`); rotate all `DEMO_PASSWORD_*` defaults.
3. **Audit-trigger drift test (Medium):** Assert `trg_block_audit_log_update_delete` + `block_audit_log_mutation()` exist after migrations; cover ORM-bypass path, not just listener path.
4. **Dependency freeze (Medium):** Pin `langgraph`, `pgvector`, `fastapi` with a lockfile; re-verify `tests/test_provider_matrix.py` + `tests/test_retrieval.py` on bump.
5. **Quota/clock robustness (Low):** Persist `quota_window_date` in UTC explicitly in `backend/app/connectors/newsapi.py`; add clock-skew unit test for `_read_quota`.
6. **Endpoint split (Low):** Decompose `backend/app/api/v1/endpoints/signals.py` (1826 lines) into CRUD/review/Athena routers; no behavior change, contract-drift test stays green.

---

*Concerns audit: 2026-09-19*
