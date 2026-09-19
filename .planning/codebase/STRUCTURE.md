# Codebase Structure

**Analysis Date:** 2026-09-19

## Directory Layout

```
novonordisk/                    # MetaRadar monorepo (Novo Nordisk Hackathon)
├── start.py                    # Unified launcher: Docker → Alembic → uvicorn + Next.js
├── setup.py                    # Zero-config 7-step environment bootstrap
├── docker-compose.yml          # Postgres 16 + pgvector, Redis backing services
├── pytest.ini                  # Backend test config
├── backend/                    # FastAPI service (Python, ~75 *.py under app/)
│   ├── app/
│   │   ├── main.py             # App factory, lifespan, middleware, 11 routers
│   │   ├── api/v1/endpoints/   # 11 routers: auth, signals, intelligence, pipeline,
│   │   │                       #   ingestion, search, feedback, registry, cache,
│   │   │                       #   observability, health (+ api/deps.py RBAC/CSRF)
│   │   ├── connectors/         # 8 source adapters + base.py contract + registry
│   │   ├── core/               # config, domain_config, logging, middleware,
│   │   │                       #   redact, security (bcrypt/session/CSRF)
│   │   ├── data/               # synthetic_signals.json reference fixtures
│   │   ├── db/                 # session.py (async engine), seed.py (sources/users)
│   │   ├── models/             # __init__.py (23 tables) + auth.py (users/sessions)
│   │   ├── providers/          # base, gemma, grok, degraded, factory
│   │   ├── schemas/            # auth, intelligence, registry Pydantic contracts
│   │   ├── services/           # 17 domain modules (scoring, routing, ingestion…)
│   │   └── workflows/          # graph.py, runner.py, state.py, nodes/ (11 nodes)
│   ├── alembic/                # env.py + versions/ (15 migrations 001..015)
│   ├── requirements.txt        # Pinned Python deps
│   ├── Dockerfile              # Backend image
│   └── tests/                  # Backend test suite
├── frontend/                   # Next.js 16 App Router (~55 *.ts/*.tsx in scope)
│   ├── app/                    # layout.tsx, page.tsx (→/login), login/,
│   │                           #   [section]/ (13 workspaces), signals/[signalId]/
│   ├── components/             # 16 feature dirs + metaradar.tsx shell + ui/
│   ├── context/                # AuthContext.tsx (session + role gate)
│   ├── lib/                    # api.ts (typed client), errors.ts, mappers.ts,
│   │                           #   hooks.ts, utils.ts
│   ├── types/                  # api.ts (shared DTOs)
│   ├── public/                 # Static assets, icon.svg
│   ├── package.json            # npm scripts + deps (pnpm-lock + package-lock kept)
│   └── next.config.mjs         # Next 16 config
├── config/
│   └── haemophilia.yaml        # Domain contract: diseases, assets, connectors,
│                               #   routing matrix, thresholds (v1.0.0)
├── contracts/                  # API/frontend parity contracts + parity matrix
├── scripts/                    # Ops + E2E: live ingestion, vertical slice, demo,
│                               #   parity matrix, pitch deck, OpenAPI export
├── tests/                      # Repo-level tests (pytest.ini)
├── docs/                       # SYSTEM_ARCHITECTURE.md, METARADAR_MASTER_PLAN_v5.0.md,
│                               #   rules/, audits/, manifests/, concept/, release/
├── models/                     # Local GGUF weights (git-ignored, runtime only)
├── data/                       # Local data drops (runtime)
├── logs/                       # backend.log, frontend.log (runtime, git-ignored)
├── .planning/                  # GSD planning state + codebase/ docs (this file)
├── AGENTS.md                   # Agent operating standard (global process rules)
└── README.md                   # Project overview
```

