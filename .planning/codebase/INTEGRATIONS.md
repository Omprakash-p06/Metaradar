# External Integrations

**Analysis Date:** 2026-09-19

## APIs & External Services

**Clinical & regulatory (Tier 1 authoritative):**
- ClinicalTrials.gov v2 API - Trial ingestion
  - Connector: `backend/app/connectors/clinical_trials.py:18-29` (`source_id = "clinical_trials"`, `BASE_URL = "https://clinicaltrials.gov/api/v2/studies"`)
  - Profiles: `config/haemophilia.yaml:222-234` (haemophilia_trials conditions/interventions, novo_pipeline sponsor filter; backfill 365d, rolling 30d, max 500/profile)
  - Poll: every 60 min (`backend/app/core/config.py:123` `SCHEDULER_CT_INTERVAL_MINUTES`, wired in `backend/app/services/scheduler.py:66-72`)
  - Auth: none (public API)
- PubMed E-utilities - Publication ingestion
  - Connector: `backend/app/connectors/pubmed.py:21-29` (`source_id = "pubmed"`)
  - Profiles: `config/haemophilia.yaml:203-220` (3 query profiles; backfill 180d, rolling 30d, max 200/profile)
  - Poll: every 60 min (`SCHEDULER_PUBMED_INTERVAL_MINUTES`, `backend/app/core/config.py:124`)
  - Auth: optional `NCBI_API_KEY` + `NCBI_TOOL/NCBI_EMAIL` (`backend/app/core/config.py:113-116`)
- OpenFDA Drugs@FDA - Approval ingestion + MedWatch/Drug-Safety RSS
  - Connector: `backend/app/connectors/fda.py:20-40` (`source_id = "fda"`, `BASE_URL = "https://api.fda.gov/drug/drugsfda.json"`, RSS branch at `fda.py:68-90`)
  - Profiles: `config/haemophilia.yaml:290-304` (approvals search terms + 2 RSS safety feeds; backfill 365d, rolling 30d)
  - Poll: every 30 min (`SCHEDULER_FDA_INTERVAL_MINUTES`, `backend/app/core/config.py:126`)
  - Auth: optional `OPENFDA_API_KEY` for higher rate limits (`backend/app/core/config.py:119`)
- EMA medicines/news RSS - Regulatory ingestion
  - Connector: `backend/app/connectors/ema.py:19-39` (`source_id = "ema"`, default `https://www.ema.europa.eu/en/medicines/rss`)
  - Profiles: `config/haemophilia.yaml:306-321` (3 profiles incl. EPARs + orphan designations; backfill 365d, rolling 30d)
  - Poll: every 30 min (`SCHEDULER_EMA_INTERVAL_MINUTES`, `backend/app/core/config.py:125`)
  - Auth: none (public RSS)
- DailyMed - **Not detected**: no `dailymed.py` in `backend/app/connectors/` (8 connectors present: `__init__.py`, `base.py`, `biopharma_dive.py`, `clinical_trials.py`, `ema.py`, `et_pharma.py`, `fda.py`, `fierce_pharma.py`, `newsapi.py`, `pubmed.py`); FDA-label coverage comes from the OpenFDA connector above

**News & trade press (Tier 3 discovery):**
- NewsAPI - Market news (quota-guarded, 100 req/day)
  - Connector: `backend/app/connectors/newsapi.py:20-33` (`source_id = "newsapi"`, `BASE_URL = "https://newsapi.org/v2/everything"`)
  - Profiles: `config/haemophilia.yaml:236-248` (2 queries, `quota_per_day: 100`, backfill 30d, rolling 7d)
  - Poll: every 15 min (`SCHEDULER_NEWS_INTERVAL_MINUTES`, `backend/app/core/config.py:127`)
  - Auth: **required** `NEWSAPI_KEY` (or `NEWS_API_KEY`); missing/placeholder key yields `CONFIGURATION_ERROR` (`backend/app/core/config.py:109-111,140-143`)
- BioPharma Dive RSS - Trade-press ingestion
  - Connector: `backend/app/connectors/biopharma_dive.py:20-40` (`source_id = "biopharmadive"`, feed `https://www.biopharmadive.com/feeds/news/`)
  - Profiles: `config/haemophilia.yaml:275-287` (broad haemophilia keyword set; backfill 30d, rolling 7d)
  - Poll: default 30 min fallback (`backend/app/services/scheduler.py:73-75` — only ct/pubmed/ema/fda/newsapi have explicit intervals; all other connectors get `30`)
  - Auth: none
