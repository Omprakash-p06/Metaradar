# External Integrations

**Analysis Date:** 2026-10-02

## APIs & External Services

### Ingestion Connectors (8 registered sources)

All connectors subclass `SourceConnector` (`backend/app/connectors/base.py`) and are instantiated as a module-level list in `backend/app/connectors/__init__.py:ALL_CONNECTORS`. Each loads per-source query profiles from `config/haemophilia.yaml:202-322` and persists **bronze rows only** — connectors never generate intelligence (`base.py` docstring, D-26).

| Connector | Class / Module | Upstream endpoint | Auth | Freshness class |
|-----------|----------------|-------------------|------|-----------------|
| PubMed | `PubMedConnector` — `backend/app/connectors/pubmed.py:29` | NCBI E-utilities `esearch.fcgi` + `efetch.fcgi` | `NCBI_API_KEY` (optional), `NCBI_TOOL`, `NCBI_EMAIL` | `batch` |
| ClinicalTrials.gov | `ClinicalTrialsConnector` — `backend/app/connectors/clinical_trials.py:26` | `https://clinicaltrials.gov/api/v2/studies` | None (public) | `near_real_time` |
| openFDA | `OpenFDAConnector` — `backend/app/connectors/fda.py:28` | `https://api.fda.gov/drug/drugsfda.json` + FAERS/MedWatch | `OPENFDA_API_KEY` (optional, raises rate limits) | `adapter_ready` |
| EMA | `EMARSSConnector` — `backend/app/connectors/ema.py:28` | `https://www.ema.europa.eu/en/medicines/rss` | None | `adapter_ready` |
| NewsAPI | `NewsAPIConnector` — `backend/app/connectors/newsapi.py:30` | `https://newsapi.org/v2/everything` | `NEWSAPI_KEY` or `NEWS_API_KEY` **required** | `delayed` |
| BioPharma Dive | `BioPharmaDiveRSSConnector` — `backend/app/connectors/biopharma_dive.py:29` | `https://www.biopharmadive.com/feeds/news/` | None | `delayed` |
| Fierce Pharma | `FiercePharmaRSSConnector` — `backend/app/connectors/fierce_pharma.py:28` | `https://www.fiercepharma.com/rss/xml` | None | `delayed` |
| ET Pharma | `ETPharmaRSSConnector` — `backend/app/connectors/et_pharma.py:28` | `https://pharma.economictimes.indiatimes.com/rss/topstories` | None | `delayed` |

**Connector contract** (`backend/app/connectors/base.py`):
- `_fetch_with_retry()` — bounded exponential backoff + jitter, `max_retries=3`, `retry_base_delay_s=1.5`, `timeout_s=30.0`. Deliberately no `tenacity` dependency.
- `RunStatus` literal vocabulary: `SUCCESS`, `NO_NEW_DATA`, `CONNECTED`, `PARTIAL`, `DEGRADED`, `FAILED`, `CONFIGURATION_ERROR`, `RATE_LIMITED`, `TIMEOUT`, `STALE`.
- `_persist_health_log()` writes `source_health_logs` and updates the live `sources` row; `redact_text()` scrubs error detail before persistence.
- RSS/XML sources parse with **stdlib `xml.etree`**, not `feedparser`.

**NewsAPI quota governor** — when `quota_remaining < 15`, `backend/app/services/scheduler.py` deliberately skips the cycle and forces a 90-minute backoff to protect the 100/day free tier.

### AI / LLM Providers