**File counts (cheap `find`/`ls`, 2026-09-19):**
- `backend/app/**/*.py`: ~75 files (services 17, endpoints 11, connectors 10 incl. base/registry, nodes 12 incl. `__init__`, core 6, providers 5, schemas 3, models 2, db 2, api root 1, main 1).
- `frontend` in-scope `*.ts/*.tsx` (`app/`, `components/`, `lib/`, `context/`, `types/`): ~55 files.
- `backend/alembic/versions/*.py`: 15 migrations (`001`–`015`).
- `frontend/components/*/`: 16 feature dirs (`auth`, `calibration`, `common`, `confluence`, `contradictions`, `developments`, `effects`, `functions`, `intelligence`, `missing-signals`, `observability`, `settings`, `signals`, `sources`, `theme`, `ui`) + `metaradar.tsx` shell.

## Directory Purposes

**`backend/app/api/` (+ `deps.py`):**
- Purpose: HTTP boundary — route handlers, auth/RBAC/CSRF gates, rate limits.
- Contains: `v1/endpoints/*.py` (11 routers); `deps.py` (`get_current_user`, `get_optional_user`, `require_role`, `require_csrf`, origin check, rate buckets).
- Key files: `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/signals.py` (largest: signals + Athena), `backend/app/api/v1/endpoints/pipeline.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/ingestion.py`.

**`backend/app/connectors/`:**
- Purpose: Source adapters; bronze-only writes; per-profile incremental runs.
- Contains: `base.py` (`SourceConnector`, `RawSignalPayload`, retry, bronze persist, state I/O, health log), 8 adapters, `__init__.py` registry (`ALL_CONNECTORS`).
- Key files: `backend/app/connectors/__init__.py`, `backend/app/connectors/base.py`, `backend/app/connectors/pubmed.py`, `backend/app/connectors/clinical_trials.py`.

**`backend/app/core/`:**
- Purpose: Cross-cutting backend plumbing.
- Contains: `config.py` (settings incl. `EMBEDDING_DIMENSION=384`), `domain_config.py` (YAML loader), `logging.py` (structlog), `middleware.py` (correlation ID, security headers), `redact.py` (secret scrubbing), `security.py` (bcrypt, session sign, CSRF HMAC).
- Key files: `backend/app/core/config.py`, `backend/app/core/security.py`, `backend/app/core/middleware.py`.

**`backend/app/db/`:**
- Purpose: Async engine/session + canonical seeds.
- Contains: `session.py` (`engine`, `AsyncSessionLocal`, `Base`, `get_db`), `seed.py` (`seed_canonical_sources_if_needed`).
- Key files: `backend/app/db/session.py`, `backend/app/db/seed.py`.

**`backend/app/models/`:**
- Purpose: All SQLAlchemy table definitions (25 tables total).
- Contains: `__init__.py` (23 domain tables + audit listeners), `auth.py` (`users`, `sessions`).
- Key files: `backend/app/models/__init__.py`, `backend/app/models/auth.py`.

**`backend/app/providers/`:**
- Purpose: LLM inference abstraction + privacy-gated fallback chain.
- Contains: `base.py` (`LLMProvider`, `ProviderCapability`, `DataClassification`), `gemma.py`, `grok.py`, `degraded.py`, `factory.py`.
- Key files: `backend/app/providers/factory.py`, `backend/app/providers/base.py`.

**`backend/app/schemas/`:**
- Purpose: Shared Pydantic request/response contracts.
- Contains: `auth.py`, `intelligence.py`, `registry.py` (endpoint-local schemas live next to routers).
- Key files: `backend/app/schemas/intelligence.py`.

**`backend/app/services/`:**
- Purpose: Reusable domain logic (the layer nodes AND endpoints both call).
- Contains: 17 modules — `ingestion.py`, `scheduler.py`, `scoring.py`, `routing.py`, `confluence.py`, `redteam.py`, `calibration.py`, `deduplication.py`, `embeddings.py`, `embeddings_backfill.py`, `vector_query.py`, `pii.py`, `provenance_urls.py`, `authority.py`, `relevance.py`, `source_independence.py`, `auth_service.py`.
- Key files: `backend/app/services/ingestion.py`, `backend/app/services/scheduler.py`, `backend/app/services/scoring.py`, `backend/app/services/routing.py`.

