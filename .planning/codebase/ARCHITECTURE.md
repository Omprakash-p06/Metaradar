<!-- refreshed: 2026-10-01 -->
# Architecture

**Analysis Date:** 2026-10-01

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│              Next.js 16 App Router Frontend                  │
│              `frontend/app/` + `frontend/components/`         │
├──────────────────┬──────────────────┬───────────────────────┤
│  Shell + Pages   │  lib/api client  │  AuthContext + types  │
│  `frontend/app/` │ `frontend/lib/`  │ `frontend/context/`   │
│  `frontend/components/metaradar.tsx`                        │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │  REST/JSON over HTTP (NEXT_PUBLIC_API_URL)         │
         ▼                                                   │
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Modular Monolith (async)                │
│         `backend/app/main.py` + `backend/app/api/`           │
│  Routers → Services → LangGraph Pipeline → Providers        │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  PostgreSQL 16 + pgvector + Redis + Local GGUF / Grok / BART │
│  `backend/app/models/` + `backend/alembic/versions/`         │
│  `models/gemma-3-4b-it-Q4_K_M.gguf`                          │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Process launcher | Starts Docker backing services, runs Alembic migrations, spawns uvicorn backend + Next.js frontend, streams telemetry | `start.py` |
| FastAPI application factory | Creates app, registers middleware (security headers, correlation ID, CORS), mounts 11 routers, owns lifespan (seed + scheduler start/stop) | `backend/app/main.py` |
| API routers | Thin HTTP adapters: parse/validate input, resolve auth deps, delegate to services/runner, serialize Pydantic schemas | `backend/app/api/v1/endpoints/*.py` |
| Auth/RBAC deps | Session cookie + CSRF verification, `get_current_user` / `get_optional_user`, per-route rate limiting, origin checks | `backend/app/api/deps.py` |
| Pipeline runner | Owns `PipelineRun` DB lifecycle, fetches unpromoted bronze rows, invokes LangGraph, persists silver/gold rows, marks bronze promoted | `backend/app/workflows/runner.py` |
| LangGraph pipeline | Canonical 11-node linear intelligence chain: ingest → validate → embed → nlp_extract → ontology → confluence → lifecycle → redteam → missing_signal → synthesize → calibrate | `backend/app/workflows/graph.py` |
| Pipeline state contract | `MetaRadarState` TypedDict with reducers (`operator.add` accumulation, `replace_list`, `merge_dicts`); initial-state factory | `backend/app/workflows/state.py` |
| Pipeline nodes | One file per intelligence stage; pure functions over `MetaRadarState` | `backend/app/workflows/nodes/*.py` |
| Domain services | Business logic: scoring, routing, relevance, calibration, deduplication, embeddings, vector search, PII, authority, confluence, redteam | `backend/app/services/*.py` |
| Ingestion service | Runs all/selected source connectors, persists `raw_signals_bronze`, writes `source_health_logs` telemetry | `backend/app/services/ingestion.py` |
| Autonomous scheduler | Singleton `SourceScheduler` started in lifespan; per-connector intervals, backoff, advisory-lock guarded, chains ingestion → pipeline | `backend/app/services/scheduler.py` |
| Source connectors | Per-source HTTP fetch + normalize to `RawSignalPayload` + bronze upsert; incremental cursor via `ConnectorState` | `backend/app/connectors/*.py` |
| LLM provider chain | Local Gemma → Grok (privacy-gated) → Degraded BART fallback behind `ProviderFactory.execute_task` | `backend/app/providers/factory.py` |
| SQLAlchemy models | Async ORM tables: bronze/silver/gold signals, developments, confluences, contradictions, calibration, routing, audit, auth, approvals | `backend/app/models/__init__.py` |
| Auth models | `User` + `Session` tables, role enum | `backend/app/models/auth.py` |
| DB session | Async engine + `AsyncSessionLocal`, `get_db` dependency, advisory-lock helpers | `backend/app/db/session.py` |
| DB seed | Demo users + canonical sources seeded at startup | `backend/app/db/seed.py` |
| Pydantic schemas | Request/response contracts for signals, intelligence views, registry, auth | `backend/app/schemas/*.py` |
| Frontend Shell | Authenticated app chrome (nav, sidebar, layout) wrapping every workspace page | `frontend/components/metaradar.tsx` |
| Frontend API client | Single `apiFetch` wrapper over `NEXT_PUBLIC_API_URL`, typed fetchers per domain, `mapSignal` normalization | `frontend/lib/api.ts` |
| Frontend auth state | `AuthProvider` with login/demo-login/logout, `/me` refresh, route guard redirect | `frontend/context/AuthContext.tsx` |
| API contract copy | Hand-maintained TS types; canonical source is template in `scripts/export_openapi.py` | `frontend/types/api.ts` |
| Domain config | Haemophilia disease-area config (assets, keywords, functions) loaded at startup | `backend/app/core/domain_config.py` + `config/haemophilia.yaml` |

