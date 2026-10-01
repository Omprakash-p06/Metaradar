# Codebase Structure

**Analysis Date:** 2026-10-01

## Directory Layout

```
novonordisk/
├── start.py                # Unified launcher (Docker + migrate + backend + frontend)
├── docker-compose.yml      # Postgres/pgvector, Redis, backend, frontend, Ollama services
├── contracts/              # Canonical API contract (openapi.json)
├── config/                 # Domain config (haemophilia.yaml)
├── data/                   # Sample/fixture signals (synthetic_signals.json)
├── models/                 # Local GGUF reasoning model + README
├── scripts/                # Export, parity, E2E, pitch/deck utilities
├── tests/                  # Root pytest suite (API, contract, security, workspaces)
├── backend/                # FastAPI modular monolith
│   ├── app/main.py         # ASGI entry point + router mounts
│   ├── app/api/            # Routers + shared auth deps
│   ├── app/services/       # Business logic (scoring, routing, ingestion…)
│   ├── app/workflows/      # LangGraph pipeline (graph/state/runner/nodes)
│   ├── app/connectors/     # Per-source ingest adapters
│   ├── app/providers/      # LLM backends + fallback factory
│   ├── app/models/         # SQLAlchemy ORM tables
│   ├── app/schemas/        # Pydantic request/response contracts
│   ├── app/core/           # Settings, security, middleware, logging
│   ├── app/db/             # Async session + seed
│   └── alembic/            # Versioned DB migrations (001–015)
├── frontend/               # Next.js 16 App Router SPA
│   ├── app/                # Routes ([section], signals/[signalId], login)
│   ├── components/         # Workspace + Shell + UI components
│   ├── lib/                # api.ts client, mappers, hooks, errors
│   ├── context/            # AuthContext session state
│   └── types/              # Hand-maintained TS API contract
├── docs/rules/             # Authoritative engineering standards (incl. ARCHITECTURE_RULES.md)
└── .planning/codebase/     # Generated codebase maps (this file)
```

## Directory Purposes

**`backend/`:**
- Purpose: Async FastAPI backend — API, domain logic, pipeline, persistence.
- Contains: `app/` source tree, `alembic/` migrations, `tests/`, `Dockerfile`, `requirements.txt`.
- Key files: `backend/app/main.py`, `backend/app/api/v1/endpoints/*.py`, `backend/app/workflows/graph.py`, `backend/app/db/session.py`

**`backend/app/api/`:**
- Purpose: HTTP boundary. Versioned routers plus shared dependencies.
- Contains: `v1/endpoints/*.py` (11 routers), `deps.py` (auth/RBAC/CSRF/rate-limit).
- Key files: `backend/app/api/v1/endpoints/signals.py`, `backend/app/api/v1/endpoints/pipeline.py`, `backend/app/api/v1/endpoints/search.py`, `backend/app/api/v1/endpoints/intelligence.py`, `backend/app/api/v1/endpoints/ingestion.py`, `backend/app/api/v1/endpoints/health.py`, `backend/app/api/deps.py`

**`backend/app/services/`:**
- Purpose: Business logic — where domain rules live. Called by routers, runner, and nodes.
- Contains: 17 service modules (no subdirectories).
- Key files: `backend/app/services/scoring.py`, `backend/app/services/routing.py`, `backend/app/services/relevance.py`, `backend/app/services/calibration.py`, `backend/app/services/ingestion.py`, `backend/app/services/scheduler.py`, `backend/app/services/vector_query.py`, `backend/app/services/embeddings.py`, `backend/app/services/deduplication.py`, `backend/app/services/auth_service.py`

**`backend/app/workflows/`:**
- Purpose: LangGraph intelligence pipeline definition + execution.
- Contains: `graph.py`, `state.py`, `runner.py`, `nodes/*.py` (11 stage modules).
- Key files: `backend/app/workflows/graph.py`, `backend/app/workflows/state.py`, `backend/app/workflows/runner.py`