| Provider | Module | Transport | Auth | Capabilities |
|----------|--------|-----------|------|--------------|
| Local Gemma | `backend/app/providers/gemma.py` | GGUF via `llama-cpp-python` (if installed) **or** Ollama HTTP `OLLAMA_HOST` | none | summarize, classify, reason, structured_output, generate_actions |
| Cloud Gemini | `backend/app/providers/gemini.py` | `https://generativelanguage.googleapis.com/v1beta/models` via `httpx` | `GEMINI_API_KEY` | summarize, classify, reason, structured_output — **`GENERATE_ACTIONS` deliberately excluded** |
| xAI Grok | `backend/app/providers/grok.py` | xAI REST via `httpx` | `XAI_API_KEY` or `GROK_API_KEY` | opt-in fallback, gated by `ENABLE_GROK_FALLBACK` |
| BART "degraded" | `backend/app/providers/degraded.py` | **in-process string truncation, no network, no model** | none | summarize only |

**Fallback chain** (`backend/app/providers/factory.py:execute_task`):
`local Gemma` → `Gemini (if key + AI_PROVIDER allows + privacy gate passes)` → `Grok (if enabled + privacy gate passes)` → `BART degraded factual summary`.

**Privacy gate** — mandatory, synchronous, enforced immediately before any external transmission:
- `GeminiProvider.validate_privacy_gate()` (`gemini.py`) allows **only** `PUBLIC` and `SYNTHETIC`; rejects `PATIENT_IDENTIFIABLE`, `CONFIDENTIAL`, `INTERNAL`, `UNKNOWN`.
- `GrokProvider.validate_privacy_gate()` applies the same allow-list (`backend/app/providers/grok.py`).
- Both providers additionally run `PIIPHIScrubber.scrub()` on every evidence item and raise `PermissionError` if PII is detected (`gemini.py`).

**Retry behaviour** — Gemini retries `408`, `429`, and `5xx` with exponential backoff + jitter up to `GEMINI_MAX_RETRIES`, raising `GeminiUnavailableError` on exhaustion so the factory falls through.

### Embeddings

- **Runtime:** `fastembed` (ONNX, CPU) — `backend/app/services/embeddings.py`
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`, revision `e4bb823e5956b6277b069d276b978c48a73507c7`, 384 dims, seq length 256 (`backend/app/core/config.py`)
- **Execution:** synchronous ONNX inference offloaded via `asyncio.get_running_loop().run_in_executor`; module-level lazy singleton cached for process lifetime
- **Backfill:** `backend/app/services/embeddings_backfill.py`
- **External API:** none — fully local, no network calls

### Semantic Search

- `POST /api/v1/search` — `backend/app/api/v1/endpoints/search.py`
- Vector query helpers: `backend/app/services/vector_query.py`; pgvector HNSW cosine over `signals.embedding`

## Data Storage

**Primary database — PostgreSQL 16 + pgvector:**
- Connection: `DATABASE_URL` (auto-normalized to `postgresql+asyncpg://`, password percent-encoded)
- Local/dev: `docker-compose.yml` service `postgres`, image `pgvector/pgvector:pg16`, db `metaradar`
- Production: **Supabase** Postgres, connection string synced into Render via `render.yaml` `DATABASE_URL: sync: false`
- ORM: SQLAlchemy 2.0 async; migrations via Alembic (15 revisions)
- Session factory: `backend/app/db/session.py` (`AsyncSessionLocal`, `async_session_factory`, `get_db`)
- **Hybrid driver strategy:** `asyncpg` at runtime; `psycopg[binary]` for Alembic (sync migrations), driven by `backend/run.py` calling `alembic upgrade head` in a subprocess

**Tables (22, `backend/app/models/__init__.py`, `backend/app/models/auth.py`):**
`pipeline_runs`, `sources`, `source_health_logs`, `companies`, `assets`, `trials`, `developments`, `events`, `lifecycle_events`, `confluences`, `raw_signals_bronze`, `connector_state`, `evidence`, `signals`, `contradictions`, `calibration_runs`, `calibration_history`, `scoring_weights`, `signal_routing`, `calibration_feedback`, `watch_items`, `audit_log`, `approval_requests`, `users`, `sessions`