**`backend/app/workflows/`:**
- Purpose: LangGraph pipeline definition, state contract, execution.
- Contains: `graph.py` (`build_graph`), `runner.py` (`PipelineRunner`), `state.py` (`MetaRadarState`), `nodes/` (11 node modules).
- Key files: `backend/app/workflows/graph.py`, `backend/app/workflows/runner.py`, `backend/app/workflows/state.py`, `backend/app/workflows/nodes/__init__.py`.

**`backend/alembic/versions/`:**
- Purpose: Versioned DDL, 001 (17-table base + HNSW) through 015 (approvals).
- Contains: `001_initial_v51_schema.py` … `015_approval_requests.py`.
- Key files: `backend/alembic/versions/001_initial_v51_schema.py`, `backend/alembic/versions/014_auditlog_user_correlation.py` (audit trigger).

**`frontend/app/`:**
- Purpose: App Router routes; only 8 files — composition over logic.
- Contains: `layout.tsx` (fonts, Theme+Auth providers), `page.tsx` (→ `/login` redirect), `login/` (layout+page), `[section]/page.tsx` (13-workspace switch), `signals/[signalId]/page.tsx` (detail), `globals.css`.
- Key files: `frontend/app/layout.tsx`, `frontend/app/[section]/page.tsx`, `frontend/app/page.tsx`.

**`frontend/components/`:**
- Purpose: One directory per workspace/feature + shared shell + shadcn `ui/`.
- Contains: `metaradar.tsx` (`Shell`, `DashboardPage`, `LifecyclePage`, `GenericPage`); per-section workspaces (`signals/SignalList`, `confluence/ConfluenceWorkspace`, `contradictions/ContradictionWorkspace`, `missing-signals/MissingSignalsWorkspace`, `developments/DevelopmentsWorkspace`, `intelligence/AthenaWorkspace`, `functions/FunctionsWorkspace`, `calibration/CalibrationWorkspace`, `sources/SourcesOperationsWorkspace`, `observability/ActivityStreamWorkspace`, `settings/SettingsWorkspace`, `auth/ProfileCard`, `effects/`, `common/ScrollReveal`, `theme/ThemeProvider`).
- Key files: `frontend/components/metaradar.tsx`, `frontend/components/signals/SignalList.tsx`, `frontend/components/intelligence/AthenaWorkspace.tsx`.

**`frontend/context/`, `frontend/lib/`, `frontend/types/`:**
- Purpose: Session state, typed API client + mappers, shared DTOs.
- Contains: `context/AuthContext.tsx`; `lib/api.ts`, `lib/errors.ts` (`ApiError`), `lib/mappers.ts` (`mapSignal`), `lib/hooks.ts`, `lib/utils.ts`; `types/api.ts`.
- Key files: `frontend/context/AuthContext.tsx`, `frontend/lib/api.ts`, `frontend/types/api.ts`.

**`config/`:**
- Purpose: Versioned domain contract (NOT secrets).
- Contains: `haemophilia.yaml` (`domain_config_version: 1.0.0`, diseases, 7 assets, signal types, 9 lifecycle stages, confluence thresholds, 6 functions + routing matrix, 4 source tiers, 8 connector blocks, cross-source + lag thresholds).
- Key files: `config/haemophilia.yaml`.

**`scripts/`:**
- Purpose: Ops + verification harnesses (run against live backend).
- Contains: `test_live_ingestion_e2e.py`, `test_e2e_vertical_slice.py`, `test_demo_scenarios_e2e.py`, `generate_parity_matrix.py`, `export_openapi.py`, `generate_pitch_deck.py`, `apply_phase7_migrations.py`, `download_model.py`, `convert_svgs_to_png.py`, `check-banned-classes.mjs`.
- Key files: `scripts/test_e2e_vertical_slice.py`, `scripts/test_live_ingestion_e2e.py`.

## Key File Locations

**Entry Points:**
- `start.py`: Unified launcher (Docker → Alembic → backend `:8000` + frontend `:3000`).
- `setup.py`: 7-step zero-config bootstrap.
- `backend/app/main.py`: FastAPI app + lifespan + 11 routers.
- `frontend/app/layout.tsx`: Root layout + providers.
- `frontend/app/page.tsx`: `/` → `/login` redirect.
- `frontend/app/[section]/page.tsx`: 13-workspace router.