**`backend/app/connectors/`:**
- Purpose: Source adapters that fetch + normalize external data into bronze rows.
- Contains: `base.py` + one module per source + `__init__.py` registry.
- Key files: `backend/app/connectors/base.py`, `backend/app/connectors/__init__.py` (`ALL_CONNECTORS`), `backend/app/connectors/pubmed.py`, `backend/app/connectors/clinical_trials.py`, `backend/app/connectors/fda.py`, `backend/app/connectors/ema.py`, `backend/app/connectors/newsapi.py`

**`backend/app/providers/`:**
- Purpose: LLM backends behind a privacy-gated fallback chain.
- Contains: `base.py`, `gemma.py`, `grok.py`, `degraded.py`, `factory.py`.
- Key files: `backend/app/providers/factory.py`, `backend/app/providers/base.py`

**`backend/app/models/`:**
- Purpose: SQLAlchemy ORM — single-module domain tables plus auth submodule.
- Contains: `__init__.py` (all tables), `auth.py` (`User`, `Session`).
- Key files: `backend/app/models/__init__.py`, `backend/app/models/auth.py`

**`backend/app/schemas/`:**
- Purpose: Pydantic wire contracts mirroring `contracts/openapi.json`.
- Contains: `__init__.py`, `auth.py`, `intelligence.py`, `registry.py`.
- Key files: `backend/app/schemas/__init__.py`, `backend/app/schemas/intelligence.py`

**`backend/app/core/`:**
- Purpose: Cross-cutting backend infrastructure.
- Contains: Settings, security, middleware, logging, redaction, domain config.
- Key files: `backend/app/core/config.py`, `backend/app/core/security.py`, `backend/app/core/middleware.py`, `backend/app/core/logging.py`, `backend/app/core/domain_config.py`

**`backend/app/db/`:**
- Purpose: Async DB access + startup seed data.
- Contains: `session.py` (engine, `AsyncSessionLocal`, `get_db`), `seed.py`.
- Key files: `backend/app/db/session.py`, `backend/app/db/seed.py`

**`backend/alembic/`:**
- Purpose: Versioned Postgres schema migrations (15 revisions, `001_initial_v51_schema.py` → `015_approval_requests.py`).
- Contains: `alembic.ini`, `env.py`, `versions/*.py`.
- Key files: `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/`

**`frontend/app/`:**
- Purpose: Next.js App Router routes. Canonical layout per `docs/rules/ARCHITECTURE_RULES.md`.
- Contains: `page.tsx` (root → `/login` redirect), `layout.tsx` (providers), `[section]/page.tsx` (workspace switch), `signals/[signalId]/page.tsx` (detail), `login/`.
- Key files: `frontend/app/page.tsx`, `frontend/app/layout.tsx`, `frontend/app/[section]/page.tsx`, `frontend/app/signals/[signalId]/page.tsx`, `frontend/app/login/page.tsx`

**`frontend/components/`:**
- Purpose: All UI — Shell chrome, per-domain workspaces, shared primitives.
- Contains: 16 subdirectories + `metaradar.tsx` barrel-adjacent Shell module.
- Key files: `frontend/components/metaradar.tsx` (Shell + pages), `frontend/components/signals/SignalList.tsx`, `frontend/components/signals/SignalDetailWorkspace.tsx`, `frontend/components/intelligence/AthenaWorkspace.tsx`, `frontend/components/confluence/ConfluenceWorkspace.tsx`, `frontend/components/contradictions/ContradictionWorkspace.tsx`

**`frontend/lib/`:**
- Purpose: Frontend service layer — API client + normalization + hooks.
- Contains: `api.ts` (908-line typed client), `mappers.ts`, `errors.ts`, `hooks.ts`, `utils.ts`.
- Key files: `frontend/lib/api.ts`, `frontend/lib/mappers.ts`, `frontend/lib/errors.ts`

**`frontend/context/` + `frontend/types/`:**
- Purpose: Session state (`AuthContext.tsx`) and hand-maintained API types (`api.ts`).
- Key files: `frontend/context/AuthContext.tsx`, `frontend/types/api.ts`