- FiercePharma RSS - Trade-press ingestion
  - Connector: `backend/app/connectors/fierce_pharma.py:19-39` (`source_id = "fierce_pharma"`, feed `https://www.fiercepharma.com/rss/xml`)
  - Profiles: `config/haemophilia.yaml:250-259` (backfill 30d, rolling 7d)
  - Poll: default 30 min fallback (same rule as above)
  - Auth: none
- ET Pharma (Economic Times) RSS - Trade-press ingestion
  - Connector: `backend/app/connectors/et_pharma.py:19-39` (`source_id = "et_pharma"`, feeds `/rss/topstories` + `/rss/drug_approvals`)
  - Profiles: `config/haemophilia.yaml:261-273` (2 profiles; backfill 30d, rolling 7d)
  - Poll: default 30 min fallback (same rule as above)
  - Auth: none

**Scheduler mechanics (all connectors):** per-source asyncio workers (`backend/app/services/scheduler.py:92-97`, started at boot `backend/app/main.py:56-59`), ±10% jitter, exponential backoff capped at 120 min, failure threshold 3 (`backend/app/core/config.py:128-131`), distributed **PostgreSQL advisory locks** (`backend/app/db/session.py:43-56` `pg_try_advisory_lock`, acquired in `backend/app/services/scheduler.py:133-179`), max 4 concurrent connectors (`scheduler.py:19`), LangGraph triggered only on new/changed records (`scheduler.py:47`).

**LLM providers:**
- Local Gemma 3 4B (primary) - Dual engine: GGUF via `llama-cpp-python` (installed by `setup.py:146-187`, loaded in `backend/app/providers/gemma.py:94-132`, model discovery `gemma.py:30-48` scanning `models/*.gguf`) **or** Ollama sidecar (`docker-compose.yml:108-131`, `OLLAMA_HOST`, model `gemma3:4b` in `backend/app/core/config.py:92-94`; HTTP client `gemma.py:76-83`, buffered + token-streaming `gemma.py:232-345`)
  - SDK/Client: `llama_cpp.Llama` (optional import) + `httpx.AsyncClient`; Auth: none (localhost)
- xAI Grok `grok-beta` (hosted fallback) - Real OpenAI-compatible chat API (`backend/app/providers/grok.py:23-24`, `XAI_API_URL = https://api.x.ai/v1/chat/completions`)
  - Chain: Gemma → Grok → BART (`backend/app/providers/factory.py:19-53`)
  - **Privacy gate**: only `PUBLIC`/`SYNTHETIC` classifications may leave the box; `UNKNOWN` blocked (`grok.py:63-74`, enforced pre-transmission in `grok.py:89-96`); missing key raises `GrokUnavailableError` → BART, keeping CI green without a key (`grok.py:149-150`)
  - Auth: `XAI_API_KEY` (or `GROK_API_KEY`); required only when `ENABLE_GROK_FALLBACK=true` (`backend/app/core/config.py:78-85,140-148`)
- BART (degraded, local heuristic) - Extractive truncation fallback, reasoning/actions disabled (`backend/app/providers/degraded.py:7-53`)

## Data Storage

**Databases:**
- PostgreSQL 16 + pgvector (`pgvector/pgvector:pg16` in `docker-compose.yml:2-3`)
  - Connection: `DATABASE_URL` (default `postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar` in `backend/app/core/config.py:30`; container variant in `docker-compose.yml:41`)
  - Client: SQLAlchemy 2 async + asyncpg; migrations Alembic (`backend/alembic.ini`, 15 revisions in `backend/alembic/versions/`); advisory-lock helpers `backend/app/db/session.py:43-56`
  - Seeds: `backend/app/db/seed.py` (canonical sources + synthetic rows, run by `setup.py:254-281` and auto-seed at boot `backend/app/main.py:44-54`)

**File Storage:**
- Local filesystem only: `models/` (GGUF, `LOCAL_GGUF_MODEL/PATH` in `backend/app/core/config.py:88-90`), `models_cache` + `ollama_models` Docker volumes (`docker-compose.yml:133-137`), `contracts/openapi.json`