## Pattern Overview

**Overall:** Modular async FastAPI monolith + Next.js App Router SPA shell + LangGraph batch intelligence pipeline over a Bronze → Silver → Gold data-lakehouse in Postgres.

**Key Characteristics:**
- Thin routers, fat services: routers in `backend/app/api/v1/endpoints/` do no business logic; all scoring/routing/ingestion lives in `backend/app/services/` and `backend/app/workflows/nodes/`.
- Stateful batch pipeline: `backend/app/workflows/graph.py` compiles a linear 11-node LangGraph executed by `backend/app/workflows/runner.py` under an `asyncio.Lock` (single-flight).
- Bronze-first ingestion: connectors write immutable raw payloads to `raw_signals_bronze`; the pipeline promotes them to `signals` (silver) and `developments`/`confluences` (gold).
- Provider fallback chain: every LLM call goes through `backend/app/providers/factory.py` (Gemma → Grok privacy-gated → BART summarize-only), never directly to a model.
- Contract-first frontend: `frontend/lib/api.ts` + `frontend/types/api.ts` mirror `contracts/openapi.json` (emitted by `scripts/export_openapi.py`).

## Layers

**Presentation (Next.js 16 App Router):**
- Purpose: Authenticated decision-intelligence workspaces (dashboard, signals, confluence, lifecycles, red-team, missing-signals, developments, intelligence/Athena, functions, calibrate, sources, observability, settings).
- Location: `frontend/app/`, `frontend/components/`
- Contains: Server-component route switch (`frontend/app/[section]/page.tsx`), client detail page (`frontend/app/signals/[signalId]/page.tsx`), workspace components per domain, `Shell` chrome (`frontend/components/metaradar.tsx`).
- Depends on: `frontend/lib/api.ts` fetchers, `frontend/context/AuthContext.tsx`, `frontend/types/api.ts`.
- Used by: Browser user; no server-side backend imports.

**API adapter (FastAPI routers):**
- Purpose: HTTP boundary — routing, auth/rate-limit deps, schema validation/serialization.
- Location: `backend/app/api/v1/endpoints/`
- Contains: 11 router modules (`auth`, `signals`, `pipeline`, `search`, `feedback`, `intelligence`, `registry`, `cache`, `observability`, `ingestion`, `health`).
- Depends on: `backend/app/api/deps.py`, `backend/app/services/*`, `backend/app/workflows/runner.py`, `backend/app/schemas/*`, `backend/app/db/session.py`.
- Used by: Frontend HTTP calls; OpenAPI export (`contracts/openapi.json`).

**Application services (business logic):**
- Purpose: All domain rules — where business logic lives. Scoring, function routing, relevance, calibration, deduplication, embeddings, hybrid vector search, PII redaction, authority tiers, confluence/redteam semantics, auth sessions, ingestion orchestration, scheduling.
- Location: `backend/app/services/`
- Contains: `scoring.py`, `routing.py`, `relevance.py`, `calibration.py`, `deduplication.py`, `embeddings.py`, `vector_query.py`, `confluence.py`, `redteam.py`, `authority.py`, `source_independence.py`, `provenance_urls.py`, `pii.py`, `ingestion.py`, `scheduler.py`, `auth_service.py`, `embeddings_backfill.py`.
- Depends on: `backend/app/models/`, `backend/app/connectors/`, `backend/app/providers/`, `backend/app/core/`.
- Used by: Routers and workflow nodes/runner. Never import routers.

**Intelligence pipeline (LangGraph):**
- Purpose: Deterministic 11-stage enrichment chain executed as batch jobs (manual trigger or scheduler).
- Location: `backend/app/workflows/`
- Contains: `graph.py` (wiring), `state.py` (contract), `runner.py` (execution + persistence), `nodes/*.py` (stage logic).
- Depends on: Services + providers + models.
- Used by: `pipeline.py` and `ingestion.py` routers, `scheduler.py`.

