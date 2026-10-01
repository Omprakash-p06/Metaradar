# External Integrations

**Analysis Date:** 2026-10-01

## APIs & External Services (Ingestion Connectors)

All connectors live in `backend/app/connectors/` and are scheduled by `backend/app/services/scheduler.py` with intervals from `backend/app/core/config.py:122-134`. Domain profiles/queries in `config/haemophilia.yaml:202-322`.

| Connector | Module | Upstream endpoint / feed | Auth / key | Evidence |
|-----------|--------|--------------------------|------------|----------|
| PubMed (NCBI E-utilities) | `backend/app/connectors/pubmed.py` | NCBI E-utilities, 3 query profiles (clinical, safety, competitive) | `NCBI_API_KEY` optional, `NCBI_TOOL=MetaRadar`, `NCBI_EMAIL` | `backend/app/connectors/pubmed.py`, `config/haemophilia.yaml:203-220`, `backend/app/core/config.py:114-116` |
| ClinicalTrials.gov | `backend/app/connectors/clinical_trials.py` | ClinicalTrials.gov API v2, haemophilia + enterprise-sponsor profiles | None (public) | `backend/app/connectors/clinical_trials.py`, `config/haemophilia.yaml:222-234` |
| NewsAPI | `backend/app/connectors/newsapi.py` | NewsAPI.org, `quota_per_day: 100`, 7-day rolling window | `NEWSAPI_KEY` (or `NEWS_API_KEY` alias) **required** — missing key yields `CONFIGURATION_ERROR` | `backend/app/connectors/newsapi.py`, `config/haemophilia.yaml:236-248`, `backend/app/core/config.py:106-111,152-158`, `.env.example:26` |
| OpenFDA | `backend/app/connectors/fda.py` | `https://api.fda.gov/drug/drugsfda.json` + MedWatch RSS + safety comms | `OPENFDA_API_KEY` optional (higher rate limits) | `backend/app/connectors/fda.py`, `config/haemophilia.yaml:290-304`, `backend/app/core/config.py:119` |
| EMA | `backend/app/connectors/ema.py` | `https://www.ema.europa.eu/en/medicines/rss`, `/en/news/rss` (3 profiles) | None (public RSS) | `backend/app/connectors/ema.py`, `config/haemophilia.yaml:306-321` |
| Fierce Pharma | `backend/app/connectors/fierce_pharma.py` | `https://www.fiercepharma.com/rss/xml` + keyword filter | None | `backend/app/connectors/fierce_pharma.py`, `config/haemophilia.yaml:250-259` |
| ET Pharma | `backend/app/connectors/et_pharma.py` | `https://pharma.economictimes.indiatimes.com/rss/topstories`, `/rss/drug_approvals` | None | `backend/app/connectors/et_pharma.py`, `config/haemophilia.yaml:261-273` |
| BioPharma Dive | `backend/app/connectors/biopharma_dive.py` | `https://www.biopharmadive.com/feeds/news/` | None | `backend/app/connectors/biopharma_dive.py`, `config/haemophilia.yaml:275-287` |
| Shared base | `backend/app/connectors/base.py` | Retry/backoff, truthful `connector_status` telemetry | n/a | `backend/app/connectors/base.py`, `backend/app/connectors/__init__.py` |

> Source tiers (authoritative → lead-only) defined in `config/haemophilia.yaml:178-200`; freshness classes (`batch`, `near_real_time`, `delayed`, `adapter_ready`) per connector in same file.

## AI / Hosted Model Services

