<!-- refreshed: 2026-09-19 -->
# Architecture

**Analysis Date:** 2026-09-19

## System Overview

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ PRESENTATION — Next.js 16 App Router (`frontend/app/`, `frontend/components/`)│
│  /login → /dashboard → /[section] (13 workspaces) + /signals/[signalId]      │
│  Shell + providers: `frontend/app/layout.tsx`, `frontend/context/AuthContext.tsx`│
├──────────────────────────────────────────────────────────────────────────────┤
│ API — FastAPI (`backend/app/main.py` → `backend/app/api/v1/endpoints/*.py`)  │
│  signals · intelligence · pipeline · ingestion · search · feedback · registry │
│  health · auth · cache · observability  (all under /api/v1)                  │
├──────────────────────────────┬───────────────────────────────────────────────┤
│ CONNECTORS                   │ 11-NODE LANGGRAPH PIPELINE                     │
│ `backend/app/connectors/`    │ `backend/app/workflows/graph.py`               │
│ pubmed · clinical_trials ·   │ ingest→validate→embed→nlp_extract→ontology→    │
│ fda · ema · newsapi ·        │ confluence→lifecycle→redteam→missing_signal→   │
│ fierce_pharma · et_pharma ·  │ synthesize→calibrate (`nodes/*.py`, 11 files)  │
│ biopharma_dive               │ orchestrated by `workflows/runner.py`          │
├──────────────────────────────┴───────────────────────────────────────────────┤
│ SERVICES + PROVIDERS (`backend/app/services/`, `backend/app/providers/`)     │
│ scoring · routing · confluence · redteam · calibration · deduplication · pii  │
│ embeddings (384-dim) · vector_query · provenance_urls · scheduler · authority │
│ providers: gemma (local) → grok (gated fallback) → degraded (BART summarize) │
├──────────────────────────────────────────────────────────────────────────────┤
│ DATA — PostgreSQL 16 + pgvector + Redis (`backend/app/models/`, `db/`)       │
│ 25 tables · signals.embedding VECTOR(384) + HNSW index · append-only audit   │
│ Alembic: `backend/alembic/versions/001..015_*.py` (15 migrations)             │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Process launcher | Starts Docker backing services, runs Alembic, launches uvicorn + Next.js, streams telemetry | `start.py` |
| Zero-config setup | Dependency checks, `.env` init, DB seed, model download | `setup.py` |
| FastAPI app | Lifespan (auto-seed + scheduler), middleware, router registration | `backend/app/main.py` |
| PipelineRunner | LangGraph execution, `PipelineRun` lifecycle, bronze→silver→gold persistence | `backend/app/workflows/runner.py` |
| Pipeline graph | Compiles canonical 11-node linear LangGraph | `backend/app/workflows/graph.py` |
| Pipeline state | `MetaRadarState` TypedDict contract + reducers | `backend/app/workflows/state.py` |
| IngestionService | Runs connectors, aggregates per-source telemetry | `backend/app/services/ingestion.py` |
| SourceScheduler | Autonomous per-connector cadence with advisory locks, semaphore(4) | `backend/app/services/scheduler.py` |
| Priority scorer | 4-factor deterministic scoring (Novelty 25 / Clinical 30 / Regulatory 25 / Recency 20) | `backend/app/services/scoring.py` |
| Router | Signal→function routing + leadership escalation | `backend/app/services/routing.py` |
| Embedding service | Fastembed 384-dim vectors (`all-MiniLM-L6-v2`) | `backend/app/services/embeddings.py` |
| Vector query | pgvector cosine retrieval with HNSW `ef_search` tuning | `backend/app/services/vector_query.py` |
| Provider factory | Local Gemma → Grok (gated) → BART degraded fallback chain | `backend/app/providers/factory.py` |
| Domain config | Single source of truth: diseases, assets, connectors, routing matrix | `config/haemophilia.yaml` |
| Frontend shell | Root layout, theme + auth providers, section router | `frontend/app/layout.tsx`, `frontend/app/[section]/page.tsx` |

