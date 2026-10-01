# Coding Conventions

**Analysis Date:** 2026-10-01

## Naming Patterns

**Files:**
- Backend Python: `snake_case.py` — e.g. `backend/app/services/deduplication.py`, `backend/app/services/pii.py`, `backend/app/providers/factory.py`
- Backend tests: `test_*.py` (enforced by `pytest.ini:python_files = test_*.py`) — e.g. `tests/test_foundation.py`, `tests/test_contract_drift.py`, `tests/test_rbac.py`
- Test classes/functions: `Test*` / `test_*` (enforced by `pytest.ini:python_classes`, `python_functions`)
- Frontend components: `kebab-case` dirs + `PascalCase.tsx` files — e.g. `frontend/components/signals/`, `frontend/components/confluence/`, `frontend/components/auth/`
- Frontend routes (App Router): lowercase dirs under `frontend/app/` — `frontend/app/`, `frontend/app/login/`
- Canonical contract: `frontend/types/api.ts` (generated template) + `contracts/openapi.json`
- Scripts: `snake_case.py` for Python (`scripts/export_openapi.py`, `scripts/test_e2e_vertical_slice.py`), `kebab-case.mjs` for Node (`scripts/check-banned-classes.mjs`)

**Functions:**
- Python: `snake_case` verbs — `generate_fingerprint()`, `chunk_text_for_embedding()` (`backend/app/services/deduplication.py`), `PIIPHIScrubber.scrub()`, `PIIPHIScrubber.classify_payload()` (`backend/app/services/pii.py`), `export_contracts()` (`scripts/export_openapi.py`)
- TypeScript/React: `camelCase` for functions/handlers, `PascalCase` for components/interfaces — `Signal`, `ModelMetadata`, `ConfluenceAlertItem` in `frontend/types/api.ts`

**Variables:**
- Python: `snake_case` locals; `UPPER_SNAKE` for module constants — `PATTERNS`, `COMPILED_PATTERNS`, `PUBLIC_SOURCES` in `backend/app/services/pii.py`
- TypeScript interfaces: `PascalCase` types, `camelCase` fields + `snake_case` passthrough for backend parity (e.g. `signal_id`, `canonical_url` alongside `detectedAt`) in `frontend/types/api.ts`
- Env vars: `UPPER_SNAKE` — `DATABASE_URL`, `REDIS_URL`, `LLM_PROVIDER`, `METARADAR_API_URL`, `METARADAR_ORIGIN`

**Types:**
- Backend: Pydantic v2 models in `backend/app/schemas/`; SQLAlchemy 2.0 models in `backend/app/models/`; enums `DataClassification`, `ProviderCapability` in `backend/app/providers/base.py`
- Frontend: hand-maintained `export interface` / `export type` in `frontend/types/api.ts` (NOT codegen — see TESTING.md contract-sync caveat)

## Code Style

**Formatting:**
- No Prettier/Black/Ruff config detected — style is enforced via ESLint (frontend) + review, not auto-formatter
- Python: 4-space indent, double quotes, type hints on public functions (`-> Tuple[str, bool, Dict[str, int]]`), docstrings on service methods — follow `backend/app/services/pii.py` as exemplar
- TypeScript: 2-space indent, single quotes in config (`frontend/eslint.config.mjs`), semicolons omitted in `frontend/next.config.mjs` style; path alias `@/*` maps to `frontend/*` (`frontend/tsconfig.json:paths`)

**Linting:**
- Frontend: ESLint flat config with `@next/eslint-plugin-next` `recommended` + `core-web-vitals` rules — see `frontend/eslint.config.mjs`
- Ignores: `.next/`, `node_modules/`, `out/`, `build/`, `src/` (note: legacy `src/` ignore; active tree is `frontend/app/`, `frontend/components/`, `frontend/types/`)
- Backend: no flake8/ruff/mypy config detected — lint = import hygiene + pytest green

**TypeScript Strictness (`frontend/tsconfig.json`):**
- `strict: true`, `noEmit: true`, `target: ES6`, `moduleResolution: bundler`, `isolatedModules: true`, `jsx: react-jsx`, `skipLibCheck: true`
- `include`: `**/*.ts`, `**/*.tsx`, `next-env.d.ts` — gate command is `pnpm exec tsc --noEmit` (0 errors required)
- Do NOT weaken: no `strict: false`, no `skipLibCheck` abuse beyond existing setting

## Import Organization

**Order (observed, enforce in new code):**
1. Stdlib (`json`, `os`, `sys`, `re`, `pathlib`, `datetime`)
2. Third-party (`fastapi`, `httpx`, `sqlalchemy`, `pytest`, `next/*`, `react`)
3. First-party `app.*` / `@/*` — backend inserts `sys.path` for `backend` dir explicitly at top of every test/script:
   ```python
   base_dir = Path(__file__).resolve().parents[1]
   sys.path.insert(0, str(base_dir / "backend"))
   ```
   Seen in `tests/conftest.py`, `tests/test_foundation.py`, `tests/test_contract_drift.py`, `scripts/export_openapi.py`, `scripts/test_e2e_vertical_slice.py`

**Path Aliases:**
- Frontend: `@/*` → `frontend/*` (`frontend/tsconfig.json`)
- Backend: absolute `app.*` imports from `backend/` root (requires `PYTHONPATH=backend:.` — see CI `ci.yml` env)