| Service | Endpoint | SDK / client | Auth | Evidence |
|---------|----------|--------------|------|----------|
| Ollama sidecar (local Gemma) | `OLLAMA_HOST` (`http://ollama:11434` in compose, `http://localhost:11434` default), `POST /api/generate`, `GET /api/tags`, model `gemma3:4b` | `httpx.AsyncClient` in `backend/app/providers/gemma.py:76-83` | None (localhost/sidecar) | `docker-compose.yml:45,111-131`, `backend/app/core/config.py:93-94`, `backend/app/providers/gemma.py:250-345` |
| xAI Grok (hosted fallback) | `https://api.x.ai/v1/chat/completions`, model `grok-beta` | `httpx.AsyncClient` in `backend/app/providers/grok.py:55-61` | `XAI_API_KEY` (or `GROK_API_KEY` alias); gated by `ENABLE_GROK_FALLBACK` + `validate_privacy_gate` (PUBLIC/SYNTHETIC only) | `backend/app/providers/grok.py:23-24,63-121`, `backend/app/core/config.py:79-85`, `backend/app/providers/factory.py:37-49` |
| Local GGUF file | `models/*.gguf` via `llama-cpp-python` (not an external service — offline) | `llama_cpp.Llama` lazy load | None | `backend/app/providers/gemma.py:94-132`, `models/README.md`, `models/gemma-3-4b-it-Q4_K_M.gguf` |
| No OpenAI/Anthropic/GCP direct | Not detected — no SDKs in `backend/requirements.txt` | n/a | n/a | `backend/requirements.txt` (only `httpx` for HTTP) |

## Data Storage & Connections

| Store | Connection string / env | Client / ORM | Evidence |
|-------|------------------------|--------------|----------|
| PostgreSQL 16 + pgvector | `DATABASE_URL=postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar` (local) / `@postgres:5432` (compose); CI uses `localhost:5432` service | SQLAlchemy 2.0 async (`asyncpg`), Alembic, `pgvector.sqlalchemy.Vector` (384-dim HNSW) | `backend/app/core/config.py:30`, `backend/alembic.ini:5`, `docker-compose.yml:41`, `backend/app/db/session.py`, `backend/app/models/__init__.py:9`, `backend/app/services/vector_query.py` |
| Redis 7 | `REDIS_URL=redis://localhost:6379/0` (local) / `redis://redis:6379/0` (compose); CI service on `6379` | `redis>=5.0.3` client; cache + scheduler + non-blocking readiness | `backend/app/core/config.py:31`, `docker-compose.yml:42`, `backend/app/api/v1/endpoints/cache.py`, `backend/app/api/v1/endpoints/health.py` |
| Local filesystem | `models/` (GGUF), `data/`, `config/` (ro mount), volumes `pgdata`, `redisdata`, `models_cache`, `ollama_models` | stdlib `pathlib`; `huggingface.co` URL for optional GGUF download | `setup.py:361-362`, `models/README.md`, `docker-compose.yml:13-14,26,50-51,118,133-137` |
| Embeddings cache | In-process lazy `fastembed TextEmbedding` singleton | `fastembed>=0.4.0` | `backend/app/services/embeddings.py:15,57` |
| No S3/GCS/blob store | Not detected | n/a | No object-store SDK in `backend/requirements.txt` |

## Authentication & Identity (Custom — No External IdP)

- **Implementation:** Custom session auth in `backend/app/api/v1/endpoints/auth.py` + `backend/app/services/auth_service.py`; `bcrypt` password hashing + `itsdangerous.TimestampSigner` signed cookies (`backend/app/core/security.py:5-21`).
- **Session:** 8h absolute / 1h idle cookies, `SESSION_COOKIE_SECURE` auto-true in production (`backend/app/core/config.py:36-41,60-63`); CSRF via `metaradar_csrf` cookie + `X-CSRF-Token` header enforced on POST/PUT/PATCH/DELETE (`frontend/lib/api.ts:163-214,390-398`).
- **Demo mode:** `DEMO_MODE=true` enables `POST /api/v1/auth/demo-login` with 8 seeded role users (passwords defaulted in `backend/app/core/config.py:40-49`, auto-seed in `backend/app/main.py:45-55`); blocked in production (`backend/app/core/config.py:140-149`, `start.py:317-328`).
- **Rate limits:** `AUTH_RATE_LIMIT_PER_MINUTE=5`, `MUTATION_RATE_LIMIT_PER_MINUTE=60` (`backend/app/core/config.py:50-53`).
- **No OAuth/OIDC/SAML/LDAP** detected — no `authlib`, `python-jose`, `next-auth` deps (`backend/requirements.txt`, `frontend/package.json`).

