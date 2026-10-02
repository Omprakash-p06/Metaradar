<!-- refreshed: 2026-10-02 -->
# Architecture

**Analysis Date:** 2026-10-02

## System Overview

```text
┌──────────────────────────────────────────────────────────────────────────┐
│            Presentation — Next.js 16 App Router (client-heavy)           │
│  `frontend/app/` · `frontend/components/` · `frontend/context/`           │
│  Login + 13 workspace views + Athena SSE copilot + Evidence Drawer        │
├──────────────────┬──────────────────┬────────────────────────────────────┤
│  Workspaces      │  Auth/Persona    │  API client + contract types       │
│  `components/*`  │ `context/Auth...`│ `lib/api.ts` · `types/api.ts`      │
└────────┬─────────┴────────┬─────────┴──────────────┬─────────────────────┘
         │ fetch (JSON + SSE, credentials: include)
         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                  API Layer — FastAPI (47 route handlers)                  │
│  `backend/app/main.py` → `backend/app/api/v1/endpoints/*`                │
│  deps.py: session auth · RBAC · CSRF · origin check · rate limits        │
├──────────────────┬──────────────────┬────────────────────────────────────┤
│  signals.py      │  intelligence.py │  health / observability            │
│  auth.py         │  registry.py     │  ingestion / pipeline / search     │
└────────┬─────────┴────────┬─────────┴──────────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      Service Layer (pure domain logic)                    │
│  `backend/app/services/` — scoring · pii · dedup · embeddings ·          │
│  confluence · redteam · routing · calibration · authority · scheduler    │
└────────┬───────────────────────────────────────────────┬─────────────────┘
         │                                               │
         ▼                                               ▼
┌────────────────────────────────────┐  ┌───────────────────────────────────┐
│  Ingestion — 8 source connectors   │  │  Intelligence — LangGraph 11 nodes│
│  `backend/app/connectors/`         │  │  `backend/app/workflows/graph.py` │
│  retry/backoff · quota · health    │  │  PipelineRunner persists results  │
└────────┬───────────────────────────┘  └──────────┬────────────────────────┘
         │ bronze only (D-26)                       │
         ▼                                          ▼
┌──────────────────────────────────────────────────────────────────────────┐
│              Persistence — PostgreSQL 16 + pgvector                       │
│  `raw_signals_bronze` → `signals` (384-dim HNSW) → `developments` …      │
│  append-only `audit_log` (trigger + ORM events) · Redis 7 (optional)      │
└──────────────────────────────────────────────────────────────────────────┘
         ▲
         │ infer / embed
┌────────┴──────────────────────────────────────────────────────────────────┐
│  Provider Layer — `backend/app/providers/`                                │
│  Local Gemma (GGUF/Ollama) → Gemini (privacy-gated) → Grok → BART degraded │
└───────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| FastAPI app + lifespan | Middleware ordering, router mounting, startup guard, scheduler boot/shutdown | `backend/app/main.py` |
| Settings + production guard | All env config; refuses insecure production boot | `backend/app/core/config.py` |
| Domain config loader | Loads and validates `config/haemophilia.yaml` | `backend/app/core/domain_config.py` |
| Auth dependencies | Session validation, RBAC, CSRF, origin checks, rate limits | `backend/app/api/deps.py` |
| Crypto primitives | bcrypt hashing, signed cookies, session-bound CSRF HMAC | `backend/app/core/security.py` |
| Signals API | Signal read/review/approval/audit/decision-object/overview/Athena | `backend/app/api/v1/endpoints/signals.py` |
| Intelligence API | Confluence, lifecycles, red-team, missing-signals, calibration, leadership | `backend/app/api/v1/endpoints/intelligence.py` |
| Connector base | Retry/backoff, bronze persistence, incremental state, honest health | `backend/app/connectors/base.py` |
| Connector registry | Instantiates all 8 connectors | `backend/app/connectors/__init__.py` |
| Source scheduler | One asyncio worker per source, advisory locks, backoff, ingestion→pipeline trigger | `backend/app/services/scheduler.py` |
| LangGraph graph | The 11-node pipeline DAG definition | `backend/app/workflows/graph.py` |
| PipelineRunner | DB lifecycle, persistence, promotion of bronze rows | `backend/app/workflows/runner.py` |
| Provider factory | Fallback chain + privacy gate orchestration | `backend/app/providers/factory.py` |
| Privacy scrubber | Regex PII/PHI redaction + payload classification | `backend/app/services/pii.py` |
| Deterministic scorer | 4-factor priority score (0–100) | `backend/app/services/scoring.py` |
| Routing resolver | Function routing + leadership escalation | `backend/app/services/routing.py` |
| Frontend shell | Nav, workspace routing, error boundaries | `frontend/components/metaradar.tsx` |
| Auth context | Session bootstrap, persona/role state | `frontend/context/AuthContext.tsx` |
| API client | Typed fetch wrapper with `ApiError`, SSE reader | `frontend/lib/api.ts`, `frontend/lib/errors.ts` |

## Pattern Overview

**Overall:** Layered, async-first, evidence-grounded pipeline architecture with deterministic fallbacks.

**Key Characteristics:**
- **Strict layering** — endpoints → services → models. Endpoints never embed scoring or dedup math.
- **Async end to end** — httpx, SQLAlchemy async, async connectors, async pipeline. CPU-bound work (embeddings) is offloaded to an executor.
- **Never-crash provider chain** — every AI provider raises a typed error so `ProviderFactory` can fall through; the terminal fallback is a local, network-free summary.
- **Honest telemetry** — connector and scheduler health are read from the DB and degrade to in-memory state rather than fabricating values.
- **Append-only audit** — enforced at both the ORM event level and by a PostgreSQL trigger.
- **Deterministic-by-default scoring** — priority is a transparent formula, not an LLM judgment.
- **Bronze/silver/gold separation** — connectors write `raw_signals_bronze`; only the pipeline promotes to `signals` and `developments`.

## Layers

**Presentation (`frontend/`):**
- Purpose: render role-scoped workspaces and stream copilot answers
- Location: `frontend/app/`, `frontend/components/`, `frontend/context/`
- Contains: App Router pages, client components, auth provider, typed API client
- Depends on: the FastAPI REST + SSE surface only
- Used by: browser clients

**API (`backend/app/api/`):**
- Purpose: HTTP boundary — validation, auth, RBAC, rate limiting, response shaping
- Location: `backend/app/api/v1/endpoints/` (11 modules, 47 route handlers), `backend/app/api/deps.py`
- Contains: route handlers, Pydantic schemas, dependency wiring
- Depends on: services, models, core
- Used by: the frontend and diagnostic clients

**Service (`backend/app/services/`):**
- Purpose: all domain logic, framework-agnostic
- Location: `backend/app/services/` (19 modules)
- Contains: `scoring.py`, `pii.py`, `deduplication.py`, `embeddings.py`, `confluence.py`, `redteam.py`, `routing.py`, `calibration.py`, `authority.py`, `provenance_urls.py`, `vector_query.py`, `scheduler.py`, `auth_service.py`, `ingestion.py`, `relevance.py`, `source_independence.py`, `embeddings_backfill.py`
- Depends on: models, core, providers
- Used by: endpoints, connectors, workflow nodes

**Ingestion (`backend/app/connectors/`):**
- Purpose: fetch, retry, deduplicate, and persist raw source payloads
- Location: `backend/app/connectors/`
- Contains: `base.py` + 8 source adapters
- Depends on: `services/deduplication.py`, `core/redact.py`, models
- Used by: `services/scheduler.py`, `services/ingestion.py`, the ingestion endpoint

**Intelligence (`backend/app/workflows/`):**
- Purpose: transform bronze records into scored, routed, evidence-linked signals
- Location: `backend/app/workflows/`
- Contains: `graph.py`, `state.py`, `runner.py`, `nodes/` (11 nodes)
- Depends on: services, providers, models
- Used by: `services/scheduler.py` (post-ingestion), the pipeline endpoint

**Provider (`backend/app/providers/`):**
- Purpose: uniform LLM interface with capability negotiation and privacy gating
- Location: `backend/app/providers/`
- Contains: `base.py` (abstract + `ProviderCapability` + `DataClassification`), `gemma.py`, `gemini.py`, `grok.py`, `degraded.py`, `factory.py`
- Depends on: `services/pii.py`, `core/config.py`
- Used by: workflow nodes (notably `node_synthesize`)

**Data (`backend/app/models/`, `backend/app/db/`):**
- Purpose: schema, sessions, seeding, advisory locks
- Location: `backend/app/models/__init__.py`, `backend/app/models/auth.py`, `backend/app/db/session.py`, `backend/app/db/seed.py`
- Contains: 22 ORM tables, async session factory, lock helpers, idempotent seeders
- Depends on: `core/config.py`
- Used by: every other backend layer

## Data Flow

### Primary Request Path (authenticated signal read)

1. Browser loads a workspace; `AuthContext` bootstraps via `GET /api/v1/auth/me` (`frontend/context/AuthContext.tsx`)
2. Client calls `fetchSignals()` (`frontend/lib/api.ts`) with `credentials: 'include'`
3. `GET /api/v1/signals` handler resolves auth + RBAC (`backend/app/api/v1/endpoints/signals.py:404`, `backend/app/api/deps.py:get_current_user`)
4. Handler applies role scoping and query filters, reads `signals` via SQLAlchemy async
5. `mapSignal()` normalizes the payload (`frontend/lib/mappers.ts`) → `SignalCard` / `SignalDetailWorkspace`

### Ingestion → Intelligence Pipeline (autonomous)

1. `SourceScheduler` boots in the FastAPI lifespan (`backend/app/main.py`)
2. One asyncio worker per connector, staggered 2–15 s, guarded by a global `Semaphore(4)` (`backend/app/services/scheduler.py`)
3. Worker acquires a distributed advisory lock (`try_advisory_lock`, `backend/app/db/session.py`) — PostgreSQL fallback when Redis is absent
4. `IngestionService.run_connectors()` executes each YAML profile; `SourceConnector._fetch_with_retry()` handles backoff
5. `check_and_persist_bronze()` (`backend/app/services/deduplication.py`) writes to `raw_signals_bronze` with a content hash
6. `_persist_health_log()` records telemetry to `source_health_logs` and updates `sources`
7. **Trigger condition:** only when `new_records_discovered > 0` does the worker run `PipelineRunner.run(batch_size=50)`
8. `PipelineRunner` creates a `pipeline_runs` row, fetches unpromoted bronze rows, and invokes the compiled LangGraph
9. `_persist_state_to_db()` upserts `signals` (fingerprint conflict key), inserts `developments` and `confluences`, and promotes bronze rows — **only those that persisted successfully**

### 11-Node LangGraph Pipeline

Linear, no conditional edges (`backend/app/workflows/graph.py`), state contract in `backend/app/workflows/state.py`:

```text
node_ingest → node_validate → node_embed → node_nlp_extract → node_ontology_enrich
  → node_confluence → node_lifecycle → node_redteam → node_missing_signal
  → node_synthesize → node_calibrate → END
```

- **`node_ingest`** — normalizes incoming raw signals
- **`node_validate`** — produces the canonical `validated_signals` list
- **`node_embed`** — enriches in place via `embedding_service`
- **`node_nlp_extract`** — entities and claims
- **`node_ontology_enrich`** — maps to `config/haemophilia.yaml` assets/modalities
- **`node_confluence`** — 48h multi-source linkage (`services/confluence.py`)
- **`node_lifecycle`** — 7-stage FSM advancement
- **`node_redteam`** — rule A–S contradiction screening (`services/redteam.py`)
- **`node_missing_signal`** — silence/overdue detection over `watch_items`
- **`node_synthesize`** — provider-chain intelligence + four-question brief; produces `model_metadata`
- **`node_calibrate`** — applies calibrated routing/scoring weights

**Reducer semantics (`backend/app/workflows/state.py`):** accumulating channels use `Annotated[List, operator.add]`; `validated_signals` uses a custom `replace_list` reducer because both `validate` and `embed` re-emit the whole list — `operator.add` would duplicate every signal. `calibration_weights` and `node_statuses` use `merge_dicts`.

**State Management:** LangGraph channel reducers only. No global mutable pipeline state. `PipelineRunner` serializes runs with a module-level `asyncio.Lock` (`_pipeline_concurrency_lock`).

### Athena Copilot Streaming

1. Client posts to `/api/v1/athena/stream` (`backend/app/api/v1/endpoints/signals.py:1630`)
2. Backend retrieves grounded evidence, runs the provider chain, emits SSE
3. Frontend reads the stream in `frontend/lib/api.ts`; citations render as `AthenaEvidenceCitation` chips in `frontend/components/intelligence/AthenaWorkspace.tsx`

### Approval Workflow

1. A non-leadership role posts `/api/v1/signals/{id}/request-approval` (`signals.py:792`) → `approval_requests` row (`PENDING`)
2. Leadership lists `/api/v1/signals/pending-approvals` (`signals.py:569`) via `PendingApprovalsPanel.tsx`
3. Leadership resolves `/api/v1/signals/{id}/resolve-approval` (`signals.py:918`) — writes `audit_log` and updates `signals.review_status`

## Key Abstractions

**`SourceConnector` (`backend/app/connectors/base.py`):**
- Purpose: uniform contract for 8 heterogeneous sources
- Examples: `backend/app/connectors/pubmed.py`, `backend/app/connectors/clinical_trials.py`, `backend/app/connectors/ema.py`
- Pattern: Template Method — base owns retry, bronze persistence, state I/O, health logging; subclasses implement `fetch_latest()` and `run_profile()`

**`LLMProvider` + `ProviderCapability` (`backend/app/providers/base.py`):**
- Purpose: capability-negotiated provider abstraction
- Examples: `backend/app/providers/gemma.py`, `gemini.py`, `grok.py`, `degraded.py`
- Pattern: Strategy + Chain of Responsibility; `factory.py:execute_task` walks the chain and catches typed errors

**`DataClassification` (`backend/app/providers/base.py`):**
- Purpose: the privacy vocabulary gating external transmission
- Values: `PUBLIC`, `SYNTHETIC`, `CONFIDENTIAL`, `INTERNAL`, `PATIENT_IDENTIFIABLE`, `UNKNOWN`
- Pattern: allow-list gate — only `PUBLIC`/`SYNTHETIC` may leave the environment

**`MetaRadarState` (`backend/app/workflows/state.py`):**
- Purpose: typed LangGraph channel contract
- Pattern: `TypedDict` + per-channel reducers; `create_initial_state()` is the only constructor

**`PipelineRunner` (`backend/app/workflows/runner.py`):**
- Purpose: DB lifecycle + persistence boundary around the pure graph
- Pattern: Orchestrator — the graph is stateless w.r.t. the DB; the runner owns `pipeline_runs`, upserts, and bronze promotion

**Routing resolution (`backend/app/services/routing.py`):**
- Purpose: explainable function routing (`MEDICAL_AFFAIRS`, `REGULATORY`, `SAFETY`, `MARKET_ACCESS`, `COMMUNICATIONS`, `LEADERSHIP`)
- Pattern: deterministic rule table from `config/haemophilia.yaml:baseline_routing_matrix`, overridable by calibration

## Entry Points

**FastAPI ASGI app:**
- Location: `backend/app/main.py` (`app = FastAPI(...)`)
- Triggers: `uvicorn app.main:app` locally, or `backend/run.py` in production
- Responsibilities: middleware, routers, lifespan seeding + scheduler

**Production backend entrypoint:**
- Location: `backend/run.py`
- Triggers: `startCommand: python run.py` on Render (`render.yaml`)
- Responsibilities: run `alembic upgrade head` in a subprocess, then bind Uvicorn to `0.0.0.0:$PORT` — **always binds even if migrations fail**, so health/diagnostics stay reachable instead of crash-looping

**Local launcher:**
- Location: `start.py`
- Triggers: `python start.py`
- Responsibilities: start Docker backing services, apply migrations, launch backend + frontend

**Next.js frontend:**
- Location: `frontend/app/layout.tsx` → `frontend/app/page.tsx` (redirects to `/login`) → `frontend/app/[section]/page.tsx`
- Responsibilities: route all workspace sections through a single dynamic segment rendering `frontend/components/metaradar.tsx`

**Scheduler:**
- Location: `backend/app/services/scheduler.py` (`SourceScheduler.get_instance()`)
- Triggers: `lifespan` startup
- Responsibilities: per-source worker loops, advisory locks, backoff, pipeline triggering

## Architectural Constraints

- **Threading / concurrency:** single asyncio event loop. `asyncio.Semaphore(4)` caps concurrent connectors; `asyncio.Lock` serializes pipeline runs. `EmbeddingService` offloads CPU ONNX inference to the default executor. `GemmaProvider` uses a `queue.Queue` + `threading` bridge when running GGUF in-process.
- **Global state:** `backend/app/core/config.py` (`settings` singleton), `backend/app/providers/factory.py` (`provider_factory` singleton), `backend/app/services/embeddings.py` (module-level `_model`), `backend/app/workflows/runner.py` (`_pipeline_concurrency_lock`), `backend/app/services/scheduler.py` (`SourceScheduler._instance` + `_global_connector_semaphore`), `backend/app/api/deps.py` (`_rate_buckets`, `_auth_rate_buckets`).
- **In-memory rate limiting:** the sliding-window buckets in `deps.py` are per-process, so they do **not** limit across multiple Render instances.
- **Compatibility shims:** `backend/app/workflows/state.py:IntelligenceState = MetaRadarState`; `security.py:hash_session_token = hash_token`; several legacy `ScoreBreakdown` fields in `frontend/types/api.ts`.
- **Contract is hand-maintained:** `frontend/types/api.ts` is a template inside `scripts/export_openapi.py` and is re-emitted verbatim; CI fails if the checked-in file drifts from the template.
- **No conditional graph edges:** the pipeline is strictly linear; there is no retry or branch node.

## Anti-Patterns

### Broad `except Exception` with `logger.warning`

**What happens:** Persistence and state I/O paths swallow all exceptions and continue — e.g. `runner.py` wraps development/signal/confluence upserts in `try/except Exception` that only logs, and `_persist_health_log()` in `connectors/base.py` does the same.
**Why it's wrong:** A schema or constraint regression can silently stop persisting signals while the pipeline still reports `completed` with a non-zero `signals_created`, hiding real data loss.
**Do this instead:** Catch narrow, expected exceptions (`IntegrityError`, `SQLAlchemyError`) and re-raise or record into `state["errors"]` so `pipeline_runs.errors_count` reflects reality — the runner already has an `errors` channel for this.

### Duplicated temporal imports inside functions

**What happens:** `import urllib.parse` inside the `DATABASE_URL` validator (`backend/app/core/config.py`), `from app.models import SourceHealthLog, Source` and `from sqlalchemy import update` inside `_persist_health_log()` (`backend/app/connectors/base.py`), and `from app.db.session import ...` inside `main.py:lifespan`.
**Why it's wrong:** Hides dependency cycles instead of resolving them and makes import-time failures surface late, at request time.
**Do this instead:** Hoist to module scope; the auth imports in `main.py` are already deferred legitimately for seeding, so keep that one and fix the others.

### Silent `pass` in exception handlers

**What happens:** `backend/app/services/scheduler.py` wraps the `next_scheduled_run` DB update in `except Exception: pass`.
**Why it's wrong:** Scheduler telemetry silently goes stale, and the `/api/v1/scheduler` endpoint will report scheduling data that no longer matches reality — a direct violation of the honest-telemetry rule.
**Do this instead:** Log at `warning` with `logger.warning("...", exc_info=True)` and leave the last known value untouched.

### Duplicated PII label vocabularies

**What happens:** `backend/app/services/pii.py:classify_payload()` returns `DataClassification.CONFIDENTIAL`, while `backend/app/api/v1/endpoints/signals.py:1654` uses the string `PATIENT_IDENTIFIABLE` for the same situation.
**Why it's wrong:** The privacy gate blocks both today, but a future allow-list edit that whitelists one label would silently open the other.
**Do this instead:** Converge on a single blocked label and reference the `DataClassification` enum everywhere instead of raw strings.

### Star component with mixed concerns

**What happens:** `frontend/components/metaradar.tsx` is 2,612 lines and owns navigation, workspace routing, global search, ingestion controls, theme toggling, and layout — while also being the one file exempted from the banned-class style gate (`scripts/check-banned-classes.mjs` skips `metaradar.tsx`).
**Why it's wrong:** The exemption means this file is the only place where raw `slate-*` and arbitrary hex colors may accumulate unchecked, and any change risks the whole shell.
**Do this instead:** Extract the shell into focused components under `frontend/components/shell/` and remove the exemption so the gate can enforce tokens there too.

## Error Handling

**Strategy:** Typed errors at boundaries; graceful degradation for optional infrastructure; fail-fast for security misconfiguration.

**Patterns:**
- **Security fail-fast:** `validate_production_settings()` raises `RuntimeError` on default `SECRET_KEY`, `DEMO_MODE` in production, or wildcard CORS (`backend/app/core/config.py`)
- **Provider degradation:** providers raise typed errors (`GeminiUnavailableError`, `OllamaUnavailableError`, `PermissionError`) that `ProviderFactory` catches to fall through (`backend/app/providers/factory.py`)
- **Connector isolation:** `ConnectorFetchError` after bounded retries; failures are recorded as `FAILED`/`DEGRADED`/`RATE_LIMITED` rather than propagating into the scheduler loop (`backend/app/connectors/base.py`)
- **Endpoint errors:** `HTTPException` with explicit status codes — 401 (no/expired session), 403 (RBAC, CSRF, origin), 429 (rate limit)
- **Audit immutability:** `PermissionError` raised by ORM events and by the DB trigger (`backend/app/models/__init__.py`)

## Cross-Cutting Concerns

**Logging:** `structlog` JSON (`backend/app/core/logging.py`), correlation IDs via `CorrelationIdMiddleware`, secret redaction via `backend/app/core/redact.py`.

**Validation:** Pydantic v2 for all request/response contracts (`backend/app/schemas/`), `pydantic-settings` for config, and `config/haemophilia.yaml` validated into typed objects by `backend/app/core/domain_config.py`.

**Authentication:** Session cookies (`metaradar_session`) signed with `itsdangerous`, verified against the `sessions` table with absolute + idle timeouts; CSRF via session-bound HMAC; RBAC via `require_role` (`backend/app/api/deps.py`).

**Privacy:** `PIIPHIScrubber` regex redaction (8 patterns) plus `DataClassification` allow-list gating at every external provider boundary.

---

*Architecture analysis: 2026-10-02*
