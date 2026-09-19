# Technology Stack

**Analysis Date:** 2026-09-19

## Languages

**Primary:**
- Python 3.11+ - Backend API, pipeline, connectors (`backend/`, requires `>=3.11` per `setup.py:70-72`, runtime `python:3.11-slim` in `backend/Dockerfile:1`)
- TypeScript 5.7.3 - Frontend (`frontend/`, pinned `typescript: 5.7.3` in `frontend/package.json:42`, `strict: true` in `frontend/tsconfig.json:7`)
- SQL (PostgreSQL dialect + pgvector) - Migrations in `backend/alembic/versions/` (15 revisions, `001_initial_v51_schema.py` → `015_approval_requests.py`)

**Secondary:**
- JavaScript (ES6 target) - Frontend interop (`frontend/tsconfig.json:5` sets `target: ES6`, `allowJs: true`)
- YAML - Domain configuration (`config/haemophilia.yaml`), CI workflows (`.github/`)
- MJS - Build scripts (`scripts/check-banned-classes.mjs`, `frontend/next.config.mjs`)

## Runtime

**Environment:**
- Python 3.11-slim (Docker) / 3.11+ (local dev) - `backend/Dockerfile:1`, `setup.py:70`
- Node.js >=20.9.0 - `frontend/package.json:6-8` (`engines: node >=20.9.0`)
- Uvicorn ASGI server - `backend/Dockerfile:19` (`uvicorn app.main:app --host 0.0.0.0 --port 8000`)

**Package Manager:**
- pnpm 9.15.5 (preferred) with npm fallback - `frontend/package.json:5` (`packageManager: pnpm@9.15.5`), `setup.py:190-217`
- pip - Backend (`setup.py:133-143` installs `backend/requirements.txt`)
- Lockfile: missing (no `pnpm-lock.yaml` / `package-lock.json` detected in `frontend/`, no `requirements*.lock` in `backend/`)

## Frameworks

**Core:**
- Next.js 16.3.0 - Frontend app (`frontend/package.json:23`, pinned `next: 16.3.0`; `eslint-config-next ^16.3.0`, `@next/eslint-plugin-next ^16.3.0`)
- React 19 - UI (`frontend/package.json:24-25`, `react ^19` / `react-dom ^19`, `@types/react ^19`)
- FastAPI >=0.110.0 - Backend API (`backend/requirements.txt:1`; app entry `backend/app/main.py:68-73`; note: floor pin is `0.110.0`, not `0.115` — installed version resolves at `pip install` time)
- SQLAlchemy >=2.0.28 (async) + asyncpg >=0.29.0 - ORM + driver (`backend/requirements.txt:5-6`)
- LangGraph >=0.2.0 - 11-node intelligence pipeline (`backend/requirements.txt:16`, graph in `backend/app/workflows/graph.py:2,30`)

**Testing:**
- pytest >=8.0.0 + pytest-asyncio >=0.23.0 + pytest-cov >=4.1.0 + pytest-httpx >=0.30.0 - Backend tests (`backend/requirements.txt:13-15,20`; config `pytest.ini:1-9` with `asyncio_mode = auto`)
- ESLint 10.8.1 + `eslint-config-next` - Frontend lint (`frontend/package.json:38-39`, script `frontend/package.json:12`)

**Build/Dev:**
- Turbopack: Not detected - `frontend/next.config.mjs:1-8` has no `turbopack` key and scripts use plain `next dev` / `next build` (`frontend/package.json:10-11`)
- PostCSS 8.5 + Tailwind CSS 4.3.3 + `@tailwindcss/postcss 4.3.3` - Styling (`frontend/package.json:34,41-42`)
- Alembic >=1.13.1 - DB migrations (`backend/requirements.txt:7`, config `backend/alembic.ini:1-5`, 15 versions in `backend/alembic/versions/`)
- `scripts/export_openapi.py` - Contract export (`contracts/openapi.json` + `frontend/types/api.ts`)

## Key Dependencies

**Critical:**
- `pgvector>=0.2.5` - Vector similarity search, 384-dim embeddings (`backend/requirements.txt:8`; image `pgvector/pgvector:pg16` in `docker-compose.yml:3`)
- `redis>=5.0.3` - Cache management + health checks (`backend/requirements.txt:9`; image `redis:7-alpine` in `docker-compose.yml:21`)
- `fastembed>=0.4.0` - ONNX/CPU embedding runtime, **replaces** torch + sentence-transformers stack (`backend/requirements.txt:17`; `backend/app/services/embeddings.py:1-15` — model `sentence-transformers/all-MiniLM-L6-v2`, 384-dim, rev pinned in `.env.example:18-20`)
- `pydantic>=2.6.0` + `pydantic-settings>=2.2.0` - Settings/validation (`backend/requirements.txt:3-4`; `backend/app/core/config.py:16-21`)
- `httpx>=0.27.0` - All outbound HTTP (connectors, Ollama, xAI) (`backend/requirements.txt:11`)
- `structlog>=24.1.0` + `asgi-correlation-id>=4.3.0` - Structured JSON logging + request correlation (`backend/requirements.txt:18-19`; `backend/app/main.py:25-26`, middleware `backend/app/main.py:76-77`)
- `llama-cpp-python` - Local GGUF inference engine, **not in `backend/requirements.txt`**; installed separately by `setup.py:146-187` (CUDA 12.4 wheel when `nvidia-smi` present, else CPU); consumed lazily in `backend/app/providers/gemma.py:97,123-131`
- `bcrypt>=4.1.0` + `itsdangerous>=2.1.0` - Auth hashing + signed sessions (`backend/requirements.txt:21-22`)