## Pattern Overview

**Overall:** Layered monolith backend (FastAPI) + App Router frontend, with a medallion data pattern (bronze → silver → gold) executed by a linear LangGraph state machine.

**Key Characteristics:**
- Bronze-first ingestion: connectors persist raw payloads only, never intelligence (`backend/app/connectors/base.py:81-88`, D-01/D-26).
- Linear 11-node pipeline with typed accumulating state (`backend/app/workflows/state.py`, `backend/app/workflows/graph.py:22-63`).
- Deterministic, explainable scoring versioned per signal (`scoring_model_version`, `scoring_config_version` on `signals`).
- Config-driven domain: all disease/asset/connector/routing definitions live in `config/haemophilia.yaml`, loaded once at startup (`backend/app/main.py:35-42`).
- Append-only compliance: `audit_log` guarded at ORM + DB-trigger level.

## Layers

**Presentation (`frontend/`):**
- Purpose: Role workspaces, signal explorer, Athena RAG chat, ops/calibration UIs.
- Location: `frontend/app/`, `frontend/components/`, `frontend/context/`, `frontend/lib/`, `frontend/types/`
- Contains: 13 section workspaces routed by `frontend/app/[section]/page.tsx:23-71`; shared shell in `frontend/components/metaradar.tsx`.
- Depends on: Backend `/api/v1` via typed client `frontend/lib/api.ts`.
- Used by: End users (demo personas per role).

**API (`backend/app/api/`):**
- Purpose: HTTP boundary, request validation, RBAC/CSRF enforcement.
- Location: `backend/app/api/v1/endpoints/` (11 routers: `auth.py`, `signals.py`, `intelligence.py`, `pipeline.py`, `ingestion.py`, `search.py`, `feedback.py`, `registry.py`, `cache.py`, `observability.py`, `health.py`); shared deps in `backend/app/api/deps.py`.
- Contains: Route handlers, Pydantic request/response schemas (with `backend/app/schemas/`).
- Depends on: Services, workflows, `backend/app/db/session.py:get_db`.
- Used by: Frontend client, ops scripts (`scripts/*.py`).

**Connectors (`backend/app/connectors/`):**
- Purpose: Source-specific, idempotent, quota-aware fetching → bronze rows only.
- Location: `backend/app/connectors/` — `base.py` (contract) + 8 adapters (`pubmed.py`, `clinical_trials.py`, `fda.py`, `ema.py`, `newsapi.py`, `fierce_pharma.py`, `et_pharma.py`, `biopharma_dive.py`), registry in `backend/app/connectors/__init__.py:16-25`.
- Contains: `SourceConnector` base (`fetch_latest`, `run_profile`, `run_all_profiles`, `_persist_bronze`, connector-state I/O, health logging).
- Depends on: `config/haemophilia.yaml` per-source profiles, `backend/app/services/deduplication.py:check_and_persist_bronze`.
- Used by: `IngestionService`, `SourceScheduler`.

**Workflows (`backend/app/workflows/`):**
- Purpose: 11-node intelligence pipeline definition + execution.
- Location: `backend/app/workflows/graph.py`, `runner.py`, `state.py`, `nodes/` (11 node modules + `__init__.py`).
- Contains: Node functions `node_ingest`, `node_validate`, `node_embed`, `node_nlp_extract`, `node_ontology_enrich`, `node_confluence`, `node_lifecycle`, `node_redteam`, `node_missing_signal`, `node_synthesize`, `node_calibrate`.
- Depends on: Services (scoring, embeddings, confluence, redteam, calibration, routing), providers.
- Used by: `POST /api/v1/pipeline/run` (`backend/app/api/v1/endpoints/pipeline.py:25-53`), scheduler promotion, E2E scripts.