## File / Artifact Storage

- GGUF models: `models/` (`models/gemma-3-4b-it-Q4_K_M.gguf` present, `.gitkeep` for empty clone) — see `models/README.md:1-15`.
- Domain + seed data: `config/haemophilia.yaml`, `backend/app/db/seed.py` (assets, companies, synthetic landscape signals).
- Runtime logs: `logs/` (`logs/backend.log`, `logs/frontend.log` via `start.py:244,275`).
- No external CDN/file upload endpoints detected in `backend/app/api/v1/endpoints/`; frontend `public/` served statically (`frontend/Dockerfile:18`).

## Monitoring & Observability

- Structured JSON logs via `structlog` + correlation-ID + security-headers middleware (`backend/app/core/logging.py`, `backend/app/core/middleware.py`, `backend/app/main.py:26,76-78`); `start.py:409-431` streams `[ATHENA]/[INGESTION]/[PIPELINE]/[LLM]` markers with 15s heartbeat.
- Health endpoints: `GET /api/v1/health/ready` (PG+Redis), `/health/connectors`, `/health/models` — consumed by `frontend/lib/api.ts:523-556` and compose `healthcheck` (`docker-compose.yml:58-61`, `backend/app/api/v1/endpoints/health.py`).
- Scheduler/observability APIs: `/observability/activity`, `/sources/health`, scheduler status (`frontend/lib/api.ts:696-698`, `backend/app/api/v1/endpoints/observability.py`, `registry.py`).
- No Sentry/Datadog/Prometheus/Grafana/OpenTelemetry integration detected (no SDKs in manifests, no env vars for them).

## CI/CD & Deployment

- **CI:** `.github/workflows/ci.yml` (`MetaRadar CI`, `contents: read` least-privilege) — pgvector:pg16 + redis:7 services → pip → alembic + seed → `pytest -v` → OpenAPI contract diff → Node 22 + pnpm 9 → `tsc --noEmit` + `check:banned-classes` + `eslint` + `next build`.
- **Hosting:** Self-hosted Docker Compose (no Vercel/AWS/GCP/Azure manifests detected): `postgres`, `redis`, `backend` (`python:3.11-slim`, port 8000), `backend-gpu` (profile `gpu`, `LLM_DEVICE=cuda:0`), `frontend` (`node:20-alpine` multi-stage, port 3000), `ollama` (GPU reservation, port 11434) — `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`.
- **CORS:** `CORS_ORIGINS=http://localhost:3000` default (`backend/app/core/config.py:51,66-67`, `.env.example:28`); `allow_credentials=True` (`backend/app/main.py:81-88`).

## Environment Configuration (Required Vars)

Source of truth: `.env.example:1-28` (template) → `.env` (runtime, created by `setup.py:48-58`); typed defaults in `backend/app/core/config.py:16-137`. (`.env` contents never read — existence only.)