**Connectors (ingestion edge):**
- Purpose: Per-source polling/normalization (PubMed, ClinicalTrials.gov, FDA, EMA, NewsAPI, BioPharma Dive, Fierce Pharma, ET Pharma) with incremental cursor state.
- Location: `backend/app/connectors/`
- Contains: `base.py` (`SourceConnector`, `RawSignalPayload`, `ProfileRunResult`), one module per source, `__init__.py` registry (`ALL_CONNECTORS`).
- Depends on: `httpx`, `backend/app/services/deduplication.py`, `backend/app/models/` (`ConnectorState`, `RawSignalBronze`).
- Used by: `backend/app/services/ingestion.py` only.

**LLM providers:**
- Purpose: Abstract reasoning backends behind capability + data-classification gate.
- Location: `backend/app/providers/`
- Contains: `base.py` (interface, `ProviderCapability`, `DataClassification`), `gemma.py`, `grok.py`, `degraded.py`, `factory.py`.
- Depends on: `backend/app/core/config.py` settings.
- Used by: Workflow `synthesize` node and Athena/search paths via `provider_factory.execute_task`.

**Persistence:**
- Purpose: Async SQLAlchemy over Postgres 16 + pgvector; Redis for cache/rate-limit backing; Alembic versioned migrations.
- Location: `backend/app/models/`, `backend/app/db/`, `backend/alembic/`
- Contains: `models/__init__.py` (all domain tables), `models/auth.py`, `db/session.py`, `db/seed.py`, `alembic/versions/001–015_*.py`.
- Depends on: `backend/app/core/config.py` (`DATABASE_URL`).
- Used by: Services, runner, routers (via `get_db`).

**Cross-cutting core:**
- Purpose: Settings, structured logging, security primitives, middleware, PII redaction, domain config.
- Location: `backend/app/core/`
- Contains: `config.py`, `security.py`, `middleware.py` (`CorrelationIdMiddleware`, `SecurityHeadersMiddleware`), `logging.py`, `redact.py`, `domain_config.py`.
- Used by: Everything backend.

## Data Flow

### Primary Request Path

1. Browser route resolves workspace — `frontend/app/[section]/page.tsx` switches on `section` param and renders the matching workspace inside `<Shell>` (`frontend/components/metaradar.tsx`).
2. Workspace component calls typed fetcher — e.g. `fetchSignals` / `fetchSignal` / `getConfluences` in `frontend/lib/api.ts:265-346`, which calls `apiFetch` (`frontend/lib/api.ts:192`) against `NEXT_PUBLIC_API_URL` (`frontend/lib/api.ts:171`) with credentials + CSRF header.
3. FastAPI middleware chain — `SecurityHeadersMiddleware` → `CorrelationIdMiddleware` → `CORSMiddleware` in `backend/app/main.py:76-88`, then router prefix dispatch (`backend/app/main.py:91-101`).
4. Route handler + auth dep — e.g. `GET /signals` in `backend/app/api/v1/endpoints/signals.py` resolves `get_db` (`backend/app/db/session.py:31`) and `get_current_user`/`get_optional_user` (`backend/app/api/deps.py`).
5. Service + DB read — handler queries `Signal`/`Development`/`Confluence` models (`backend/app/models/__init__.py`) via `AsyncSession`, applies mappers/scoring/ routing helpers, returns Pydantic schema (`backend/app/schemas/`).
6. Frontend normalization — `mapSignal` (`frontend/lib/mappers.ts` via `frontend/lib/api.ts:48`) converts wire shape to UI `Signal` (`frontend/types/api.ts`) for workspace rendering.

### Ingestion → Intelligence Flow

1. Trigger: `POST /api/v1/ingestion/run` (`backend/app/api/v1/endpoints/ingestion.py`) or `SourceScheduler` tick (`backend/app/services/scheduler.py`) or `POST /pipeline/run` (`backend/app/api/v1/endpoints/pipeline.py`).
2. `IngestionService.run_connectors` (`backend/app/services/ingestion.py`) executes each `SourceConnector` profile (`backend/app/connectors/base.py`), upserts immutable rows into `raw_signals_bronze` via `check_and_persist_bronze` (`backend/app/services/deduplication.py`), writes `source_health_logs` rows.
3. `PipelineRunner.run` (`backend/app/workflows/runner.py:43`) acquires the global `asyncio.Lock`, creates a `pipeline_runs` row, loads unpromoted bronze payloads, builds initial `MetaRadarState` (`backend/app/workflows/state.py:68`).
4. `build_graph()` chain (`backend/app/workflows/graph.py:22`) runs 11 nodes in order (`backend/app/workflows/nodes/*.py`): ingest → validate → embed (`embeddings.py`) → nlp_extract → ontology → confluence → lifecycle → redteam → missing_signal → synthesize (via `provider_factory.execute_task`, `backend/app/providers/factory.py:19`) → calibrate.
5. `runner._persist_state_to_db` (`backend/app/workflows/runner.py:177`) upserts `developments`, `signals` (with pgvector embedding, `score_breakdown` from `scoring.py`, routing from `routing.py`, provenance URL from `provenance_urls.py`), inserts `confluences`, marks bronze rows promoted, completes the `pipeline_runs` row.