**`contracts/`:**
- Purpose: Canonical OpenAPI snapshot consumed by parity/contract tests.
- Contains: `contracts/openapi.json` (emitted by `scripts/export_openapi.py`).
- Key files: `contracts/openapi.json`

**`config/` + `data/` + `models/`:**
- Purpose: Domain config, fixture data, local model weights.
- Key files: `config/haemophilia.yaml`, `data/synthetic_signals.json`, `backend/app/data/synthetic_signals.json`, `models/gemma-3-4b-it-Q4_K_M.gguf`, `models/README.md`

**`tests/` + `backend/tests/` + `scripts/`:**
- Purpose: Root pytest suite (30+ files), backend login test, operational scripts (export, parity, E2E, deck).
- Key files: `tests/conftest.py`, `tests/test_api_endpoints.py`, `tests/test_contract_drift.py`, `scripts/export_openapi.py`, `pytest.ini`

**`docs/rules/`:**
- Purpose: Authoritative process + architecture standards (AGENTS.md-mandated).
- Key files: `docs/rules/ARCHITECTURE_RULES.md`, `docs/rules/ENGINEERING_STANDARDS.md`, `docs/rules/TESTING_STRATEGY.md`, `docs/rules/SECURITY_STANDARDS.md`

## Key File Locations

**Entry Points:**
- `start.py`: Unified launcher — Docker backing services + `alembic upgrade head` + uvicorn backend + Next.js frontend. Run `python start.py --help`.
- `backend/app/main.py`: FastAPI ASGI app (`app`), lifespan, middleware, 11 router mounts. Served via `uvicorn app.main:app` with `cwd=backend`.
- `frontend/app/page.tsx`: Root route, redirects to `/login`.
- `frontend/app/layout.tsx`: Root layout — font, `ThemeProvider`, `AuthProvider`, `ScrollReveal`.
- `frontend/app/[section]/page.tsx`: Workspace router — maps `dashboard|signals|confluence|lifecycles|red-team|missing-signals|developments|intelligence|functions|calibrate|sources|observability|settings` to workspace components inside `<Shell>`.
- `frontend/app/signals/[signalId]/page.tsx`: Signal detail client page — `fetchSignal` + confluence/contradiction fetchers → `SignalDetailWorkspace`.
- `frontend/app/login/page.tsx` (+ `layout.tsx`): Login entry.

**Configuration:**
- `backend/app/core/config.py`: `Settings` (pydantic-settings, loads root `.env`); `PROJECT_NAME`, `API_V1_STR=/api/v1`, `DATABASE_URL`, LLM/provider flags. Existence of `.env` / `.env.example` noted — never read secret values.
- `frontend/next.config.mjs`: Minimal Next config (`images.unoptimized`).
- `frontend/package.json`: `dev`/`build`/`start` scripts; `frontend/tsconfig.json`, `frontend/eslint.config.mjs`, `frontend/postcss.config.mjs`, `frontend/components.json`.
- `backend/alembic.ini` + `backend/app/core/domain_config.py` + `config/haemophilia.yaml`: Migration config + disease-area config.
- `docker-compose.yml`: `postgres` (pgvector:pg16), `redis`, `backend`, `backend-gpu`, `frontend`, `ollama` services.
- `pytest.ini`: Root test config.

**Core Logic:**
- Pipeline wiring/state/execution: `backend/app/workflows/graph.py`, `backend/app/workflows/state.py`, `backend/app/workflows/runner.py`
- Stage logic: `backend/app/workflows/nodes/ingest.py`, `validate.py`, `embed.py`, `nlp_extract.py`, `ontology.py`, `confluence.py`, `lifecycle.py`, `redteam.py`, `missing_signal.py`, `synthesize.py`, `calibrate.py`
- Domain rules: `backend/app/services/scoring.py`, `routing.py`, `relevance.py`, `calibration.py`, `confluence.py`, `redteam.py`, `vector_query.py`, `embeddings.py`, `deduplication.py`
- Ingestion edge: `backend/app/connectors/base.py`, `backend/app/connectors/__init__.py`, `backend/app/services/ingestion.py`, `backend/app/services/scheduler.py`
- AuthN/Z: `backend/app/api/deps.py`, `backend/app/core/security.py`, `backend/app/services/auth_service.py`, `backend/app/models/auth.py`

