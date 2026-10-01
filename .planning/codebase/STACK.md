# Technology Stack

**Analysis Date:** 2026-10-01

## Languages

| Language | Version | Where used | Evidence |
|----------|---------|------------|----------|
| Python | `>=3.11` (Docker `python:3.11-slim`) | Backend API, LangGraph pipeline, connectors, providers | `backend/Dockerfile:1`, `backend/requirements.txt`, `setup.py:69-72`, `.github/workflows/ci.yml:44-48` |
| TypeScript | `5.7.3` (pinned) | Next.js frontend, all `app/`, `components/`, `lib/`, `types/` | `frontend/package.json:42`, `frontend/tsconfig.json:2-33` |
| SQL (PostgreSQL + pgvector dialect) | PostgreSQL 16 | Migrations, vector index DDL | `backend/alembic.ini:5`, `backend/alembic/versions/`, `backend/app/models/__init__.py:9` |
| YAML | n/a | Domain config, CI, compose | `config/haemophilia.yaml`, `docker-compose.yml`, `.github/workflows/ci.yml` |
| JavaScript (ESM) | ES6 target | Build/tooling scripts | `frontend/tsconfig.json:5`, `frontend/next.config.mjs`, `scripts/check-banned-classes.mjs` |

## Runtime

| Component | Version | Evidence |
|-----------|---------|----------|
| Node.js | `>=20.9.0` engines; `.nvmrc` pins `20`; Docker builder `node:20-alpine`; CI uses Node `22` | `frontend/package.json:6-8`, `frontend/.nvmrc:1`, `frontend/Dockerfile:1,11`, `.github/workflows/ci.yml:88-93` |
| Python | `3.11` (CI `setup-python@v5 python-version: "3.11"`, Docker `python:3.11-slim`) | `backend/Dockerfile:1`, `.github/workflows/ci.yml:44-48`, `setup.py:69-72` |
| Uvicorn (ASGI server) | `>=0.28.0` | `backend/requirements.txt:2`, `backend/Dockerfile:19`, `start.py:252-260` |
| Next.js server | `16.3.0` | `frontend/package.json:23`, `frontend/Dockerfile:9,23`, `start.py:273-297` |

## Package Manager

| Ecosystem | Manager + version | Lockfile | Install command |
|-----------|-------------------|----------|-----------------|
| Frontend | `pnpm@9.15.5` preferred, `npm` fallback | `frontend/pnpm-lock.yaml` + `frontend/package-lock.json` both committed | `pnpm install` (see `setup.py:200-217`, `frontend/Dockerfile:6`, `.github/workflows/ci.yml:98`) |
| Backend | `pip` (no poetry/uv) | None (`requirements.txt` only, no `requirements.lock`) | `pip install -r backend/requirements.txt` (see `setup.py:130-143`, `backend/Dockerfile:10`) |
| Python AI extras | `pip` + custom CUDA wheel index | None | `llama-cpp-python` via PyPI or `https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu124` (see `setup.py:146-187`) |

> Note: `frontend/.pnpmrc:1` sets `minimum-release-age=0`; `frontend/pnpm-workspace.yaml:1-2` declares single package `'.'`.

## Frameworks

### Frontend (`frontend/`)

| Package | Version | Purpose | Evidence |
|---------|---------|---------|----------|
| `next` | `16.3.0` (pinned) | App Router framework | `frontend/package.json:23` |
| `react` / `react-dom` | `^19` | UI runtime | `frontend/package.json:24-25` |
| `typescript` | `5.7.3` | Type safety (`strict: true`, `noEmit`, path alias `@/*`) | `frontend/package.json:42`, `frontend/tsconfig.json:7,21-23` |
| `tailwindcss` | `^4.3.3` + `@tailwindcss/postcss ^4.3.3` | CSS-first styling (`@theme inline` per PROJECT.md) | `frontend/package.json:34,41`, `frontend/postcss.config.mjs:4` |
| `framer-motion` | `^13.1.0` | Animation | `frontend/package.json:21` |
| `recharts` | `^3.10.1` | Portfolio momentum / charts | `frontend/package.json:26` |
| `@base-ui/react` | `^1.5.0` | Headless UI primitives | `frontend/package.json:17` |
| `shadcn` | `^4.8.0` + `components.json` style `base-nova`, `lucide` icons, `tailwind-merge`, `clsx`, `class-variance-authority`, `tw-animate-css` | Design system | `frontend/package.json:17-29`, `frontend/components.json:1-21` |
| `eslint` / `eslint-config-next` / `@next/eslint-plugin-next` | `^10.8.1` / `^16.3.0` | Flat-config lint (`eslint.config.mjs`) | `frontend/package.json:32-39`, `frontend/eslint.config.mjs:1-16` |