### Ask Athena (RAG) Flow

1. `AthenaWorkspace` (`frontend/components/intelligence/`) posts to `POST /athena` (`backend/app/api/v1/endpoints/signals.py` Athena routes) or `POST /api/v1/search` (`backend/app/api/v1/endpoints/search.py`).
2. `vector_query_service` (`backend/app/services/vector_query.py`) embeds the query (`backend/app/services/embeddings.py`) and runs pgvector similarity over `signals.embedding` with metadata filters.
3. `provider_factory.execute_task` (`backend/app/providers/factory.py:19`) synthesizes the answer (Gemma → Grok gated → BART) with evidence citations; response typed as `AthenaQueryResponse` (`backend/app/schemas/`, `frontend/types/api.ts`).

**State Management:**
- Backend pipeline state is ephemeral per run (`MetaRadarState` dict, `backend/app/workflows/state.py`); durable state is Postgres rows + `connector_state` cursors + `pipeline_runs` ledger.
- Frontend state is local React state + `AuthContext` (`frontend/context/AuthContext.tsx`); no global store. Server state is refetched per workspace via `lib/api.ts` fetchers with `AbortSignal` cancellation.

## Key Abstractions

**Bronze → Silver → Gold signals:**
- Purpose: Separates raw evidence (bronze), validated scored signals (silver), and aggregated intelligence (gold developments/confluences).
- Examples: `backend/app/models/__init__.py` (`RawSignalBronze`, `Signal`, `Development`, `Confluence`), `backend/app/workflows/nodes/ingest.py`, `backend/app/workflows/nodes/validate.py`, `backend/app/workflows/runner.py:177`
- Pattern: Immutable bronze insert with `(source_id, external_id)` uniqueness; silver upsert on `fingerprint`; gold created per development cluster.

**Signal decision object:**
- Purpose: Every signal carries an explainable routing/action recommendation (what changed, why it matters, responsible function, escalation, suggested action).
- Examples: `backend/app/services/routing.py`, `backend/app/services/relevance.py`, `backend/app/workflows/runner.py:296-310`, `GET /signals/{id}/decision-object` in `backend/app/api/v1/endpoints/signals.py`
- Pattern: `resolve_signal_routing(...)` merges scorer output + rules into `relevant_function` / `route_destination` / `is_escalated` columns on `Signal`.

**Calibration feedback loop:**
- Purpose: Stakeholder relevance ratings adjust per-function scoring weights over time.
- Examples: `backend/app/services/calibration.py`, `backend/app/workflows/nodes/calibrate.py`, `backend/app/models/__init__.py` (`CalibrationFeedback`, `CalibrationRun`, `ScoringWeights`), `backend/app/api/v1/endpoints/feedback.py`
- Pattern: Feedback rows accumulate → calibration run recomputes weights → `signal_routing` stores baseline vs calibrated routing for audit.

## Entry Points

**Unified launcher:**
- Location: `start.py`
- Triggers: `python start.py [--no-frontend] [--no-backend] [--no-docker] [--port-backend] [--port-frontend] [--daemon]`
- Responsibilities: Starts Postgres+Redis via compose, runs `alembic upgrade head`, spawns `uvicorn app.main:app` (backend dir, `PYTHONPATH=backend`) and `next dev -p` (frontend dir) with `NEXT_PUBLIC_API_URL` injection, health-poll telemetry loop.

**Backend ASGI app:**
- Location: `backend/app/main.py:69`
- Triggers: `uvicorn app.main:app` (dev via `start.py:241`; prod `metaradar-backend` service in `docker-compose.yml`).
- Responsibilities: Lifespan (validate settings, load domain config, seed demo users/sources, start scheduler), middleware + 11 router mounts, `GET /` version probe.

**Frontend root:**
- Location: `frontend/app/page.tsx` → redirects to `frontend/app/login/page.tsx`; authenticated shell at `frontend/app/[section]/page.tsx`; detail at `frontend/app/signals/[signalId]/page.tsx`
- Triggers: Browser navigation; `AuthProvider` (`frontend/app/layout.tsx:42`) guards routes and pushes `/dashboard` after login.
- Responsibilities: Route switch → workspace component inside `Shell`; detail page orchestrates `fetchSignal` + confluence/contradiction fetchers (`frontend/app/signals/[signalId]/page.tsx:30`).