| Var | Required? | Default | Evidence |
|-----|-----------|---------|----------|
| `DATABASE_URL` | Yes (has local default) | `postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar` | `.env.example:2`, `backend/app/core/config.py:30` |
| `REDIS_URL` | Yes (has local default) | `redis://localhost:6379/0` | `.env.example:3`, `backend/app/core/config.py:31` |
| `LLM_PROVIDER` | Yes | `local` (`local\|xai\|auto`) | `.env.example:6`, `docker-compose.yml:43`, `backend/app/core/config.py:71` |
| `LOCAL_LLM_MODEL` / `OLLAMA_MODEL` / `OLLAMA_HOST` | For local reasoning | `google/gemma-3-4b-it` / `gemma3:4b` / `http://localhost:11434` | `.env.example:7`, `backend/app/core/config.py:72,93-94` |
| `LLM_DEVICE` / `LLM_DTYPE` / `MAX_CONTEXT_TOKENS` / `MAX_OUTPUT_TOKENS` | Tuning | `auto` / `int4` / `2048` / `512` | `.env.example:8-11`, `backend/app/core/config.py:73-76` |
| `LOCAL_GGUF_MODEL` / `LOCAL_GGUF_PATH` / `MODELS_DIR` | Optional (auto-scan `models/*.gguf`) | unset / `models/` | `models/README.md:11-14`, `backend/app/core/config.py:88-90`, `backend/app/providers/gemma.py:30-48` |
| `ENABLE_GROK_FALLBACK` + `XAI_API_KEY` (`GROK_API_KEY` alias) | Only for hosted fallback | `false` / empty; missing key while enabled → `CONFIGURATION_ERROR` | `.env.example:14-15`, `backend/app/core/config.py:79-85,159-162` |
| `EMBEDDING_MODEL` / `EMBEDDING_MODEL_REVISION` / `EMBEDDING_DIMENSION` / `EMBEDDING_MAX_SEQ_LENGTH` | Yes (pinned) | `sentence-transformers/all-MiniLM-L6-v2` / `e4bb823…` / `384` / `256` | `.env.example:18-21`, `backend/app/core/config.py:97-100` |
| `NEWSAPI_KEY` (`NEWS_API_KEY` alias) | Required for NewsAPI connector | empty → connector reports `CONFIGURATION_ERROR` | `.env.example:26`, `backend/app/core/config.py:106-111,152-158` |
| `NCBI_API_KEY` / `NCBI_TOOL` / `NCBI_EMAIL` | Optional | unset / `MetaRadar` / `metaradar@example.com` | `backend/app/core/config.py:114-116` |
| `OPENFDA_API_KEY` | Optional | unset | `backend/app/core/config.py:119` |
| `CORS_ORIGINS` | Yes | `http://localhost:3000` | `.env.example:28`, `backend/app/core/config.py:51` |
| `RAW_SIGNAL_RETENTION_DAYS` | Housekeeping | `30` | `.env.example:24`, `backend/app/core/config.py:103` |
| `APP_ENV` / `SECRET_KEY` / `DEMO_MODE` / `DEMO_*_PASSWORD` / `SESSION_*` / `METARADAR_API_KEY` | Prod-critical (`SECRET_KEY` + `DEMO_MODE=false` enforced in prod) | `development` / `dev-secret-change-in-production` / `true` | `backend/app/core/config.py:34-53,140-149`, `start.py:317-328` |
| `NEXT_PUBLIC_API_URL` (code) vs `NEXT_PUBLIC_API_BASE_URL` (compose) | Yes — mismatch, see gaps | `http://localhost:8000/api/v1` fallback in code | `frontend/lib/api.ts:171`, `start.py:283`, `docker-compose.yml:102` |
| Scheduler tunables `SCHEDULER_*` / `ENABLE_BACKGROUND_SCHEDULER` | Optional | `True`, per-connector 15–60 min, jitter 10% | `backend/app/core/config.py:122-134` |

## Inter-Service Contracts (Frontend ↔ Backend)

