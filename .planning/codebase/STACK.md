# Technology Stack

**Analysis Date:** 2026-10-02

## Languages

| Language | Version | Where used | Evidence |
|----------|---------|------------|----------|
| Python | `>=3.11` declared; CI runs **3.11**; Render runs **3.13.5** | Backend API, LangGraph pipeline, connectors, providers, tests | `backend/requirements.txt`, `.github/workflows/ci.yml:44-48`, `render.yaml:14-15`, `backend/Dockerfile` |
| TypeScript | **5.7.3 (pinned, exact)** | All frontend `app/`, `components/`, `lib/`, `context/`, `types/` | `frontend/package.json:42` |
| SQL | PostgreSQL 16 dialect | Alembic migrations, pgvector DDL, hybrid queries | `backend/alembic.ini`, `backend/alembic/versions/` |
| YAML | n/a | Domain knowledge config, CI, compose, Render blueprint | `config/haemophilia.yaml`, `.github/workflows/ci.yml`, `docker-compose.yml`, `render.yaml` |
| JavaScript (ESM) | Node | Banned-class style gate, SVG→PNG conversion | `scripts/check-banned-classes.mjs` |

## Runtime

**Python:**
- Declared floor `>=3.11` in `setup.py`
- CI pins `python-version: "3.11"` (`.github/workflows/ci.yml:44-48`)
- Render blueprint pins `PYTHON_VERSION: 3.13.5` (`render.yaml:14-15`) — **runtime skew to be aware of**
- Docker image `python:3.11-slim` (`backend/Dockerfile`)

**Node:**
- `engines.node: ">=20.9.0"` (`frontend/package.json:8-10`)
- CI uses Node **22** (`.github/workflows/ci.yml`)
- Netlify pins `NODE_VERSION = "20"` (`netlify.toml:7-9`)

**Package Managers:**
- Backend: `pip` (`backend/requirements.txt`, no lockfile, no Poetry/uv)
- Frontend: **pnpm 9.15.5** via `packageManager` field (`frontend/package.json:6`); `frontend/pnpm-lock.yaml` is the lockfile
- Netlify installs with `PNPM_FLAGS = "--frozen-lockfile=false"` (`netlify.toml:7-9`) — lockfile is *not* enforced on deploy

**Dev orchestration:**
- `start.py` — unified launcher (Docker services + Alembic migrate + backend + frontend)
- `setup.py` / `scripts/*` — env bootstrap, model download, OpenAPI export
- `docker-compose.yml` — Postgres/pgvector, Redis, backend, backend-gpu (profile `gpu`), frontend, Ollama sidecar

## Frameworks

**Backend core:**
- **FastAPI** `>=0.110.0` — REST + SSE API (`backend/app/main.py`)
- **Uvicorn** `>=0.28.0` — ASGI server
- **Pydantic** `>=2.6.0` + **pydantic-settings** `>=2.2.0` — schemas and `Settings` (`backend/app/core/config.py`)
- **SQLAlchemy** `[asyncio]>=2.0.28` + **greenlet** + **asyncpg** `>=0.29.0` — async ORM
- **psycopg[binary]** `>=3.1.18` — synchronous driver used by Alembic migrations
- **Alembic** `>=1.13.1` — 15 migrations, `001_initial_v51_schema.py` → `015_approval_requests.py`
- **LangGraph** `>=0.2.0` — 11-node stateful pipeline (`backend/app/workflows/graph.py`)
- **pgvector** `>=0.2.5` — 384-dim vector column on `signals.embedding`
- **Redis** `>=5.0.3` — optional distributed locking/cache (`tests/test_redis_optional.py`)

**AI / ML:**
- **fastembed** `>=0.4.0` — ONNX CPU embedding runtime, model `sentence-transformers/all-MiniLM-L6-v2`, revision `e4bb823e...`, **384-dim**, sequence length 256 (`backend/app/services/embeddings.py:1-40`)
- **Ollama** (sidecar, not a pip dep) — hosts `gemma3:4b` (`docker-compose.yml`, `backend/app/core/config.py:OLLAMA_*`)
- **llama-cpp-python** — *optional, not declared in `requirements.txt`*; loaded opportunistically for local `.gguf` files (`backend/app/providers/gemma.py:1-50`)
- **Google Gemini** — REST via `httpx`, `gemini-2.5-flash`, no SDK (`backend/app/providers/gemini.py`)
- **xAI Grok** — opt-in hosted fallback, REST via `httpx` (`backend/app/providers/grok.py`)
- **BART degraded mode** — `backend/app/providers/degraded.py` (see CONCERNS: it is truncation-based, not an actual BART model)

**Testing:**
- **pytest** `>=8.0.0`, **pytest-asyncio** `>=0.23.0` (`asyncio_mode = auto`), **pytest-cov** `>=4.1.0`, **pytest-httpx** `>=0.30.0`
- Config: `pytest.ini` — `testpaths = tests`, `pythonpath = backend .`, marker `live`
- Frontend has **no Jest/Vitest**; the suite is `tsc --noEmit` + `eslint` + `next build`