**Infrastructure:**
- `pyyaml>=6.0.1` + `python-dotenv>=1.0.1` - Domain config + env loading (`backend/requirements.txt:10,12`)
- `recharts ^3.10.1` - Dashboard charts (`frontend/package.json:26`)
- `framer-motion ^13.1.0`, `lucide-react ^1.16.0`, `class-variance-authority ^0.7.1`, `clsx ^2.1.1`, `tailwind-merge ^3.3.1` - UI primitives (`frontend/package.json:19-22,27-29`)
- `@base-ui/react ^1.5.0`, `@designcodeio/threeui ^1.0.0`, `shadcn ^4.8.0`, `tw-animate-css ^1.4.0` - Component layers (`frontend/package.json:17-18,27,29`)

## ML / Reasoning Models (with evidence)

| Model | Role | Evidence |
|-------|------|----------|
| Gemma 3 4B Instruct (Q4_K_M GGUF, ~2.48 GB) | Primary local reasoning via `llama-cpp-python` or Ollama sidecar | `setup.py:361-362` download URL `unsloth/gemma-3-4b-it-GGUF`; `backend/app/providers/gemma.py:30-48,94-132`; `docker-compose.yml:108-131` ollama service (`ollama/ollama:latest`); `backend/app/core/config.py:72-76,92-94` (`LOCAL_LLM_MODEL=google/gemma-3-4b-it`, `OLLAMA_MODEL=gemma3:4b`, `MAX_CONTEXT_TOKENS=2048`) |
| xAI Grok `grok-beta` | Hosted fallback behind privacy gate | `backend/app/providers/grok.py:23-24` (`XAI_API_URL`, `XAI_MODEL = grok-beta`); factory chain `backend/app/providers/factory.py:19-53` (Gemma → Grok → BART) |
| `facebook/bart-large-cnn` (label only) | Degraded factual summarizer — **heuristic truncation, no model weights loaded** | `backend/app/providers/degraded.py:11-19` (default `model_name`, `cleaned[:297]` truncation); capabilities `[SUMMARIZE]` only (`degraded.py:9`) |
| BART-Large-MNLI | **Not detected** — no `mnli`/`transformers` reference anywhere in `backend/`; contradiction detection is heuristic (`backend/app/services/redteam.py:62-64` in-process cache, no NLI model load) | — |
| `sentence-transformers/all-MiniLM-L6-v2` rev `e4bb823e…` (384-dim, seq 256) | Embeddings via fastembed ONNX (no torch) | `.env.example:18-20`, `backend/app/core/config.py:97-100`, `backend/app/services/embeddings.py:1-15`, `backend/app/workflows/nodes/embed.py:4` |

## Configuration

**Environment:**
- `.env` bootstrapped from `.env.example` by `setup.py:48-58` (keys: `DATABASE_URL`, `REDIS_URL`, `LLM_PROVIDER/LLM_DEVICE/LLM_DTYPE`, `ENABLE_GROK_FALLBACK/XAI_API_KEY`, `EMBEDDING_MODEL[/_REVISION/_DIMENSION]`, `NEWSAPI_KEY`, `CORS_ORIGINS`, `RAW_SIGNAL_RETENTION_DAYS=30`)
- Layered env-file lookup in `backend/app/core/config.py:6-21` (repo-root `.env` → `backend/.env`)
- Secrets: `.env` file present at repo root (existence only — contents never read); template values only in `.env.example`
- Domain config: `config/haemophilia.yaml` (v`1.0.0`: diseases, 7 assets, signal types, routing matrix, source tiers, per-connector profiles) mounted read-only into containers (`docker-compose.yml:49,80`)

**Build:**
- `frontend/next.config.mjs` (images unoptimized), `frontend/tsconfig.json` (strict, `@/*` alias → `./*`, `moduleResolution: bundler`)
- `backend/alembic.ini` (script location `alembic/`, local-dev `sqlalchemy.url`)
- `backend/Dockerfile` (python:3.11-slim, non-root `appuser`), `frontend/Dockerfile`, `docker-compose.yml` (6 services + 4 volumes)
- `setup.py` 7-step zero-config launcher (prereqs → backend deps → llama-cpp → frontend → docker → migrations/seed → model setup)

## Platform Requirements

**Development:**
- Python 3.11+, Node 20+, pnpm 9 (or npm), Docker (Postgres + Redis), optional NVIDIA GPU (`nvidia-smi` gates CUDA wheel in `setup.py:108-127,146-187`); optional 2.48 GB GGUF download into `models/` or `XAI_API_KEY`
- Start: `python setup.py` then `python start.py`; app at `http://localhost:3000/dashboard`

**Production:**
- Docker Compose topology: `postgres` (5432) → `redis` (6379) → `ollama` (11434) → `backend` (8000, CPU or `backend-gpu` profile with `LLM_DEVICE=cuda:0`) → `frontend` (3000, `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`) — all in `docker-compose.yml:1-137`
- Health-gated startup (`depends_on: service_healthy` for postgres/redis; backend healthcheck `GET /api/v1/health` at `docker-compose.yml:58-62`)

---

*Stack analysis: 2026-09-19*