### Backend (`backend/`)

| Package | Version | Purpose | Evidence |
|---------|---------|---------|----------|
| `fastapi` | `>=0.110.0` | REST API (`app/main.py` lifespan, 11 routers) | `backend/requirements.txt:1`, `backend/app/main.py:69-101` |
| `uvicorn` | `>=0.28.0` | ASGI server | `backend/requirements.txt:2` |
| `pydantic` / `pydantic-settings` | `>=2.6.0` / `>=2.2.0` | Schemas + `Settings` env config | `backend/requirements.txt:3-4`, `backend/app/core/config.py:16-137` |
| `sqlalchemy` + `asyncpg` | `>=2.0.28` + `>=0.29.0` | Async ORM + PG driver | `backend/requirements.txt:5-6`, `backend/app/db/session.py` |
| `alembic` | `>=1.13.1` | Async migrations | `backend/requirements.txt:7`, `backend/alembic.ini:1-5` |
| `pgvector` | `>=0.2.5` | `Vector` column type, HNSW cosine search | `backend/requirements.txt:8`, `backend/app/models/__init__.py:9`, `backend/app/services/vector_query.py:1-53` |
| `redis` | `>=5.0.3` | Cache + health checks | `backend/requirements.txt:9`, `docker-compose.yml:20-32` |
| `langgraph` | `>=0.2.0` | 10-node intelligence workflow (`StateGraph`) | `backend/requirements.txt:16`, `backend/app/workflows/graph.py:2` |
| `structlog` + `asgi-correlation-id` | `>=24.1.0` + `>=4.3.0` | JSON structured logging + request-ID middleware | `backend/requirements.txt:18-19`, `backend/app/core/logging.py:22-51`, `backend/app/main.py:26,77-78` |
| `bcrypt` + `itsdangerous` | `>=4.1.0` + `>=2.1.0` | Password hashing + signed session/CSRF cookies | `backend/requirements.txt:21-22`, `backend/app/core/security.py:5-21` |
| `httpx` | `>=0.27.0` | Connector HTTP + Ollama/Grok clients | `backend/requirements.txt:11`, `backend/app/providers/gemma.py:21`, `backend/app/providers/grok.py:14` |
| `pyyaml` / `python-dotenv` | `>=6.0.1` / `>=1.0.1` | Domain YAML + `.env` loading | `backend/requirements.txt:10,12`, `backend/app/core/config.py:6-13` |

### Testing

| Package | Version | Purpose | Evidence |
|---------|---------|---------|----------|
| `pytest` / `pytest-asyncio` / `pytest-cov` / `pytest-httpx` | `>=8.0.0` / `>=0.23.0` / `>=4.1.0` / `>=0.30.0` | Backend suite (`asyncio_mode=auto`, `testpaths=tests`) | `backend/requirements.txt:13-15,20`, `pytest.ini:1-9` |
| `tsc --noEmit` (TS 5.7.3) | pinned | Frontend type gate | `.github/workflows/ci.yml:99`, `frontend/tsconfig.json` |
| `eslint .` (v10 flat) + `check:banned-classes` | — | Frontend lint + design-system gate | `frontend/package.json:14`, `scripts/check-banned-classes.mjs`, `.github/workflows/ci.yml:100-101` |
| `next build` (Next 16.3.0) | — | Production build gate | `frontend/package.json:11`, `.github/workflows/ci.yml:102` |

## Database & Storage

| System | Version / detail | Evidence |
|--------|------------------|----------|
| PostgreSQL + pgvector | `pgvector/pgvector:pg16` image; `384-dim` HNSW cosine index | `docker-compose.yml:3`, `.github/workflows/ci.yml:18`, `backend/app/services/embeddings.py`, `backend/app/services/vector_query.py` |
| Redis | `redis:7-alpine` image | `docker-compose.yml:21`, `.github/workflows/ci.yml:32` |
| Alembic | `>=1.13.1`, `sqlalchemy.url` asyncpg | `backend/alembic.ini:5`, `backend/alembic/versions/` |
| Local file storage | `models/*.gguf`, `data/`, Docker volumes `pgdata`, `redisdata`, `models_cache`, `ollama_models` | `models/README.md`, `docker-compose.yml:13-14,26,50-51,118,133-137` |
| No S3 / object store | Not detected — local filesystem + PG only | `docker-compose.yml`, `backend/app/` (no boto/s3 deps in `backend/requirements.txt`) |

