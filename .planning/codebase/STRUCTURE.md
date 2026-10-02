# Codebase Structure

**Analysis Date:** 2026-10-02

## Directory Layout

```text
MetaRadar/
├── backend/
│   ├── app/
│   │   ├── api/         # deps.py + v1/endpoints/ (11 modules, 47 handlers)
│   │   ├── connectors/  # SourceConnector base + 8 source adapters
│   │   ├── core/        # config, security, logging, middleware, redact, domain_config
│   │   ├── db/          # async session factory, advisory locks, seeders
│   │   ├── models/      # SQLAlchemy ORM (22 tables) + auth models
│   │   ├── providers/   # base, gemma, gemini, grok, degraded, factory
│   │   ├── schemas/     # Pydantic v2 request/response contracts
│   │   ├── services/    # 19 domain-logic modules
│   │   └── workflows/   # LangGraph graph, state, runner, nodes/ (11)
│   ├── alembic/         # alembic.ini + versions/ (15 migrations)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py           # production entrypoint (migrate then serve)
├── frontend/
│   ├── app/             # App Router: layout, login/, [section]/, signals/[signalId]/
│   ├── components/      # 13 workspace + shared UI components
│   ├── context/         # AuthContext.tsx
│   ├── lib/             # api.ts, errors.ts, hooks.ts, mappers.ts, utils.ts
│   ├── public/          # icon.svg, icon-light.svg, silhouette-avatar.svg
│   ├── types/           # api.ts (canonical hand-maintained contract)
│   ├── package.json     # pnpm 9.15.5, Next 16.3.0, React 19
│   └── pnpm-lock.yaml
├── config/              # haemophilia.yaml — domain ontology (339 lines)
├── contracts/           # openapi.json (generated, ~183 KB)
├── data/                # synthetic_signals.json fixtures
├── docs/                # 11 numbered design docs + rules/ + DEPLOYMENT.md
├── models/              # local GGUF weights (gitignored except .gitkeep/README)
├── pitch/               # PITCH.md, SVG/PNG diagrams, slide decks
├── poster/              # generate_poster.py + poster assets
├── scripts/             # launchers, OpenAPI export, eval scripts, style gate
├── tests/               # 36 pytest modules (~186 tests)
├── .agents/rules/       # mirrored engineering standards (tracked)
├── .github/workflows/   # ci.yml
├── .planning/           # GSD project memory (STATE, ROADMAP, phases, codebase/)
├── docker-compose.yml   # postgres, redis, backend, backend-gpu, frontend, ollama
├── netlify.toml         # frontend deploy config
├── render.yaml          # backend deploy blueprint
├── pytest.ini           # asyncio_mode=auto, testpaths=tests
├── setup.py             # interactive env bootstrap wizard
└── start.py             # unified local launcher
```

## Directory Purposes

**`backend/app/api/`:**
- Purpose: HTTP boundary
- Contains: `deps.py` (auth, RBAC, CSRF, origin validation, rate limiting) and `v1/endpoints/`
- Key files: `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/signals.py` (1,826 lines — the largest module), `backend/app/api/v1/endpoints/intelligence.py`, `backend/app/api/v1/endpoints/auth.py`

**`backend/app/services/`:**
- Purpose: framework-agnostic domain logic; the only place business rules should live
- Contains: 19 modules
- Key files: `backend/app/services/scoring.py`, `backend/app/services/pii.py`, `backend/app/services/deduplication.py`, `backend/app/services/embeddings.py`, `backend/app/services/confluence.py`, `backend/app/services/redteam.py`, `backend/app/services/routing.py`, `backend/app/services/calibration.py`, `backend/app/services/scheduler.py`

**`backend/app/workflows/`:**
- Purpose: the LangGraph intelligence engine
- Contains: `graph.py`, `state.py`, `runner.py`, `nodes/` (11 node modules)
- Key files: `backend/app/workflows/graph.py`, `backend/app/workflows/state.py`, `backend/app/workflows/runner.py`, `backend/app/workflows/nodes/synthesize.py`