## Architectural Constraints

- **Threading:** Single-process `asyncio` throughout backend; pipeline runs are single-flight via `asyncio.Lock` in `backend/app/workflows/runner.py:30`; connector fan-out capped by `asyncio.Semaphore(4)` in `backend/app/services/scheduler.py`.
- **Global state:** Module-level singletons — `provider_factory` (`backend/app/providers/factory.py:63`), `SourceScheduler.get_instance()` (`backend/app/services/scheduler.py`), SQLAlchemy `engine`/`AsyncSessionLocal` (`backend/app/db/session.py:10-25`), embedding service singleton (`backend/app/services/embeddings.py`).
- **Circular imports:** No sanctioned cycles; routers must not be imported by services/nodes. Shared auth helpers live in `backend/app/api/deps.py`; shared config in `backend/app/core/config.py`.
- **Async-only DB:** All DB access via `AsyncSession` + `asyncpg`; Alembic runs sync migrations against the same Postgres — models must stay in sync with `backend/alembic/versions/`.
- **LLM access discipline:** Never instantiate `GemmaProvider`/`GrokProvider` directly in nodes/routers — always call `provider_factory.execute_task` with explicit `ProviderCapability` + `DataClassification` so the privacy gate applies.
- **Audit immutability:** `AuditLog` rows are append-only enforced by SQLAlchemy `before_update`/`before_delete` guards (`backend/app/models/__init__.py:438-445`).
- **Contract sync:** `frontend/types/api.ts` is hand-maintained; changes require editing the template in `scripts/export_openapi.py` and regenerating `contracts/openapi.json` together (see `tests/test_contract_drift.py`).

## Anti-Patterns

### Business logic in routers

**What happens:** Adding scoring, routing, or enrichment inline in a new endpoint module under `backend/app/api/v1/endpoints/`.
**Why it's wrong:** Duplicates rules already in services/nodes, breaks the thin-router invariant, and bypasses calibration/provenance handling.
**Do this instead:** Put rules in `backend/app/services/` (or a new node in `backend/app/workflows/nodes/` + wiring in `backend/app/workflows/graph.py`) and call it from the router, following `backend/app/api/v1/endpoints/signals.py` → `backend/app/services/routing.py`.

### Direct provider instantiation

**What happens:** Importing `GemmaProvider`/`GrokProvider` in a node or router and calling `generate_intelligence` directly.
**Why it's wrong:** Skips the Gemma → Grok-gated → BART fallback chain and the PII/privacy classification gate.
**Do this instead:** Call `provider_factory.execute_task(required_capability, evidence, task, classification)` as in `backend/app/providers/factory.py:19`.

## Error Handling

**Strategy:** Router-level `HTTPException` with status codes; pipeline-level error accumulation in `MetaRadarState.errors` plus `pipeline_runs.error_summary`; connector-level per-source telemetry rows instead of failing the whole run.

**Patterns:**
- Routers raise `HTTPException(status_code, detail)`; shared `ApiError` on the frontend (`frontend/lib/errors.ts`, re-exported by `frontend/lib/api.ts:50`).
- Pipeline nodes append to `state["errors"]` and continue; `runner.py:164-175` marks the run `failed` only on graph-level exceptions.
- Connectors raise `ConnectorFetchError` (`backend/app/connectors/base.py`) after retries; `IngestionService` records `connector_status`/`last_error` per source and continues with remaining connectors.
- Scheduler uses exponential backoff + `consecutive_failures` counters (`backend/app/services/scheduler.py`) and Postgres advisory locks (`backend/app/db/session.py:43`) to avoid overlapping runs.

## Cross-Cutting Concerns

**Logging:** `structlog` JSON logging configured in `backend/app/core/logging.py`, initialized in `backend/app/main.py:26`; per-request correlation IDs via `CorrelationIdMiddleware` (`backend/app/core/middleware.py`).
**Validation:** Pydantic schemas at the API boundary (`backend/app/schemas/`); `RawSignalPayload` model in `backend/app/connectors/base.py`; `SearchRequest` inline in `backend/app/api/v1/endpoints/search.py`.
**Authentication:** Session-cookie + signed token + CSRF (`backend/app/core/security.py`, `backend/app/services/auth_service.py`), enforced via `backend/app/api/deps.py` (`get_current_user`, `require_csrf`, `require_preauth_origin`, rate-limit buckets); frontend session mirrored in `frontend/context/AuthContext.tsx`.

---

*Architecture analysis: 2026-10-01*