## AI / LLM Stack (Local Gemma-first chain)

| Layer | Implementation | Evidence |
|-------|---------------|----------|
| Primary: Local Gemma 3 4B GGUF | `llama-cpp-python` loads `models/gemma-3-4b-it-Q4_K_M.gguf` (~2.48 GB, `Q4_K_M` quant); `n_gpu_layers=-1` on CUDA else `0`; `n_ctx=2048`, `max_tokens=512`, `temp=0.2` | `backend/app/providers/gemma.py:94-160,232-248`, `models/README.md:1-15`, `setup.py:361-362`, `backend/app/core/config.py:71-76,87-90` |
| Primary alt: Ollama sidecar | `ollama/ollama:latest` service, model `gemma3:4b`, `OLLAMA_HOST=http://ollama:11434` (compose) / `http://localhost:11434` (local default); `/api/generate` buffered + NDJSON streaming | `docker-compose.yml:108-131`, `backend/app/providers/gemma.py:250-345`, `backend/app/core/config.py:93-94` |
| Hosted fallback: xAI Grok | `grok-beta` at `https://api.x.ai/v1/chat/completions`, gated by `validate_privacy_gate` (PUBLIC/SYNTHETIC only), key via `XAI_API_KEY`/`GROK_API_KEY`, enabled by `ENABLE_GROK_FALLBACK` | `backend/app/providers/grok.py:23-24,63-74`, `backend/app/providers/factory.py:37-49` |
| Degraded fallback: BART-labeled factual mode | `DegradedProvider` (`facebook/bart-large-cnn` label) — truncation to 280–300 chars, `reasoning_available=False`, `actions_available=False`; no torch/transformers inference, stdlib only | `backend/app/providers/degraded.py:7-58`, `backend/app/providers/factory.py:51-53` |
| Orchestration | `ProviderFactory` chain: Local Gemma → Grok (if key + privacy gate) → BART degraded; `LLM_PROVIDER=local\|xai\|auto` | `backend/app/providers/factory.py:19-53`, `backend/app/core/config.py:71` |
| Embeddings | `fastembed` (`>=0.4.0`) ONNX CPU, model `sentence-transformers/all-MiniLM-L6-v2` rev `e4bb823e5956b6277b069d276b978c48a73507c7`, `EMBEDDING_DIMENSION=384`, `MAX_SEQ_LENGTH=256`; no torch/sentence-transformers stack | `backend/requirements.txt:17`, `backend/app/services/embeddings.py:1-57`, `backend/app/core/config.py:97-100`, `.env.example:18-21` |
| Workflow reasoning | `langgraph>=0.2.0` 10-node graph (`graph.py`, `nodes/`, `runner.py`, `state.py`) | `backend/requirements.txt:16`, `backend/app/workflows/` |
| GPU path | CUDA 12.4 wheel index for `llama-cpp-python` on RTX 3050 4 GB (`MAX_CONTEXT_TOKENS=2048`); `LLM_DEVICE=cpu\|cuda:0\|cuda\|auto`, `LLM_GPU_LAYERS`, `LLM_DTYPE=int4`; compose `backend-gpu` profile (`LLM_DEVICE=cuda:0`) | `setup.py:166-187`, `docker-compose.yml:64-93`, `backend/app/providers/gemma.py:106-116`, `docker-compose.yml:109-110` |

## Infra / Tooling / Operations