**Services (`backend/app/services/`):**
- Purpose: Pure domain logic shared by nodes, endpoints, scheduler.
- Location: `backend/app/services/` (17 modules: `auth_service.py`, `authority.py`, `calibration.py`, `confluence.py`, `deduplication.py`, `embeddings.py`, `embeddings_backfill.py`, `ingestion.py`, `pii.py`, `provenance_urls.py`, `redteam.py`, `relevance.py`, `routing.py`, `scheduler.py`, `scoring.py`, `source_independence.py`, `vector_query.py`).
- Depends on: Models, domain config, providers.
- Used by: Workflow nodes, API endpoints.

**Providers (`backend/app/providers/`):**
- Purpose: LLM inference abstraction with privacy-gated fallback.
- Location: `backend/app/providers/` — `base.py`, `gemma.py`, `grok.py`, `degraded.py`, `factory.py`.
- Chain: Local Gemma (`llama-cpp` GGUF in `models/`) → Grok (only with key + permitted classification) → BART degraded (summarize-only) — `backend/app/providers/factory.py:19-40`.
- Used by: `node_synthesize`, Athena endpoints in `backend/app/api/v1/endpoints/signals.py`.

**Persistence (`backend/app/models/`, `backend/app/db/`, `backend/alembic/`):**
- Purpose: Async SQLAlchemy models, session management, versioned DDL.
- Location: `backend/app/models/__init__.py` (23 tables), `backend/app/models/auth.py` (`users`, `sessions`), `backend/app/db/session.py`, `backend/app/db/seed.py`, `backend/alembic/versions/` (15 migrations).
- Used by: Everything backend.

## Data Flow

### Primary Request Path (ingestion → role brief)

1. Scheduler / manual trigger — `SourceScheduler` tick or `POST /api/v1/ingestion/run` (`backend/app/services/scheduler.py`, `backend/app/api/v1/endpoints/ingestion.py:43-62`).
2. Connector fetch with retry/backoff + quota awareness — `backend/app/connectors/base.py:133-166` (`_fetch_with_retry`, max 3, exponential + jitter).
3. Bronze persist (dedup on `(source_id, external_id)`, SHA-256 `content_hash`) — `backend/app/connectors/base.py:224-239`, `backend/app/services/deduplication.py`; table `raw_signals_bronze` (`backend/app/models/__init__.py:176-193`, unique constraint `uq_raw_source_external`).
4. Pipeline fetch of unpromoted bronze (`pipeline_run_id IS NULL`, `retrieved_at DESC`, limit=batch_size) — `backend/app/workflows/runner.py:94-124`.
5. Scrub + validate — `node_validate` (`backend/app/workflows/nodes/validate.py`): PII scrub (`backend/app/services/pii.py`), authority tiering (`backend/app/services/authority.py`), validation status.
6. Embed (384-dim Fastembed) — `node_embed` (`backend/app/workflows/nodes/embed.py`) via `backend/app/services/embeddings.py:82-88`; replacement reducer semantics keep one canonical list (`backend/app/workflows/state.py:13-23`).
7. NLP extract → ontology enrich — `nodes/nlp_extract.py`, `nodes/ontology.py` (BART zero-shot + haemophilia ontology from `config/haemophilia.yaml`).
8. Confluence (48h window, ≥3 independent signals) → lifecycle (9 stages) → red-team (contradiction rules) → missing-signal FSM — `nodes/confluence.py`, `nodes/lifecycle.py`, `nodes/redteam.py`, `nodes/missing_signal.py`; thresholds in `config/haemophilia.yaml:135-138,324-338`.
9. Deterministic 4-factor scoring + explainable routing — `backend/app/services/scoring.py` (`SCORING_VERSION = "haemophilia_v2.0"`), `backend/app/services/routing.py:resolve_signal_routing` (baseline matrix `config/haemophilia.yaml:154-176`).
10. Synthesize briefs → calibrate weights — `nodes/synthesize.py` (Gemma/Grok/BART chain), `nodes/calibrate.py` (feedback-weighted per-function weights, `calibration_feedback` → `scoring_weights`).
11. Persist silver/gold + promote bronze — `PipelineRunner._persist_state_to_db` (`backend/app/workflows/runner.py:177-432`): `developments`, `signals` (upsert on `fingerprint`), `confluences`; bronze marked with `pipeline_run_id`; failed rows left unpromoted for retry (`runner.py:412-430`).
12. Serve role workspaces — `GET /api/v1/signals`, `/intelligence/*`, `/functions/*` → 13 frontend workspaces (`frontend/app/[section]/page.tsx`).
13. Audit every mutation — `audit_log` rows with `correlation_id` + `user_id` FK (`backend/app/models/__init__.py:424-435`); immutable via ORM listeners (`models/__init__.py:438-445`) + DB trigger `block_audit_log_mutation` (`backend/alembic/versions/014_auditlog_user_correlation.py:24-35`).