**Configuration:**
- `config/haemophilia.yaml`: Domain contract (diseases/assets/connectors/routing).
- `backend/app/core/config.py`: Runtime settings (DB URL, CORS, embedding dim, LLM provider).
- `.env` / `.env.example`: Secrets + env overrides (existence only — never read `.env` contents).
- `docker-compose.yml`: Postgres 16 + pgvector + Redis.
- `frontend/next.config.mjs`, `frontend/tsconfig.json`, `frontend/components.json`: Frontend build.
- `backend/alembic.ini`, `pytest.ini`: Migrations + test config.

**Core Logic:**
- `backend/app/workflows/graph.py` + `runner.py` + `state.py`: Pipeline definition/execution/state.
- `backend/app/services/scoring.py` + `routing.py`: Scoring + function routing.
- `backend/app/connectors/__init__.py` + `base.py`: Connector registry + contract.
- `frontend/lib/api.ts` + `frontend/types/api.ts`: Typed backend client + DTOs.

**Testing:**
- `backend/tests/`: Backend suite (`pytest.ini` at root).
- `tests/`: Repo-level tests.
- `scripts/test_*_e2e.py`: Live E2E harnesses (ingestion, vertical slice, demo scenarios).

## Naming Conventions

**Files:**
- Backend: `snake_case.py` everywhere (`source_independence.py`, `missing_signal.py`); node modules mirror node names (`nodes/confluence.py` → `node_confluence`); migrations `NNN_slug.py` (`013_auth_user_role_session.py`).
- Frontend: App Router `page.tsx`/`layout.tsx` lowercase; components `PascalCase.tsx` (`SignalList.tsx`, `AthenaWorkspace.tsx`, `ConfluenceWorkspace.tsx`); utilities camelCase (`api.ts`, `mappers.ts`, `hooks.ts`).
- Workspaces: `<Domain>Workspace.tsx` (`SourcesOperationsWorkspace`, `ActivityStreamWorkspace`).

**Directories:**
- Backend: plural domain nouns (`connectors/`, `services/`, `providers/`, `schemas/`, `models/`, `workflows/nodes/`); versions under `alembic/versions/`.
- Frontend: plural feature nouns (`signals/`, `sources/`, `contradictions/`, `developments/`); dynamic routes in brackets (`[section]/`, `[signalId]/`).

## Where to Add New Code

**New Connector (source adapter):**
- Implementation: `backend/app/connectors/<source_id>.py` — subclass `SourceConnector` from `backend/app/connectors/base.py`; set `source_id`, `freshness_class`, `connector_version`; implement `fetch_latest` + `run_profile`; reuse `_persist_bronze`, `_read/_write_connector_state`, `_persist_health_log`.
- Config: add `<source_id>:` block with `profiles:` under `connectors:` in `config/haemophilia.yaml` (queries, windows, quotas — mirrors `pubmed:`/`clinical_trials:` shapes).
- Registry: append instance to `ALL_CONNECTORS` in `backend/app/connectors/__init__.py`.
- DB: ensure `sources` seed row exists (`backend/app/db/seed.py`); no migration needed unless new columns.
- Tests: extend `scripts/test_live_ingestion_e2e.py` pattern for the new `source_id`.

**New API Endpoint:**
- Implementation: add handler to the matching router in `backend/app/api/v1/endpoints/<domain>.py` (or create `<domain>.py` + `app.include_router(...)` in `backend/app/main.py:90-100`).
- Contracts: shared DTOs in `backend/app/schemas/<domain>.py`; endpoint-local `BaseModel`s stay in the endpoint file (see `ingestion.py:22-40`).
- Auth: protect with `Depends(get_current_user)` / `Depends(require_role("LEADERSHIP", ...))` / `Depends(require_csrf)` from `backend/app/api/deps.py`.
- Frontend: add typed client fn in `frontend/lib/api.ts` + DTOs in `frontend/types/api.ts`; run `scripts/export_openapi.py` to refresh the contract.

