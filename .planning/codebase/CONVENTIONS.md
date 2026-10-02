# Coding Conventions

**Analysis Date:** 2026-10-02

## Naming Patterns

**Files:**
- Backend Python: `snake_case.py` — `backend/app/services/deduplication.py`, `backend/app/services/provenance_urls.py`, `backend/app/core/domain_config.py`
- Backend tests: `test_*.py` (enforced by `pytest.ini:python_files = test_*.py`) — `tests/test_foundation.py`, `tests/test_contract_drift.py`, `tests/test_rbac.py`
- Alembic migrations: `NNN_snake_case_description.py` — `backend/alembic/versions/013_auth_user_role_session.py`, `.../015_approval_requests.py`
- Frontend component dirs: `kebab-case/` — `frontend/components/missing-signals/`, `frontend/components/star-portal/`
- Frontend components: `PascalCase.tsx` — `frontend/components/signals/SignalDetailWorkspace.tsx`
- Frontend modules: `camelCase.ts` — `frontend/lib/api.ts`, `frontend/lib/mappers.ts`, `frontend/lib/errors.ts`
- Scripts: `snake_case.py` for Python (`scripts/export_openapi.py`), `kebab-case.mjs` for Node (`scripts/check-banned-classes.mjs`)

**Functions / methods:**
- Python: `snake_case` — `resolve_canonical_provenance()`, `check_and_persist_bronze()`, `validate_production_settings()`
- Private helpers: leading underscore — `SourceConnector._persist_bronze()`, `PipelineRunner._persist_state_to_db()`, `deps.py:_rate_buckets`
- Async coroutines: no suffix; `async def` is the signal — `async def run_profile(...)`
- React components: `PascalCase` — `SignalDetailWorkspace`, `EvidenceDrawer`, `ApprovalRequestModal`
- React hooks: `use` prefix, defined in `frontend/lib/hooks.ts` or component scope — `useTheme`, `useAuth`
- Frontend API functions: `camelCase` verb-first — `fetchSignals`, `fetchSignal`, `fetchConfluenceAlerts`, `getHealthReady`
- Test functions: `test_snake_case` (enforced by `pytest.ini:python_functions = test_*`) — `test_gemini_capabilities_exclude_actions`

**Variables:**
- Python: `snake_case`; DB/schema constants and enum-like values are `SCREAMING_SNAKE_CASE` or plain uppercase strings — `DataClassification.PUBLIC`, `"CONFIGURATION_ERROR"`, `"PENDING"`
- Frontend: `camelCase`; module-level constants `SCREAMING_SNAKE_CASE` — `GEMINI_API_BASE` (Python), `BANNED_PATTERNS` (JS)
- Booleans read as assertions: `has_gemini_key`, `is_production`, `is_synthetic`, `has_pii`, `new_records_discovered`, `failed_signal_ids`

**Types:**
- Python: `PascalCase` for classes/Pydantic models — `RawSignalPayload`, `ProfileRunResult`, `ConnectorStatus`, `MetaRadarState`
- `TypedDict` for graph state; `BaseModel` for I/O contracts
- Enums subclass `str, Enum` so values serialize as plain strings — `ProviderCapability(str, Enum)`, `DataClassification(str, Enum)`
- TypeScript: `PascalCase` interfaces/types — `Signal`, `ScoreBreakdown`, `ModelMetadata`, `ApprovalRequest`
- Union string literals for closed vocabularies — `export type DataMode = "live" | "recorded_demo" | ...`

## Code Style

**Formatting:**
- **Python:** no formatter is configured — no `black`, `ruff`, `isort`, or `pre-commit`. Style is maintained by hand-consistency.
- **TypeScript/JS:** no Prettier or Biome config detected. Formatting is Next.js/ESLint-driven only.
- Observed Python style: 4-space indent, double quotes for strings, docstrings on every module and public class, `f"..."` for interpolation, no trailing whitespace, no enforced line limit (some lines exceed 120 chars, e.g. in `backend/app/workflows/runner.py`).