**`backend/app/providers/`:**
- Purpose: LLM abstraction with capability negotiation and privacy gating
- Contains: abstract base, 3 real providers, 1 degraded provider, 1 factory
- Key files: `backend/app/providers/base.py`, `backend/app/providers/factory.py`, `backend/app/providers/gemini.py`, `backend/app/providers/grok.py`

**`backend/app/connectors/`:**
- Purpose: one adapter per monitored external source
- Contains: `base.py` + 8 adapters + registry
- Key files: `backend/app/connectors/base.py`, `backend/app/connectors/__init__.py` (`ALL_CONNECTORS`)

**`backend/app/core/`:**
- Purpose: cross-cutting infrastructure
- Contains: `config.py`, `domain_config.py`, `security.py`, `logging.py`, `middleware.py`, `redact.py`
- Key files: `backend/app/core/config.py` (single `settings` object; production guard)

**`backend/app/models/`:**
- Purpose: ORM schema — the system of record for shape
- Contains: `__init__.py` (22 tables) and `auth.py` (`User`, `Session`)
- Key files: `backend/app/models/__init__.py`

**`frontend/components/`:**
- Purpose: all UI, grouped by workspace domain
- Contains: `common/`, `auth/`, `signals/`, `confluence/`, `contradictions/`, `developments/`, `missing-signals/`, `functions/`, `intelligence/`, `calibration/`, `observability/`, `sources/`, `settings/`, `effects/`, `theme/`, `ui/`, plus `metaradar.tsx`
- Key files: `frontend/components/metaradar.tsx` (shell, 2,612 lines), `frontend/components/signals/SignalDetailWorkspace.tsx`, `frontend/components/common/EvidenceDrawer.tsx`

**`frontend/lib/`:**
- Purpose: data access and normalization between the API and components
- Contains: `api.ts`, `errors.ts`, `hooks.ts`, `mappers.ts`, `utils.ts`
- Key files: `frontend/lib/api.ts` (1,139 lines — all fetches + SSE), `frontend/lib/mappers.ts`

**`frontend/types/`:**
- Purpose: the canonical TypeScript API contract
- Contains: one file
- Key files: `frontend/types/api.ts` — a template duplicated verbatim inside `scripts/export_openapi.py`

**`config/`:**
- Purpose: domain knowledge as data, not code
- Contains: `haemophilia.yaml` (diseases, assets, signal types, lifecycle stages, confluence rules, functions, routing matrix, source tiers, connectors, lag thresholds)
- Key files: `config/haemophilia.yaml`

**`tests/`:**
- Purpose: pytest suite
- Contains: 36 `test_*.py` modules + `conftest.py`
- Key files: `tests/conftest.py` (`cleanup_db_connections` autouse fixture), `tests/test_privacy_boundary.py`, `tests/test_contract_drift.py`

**`scripts/`:**
- Purpose: operators' and CI's toolbox — nothing here is imported by the app
- Contains: launchers, OpenAPI export, model download, SVG→PNG, parity matrix, E2E scripts, style gate
- Key files: `scripts/export_openapi.py`, `scripts/check-banned-classes.mjs`, `scripts/test_e2e_vertical_slice.py`, `scripts/run`-style E2E scripts

**`docs/`:**
- Purpose: numbered design/requirements set plus the mandatory rule set
- Contains: `1_`–`11_` numbered docs, `DEPLOYMENT.md`, `DEMO_SCRIPT.md`, `SYSTEM_ARCHITECTURE.md`, `FEATURE_PARITY_MATRIX.md`, and `rules/`
- Key files: `docs/rules/ENGINEERING_STANDARDS.md`, `docs/rules/DEFINITION_OF_DONE.md`, `docs/rules/TESTING_STRATEGY.md`

**`.agents/rules/` and `docs/rules/`:**
- Purpose: mirrored copies of the mandatory engineering standards
- Note: `.gitignore` tracks only `.agents/rules/` inside `.agents/` (`.agents/*` + `!.agents/rules/**`), so the two copies are expected to stay in sync — **they are duplicated content, not a single source of truth**

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: FastAPI app, middleware, router mounting, lifespan (seed + scheduler)
- `backend/run.py`: production entrypoint — Alembic then Uvicorn on `$PORT`
- `start.py`: local unified launcher
- `frontend/app/layout.tsx`: Next.js root layout
- `frontend/app/page.tsx`: redirects to `/login`
- `frontend/app/[section]/page.tsx`: dynamic section router into `metaradar.tsx`
- `backend/app/services/scheduler.py`: `SourceScheduler.get_instance()` — autonomous worker loops