## Branching & Commits (mandatory per `AGENTS.md` + `docs/rules/DEVELOPMENT_WORKFLOW.md`)

**Branches — never push to `main`:**
- `feature/*` — new functional feature (e.g. `feature/phase-13-reach-poster-and-concerns`)
- `fix/*` — bug resolution (e.g. `fix/concerns-md-audit-fixes`)
- `refactor/*` — optimization without structural change
- `security/*` — security patches / scrubber rules
- `docs/*` — architectural documentation updates
- Lifecycle: `PLAN → BRANCH → IMPLEMENT → TEST → VERIFY → DOCUMENT → COMMIT → PR → CI → MERGE`

**Commit message style (enforced by history — follow it):**
- Conventional prefix: `feat(phase-N): …`, `fix(scope): …`, `docs(scope): …` — e.g. `4280ba9 fix(phase-13): remediate all 14 code review findings…`, `37b8f4f feat(phase-13): REACH 2026 scientific poster suite…`
- Atomic commits, one concern per commit; PR required with `.github/pull_request_template.md` checklist

## Banned Patterns (CI-blocking or AGENTS.md-forbidden)

**Frontend CSS gate — `scripts/check-banned-classes.mjs` (runs as `pnpm run check:banned-classes`):**
- Banned in `frontend/components/**/*.tsx` (except `metaradar.tsx` which is exempt): `bg-slate-*`, `text-slate-*`, `border-slate-*` and `dark:` variants; arbitrary hex `bg-[#…]`, `text-[#…]`, `border-[#…]` and `dark:` variants
- Use design-system tokens instead; gate prints `BANNED-CLASS-GATE` violations with `file:line` and exits 1

**Global suppressions — NEVER use (per `AGENTS.md` Core Rules 4–5):**
- `// @ts-ignore`, `ignoreBuildErrors` in `next.config.mjs`, silent `try...except: pass` to hide failures
- Never fabricate test output, health status, or mock/synthetic data without explicit `is_synthetic` / `DataMode="synthetic"` labeling (`frontend/types/api.ts:DataMode`)
- Never commit secrets: `.env`, `*_credentials.json`, `*.pem/*.key`, tokens — existence only, never content (see `SECURITY_STANDARDS.md`)

**Backend hygiene:**
- No bare `except:` swallowing domain errors; the only tolerated `except Exception: pass` is test-cleanup isolation in `tests/conftest.py:cleanup_db_connections`
- UTC everywhere: `datetime.now(timezone.utc)` — see `tests/test_foundation.py:31`, `scripts/test_e2e_vertical_slice.py:43`
- PII boundary: scrub via `PIIPHIScrubber.scrub()` before persistence/external transmission; gate classification via `validate_privacy_gate` (`docs/rules/SECURITY_STANDARDS.md`)

## Error Handling

- Backend: raise HTTP exceptions with explicit status codes; terminal FSM states return `409` on illegal re-mutation (verified in `scripts/test_e2e_vertical_slice.py:296-298`)
- Frontend: `async/await` with typed responses from `frontend/types/api.ts`; surface `provenance_status` / `confidence_type` honestly in UI
- Fallback chain only: Local Gemma → Grok (privacy-gated) → Degraded BART factual mode — never crash hard (`tests/test_foundation.py:test_provider_execution_and_degraded_bart_fallback`)

## Logging

**Framework:** `structlog` (backend, see `backend/requirements.txt`) + `asgi-correlation-id` for request IDs
**Patterns:** structured events with `pipeline_run_id`, `request_id`, `duration_ms` — see `frontend/types/api.ts:ActivityLogItem`

## Comments & Docs

- Python: docstrings on services/providers; honesty notes where behavior is surprising — exemplar is the contract caveat docstring in `scripts/export_openapi.py:14-23`
- TypeScript: file-header comment on canonical contract explaining manual-sync process (`frontend/types/api.ts` header emitted by `scripts/export_openapi.py:39-43`)
- Skip comment lines starting `//`, `/*`, `*` are ignored by the banned-class scanner — keep them meaningful, not decorative

## Function & Module Design

**Size:** single-responsibility services — one file per domain (`auth_service.py`, `calibration.py`, `confluence.py`, `deduplication.py`, `pii.py`, `redteam.py`, `routing.py`, `scheduler.py`, `scoring.py` in `backend/app/services/`)
**Parameters:** keyword-friendly defaults (`batch_size`, `calibration_weights` in `PipelineRunRequest`); Pydantic validation at API boundary
**Return values:** tuples `(redacted, has_pii, counts)` for scrub; dicts with `model_metadata` for providers; typed Pydantic responses at endpoints
**Exports:** explicit `export interface` / `export type` in TS; plain module-level functions/classes in Python — no barrel-file re-export pattern detected, import from owning module directly

## Definition of Done Reference

Every change must satisfy `docs/rules/DEFINITION_OF_DONE.md` before DONE: requirements aligned, implementation clean, `tsc` 0 errors, `eslint` 0 errors, `next build` clean, pytest clean, contract sync done, PII/privacy verified, `docker compose config` clean, CI green, docs updated, feature branch + atomic commit + PR. If any gate cannot be verified → status is **BLOCKED**.

---

*Convention analysis: 2026-10-01*