**Linting:**
- **Frontend:** `frontend/eslint.config.mjs` (flat config) using only `@next/eslint-plugin-next` with `recommended` + `core-web-vitals` rules. Ignores `.next/`, `node_modules/`, `out/`, `build/`, `src/`.
- **Backend:** no linter (no `flake8`, `pylint`, `ruff`, `mypy`).
- **Custom style gate:** `scripts/check-banned-classes.mjs`, invoked as `pnpm run check:banned-classes` and enforced in CI. It rejects, across `frontend/components/**/*.tsx`:
  - `bg-slate-\d+`, `text-slate-\d+`, `border-slate-\d+` and their `dark:` variants
  - Arbitrary hex colors: `bg-[#...]`, `text-[#...]`, `border-[#...]` and their `dark:` variants
  - Comment lines are skipped; **`metaradar.tsx` is explicitly exempted** by filename check.
  - **Use design tokens instead** — the intent is that all color comes from CSS variables/token utilities.

**Type checking:**
- `frontend/tsconfig.json`: `strict: true`, `noEmit: true`, `isolatedModules: true`, `moduleResolution: "bundler"`, `target: ES6`, `jsx: "react-jsx"`, path alias `@/* → ./*`
- CI runs `pnpm exec tsc --noEmit` as a hard gate
- Backend has no static type checker; Pydantic v2 validates at runtime

## Import Organization

**Python order:**
1. Standard library — `asyncio`, `json`, `logging`, `uuid`, `datetime`, `pathlib`, `typing`
2. Third-party — `httpx`, `sqlalchemy`, `pydantic`, `pytest`, `structlog`, `bcrypt`, `langgraph`
3. First-party `app.*` — `from app.core.config import settings`, `from app.models import Signal`

Separated by blank lines. First-party imports are always absolute (`app.services.…`), never relative. `sys.path` bootstrapping in tests uses `base_dir = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(base_dir / "backend"))` before `app.*` imports (mirrors `pytest.ini:pythonpath = backend .`).

**TypeScript order:**
1. `import type { ... } from '@/types/api'` — types first
2. Relative module imports — `./errors`, `./mappers`
3. Package imports as needed

**Path aliases:**
- `@/*` maps to the `frontend/` root (`frontend/tsconfig.json`)
- Always used for cross-directory imports — `@/components/ui/SpecularButton`, `@/context/AuthContext`, `@/types/api`
- Relative imports (`./`, `../`) reserved for siblings in the same directory

**Note:** `'use client'` is the first line of every interactive component (e.g. `frontend/components/metaradar.tsx`).

## Error Handling

**Patterns:**
- **Typed domain exceptions** at layer boundaries:
  - `ConnectorFetchError` (`backend/app/connectors/base.py`) — raised only after bounded retries are exhausted
  - `GeminiUnavailableError` (`backend/app/providers/gemini.py`) — signals "fall through the chain"
  - `OllamaUnavailableError` (`backend/app/providers/gemma.py`), aliased as `LocalLLMUnavailableError`
  - `EmbeddingError` (`backend/app/services/embeddings.py`) — explicitly never returns a silent zero-vector
- **Provider chain contract:** providers raise typed errors; `ProviderFactory.execute_task()` catches `Exception`, logs `logger.warning(...)`, and tries the next provider (`backend/app/providers/factory.py`)
- **`PermissionError` is the privacy violation signal** — raised by `validate_privacy_gate()` failures and by the audit-immutability ORM events
- **HTTP errors via `HTTPException`** with explicit codes: 401 unauth/expired session, 403 RBAC/CSRF/origin, 429 rate limit (`backend/app/api/deps.py`)
- **Never-crash scheduler:** `_connector_worker_loop` catches `asyncio.CancelledError` (re-raises to break) and generic `Exception` (logs, increments `consecutive_failures`, backs off) so one bad source cannot kill the loop
- **Startup guard:** `validate_production_settings()` raises `RuntimeError` for insecure production config — this is the one place failing hard is intentional
- **`try/except Exception` with a logged warning** is common in DB-persistence paths (see CONCERNS.md for the risk this carries)
- **Frontend:** `ApiError` class in `frontend/lib/errors.ts`; components render `frontend/components/common/ErrorState.tsx` on failure and `EmptyState.tsx` on no data

## Logging

**Framework:**
- Backend: `structlog` (JSON rendering configured once in `backend/app/core/logging.py:configure_structlog(json_logs=True)`)
- Module loggers: `logger = structlog.get_logger("metaradar.main")` for the app, `logger = logging.getLogger(__name__)` in most modules, and `get_logger("gemini_provider")` from `app.core.logging` in newer providers
- Frontend: `console` only; no logging library