**Caching:**
- Redis 7 (`redis:7-alpine` in `docker-compose.yml:20-21`; `redis>=5.0.3` in `backend/requirements.txt:9`)
  - Connection: `REDIS_URL` (`backend/app/core/config.py:31`)
  - Usage: cache-clear endpoint (`backend/app/api/v1/endpoints/cache.py:4,21-32` via `redis.asyncio`) + readiness probe (`backend/app/api/v1/endpoints/health.py:59-65`); **not** used for locking (locks are PostgreSQL advisory locks — see above)

## Authentication & Identity

**Auth Provider:**
- Custom session auth
  - Implementation: `backend/app/services/auth_service.py` (demo-persona seeding at startup), `bcrypt` hashing, `itsdangerous` signed cookies, 8h absolute / 1h idle sessions, 5/min auth rate limit (`backend/app/core/config.py:40-53`); demo login gated by `DEMO_MODE` (`config.py:40`)

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry/Datadog): structured JSON logs via `structlog` (`backend/app/main.py:25-26`, `backend/app/core/logging.py`), per-request correlation IDs (`CorrelationIdMiddleware` + `SecurityHeadersMiddleware` in `backend/app/main.py:75-77`), persisted `SourceHealthLog` rows + connector health endpoints (`backend/app/api/v1/endpoints/health.py`, `observability.py`)

**Logs:**
- structlog JSON to stdout + `logs/` directory at repo root; activity-log API (`frontend/types/api.ts:686-700` `ActivityLogItem`)

## CI/CD & Deployment

**Hosting:**
- Docker Compose (local + demo target): `postgres`, `redis`, `backend`, `backend-gpu` (profile `gpu`, `LLM_DEVICE=cuda:0`), `frontend`, `ollama` (`docker-compose.yml:1-137`); health-gated startup; `config/` mounted read-only

**CI Pipeline:**
- GitHub Actions (`.github/`): contract-sync gate — `scripts/export_openapi.py` re-emits `contracts/openapi.json` (live schema) + `frontend/types/api.ts` (hand-maintained template, **not** codegen — drift must be caught by human review of `openapi.json` diffs, per docstring at `export_openapi.py:13-23`); `scripts/check-banned-classes.mjs` (`frontend/package.json:14`); backend gates `tsc`/`pytest` per repo testing strategy

## Environment Configuration

**Required env vars:**
- `DATABASE_URL`, `REDIS_URL` (have working local defaults in `backend/app/core/config.py:30-31`)
- `LLM_PROVIDER` (`local|xai|auto`), `LLM_DEVICE`, `OLLAMA_HOST`, `MAX_CONTEXT_TOKENS=2048`/`MAX_OUTPUT_TOKENS=512`
- `NEWSAPI_KEY` — **required for news connector** (configuration-error state without it)
- `XAI_API_KEY` — required only when `ENABLE_GROK_FALLBACK=true`
- Optional tuning: `NCBI_API_KEY`, `OPENFDA_API_KEY`, `EMBEDDING_MODEL[/_REVISION/_DIMENSION]`, `RAW_SIGNAL_RETENTION_DAYS=30`, `CORS_ORIGINS`
- Full template: `.env.example:1-28`

**Secrets location:**
- Local `.env` at repo root (created from `.env.example` by `setup.py:48-58`; layered lookup `backend/app/core/config.py:6-21`); CI/prod injects via environment — never committed (see `.gitignore`)

## Webhooks & Callbacks

**Incoming:**
- None (no webhook receivers; ingestion is poll-based via `SourceScheduler`)

**Outgoing:**
- `POST https://api.x.ai/v1/chat/completions` (Grok fallback, gated) — `backend/app/providers/grok.py:107-114`
- `POST {OLLAMA_HOST}/api/generate` (local inference, buffered + NDJSON stream) — `backend/app/providers/gemma.py:255-265,323`
- Upstream source fetches: ClinicalTrials.gov v2, PubMed E-utilities, `api.fda.gov`, EMA/RSS feeds, `newsapi.org` (connector `BASE_URL`s above)

## Realtime / Streaming

- SSE `text/event-stream` for Ask Athena: `StreamingResponse` in `backend/app/api/v1/endpoints/signals.py:1755-1757`, events `meta`/`token`/`degraded`/`done` (`signals.py:1412,1676-1753`); token path streams Gemma (`generate_stream` in `gemma.py:281-345`), degraded path replays 24-char chunks (`signals.py:1746-1749`)
- Contract: `AthenaResponse` / `AthenaEvidenceCitation` in `frontend/types/api.ts:332-352`

---

*Integration audit: 2026-09-19*