### Athena RAG Q&A (secondary flow)

1. `POST /api/v1/athena/query` (`backend/app/api/v1/endpoints/signals.py:1420+`) → `VectorQueryService` (`backend/app/services/vector_query.py`) pgvector cosine search over `signals.embedding` (HNSW, `ef_search` per-txn at `vector_query.py:140-142`).
2. Evidence gate: max cosine distance threshold; keyword/landscape fallbacks when vector recall is thin.
3. Provider chain generates grounded answer with citations (`AthenaEvidenceCitation`); activity logged to `audit_log`.

### Calibration loop (secondary flow)

1. `POST /api/v1/feedback` stores `calibration_feedback` rows (`is_applied=false`).
2. Recalibration run flips `is_applied`, writes `calibration_runs` + `calibration_history`, updates `scoring_weights` per stakeholder function (`backend/app/services/calibration.py`).
3. Next pipeline run loads fresh weights into `MetaRadarState.calibration_weights` (`backend/app/workflows/state.py:58-65` defaults).

**State Management:**
- Pipeline state is an ephemeral `MetaRadarState` TypedDict (`backend/app/workflows/state.py:26-51`): `operator.add` accumulation for entity lists, `replace_list` for `validated_signals`, `merge_dicts` for `calibration_weights`/`node_statuses`; scalars (`batch_size`, `signals_processed`) replaced.
- Durable state: `pipeline_runs` (run lifecycle), `connector_state` (per-connector/per-profile cursors), `raw_signals_bronze.pipeline_run_id` (promotion watermark).
- Concurrency: single-flight `_pipeline_concurrency_lock` (`runner.py:30`); per-source Postgres advisory locks + global semaphore(4) in scheduler.
- Frontend: `AuthContext` (`frontend/context/AuthContext.tsx`) + localStorage demo-role key; server components for section routing.

## Key Abstractions

**SourceConnector (bronze-only contract):**
- Purpose: Uniform fetch→persist→telemetry lifecycle every source honors.
- Examples: `backend/app/connectors/base.py:81-98`; 8 subclasses; registry `backend/app/connectors/__init__.py`.
- Pattern: Template method (`fetch_latest`/`run_profile` overridden; retry, bronze persist, state I/O, health log inherited).

**PipelineRunner (execution orchestrator):**
- Purpose: Owns run lifecycle end-to-end: `PipelineRun` row → bronze fetch → `graph.ainvoke` → persistence → completion/failure marking.
- Examples: `backend/app/workflows/runner.py:33-175`.
- Pattern: Async orchestrator with injected `AsyncSession`; concurrency lock; never loses data (failed bronze rows stay unpromoted).

**MetaRadarState (accumulating contract):**
- Purpose: Single typed channel contract all 11 nodes read/append.
- Examples: `backend/app/workflows/state.py`; factory `create_initial_state`.
- Pattern: TypedDict + LangGraph reducers; backward alias `IntelligenceState`.