| Area | Tool | Evidence |
|------|------|----------|
| Orchestration | Docker Compose: `postgres`, `redis`, `backend`, `backend-gpu` (profile `gpu`), `frontend`, `ollama` | `docker-compose.yml:1-137` |
| Zero-config setup | `python setup.py` — 7 steps: prereqs → backend pip → llama-cpp (CUDA/CPU) → frontend pnpm/npm → docker postgres+redis → alembic + seed → Gemma GGUF / Grok key | `setup.py:32,412-464` |
| Process launcher | `python start.py` — docker backing services, alembic upgrade, uvicorn `app.main:app`, `pnpm/npm run dev`, live log telemetry, production `SECRET_KEY`/`DEMO_MODE` guard | `start.py:173-230,241-297,317-328` |
| CI | GitHub Actions `MetaRadar CI`: pip install → alembic + seed → `pytest -v` → `export_openapi.py` contract diff → pnpm install → `tsc --noEmit` + `check:banned-classes` + `eslint` + `next build` | `.github/workflows/ci.yml:41-102` |
| Contract export | `python scripts/export_openapi.py` — dumps `contracts/openapi.json`, re-emits `frontend/types/api.ts` template verbatim | `scripts/export_openapi.py:13-33` |
| Domain config | `config/haemophilia.yaml` (v1.0.0, 7 assets, 9 lifecycle stages, tiered sources, scheduler profiles) mounted read-only into backend | `config/haemophilia.yaml:1-339`, `docker-compose.yml:49,80` |
| Logging | `structlog` JSON logs + correlation-ID + security-headers middleware | `backend/app/core/logging.py`, `backend/app/core/middleware.py`, `backend/app/main.py:76-78` |
| Lint/format | ESLint v10 flat (`@next/next` recommended + core-web-vitals); no Prettier/Biome config detected | `frontend/eslint.config.mjs`, `frontend/package.json` (no prettier dep) |

## Build / Test / Run Commands

```bash
# Full zero-config bootstrap + launch
python setup.py [--skip-docker --skip-models --skip-cuda --skip-frontend --skip-db-seed --download-model --api-key KEY --no-interactive]  # setup.py:13-20
python start.py [--no-frontend --no-backend --no-docker --port-backend 8000 --port-frontend 3000 --daemon]  # start.py:9-16

# Backend
pip install -r backend/requirements.txt            # backend/Dockerfile:10, setup.py:137-140
cd backend && alembic upgrade head                 # backend/alembic.ini, .github/workflows/ci.yml:63
python backend/app/db/seed.py                      # .github/workflows/ci.yml:65, setup.py:271-277
pytest -v                                          # pytest.ini:1-9, .github/workflows/ci.yml:74
python scripts/export_openapi.py                    # scripts/export_openapi.py:13-33

# Frontend (frontend/)
pnpm install          # preferred (packageManager pnpm@9.15.5)
pnpm exec tsc --noEmit
pnpm run check:banned-classes
pnpm lint             # eslint .
pnpm build            # next build
pnpm run dev -- -p 3000
```

## Platform Requirements

- **Development:** Python `>=3.11`, Node `>=20.9.0` (`.nvmrc: 20`), pnpm 9 (npm fallback), Docker (postgres + redis) or local PG16+Redis7 on `5432`/`6379`, ~2.5 GB free for GGUF optional, NVIDIA GPU optional (`nvidia-smi` check in `setup.py:109-127`).
- **Production:** Docker images `python:3.11-slim` (backend, non-root `appuser`) and `node:20-alpine` multi-stage (frontend); `APP_ENV=production` requires non-default `SECRET_KEY` and `DEMO_MODE=false` (`backend/app/core/config.py:140-149`, `start.py:317-328`); Postgres 16 + pgvector, Redis 7, Ollama sidecar with `gemma3:4b`.

## Unknown / Needs Verification

- Exact installed (resolved) versions not pinned — all manifests use `>=`/`^` ranges; no `requirements.lock` and `pnpm install --frozen-lockfile=false` in CI (`.github/workflows/ci.yml:98`) means reproducible builds are not guaranteed.
- `llama-cpp-python` version is unpinned and installed outside `backend/requirements.txt` (`setup.py:146-187`); CUDA wheel index is a third-party GitHub Pages URL (`jllllll.github.io`) — availability/SLA unverified.
- `docker-compose.yml:102` sets `NEXT_PUBLIC_API_BASE_URL` but `frontend/lib/api.ts:171` and `start.py:283` use `NEXT_PUBLIC_API_URL` — which var the deployed frontend actually honors needs runtime verification.
- `DegradedProvider` default `facebook/bart-large-cnn` is a label only — no transformers/BART inference code or weight download detected (`backend/app/providers/degraded.py`, `models/` contains only GGUF).
- Deprecated `NEWS_API_KEY` vs `NEWSAPI_KEY` alias and `GROK_API_KEY` vs `XAI_API_KEY` alias both accepted (`backend/app/core/config.py:106-111,81-85`) — canonical var for docs needs a decision.
- Frontend `package-lock.json` and `pnpm-lock.yaml` both committed — single source of truth for frontend lockfile unverified.

---

*Stack analysis: 2026-10-01*