**Frontend core:**
- **Next.js 16.3.0** (App Router, Turbopack) + **React ^19**
- **TypeScript 5.7.3** with `strict` mode
- **Tailwind CSS v4** via `@tailwindcss/postcss` (`^4.3.3`) — CSS-first config, no `tailwind.config.js`
- **framer-motion** `^13.1.0` — page/scroll animation
- **lucide-react** `^1.16.0` — icon set
- **recharts** `^3.10.1` — charts
- **@base-ui/react** `^1.5.0`, **shadcn** `^4.8.0`, **class-variance-authority**, **clsx**, **tailwind-merge**, **tw-animate-css**
- **@designcodeio/threeui** `^1.0.0` — 3D/holographic effects (`frontend/components/effects/star-portal/`)

**Build/Dev:**
- **ESLint** `^10.8.1` + `eslint-config-next` `^16.3.0`
- `scripts/check-banned-classes.mjs` — custom style gate, CI-enforced

## Key Dependencies

**Critical:**
- `langgraph>=0.2.0` — the intelligence engine itself; graph is defined in `backend/app/workflows/graph.py`
- `fastembed>=0.4.0` — powers novelty scoring, semantic search, confluence clustering
- `sqlalchemy[asyncio]>=2.0.28` + `asyncpg` — every endpoint and service is async
- `pgvector>=0.2.5` — HNSW cosine index used by `backend/app/services/vector_query.py`
- `bcrypt>=4.1.0` + `itsdangerous>=2.1.0` — password hashing and signed session cookies (`backend/app/core/security.py`)
- `structlog>=24.1.0` + `asgi-correlation-id>=4.3.0` — JSON logging and correlation IDs (`backend/app/core/logging.py`, `backend/app/core/middleware.py`)

**Infrastructure:**
- `httpx>=0.27.0` — every connector, the Gemini and Grok providers, and all tests (`pytest-httpx`)
- `pyyaml>=6.0.1` — loads `config/haemophilia.yaml` domain ontology
- `redis>=5.0.3` — *optional*; app must boot with `REDIS_URL=""`

## Configuration

**Environment:**
- Settings class: `backend/app/core/config.py` (`Settings(BaseSettings)`, `extra="ignore"`)
- Env file resolution order: `<root>/.env` → `backend/.env` → `.env` → `../.env` (`config.py:_ENV_FILES`)
- A `.env` and `.env.example` exist at repo root — **contents never read by this analysis**
- Production guard: `validate_production_settings()` raises when `APP_ENV` is `production`/`prod` and any of: default `SECRET_KEY`, `DEMO_MODE=True`, or a wildcard CORS origin is present (`config.py:140-149`)

**Notable settings groups** (`backend/app/core/config.py`):
- API: `PROJECT_NAME`, `API_V1_STR=/api/v1`, `VERSION`
- DB: `DATABASE_URL` (auto-normalized to `postgresql+asyncpg://` and password percent-encoded by a `field_validator`), `REDIS_URL` (optional)
- Auth: `SECRET_KEY`, `SESSION_LIFETIME_SECONDS=28800`, `SESSION_IDLE_TIMEOUT_SECONDS=3600`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_SAMESITE`, `AUTH_RATE_LIMIT_PER_MINUTE=5`, `MUTATION_RATE_LIMIT_PER_MINUTE=60`
- Demo: `DEMO_MODE`, `DEMO_AUTO_SEED_USERS`, and 8 plaintext `DEMO_PASSWORD_*` defaults
- AI: `AI_PROVIDER` (`auto|local|gemini|off`), `LLM_PROVIDER` (`local|xai|auto`), `GEMINI_MODEL=gemini-2.5-flash`, `GEMINI_TIMEOUT_S=60`, `GEMINI_MAX_RETRIES=3`, `ENABLE_GROK_FALLBACK`
- Providers: `XAI_API_KEY` / `GROK_API_KEY`, `NEWSAPI_KEY` / `NEWS_API_KEY`, `NCBI_API_KEY`, `OPENFDA_API_KEY`, `METARADAR_API_KEY`
- Scheduler: `ENABLE_BACKGROUND_SCHEDULER`, per-source `SCHEDULER_*_INTERVAL_MINUTES`, `SCHEDULER_JITTER_PERCENT=10`, `SCHEDULER_MAX_BACKOFF_MINUTES=120`
- Embeddings: `EMBEDDING_MODEL`, `EMBEDDING_MODEL_REVISION`, `EMBEDDING_DIMENSION=384`

**Build:**
- `frontend/next.config.mjs`, `frontend/tsconfig.json`, `frontend/postcss.config.*`
- `backend/alembic.ini`, `backend/Dockerfile`
- `netlify.toml` (frontend), `render.yaml` (backend), `docker-compose.yml`, `pytest.ini`
- API contract: `contracts/openapi.json` + hand-maintained `frontend/types/api.ts`, re-emitted by `scripts/export_openapi.py`

## Platform Requirements

**Development:**
- Docker Desktop/Engine (Postgres 16 + pgvector, Redis 7, optional Ollama)
- Python 3.11+
- Node.js 20.9+ and pnpm 9

**Production:**
- Frontend → **Netlify** (`netlify.toml`, base `frontend`, `@netlify/plugin-nextjs`)
- Backend → **Render** web service, `plan: free`, `region: oregon`, `rootDir: backend`, `startCommand: python run.py` (`render.yaml`)
- Database → **Supabase** Postgres (connection string injected via `DATABASE_URL`); `REDIS_URL` is deliberately empty on Render
- AI → Google **Gemini free tier** (`AI_PROVIDER=gemini`), with BART degraded mode as the terminal fallback
- Deployment runbook: `docs/DEPLOYMENT.md`

---

*Stack analysis: 2026-10-02*