| Concern | Contract | Evidence |
|---------|----------|----------|
| Base URL | `API_BASE = process.env.NEXT_PUBLIC_API_URL \|\| 'http://localhost:8000/api/v1'`; `credentials: 'include'`, JSON headers, `x-request-id` propagation, `ApiError(retryable = status>=500 \|\| 429)` | `frontend/lib/api.ts:171,192-258` |
| Canonical TS contract | `frontend/types/api.ts` — hand-maintained (~790-line template: `Signal`, `AthenaResponse`, `ConfluenceAlertItem`, `LifecycleTimelineItem`, `ContradictionItem`, `MissingSignalWatchItem`, `Health*`, calibration/feedback, auth types) | `frontend/types/api.ts`, `scripts/export_openapi.py:39-779` |
| OpenAPI export | `python scripts/export_openapi.py` dumps live FastAPI schema (`app.openapi()`) to `contracts/openapi.json` + re-emits `frontend/types/api.ts` verbatim; CI fails on `git diff --exit-code frontend/types/api.ts` | `scripts/export_openapi.py:13-33,781-785`, `contracts/openapi.json`, `.github/workflows/ci.yml:76-81` |
| REST client | `frontend/lib/api.ts` (908 lines): overview, signals CRUD + review/approval, confluence/lifecycle/red-team/missing/developments, search (`POST /search`), Athena + SSE stream (`POST /athena`, `/athena/stream`, `/athena/suggested-questions`), feedback/calibration, ingestion run/sync-live, sources, cache clear, auth (login/demo-login/logout/me/csrf) | `frontend/lib/api.ts:264-908`, `frontend/lib/mappers.ts`, `frontend/lib/errors.ts` |
| Backend routers (prefix `/api/v1`) | `/health`, `/auth`, `/signals…`, intelligence (`/overview`, `/confluence`, `/lifecycles`, `/red-team`, `/missing-signals`, `/developments`, `/leadership/summary`, …), `/registry`+`/sources`, `/observability`, `/cache`, `/pipeline`, `/ingestion`, `/search`, `/feedback`+`/calibration` | `backend/app/main.py:69-101`, `backend/app/api/v1/endpoints/` (11 modules) |
| Streaming contract | SSE events `meta → token* → done` (+ `degraded`/`error` honest signals) on `POST /athena/stream`; frontend `streamAthena()` parses `event:/data:` frames | `frontend/lib/api.ts:367-485` |
| Health contract | `GET /api/v1/health/ready` → `{status: ready\|degraded, database, redis}`, `/health/connectors`, `/health/models` (`llm_provider`, `gemma_available`, `grok_configured`, embedding meta) | `frontend/lib/api.ts:55-57,523-556`, `scripts/export_openapi.py:241-311` |
| Auth contract | `POST /auth/login\|demo-login\|logout`, `GET /auth/me`, `GET /auth/csrf`; CSRF cookie `metaradar_csrf` + header `X-CSRF-Token` on mutating requests | `frontend/lib/api.ts:778-812,163-189`, `backend/app/api/v1/endpoints/auth.py` |

## Webhooks & Callbacks

- **Incoming:** None detected — no webhook receiver routes in `backend/app/api/v1/endpoints/`; ingestion is poll-based via `SourceScheduler` (`backend/app/main.py:57-60`).
- **Outgoing:** Only outbound client calls are connector fetches (PubMed/ClinicalTrials/NewsAPI/OpenFDA/EMA RSS/Tier-3 RSS), Ollama `POST /api/generate`, and xAI `POST /v1/chat/completions` — no third-party webhook delivery detected.

## Unknown / Needs Verification

- `NEXT_PUBLIC_API_URL` vs `NEXT_PUBLIC_API_BASE_URL` mismatch: compose injects `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` (`docker-compose.yml:102`) but the frontend client and `start.py` use `NEXT_PUBLIC_API_URL` (`frontend/lib/api.ts:171`, `start.py:283`) — verify which var the production `frontend/Dockerfile` build actually bakes in (`next start` serves pre-built client env).
- `scripts/export_openapi.py:13-23` honesty note: `frontend/types/api.ts` is re-emitted verbatim, NOT codegen'd from `contracts/openapi.json` — FastAPI↔TS drift can only be caught by human review of `openapi.json` diffs until `openapi-typescript` is adopted.
- NewsAPI quota (`100/day`, `.env.example:26` empty key) — whether CI/E2E runs with a real key or always exercises the `CONFIGURATION_ERROR` path is unverified; `tests/test_live_ingestion_e2e.py` vs `pytest.ini:9` `live` marker needs a key-in-CI check.
- xAI `grok-beta` model ID currency and `response_format: {"type": "json_object"}` support (`backend/app/providers/grok.py:24,100-105`) — verify against current `https://api.x.ai` docs; no pinned API version.
- NCBI `NCBI_TOOL`/`NCBI_EMAIL` defaults (`metaradar@example.com`) are placeholders (`backend/app/core/config.py:115-116`) — confirm compliance contact before production traffic.
- Secrets handling: `.env` file presence confirmed (never read per policy); whether `.env` is git-ignored and whether `XAI_API_KEY`/`NEWSAPI_KEY`/`SECRET_KEY`/`DEMO_*_PASSWORD` defaults ever ship to prod needs a secrets-scan verification (see `SECURITY_STANDARDS.md`).

---

*Integration audit: 2026-10-01*