**ProviderFactory (privacy-gated fallback):**
- Purpose: Capability-based LLM dispatch with data-classification gate.
- Examples: `backend/app/providers/factory.py`, `base.py` (`ProviderCapability`, `DataClassification`).
- Pattern: Chain-of-responsibility with graceful degradation (never fails hard — BART always available).

**Signal decision object:**
- Purpose: Every signal carries what-changed / why-it-matters / routing / suggested action for role workspaces.
- Examples: Columns on `signals` (`backend/app/models/__init__.py:264-280`); migration `012_signal_decision_object_fields.py`.

## Entry Points

**Unified launcher:**
- Location: `start.py`
- Triggers: `python start.py [--no-frontend] [--no-backend] [--no-docker] [--port-backend] [--port-frontend] [--daemon]`
- Responsibilities: Docker Postgres/Redis up, `alembic upgrade head`, uvicorn `app.main:app` (cwd `backend/`), Next.js dev server, log streaming + heartbeat telemetry, graceful shutdown.

**Environment setup:**
- Location: `setup.py`
- Triggers: `python setup.py [--skip-docker] [--skip-models] [--skip-frontend] [--skip-db-seed] [--download-model]`
- Responsibilities: 7-step bootstrap (.env, deps, backing services, migrations, seeds, models).

**Backend app:**
- Location: `backend/app/main.py:68-100`
- Triggers: uvicorn import; lifespan seeds demo users + canonical sources, starts `SourceScheduler`.
- Responsibilities: Middleware order (security headers → correlation ID → CORS), 11 routers under `/api/v1`.

**Frontend root:**
- Location: `frontend/app/layout.tsx` (Plus Jakarta Sans, `ThemeProvider`, `AuthProvider`), `frontend/app/page.tsx` (redirects `/` → `/login`).
- Triggers: Every page load; `AuthContext` auto-bootstraps session via `GET /api/v1/auth/me`.

**Pipeline trigger:**
- Location: `POST /api/v1/pipeline/run` (`backend/app/api/v1/endpoints/pipeline.py`), `GET /api/v1/pipeline/status/{id}`.
- Triggers: Manual runs, scheduler promotion, E2E scripts (`scripts/test_e2e_vertical_slice.py`).

## Architectural Constraints

- **Threading:** Async single-process FastAPI (asyncio); CPU-bound inference (llama-cpp Gemma, BART) runs in threads/process pool off the event loop; scheduler uses one loop + semaphore(4). No multi-process backend.
- **Global state:** `SourceScheduler.get_instance()` singleton (`backend/app/services/scheduler.py`); `_pipeline_concurrency_lock` module-level (`runner.py:30`); `embedding_service` singleton (`services/embeddings.py`); `_rate_buckets` in-memory rate limits (`api/deps.py:22-23`, reset on restart).
- **Circular imports:** Avoided by lazy imports inside functions (e.g. `domain_config` import inside `base.py:117`, seed imports inside `main.py:46-48` lifespan).
- **Append-only invariants:** `raw_signals_bronze` is logically append-only (unique `(source_id, external_id)`, promotion via FK stamp, never deleted); `audit_log` hard append-only (ORM listeners + `block_audit_log_mutation` trigger).
- **Connector isolation:** Connectors never import services beyond `deduplication`/`redact`; never write silver/gold tables (D-26).
- **Secrets:** Never in code; `.env` + `backend/app/core/config.py` only (see INTEGRATIONS.md).

## Anti-Patterns

### Bypassing bronze for intelligence writes

**What happens:** A new connector or script inserts directly into `signals`/`developments`.
**Why it's wrong:** Breaks dedup identity, provenance (`raw_record_reference`), retry watermark, and truthfulness gates; Phase-1 contract D-26 forbids it.
**Do this instead:** Persist `RawSignalPayload` via `SourceConnector._persist_bronze` (`backend/app/connectors/base.py:224-239`) and let `PipelineRunner` promote it.