**Configuration:**
- `pytest.ini`: pytest behavior (`asyncio_mode = auto`, `testpaths = tests`, `pythonpath = backend .`)
- `backend/app/core/config.py`: all runtime settings + production guard
- `config/haemophilia.yaml`: domain ontology
- `docker-compose.yml`: local service topology
- `netlify.toml` / `render.yaml`: deployment blueprints
- `.github/workflows/ci.yml`: the CI gate definition
- `frontend/next.config.mjs`, `frontend/tsconfig.json`

**Core Logic:**
- `backend/app/workflows/graph.py`: the pipeline DAG
- `backend/app/workflows/runner.py`: persistence and run lifecycle
- `backend/app/services/scoring.py`: deterministic 4-factor priority model
- `backend/app/services/pii.py`: PII/PHI scrubber + payload classification
- `backend/app/services/deduplication.py`: SHA-256 bronze dedup + text chunking
- `backend/app/services/scheduler.py`: autonomous ingestion orchestration
- `backend/app/api/deps.py`: auth/RBAC/CSRF/rate-limit dependencies
- `frontend/components/metaradar.tsx`: application shell

**Testing:**
- `tests/conftest.py`: global autouse DB cleanup + auth bucket reset
- `tests/test_privacy_boundary.py`: privacy gate invariants
- `tests/test_contract_drift.py`: OpenAPI ↔ TS contract synchronization
- `tests/test_e2e_calibration_scenario.py`, `tests/test_e2e_vertical_slice` (via `scripts/`)
- `tests/test_providers_live.py`, `tests/test_ingestion.py`: marked `live`, require external services

## Naming Conventions

**Backend Python files:**
- `snake_case.py` — one module per concern, no abbreviations (`deduplication.py` not `dedup.py`; `provenance_urls.py` not `prov.py`)
- Tests: `test_*.py` (enforced by `pytest.ini:python_files`)

**Frontend files:**
- Component directories: `kebab-case/` — `frontend/components/missing-signals/`, `frontend/components/star-portal/`
- Component files: `PascalCase.tsx` — `SignalDetailWorkspace.tsx`, `EvidenceDrawer.tsx`
- Non-component modules: `camelCase.ts` — `frontend/lib/api.ts`, `frontend/lib/mappers.ts`
- App Router routes: lowercase directories — `frontend/app/login/`, `frontend/app/[section]/`

**Directories:**
- Backend: singular concern nouns under `app/` (`services/`, `models/`, `providers/`); plural only for `nodes/`
- Migration files: `NNN_description.py` — zero-padded three digits (`015_approval_requests.py`)
- Phase artifacts: `NN-slug/` under `.planning/phases/`

## Where to Add New Code

**New monitored data source (connector):**
- Implementation: `backend/app/connectors/<source_id>.py`, subclassing `SourceConnector` from `backend/app/connectors/base.py`; set `source_id`, `source_type`, `freshness_class`; implement `fetch_latest()` and `run_profile()`
- Register: add the instance to `ALL_CONNECTORS` in `backend/app/connectors/__init__.py`
- Config: add its query profiles under `connectors:` in `config/haemophilia.yaml`
- Scheduling: add `SCHEDULER_<SOURCE>_INTERVAL_MINUTES` to `backend/app/core/config.py` and wire it into `SourceScheduler._init_job_states()`
- Credentials: add an `Optional[str]` setting + a `configuration_error_for()` branch in `backend/app/core/config.py`
- Tests: `tests/test_ingestion.py`, `tests/test_connector_health.py`

**New AI provider:**
- Implementation: `backend/app/providers/<name>.py`, subclass `LLMProvider` from `backend/app/providers/base.py`; declare `name` and `capabilities`; implement `generate_summary()` and `generate_intelligence()`; implement `validate_privacy_gate()` before any outbound call
- Registration: instantiate in `ProviderFactory.__init__` and insert the step in `execute_task()` at `backend/app/providers/factory.py`
- Tests: `tests/test_provider_matrix.py`, `tests/test_privacy_boundary.py`
- **Do not** grant `ProviderCapability.GENERATE_ACTIONS` to a cloud provider — that exclusion is load-bearing (see `gemini.py`)