**Testing:**
- `tests/`: Root suite — `conftest.py`, `test_api_endpoints.py`, `test_signals_endpoints.py`, `test_contract_drift.py`, `test_parity_matrix.py`, `test_security.py`, `test_rbac.py`, `test_privacy_boundary.py`, `test_intelligence_nodes.py`, `test_ingestion.py`, `test_retrieval.py`, and 20+ more.
- `backend/tests/test_login_credentials.py`: Backend-local login test.

## Naming Conventions

**Files:**
- Backend: `snake_case` modules grouped by layer — `endpoints/signals.py`, `services/scoring.py`, `workflows/nodes/nlp_extract.py`, `connectors/clinical_trials.py`, `providers/factory.py`, `alembic/versions/015_approval_requests.py`.
- Frontend routes: App Router lowercase segments — `frontend/app/[section]/page.tsx`, `frontend/app/signals/[signalId]/page.tsx`, `frontend/app/login/page.tsx`.
- Frontend components: `PascalCase` workspaces — `SignalList.tsx`, `AthenaWorkspace.tsx`, `ConfluenceWorkspace.tsx`, `CalibrationWorkspace.tsx`, `SourcesOperationsWorkspace.tsx`.

**Directories:**
- Backend layers are plural nouns: `api/`, `services/`, `workflows/`, `connectors/`, `providers/`, `models/`, `schemas/`, `core/`, `db/`.
- Frontend follows App Router + feature folders: `app/`, `components/<domain>/`, `lib/`, `context/`, `types/`, `public/`.

## Where to Add New Code

**New Feature:**
- Primary code: Backend rule → `backend/app/services/<domain>.py`; pipeline stage → `backend/app/workflows/nodes/<stage>.py` + wire in `backend/app/workflows/graph.py`; UI → `frontend/components/<domain>/<Name>Workspace.tsx` + case in `frontend/app/[section]/page.tsx`.
- Tests: `tests/test_<domain>.py` (mirror existing names like `tests/test_confluence_semantics.py`); contract change → update template in `scripts/export_openapi.py`, regenerate `contracts/openapi.json` + `frontend/types/api.ts`.

**New Component/Module:**
- Implementation: Backend router → `backend/app/api/v1/endpoints/<name>.py` + `app.include_router(...)` in `backend/app/main.py`; connector → `backend/app/connectors/<source>.py` + register in `backend/app/connectors/__init__.py`; provider → `backend/app/providers/<name>.py` + wire into `backend/app/providers/factory.py`.

**Utilities:**
- Shared helpers: Backend → `backend/app/core/` (config/security/middleware/logging); frontend → `frontend/lib/` (`api.ts`, `mappers.ts`, `hooks.ts`, `utils.ts`, `errors.ts`).

## Special Directories

**`models/`:**
- Purpose: Local GGUF weights for the Gemma reasoning backend (`gemma-3-4b-it-Q4_K_M.gguf`).
- Generated: No (downloaded via `scripts/download_model.py`).
- Committed: Weights file present in working tree; confirm Git LFS/ignore policy before committing large binaries.

**`data/` + `backend/app/data/`:**
- Purpose: `synthetic_signals.json` fixtures for demo/test-fixture modes.
- Generated: No.
- Committed: Yes.

**`logs/`:**
- Purpose: Runtime output from `start.py` (`backend.log`, `frontend.log`).
- Generated: Yes.
- Committed: No (gitignored runtime logs).

**`frontend/node_modules/`, `__pycache__/`, `.pytest_cache/`:**
- Purpose: Build/test caches.
- Generated: Yes.
- Committed: No.

---

*Structure analysis: 2026-10-01*