### Fabricating connector health

**What happens:** Returning hard-coded `HEALTHY`/`last_success` instead of reading `connector_state`.
**Why it's wrong:** Violates honesty invariant D-22; ops dashboards lie about source freshness.
**Do this instead:** Follow `SourceConnector.get_status` (`base.py:298-345`) — degrade to in-memory state, never invent values.

### stashing secrets in code or logs

**What happens:** API keys in connector code or raw `_fetch_with_retry` error strings.
**Why it's wrong:** Secret leak; log exfiltration of query params.
**Do this instead:** Keys via `settings`/env only; all outbound error text passes through `redact_mapping`/`redact_text` (`backend/app/connectors/base.py:143,163-166`; `backend/app/core/redact.py`).

## Error Handling

**Strategy:** Bounded retries at the edge, degraded-but-honest mid-pipeline, never-lose-data persistence, structured surfacing via `PipelineRun.error_summary` + `node_statuses`.

**Patterns:**
- Connector HTTP: max 3 attempts, exponential backoff + jitter, typed `ConnectorFetchError` (`base.py:133-171`); per-profile `ProfileRunResult` aggregates to `SUCCESS | NO_NEW_DATA | PARTIAL | DEGRADED | FAILED | CONFIGURATION_ERROR` (`base.py:199-218`).
- Pipeline: per-node try/except appends to `state["errors"]`; run marked `completed`/`partial`/`failed` (`endpoints/pipeline.py:40`); bronze promotion skips failed rows for retry (`runner.py:386-430`).
- Embeddings/LLM:Fail-soft — missing embeddings leave `signals.embedding NULL` (retrieval falls back to keyword); provider chain always terminates at BART degraded mode.
- API: `HTTPException` with precise codes (400 bad UUID, 403 origin/CSRF/role, 429 rate limit); request-scoped `X-Request-ID`/`X-Correlation-ID` on every response (`backend/app/core/middleware.py`).
- Frontend: typed `ApiError` (`frontend/lib/errors.ts`) + `mapSignal` normalization (`frontend/lib/mappers.ts`).

## Cross-Cutting Concerns

**Logging:** structlog JSON (`backend/app/core/logging.py`, `configure_structlog(json_logs=True)` in `main.py:26`); correlation IDs bound via contextvars (`middleware.py:20-60`); launcher streams `[ATHENA]`/`[INGESTION]`/`[PIPELINE]`/`[LLM]` markers (`start.py:389-411`).
**Validation:** Pydantic v2 schemas at API boundary (`backend/app/schemas/` + inline `BaseModel`s in endpoints); domain validation in `node_validate`; decision-object columns non-nullable where safety-critical.
**Authentication:** Session-cookie + HMAC-bound CSRF (see Auth section below); `get_current_user` / `get_optional_user` / `require_role` deps (`backend/app/api/deps.py`); frontend `AuthContext` gate (`frontend/context/AuthContext.tsx:118-149`).

## Data Layer

**Tables (25 across 15 Alembic migrations `001..015`):** `pipeline_runs`, `sources`, `source_health_logs`, `companies`, `assets`, `trials`, `developments`, `events`, `lifecycle_events`, `confluences`, `raw_signals_bronze`, `connector_state`, `evidence`, `signals`, `contradictions`, `calibration_runs`, `calibration_history`, `scoring_weights`, `signal_routing`, `calibration_feedback`, `watch_items`, `audit_log`, `approval_requests` (`backend/app/models/__init__.py`), plus `users`, `sessions` (`backend/app/models/auth.py`). Base DDL in `001_initial_v51_schema.py` (17 tables); auth in `013`, audit FK in `014`, approvals in `015`; telemetry widened in `007`/`008`; decision-object fields in `012`.