**New pipeline node:**
- Implementation: `backend/app/workflows/nodes/<name>.py` exporting a `node_<name>()` callable
- Wiring: add the node and its linear edges in `backend/app/workflows/graph.py`
- State: add any new channel to `MetaRadarState` in `backend/app/workflows/state.py` **with an explicit reducer** — use `operator.add` only for genuinely accumulating channels; use `replace_list` for full-list re-emission
- Tests: `tests/test_intelligence_nodes.py`

**New API endpoint:**
- Handler: the appropriate module in `backend/app/api/v1/endpoints/` (`signals.py` for signal-centric, `intelligence.py` for derived views)
- Registration: routers are mounted in `backend/app/main.py`; add to an existing router rather than creating a new one unless it is a distinct domain
- Auth: use `Depends(get_current_user)` + `Depends(require_role(...))`; add `Depends(require_csrf)` for mutations
- Schemas: `backend/app/schemas/__init__.py` (or `schemas/auth.py`)
- Contract: **edit the template inside `scripts/export_openapi.py`**, then run `python scripts/export_openapi.py` to regenerate `frontend/types/api.ts`
- Tests: `tests/test_api_endpoints.py`, `tests/test_signals_endpoints.py`

**New frontend workspace view:**
- Component: `frontend/components/<domain>/<Name>Workspace.tsx` (use `kebab-case/` + `PascalCase.tsx`)
- Wiring: register the section in `frontend/components/metaradar.tsx` (nav + switch)
- Data: add a typed function to `frontend/lib/api.ts`; types come from `frontend/types/api.ts`
- Normalization: add a mapper in `frontend/lib/mappers.ts`
- **Styling:** use design tokens only — never `slate-*` or arbitrary hex (`scripts/check-banned-classes.mjs` will fail CI)

**New shared UI primitive:**
- Location: `frontend/components/ui/`
- Convention: `PascalCase.tsx` plus an optional co-located `.css` (see `Counter.tsx`/`Counter.css`)

**New domain knowledge:**
- Edit `config/haemophilia.yaml`; never hardcode asset names, modalities, or routing rules in Python
- Loader/model: `backend/app/core/domain_config.py`

**Utilities:**
- Backend shared helpers: `backend/app/core/` (`redact.py`, `security.py`)
- Frontend shared helpers: `frontend/lib/utils.ts`, `frontend/lib/hooks.ts`

## Special Directories

**`models/`:**
- Purpose: local GGUF weights for `GemmaProvider`
- Generated: No (downloaded by `scripts/download_model.py` / `python setup.py --download-model`)
- Committed: No — `.gitignore` ignores `/models/*` but keeps `.gitkeep` and `README.md`. The pattern is root-anchored specifically so it does **not** match `backend/app/models/`

**`contracts/`:**
- Purpose: generated OpenAPI artifact
- Generated: Yes — by `scripts/export_openapi.py`
- Committed: Yes (CI diffs it indirectly via `frontend/types/api.ts`)

**`.planning/`:**
- Purpose: GSD project memory — PROJECT, ROADMAP, REQUIREMENTS, STATE, `phases/`, `codebase/`, `debug/`, `milestones/`
- Generated: Partly (`codebase/` is written by this mapper workflow)
- Committed: Yes

**`.agents/rules/`:**
- Purpose: agent-facing copy of the engineering standards
- Generated: No — duplicated from `docs/rules/`
- Committed: Yes (the only tracked path under `.agents/`)

**`logs/`, `scratch/`, `.pytest_cache/`, `__pycache__/`:**
- Purpose: runtime scratch
- Committed: No — `scratch/` and caches are gitignored

**`pitch/`, `poster/`:**
- Purpose: hackathon/REACH submissions (deck, diagrams, poster generator)
- Generated: Partly (`poster/generate_poster.py`)
- Committed: Yes — `.gitignore` explicitly re-includes `pitch/`

---

*Structure analysis: 2026-10-02*