**Immutability control:**
- SQLAlchemy `before_update` / `before_delete` events on `AuditLog` raise `PermissionError` (`models/__init__.py`)
- Matching PostgreSQL trigger `block_audit_log_mutation`, created in `backend/alembic/versions/014_auditlog_user_correlation.py`

**Caching / Locking — Redis 7 (optional):**
- `REDIS_URL` is `Optional[str]` and defaults to `redis://localhost:6379/0` locally
- Used for cross-instance coordination: `try_advisory_lock` / `release_advisory_lock` in `backend/app/db/session.py`
- Production Render blueprint sets `REDIS_URL: ""` — the app must and does boot without Redis (`tests/test_redis_optional.py`)
- Scheduler falls back to PostgreSQL advisory locks (`pg_try_advisory_lock`) when Redis is absent

**File storage — local filesystem only:**
- GGUF model files: `models/` (`settings.MODELS_DIR`)
- Poster/report artifacts: `poster/`, `data/`, `logs/`
- No S3/GCS/Azure blob integration detected

## Authentication & Identity

**Auth provider: custom, first-party.** No Auth0/Clerk/Cognito/Firebase.

- **Password hashing:** bcrypt via `backend/app/core/security.py:hash_password` / `verify_password`
- **Session tokens:** `itsdangerous.TimestampSigner` → signed cookie `metaradar_session`; SHA-256 hash index persisted for lookup
- **Timeouts:** absolute 8h (`SESSION_LIFETIME_SECONDS`), idle 1h (`SESSION_IDLE_TIMEOUT_SECONDS`)
- **CSRF:** session-bound HMAC-SHA256 token in cookie `metaradar_csrf` + `X-CSRF-Token` header, verified by `require_csrf` (`backend/app/api/deps.py`)
- **Pre-auth origin check:** `require_preauth_origin` — exact scheme/host/port match against `CORS_ORIGINS` (OWASP login-CSRF defense)
- **RBAC:** `require_role(*roles)` dependency factory; `ADMIN` bypasses all role checks (`deps.py`)
- **Rate limiting:** in-memory sliding window — `auth_rate_limit` (5/min) and `mutation_rate_limit` (60/min), both per client IP
- **API key:** optional `X-API-Key` gate via `require_mutation_auth` when `METARADAR_API_KEY` is set
- **Split-origin production posture** (`render.yaml`): `SESSION_COOKIE_SAMESITE=none` + `SESSION_COOKIE_SECURE=true`, with `CORS_ORIGINS` pinned to the Netlify origin

**Endpoints:** `backend/app/api/v1/endpoints/auth.py` — `POST /auth/login`, `POST /auth/demo-login`, `POST /auth/logout`, `GET /auth/me`, `GET /auth/csrf`

## Monitoring & Observability

**Error tracking:** none detected — no Sentry, Datadog, New Relic, or Rollbar integration.

**Logs:**
- `structlog` JSON rendering configured in `backend/app/core/logging.py` (`configure_structlog(json_logs=True)`)
- `asgi-correlation-id` + `CorrelationIdMiddleware` (`backend/app/core/middleware.py`) stamp a correlation ID on every request; it is persisted to `audit_log.correlation_id`
- Secret redaction helper: `backend/app/core/redact.py` (`redact_text`, `redact_mapping`)

**Health & telemetry endpoints** (`backend/app/api/v1/endpoints/health.py`):
- `GET /api/v1/health` — liveness
- `GET /api/v1/health/ready` — readiness (DB connectivity)
- `GET /api/v1/health/models` — provider/model metadata
- `GET /api/v1/health/connectors` — per-source connector health
- `GET /api/v1/sources/health` — `observability.py:98`, `SourceRegistryItem` list
- `GET /api/v1/observability/activity` — `observability.py:19`
- `GET /api/v1/scheduler` — `observability.py:250`, live scheduler job state (intervals, backoff, last status)