**pgvector 384-dim HNSW:** `signals.embedding VECTOR(384)` (`models/__init__.py:294`, dim from `EMBEDDING_DIMENSION=384` in `backend/app/core/config.py:99`, model `all-MiniLM-L6-v2` per `services/embeddings.py:3`); index `signals_embedding_hnsw USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)` (`001_initial_v51_schema.py:195-201`); extensions `vector` + `pg_trgm` enabled in-migration. Partial unique indexes on `pmid`/`nct_id`/`regulatory_id`/`canonical_url`; unique `fingerprint` (upsert key, widened in `011`).

**Bronze discipline:** `raw_signals_bronze` (`models/__init__.py:176-193`) carries `raw_payload JSONB` verbatim (D-23), `content_hash`, `connector_version`, `cross_source_group_id`, `pipeline_run_id` promotion watermark; unique `(source_id, external_id)`.

**Audit immutability:** `block_audit_log_mutation()` PL/pgSQL function + `trg_block_audit_log_update_delete` trigger (`014_auditlog_user_correlation.py:24-35`) raise on any UPDATE/DELETE; mirrored by SQLAlchemy `before_update`/`before_delete` listeners (`models/__init__.py:438-445`); every row carries `correlation_id` + nullable `user_id` FK for attribution.

## Authentication & RBAC

- **Mechanism:** bcrypt passwords (`backend/app/core/security.py:12-23`), opaque session IDs signed with `TimestampSigner` into `metaradar_session` cookie, server-side `sessions` table indexed by SHA-256 `token_hash` (`models/auth.py:25-41`); CSRF tokens HMAC-bound to session ID in `metaradar_csrf` cookie (`security.py:55-74`).
- **Deps:** `get_current_user` (hard gate), `get_optional_user` (public+personalized), `require_role(*roles)` with `ADMIN` override (`backend/app/api/deps.py:154-163`); pre-auth origin allow-list + per-IP auth rate limit on `/login`/`/demo-login` (`deps.py:39-90`).
- **Roles:** 6 stakeholder functions from `config/haemophilia.yaml:140-152` double as RBAC roles (`MEDICAL_AFFAIRS`, `REGULATORY`, `SAFETY`, `MARKET_ACCESS`, `COMMUNICATIONS`, `LEADERSHIP`) + `ADMIN`; demo login seeds one persona per role at startup (`main.py:44-54` via `auth_service.seed_demo_users_if_needed`).
- **Frontend:** `AuthProvider` (`frontend/context/AuthContext.tsx`) holds `user`/`role`, redirects unauthenticated to `/login`, persists demo role to localStorage; approval actions (`approval_requests` table) enforce requester/approver role separation (`models/__init__.py:448-461`).

## Key Design Decisions

1. **Medallion (bronze→silver→gold) with promotion watermark** — raw fidelity + replayability; unpromoted-rows query makes reruns idempotent (`runner.py:94-124`).
2. **Deterministic scoring, probabilistic assistance** — 4-factor regex/clinical model (`scoring.py`, `haemophilia_v2.0`) is the source of truth; LLMs only write `interpretation`/`speculation`, never scores (truthfulness phases 004/005).
3. **Facts vs interpretation vs speculation split** — separate `signals` columns (`facts JSONB`, `interpretation`, `speculation`) so UI can render evidence and inference distinctly.
4. **Config-as-contract** — `config/haemophilia.yaml` versions the whole domain (`domain_config_version: 1.0.0`); connector queries, routing matrix, confluence thresholds, lifecycle lags all change without code deploys.
5. **Privacy-gated provider fallback** — local-first Gemma keeps PHI/PII on-box; Grok only fires with key + `PUBLIC` classification; BART guarantees the demo never goes dark.
6. **Honest health (D-22)** — connectors report `NEVER_CONNECTED`/`STALE`/`DEGRADED` from real state; no synthetic heartbeats.
7. **Single-flight pipeline + advisory-locked scheduler** — correctness over throughput for a hackathon pilot; scales by adding workers later, not by complicating the graph.

---

*Architecture analysis: 2026-09-19*