**New Frontend View (workspace):**
- Implementation: create `frontend/components/<feature>/<Name>Workspace.tsx`; wire one `case '<slug>':` in `frontend/app/[section]/page.tsx:23-71` (this switch is the 13-workspace registry — now 13 cases).
- Shell: reuse `Shell`/`GenericPage` from `frontend/components/metaradar.tsx`; data via `frontend/lib/api.ts` + `useAuth()` from `frontend/context/AuthContext.tsx`.
- Detail routes: follow `frontend/app/signals/[signalId]/page.tsx` for `/:id` views.

**New LangGraph Node (pipeline stage):**
- Implementation: create `backend/app/workflows/nodes/<stage>.py` exporting `node_<stage>(state) -> dict` (read needed channels, return channel deltas only).
- Registry: export from `backend/app/workflows/nodes/__init__.py`; `add_node` + `add_edge` in `build_graph()` (`backend/app/workflows/graph.py:33-56`) keeping the linear order; extend `MetaRadarState` in `backend/app/workflows/state.py` if new channels are needed (choose `operator.add` vs `replace_list` vs `merge_dicts` deliberately).
- Persistence: if the node emits durable entities, extend `_persist_state_to_db` in `backend/app/workflows/runner.py:177-432`.
- Described order today: `ingest → validate → embed → nlp_extract → ontology_enrich → confluence → lifecycle → redteam → missing_signal → synthesize → calibrate`.

**New Migration:**
- Location: `backend/alembic/versions/NNN_slug.py` (next NNN after `015`; chain `down_revision` to the current head).
- Base reference: `backend/alembic/versions/001_initial_v51_schema.py` for extension/index patterns (notably the HNSW block at lines 195-201).
- Guardrails: never edit landed migrations; keep `audit_log` append-only trigger (`014`) intact; widen-with-backfill pattern per `006`/`010`/`011`; run `alembic upgrade head` via `start.py`'s `apply_database_migrations()`.

**New Service / Provider:**
- Services: `backend/app/services/<name>.py` (pure functions/classes, no router imports); consumed by nodes + endpoints.
- Providers: implement `LLMProvider` in `backend/app/providers/<name>.py`, register in `ProviderFactory` (`backend/app/providers/factory.py`), honor `ProviderCapability` + `DataClassification` gates.

## Special Directories

**`models/` (git-ignored weights):**
- Purpose: Local GGUF binaries for Gemma (`*.gguf`, e.g. Gemma-3 4B); resolved at runtime by `start.py` detection + `backend/app/providers/gemma.py`.
- Generated: No (downloaded via `scripts/download_model.py` / `setup.py --download-model`).
- Committed: No.

**`logs/` (runtime):**
- Purpose: `backend.log` + `frontend.log` tailed by `start.py` telemetry loop.
- Generated: Yes. Committed: No.

**`data/` + `backend/app/data/`:**
- Purpose: `backend/app/data/synthetic_signals.json` demo fixtures; root `data/` for local drops.
- Generated: No. Committed: Yes (fixtures only).

**`docs/` (33 entries):**
- Purpose: System architecture + master plan + rulebooks + audits + release manifests.
- Key: `docs/SYSTEM_ARCHITECTURE.md` (mermaid v5.1 diagram), `docs/METARADAR_MASTER_PLAN_v5.0.md`, `docs/rules/` + `docs/*.md` rulebooks mirrored from `AGENTS.md`.
- Generated: No. Committed: Yes.

**`contracts/`, `pitch/`, `poster/`, `scratch/`:**
- Purpose: API parity contracts, hackathon pitch assets, poster, operator scratch space.
- Generated: Partially (`contracts/` parity matrix via `scripts/generate_parity_matrix.py`). Committed: Yes (except scratch).

**`.planning/`:**
- Purpose: GSD state (`codebase/` docs incl. this file, phases, roadmap).
- Generated: Yes (agent-written). Committed: Yes (planning history).

---

*Structure analysis: 2026-09-19*