Honest-telemetry contract: connector health degrades to in-memory state when the DB is unreachable and never fabricates values (`backend/app/connectors/base.py:get_status`, D-22).

## CI/CD & Deployment

**Hosting:**
- Frontend → **Netlify** (`netlify.toml`): base `frontend`, publish `.next`, plugin `@netlify/plugin-nextjs`, security headers (`X-Frame-Options: DENY`, `nosniff`, `strict-origin-when-cross-origin`, restrictive `Permissions-Policy`)
- Backend → **Render** free web service (`render.yaml`): `region: oregon`, `branch: main`, build `pip install -r requirements.txt`, start `python run.py`, health check `/api/v1/health`
- Blueprint env vars: `AI_PROVIDER=gemini`, `GEMINI_MODEL=gemini-2.5-flash`, `APP_ENV=production`, `DEMO_MODE=false`, `SECRET_KEY` auto-generated, `DATABASE_URL`/`CORS_ORIGINS`/`GEMINI_API_KEY` synced manually

**CI pipeline — GitHub Actions** (`.github/workflows/ci.yml`), triggers on push to `main`/`develop`/`feature/*` and PRs to `main`/`develop`:
1. Service containers: `pgvector/pgvector:pg16` + `redis:7-alpine` with healthchecks
2. Python 3.11 + pip cache on `backend/requirements.txt`
3. `alembic upgrade head` then `python backend/app/db/seed.py`
4. `pytest -v`
5. `python scripts/export_openapi.py` then `git diff --exit-code frontend/types/api.ts` — **contract-drift gate**
6. pnpm 9 + Node 22
7. `tsc --noEmit` → `pnpm run check:banned-classes` → `pnpm lint` → `pnpm build`

**No CD job exists** — deployment is Netlify/Render git-integration only.

## Environment Configuration

**Required env vars (production):**
- `DATABASE_URL` — Postgres/Supabase connection string
- `SECRET_KEY` — session signing (auto-generated on Render)
- `CORS_ORIGINS` — exact Netlify origin, comma-separated
- `GEMINI_API_KEY` + `GEMINI_MODEL` — cloud AI provider
- `APP_ENV=production`, `DEMO_MODE=false`
- `SESSION_COOKIE_SAMESITE=none`, `SESSION_COOKIE_SECURE=true`
- `REDIS_URL` — set to `""` on Render (Redis optional)

**Optional / connector vars:**
- `NEWSAPI_KEY` (required for the NewsAPI connector to succeed — otherwise `CONFIGURATION_ERROR`)
- `NCBI_API_KEY`, `NCBI_TOOL`, `NCBI_EMAIL`, `OPENFDA_API_KEY`
- `XAI_API_KEY` / `GROK_API_KEY` (only when `ENABLE_GROK_FALLBACK=true`)
- `METARADAR_API_KEY` (enables `X-API-Key` gate on mutating endpoints)
- `OLLAMA_HOST`, `OLLAMA_MODEL` (local inference)

**Secrets location:**
- Local: `.env` at repo root and/or `backend/.env` (present, gitignored — contents not read)
- Reference template: `.env.example` (present, tracked)
- Production: Render dashboard env vars (`sync: false` entries) and Netlify environment settings
- **No secret manager (Vault/AWS Secrets Manager/Doppler) is integrated**

## Webhooks & Callbacks

**Incoming:** None. All integration traffic is outbound polling; connectors are invoked by the in-process `SourceScheduler` or by manual API calls.

**Outgoing:** None. No outbound webhooks, no Slack/Teams/email delivery.

**Server-Sent Events (not a webhook, but a push channel):**
- `POST /api/v1/athena/stream` — `backend/app/api/v1/endpoints/signals.py:1630`, streams Athena Copilot reasoning with inline citations
- Consumed by `frontend/lib/api.ts` and `frontend/components/intelligence/AthenaWorkspace.tsx`

---

*Integration audit: 2026-10-02*