**Patterns:**
- **Structured key-value over interpolation:** `logger.info("domain_config_loaded", disease_area=..., version=...)` — pass fields as kwargs, not f-strings, so JSON output stays queryable
- **Event-name-first messages** in newer code: `"service_startup"`, `"service_shutdown"`, `"domain_config_load_failed"`
- **`exc_info=True`** on genuine failures: `logger.error(..., exc_info=True)` in `backend/app/services/scheduler.py`
- **Bracketed console-style tags in deploy/runtime paths:** `[METARADAR DEPLOY]`, `[PIPELINE]` (`backend/run.py`, `backend/app/workflows/runner.py`)
- **Beyond-debug detail uses `logger.debug`** — e.g. `logger.debug("Startup auto-seed skipped/failed: %s", e)` in `backend/app/main.py`
- **Never log secrets:** use `redact_text()` / `redact_mapping()` from `backend/app/core/redact.py` before persisting or emitting error detail (see `SourceConnector._fetch_with_retry`)

## Comments

**When to comment:**
- Module docstrings are mandatory on backend modules and state the contract — e.g. `backend/app/providers/degraded.py`, `backend/app/services/embeddings.py`
- Non-obvious *why* decisions carry a short rationale, often with a spec/decision ID in parentheses: `(D-22)`, `(D-26)`, `(REQ-P15-07)`, `(OWASP Login CSRF defense)`, `(IN-02, WR-03)`
- Reducer semantics are documented inline — `backend/app/workflows/state.py:replace_list` explains at length why `operator.add` would duplicate signals
- Inline "NOTE:" for deliberate omissions — `backend/app/providers/gemini.py` marks the `GENERATE_ACTIONS` exclusion

**TSDoc/JSDoc:**
- Not used. Frontend files rely on TypeScript types and descriptive names; comments appear as short `//` notes.
- `frontend/types/api.ts` opens with a multi-line contract note explaining that the file is a hand-maintained template re-emitted by `scripts/export_openapi.py`.

## Function Design

**Size:**
- Service/domain functions are short and single-purpose (`backend/app/services/scoring.py`, `routing.py`)
- Endpoint handlers run long where logic is inherently sequential — `backend/app/api/v1/endpoints/signals.py` at 1,826 lines and `.../intelligence.py` at 674 lines are the outliers
- `PipelineRunner._persist_state_to_db()` is a single large method handling all persistence phases

**Parameters:**
- Keyword arguments with defaults for optional behaviour — `async def run(self, batch_size: int = 50, pipeline_run_id: Optional[str] = None, ...)`
- Optional params typed `Optional[T] = None`, never bare `= None` without a type
- Settings-like objects are read from the module-level `settings`, not threaded through signatures

**Return Values:**
- Pydantic models for I/O boundaries (`RawSignalPayload`, `ConnectorStatus`, `ProfileRunResult`)
- Plain `Dict[str, Any]` for internal pipeline payloads
- `List[Dict[str, Any]]` for graph state channels
- Tuple returns for multi-value results, documented in the docstring — `PIIPHIScrubber.scrub()` returns `(redacted_text, is_scrubbed, match_counts)`
- `run_profile()` returns a `ProfileRunResult` and never raises for expected upstream failure — status is data

## Module Design

**Exports:**
- Backend: no `__all__` except in registries — `backend/app/connectors/__init__.py` defines `__all__` alongside `ALL_CONNECTORS`
- Python modules export plain top-level functions and classes; simple "pure function" modules like `backend/app/services/scoring.py` expose a module-level singleton (`priority_scorer`) alongside the class
- Frontend: barrel files are **not** used. Components are imported by full path — `@/components/signals/SignalCard`

**Singletons:**
- Module-level instance created and exported at import time: `settings = Settings()`, `provider_factory = ProviderFactory()`, `embedding_service = EmbeddingService()` (backend), `app = FastAPI(...)`
- Class-level singletons where construction is expensive: `SourceScheduler.get_instance()` (`backend/app/services/scheduler.py`)

**Barrel Files:**
- Not used anywhere in the frontend.
- Backend package `__init__.py` files exist but re-export sparingly — `backend/app/connectors/__init__.py` (registry) and `backend/app/workflows/nodes/__init__.py` (node callables) are the meaningful ones.

**Registry pattern:**
- Connectors: `ALL_CONNECTORS` list in `backend/app/connectors/__init__.py`
- Red-team rules: `REDTEAM_RULES` dict in `backend/app/services/redteam.py`
- Routers: explicit `app.include_router(...)` calls in `backend/app/main.py`
- Domain rules/tables: data-driven via `config/haemophilia.yaml` — **prefer extending the YAML over adding Python branches**

---

*Convention analysis: 2026-10-02*
