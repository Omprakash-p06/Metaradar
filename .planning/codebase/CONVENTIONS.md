# Coding Conventions

**Analysis Date:** 2026-09-19

## Naming Patterns

**Files:**
- Backend Python: `snake_case.py` — `backend/app/core/logging.py`, `backend/app/api/v1/endpoints/signals.py`, `backend/app/schemas/auth.py`, `backend/app/services/ingestion.py`
- Backend packages: `snake_case` dirs — `backend/app/core/`, `backend/app/schemas/`, `backend/app/models/`, `backend/app/providers/`, `backend/app/services/`, `backend/app/api/v1/endpoints/`
- Backend tests: `test_*.py` (enforced by `pytest.ini: python_files = test_*.py`) — `tests/test_auth.py`, `tests/test_signals_endpoints.py`, `tests/test_foundation.py`
- Frontend components: `PascalCase.tsx` — `frontend/components/auth/ProfileCard.tsx`, `frontend/components/common/EvidenceDrawer.tsx`, `frontend/components/signals/SignalCard.tsx`
- Frontend component folders: `kebab-case` — `frontend/components/common/`, `frontend/components/signals/`, `frontend/components/ui/`, `frontend/components/auth/`
- Frontend utilities/types: `camelCase.ts` — `frontend/types/api.ts`; co-located CSS: `ProfileCard.css` next to `ProfileCard.tsx`
- Scripts: `snake_case.py` for Python (`scripts/export_openapi.py`, `scripts/test_e2e_vertical_slice.py`), `kebab-case.mjs` for Node (`scripts/check-banned-classes.mjs`)

**Functions:**
- Python: `snake_case` verbs — `configure_structlog()` in `backend/app/core/logging.py:22`, `export_contracts()` in `scripts/export_openapi.py:13`, `generate_fingerprint()` in `backend/app/services/deduplication.py`, `utc_now()` in `backend/app/models/__init__.py:16`
- TypeScript/React: `camelCase` handlers — `handleFeedback` in `frontend/components/common/EvidenceDrawer.tsx:40`, `handleContactClick` in `frontend/components/auth/ProfileCard.tsx:334`; hooks `useState`, `useMemo`, `useCallback`, `useRef`, `useEffect`
- Test functions: `test_<subject>` matching `pytest.ini: python_functions = test_*` — `test_contract_sync_drift` in `tests/test_contract_drift.py:11`, `test_domain_config_loader` in `tests/test_foundation.py:20`

**Variables:**
- Python locals: `snake_case` — `openapi_schema`, `contracts_dir`, `json_path` in `scripts/export_openapi.py:24-30`
- TypeScript locals/props: `camelCase` — `selectedFunction`, `feedbackSuccess`, `isOpen`, `onClose` in `frontend/components/common/EvidenceDrawer.tsx:23-36`
- CSS custom properties: `--kebab-case` design tokens — `--surface`, `--surface-secondary`, `--foreground`, `--muted-foreground`, `--border`, `--primary`, `--success`, `--danger` in `frontend/app/globals.css:30-65`
- Env vars: `UPPER_SNAKE_CASE` — `DATABASE_URL`, `REDIS_URL`, `LLM_PROVIDER`, `METARADAR_API_URL`, `METARADAR_ORIGIN` (see `.github/workflows/ci.yml:57-73`, `scripts/test_e2e_vertical_slice.py:36-37`)

**Types:**
- Pydantic v2 schemas: `PascalCase` + `Schema`/`Request`/`Response` suffix — `SignalReviewRequest`, `SignalSchema`, `HealthResponse`, `ModelMetadataSchema`, `FactInterpretationSpeculationSchema` in `backend/app/schemas/__init__.py`; `LoginRequest`, `DemoLoginRequest`, `UserMe` in `backend/app/schemas/auth.py`; `ConfluenceAlertItem`, `ContradictionItem` in `backend/app/schemas/intelligence.py`
- SQLAlchemy models: `PascalCase` singular — `PipelineRun`, `Source`, `SourceHealthLog`, `Company`, `Asset`, `ClinicalTrial`, `Signal`, `User`, `Session` in `backend/app/models/__init__.py`, `backend/app/models/auth.py`
- TypeScript: `PascalCase` interfaces/types — `Signal`, `DataMode`, `ConfidenceType`, `ScoreBreakdown`, `SignalReviewPayload`, `EvidenceDrawerProps`, `ProfileCardProps` in `frontend/types/api.ts`, `frontend/components/common/EvidenceDrawer.tsx:9`, `frontend/components/auth/ProfileCard.tsx:7`
- Test classes: `Test*` prefix per `pytest.ini: python_classes = Test*`

## Code Style

**Formatting:**
- No Prettier config in repo — formatting is enforced implicitly via `eslint .` + `tsc --noEmit` + `next build` gates (see `frontend/package.json:11-15`, `.github/workflows/ci.yml:95-102`)
- Python: 4-space indent, double quotes, ~120-col soft limit (observed in `backend/app/core/logging.py`, `scripts/export_openapi.py`); type annotations on all public functions
- TSX: single quotes, semicolons omitted inconsistently — match surrounding file; 2-space indent

**Linting:**
- Frontend: ESLint flat config in `frontend/eslint.config.mjs` — `@next/eslint-plugin-next` recommended + `core-web-vitals` rules only; ignores `.next/`, `node_modules/`, `out/`, `build/`, `src/`. Run: `pnpm lint` (=`eslint .`) from `frontend/`
- Backend: no flake8/ruff config — linting is type + test discipline (Pydantic v2 validation, pytest suite). Do NOT add a new linter without a phase plan
- Custom CSS gate: `scripts/check-banned-classes.mjs` bans `bg-slate-*`, `text-slate-*`, `border-slate-*`, `dark:*slate-*`, and arbitrary hex `bg-[#...]`/`text-[#...]`/`border-[#...]` in `frontend/components/**/*.tsx` (except `metaradar.tsx`); comment lines skipped. Run: `pnpm run check:banned-classes` from `frontend/`

**Strictness:**
- TypeScript strict mode ON in `frontend/tsconfig.json:7` (`"strict": true`, `"noEmit": true`, `"jsx": "react-jsx"`, path alias `"@/*": ["./*"]`). Zero-error `pnpm exec tsc --noEmit` is a DoD gate — never use `@ts-ignore`/`@ts-expect-error` to suppress (banned by `AGENTS.md` rule 5)
- Pydantic v2 throughout backend: `BaseModel` + `Field(...)` with descriptions, `ConfigDict(from_attributes=True)` for ORM-mapped responses (e.g. `backend/app/schemas/auth.py:4-17`), `Field(default_factory=...)` for mutable defaults, `field_validator` for coercion (see `backend/app/schemas/__init__.py:5`)
- SQLAlchemy 2.0 classic-Column style (not `Mapped[]`): `Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`, `Column(DateTime(timezone=True), default=utc_now)` — see `backend/app/models/__init__.py:1-33`. All datetimes timezone-aware via `utc_now()` helper

## Import Organization

**Order:**
1. Stdlib (`asyncio`, `os`, `sys`, `pathlib`, `datetime`, `uuid`, `time`)
2. Third-party (`fastapi`, `structlog`, `sqlalchemy`, `pydantic`, `httpx`, `react`, `lucide-react`)
3. First-party `app.*` / `@/*` (`from app.core.logging import get_logger`, `import type { Signal } from '@/types/api'`, `from '@/components/metaradar'`)
4. Relative / local (`./ProfileCard.css`)

**Path Aliases:**
- Frontend: `"@/*": ["./*"]` in `frontend/tsconfig.json:21-23` — always import via `@/` (`@/types/api`, `@/components/metaradar`), never deep relative `../../../`
- Backend: `sys.path.insert(0, str(base_dir / "backend"))` preamble in every `scripts/*.py` and `tests/*.py` so `from app.main import app` works from repo root (see `scripts/export_openapi.py:6-10`, `tests/conftest.py:8-9`, `tests/test_foundation.py:8-9`). CI sets `PYTHONPATH: backend:.` instead (`.github/workflows/ci.yml:58,69`)
- `pytest.ini: pythonpath = backend .` makes the alias work under pytest without the preamble

## Error Handling

**Patterns:**
- Backend: raise `fastapi.HTTPException` with explicit status codes at endpoint layer; terminal-state guard returns **409** (verified in `scripts/test_e2e_vertical_slice.py:297-298` — re-mutating an `ACTIONED` signal must return 409). Auth/origin failures return **403** with `detail` strings `"Missing Origin/Referer"` / `"Untrusted request origin"` (see `tests/test_security.py:50-70`)
- Never use bare `except:` or silent `try...except: pass` in production paths — banned by `AGENTS.md` rule 5. Test-only cleanup in `tests/conftest.py:43-45` is the sole `except Exception: pass` allowance (fixture teardown)
- Frontend: `try/catch/finally` around every async mutation with user-visible error state — canonical example `handleFeedback` in `frontend/components/common/EvidenceDrawer.tsx:40-67` (`setSubmitting`/`setFeedbackSuccess`/`setFeedbackError` + `finally { setSubmitting(false) }`)
- Frontend error UI: use `ErrorState` (`frontend/components/common/ErrorState.tsx`) with `title`, `message`, `requestId` (correlation ID with copy button), `endpoint`, `statusCode`, `onRetry`, `compact` props; `role="alert"` + `aria-live="assertive"` required. Empty states use `EmptyState` (`frontend/components/common/EmptyState.tsx`)
- Backend validation errors: Pydantic `Field(ge=1, le=500)` range guards (e.g. `PipelineRunRequestSchema.batch_size` in `backend/app/schemas/__init__.py:429`); frontend numeric inputs mirror with `min`/`max` attributes (`EvidenceDrawer.tsx:253-271`)

## Logging

**Framework:** `structlog` with JSON renderer (backend only). Frontend has no logger — use `console.error` sparingly (only in non-render paths, e.g. `ProfileCard.tsx:288`).

**Patterns:**
- Import via factory, never `structlog` directly in modules: `from app.core.logging import get_logger; logger = get_logger("ingestion_service")` (see `backend/app/services/ingestion.py:14-16`, `backend/app/providers/grok.py:17-21`). Module names: `"metaradar.main"`, `"metaradar.http"`, `"ingestion_router"`, `"grok_provider"`
- Configure once: `configure_structlog(json_logs=True)` in `backend/app/main.py:26` and default-on-import in `backend/app/core/logging.py:55`. Processors: `merge_contextvars` + `add_log_level` + `TimeStamper(fmt="iso", utc=True)` + `StackInfoRenderer` + `_scrub_secrets` + `JSONRenderer` (`backend/app/core/logging.py:22-43`)
- Request tracing: `CorrelationIdMiddleware` (`backend/app/core/middleware.py:11-73`) binds `request_id`/`correlation_id`/`path`/`method` to contextvars, echoes `X-Request-ID`/`X-Correlation-ID` response headers, and emits `logger.info("http_request_completed", status_code=..., duration_ms=...)` per request
- Secret scrubbing is automatic (`_scrub_secrets` + `SecretScrubFilter` in `backend/app/core/logging.py:10-19`, `backend/app/core/redact.py:48`) — never log raw `email`, tokens, or keys; keys containing sensitive substrings render as `[REDACTED_SECRET]`, emails as `[REDACTED_PII]`
- Log events in `snake_case`: `"http_request_completed"` — pass structured kwargs, never f-string interpolation

## Comments

**When to Comment:**
- Every module with non-obvious honesty limits gets a docstring — canonical example `export_contracts()` in `scripts/export_openapi.py:14-23` documents that `frontend/types/api.ts` is a re-emitted static template, NOT generated, and drift must be caught by human review
- Middleware/classes carry purpose docstrings (`CorrelationIdMiddleware` in `backend/app/core/middleware.py:12-17`, `SecurityHeadersMiddleware` in `:76-79`)
- E2E harness header comment enumerates the 6-function workflow steps (`scripts/test_e2e_vertical_slice.py:1-12`)
- Inline comments only for non-obvious guards — e.g. `# Skip comment lines` in `scripts/check-banned-classes.mjs:60`, `# Clear prior task context` in `backend/app/core/middleware.py:27`, `# Inject mock client into gemma provider` in `tests/test_foundation.py:81`

**JSDoc/TSDoc:**
- Not used. Props are documented via TypeScript interfaces with optional `?` markers (`EvidenceDrawerProps`, `ProfileCardProps`, `ErrorStateProps`). Pydantic fields carry `description=` strings instead (e.g. `SignalReviewRequest.status` in `backend/app/schemas/__init__.py:173`)

## Function Design

**Size:** Keep endpoint handlers thin (auth → service → schema); business logic lives in `backend/app/services/` and `backend/app/providers/`. React components under ~430 lines (`ProfileCard.tsx` 427 lines is the upper bound — extract subcomponents beyond that). E2E step blocks are sequential, one function-role per block.

**Parameters:** Pydantic models for all request bodies (`SignalReviewRequest` with `status/reviewer/decision/notes/resulting_action/escalate/escalation_reason/resolve_escalation/is_override` in `backend/app/schemas/__init__.py:172-181`); query/path params typed inline. React props as single `Props` interface with defaults destructured in signature (`ProfileCard.tsx:46-68`).

**Return Values:** Backend returns Pydantic response models (`PipelineRunResponseSchema`, `LeadershipSummaryResponse`, `HealthReadyResponse`); review endpoint returns full signal + audit write. Frontend handlers return `Promise<void>` and drive local state, never raw `fetch` responses. Test helpers return `Dict[str, Any]` / `List[Dict[str, Any]]` (`AuthenticatedDecisionClient` in `scripts/test_e2e_vertical_slice.py:89-144`).

## Module Design

**Exports:** Named exports for components (`export function EvidenceDrawer`, `export function ErrorState`, `export interface ...Props`); default export only for memoized top-level cards (`export default ProfileCard` via `React.memo` in `ProfileCard.tsx:426`). Backend uses plain module-level names, no `__all__`.

**Barrel Files:** `frontend/components/metaradar.tsx` is the shared UI barrel (`Card`, `Badge` imported from `@/components/metaradar` in `EvidenceDrawer.tsx:5`, `ErrorState.tsx:4`). `scripts/check-banned-classes.mjs:39` explicitly excludes `metaradar.tsx` from the banned-class scan — keep shared primitives there. Backend `app/schemas/__init__.py` re-exports domain schemas from `auth.py`/`intelligence.py`/`registry.py`.

## CSS / Styling Conventions (Vanilla CSS Tokens — MANDATORY)

- **Use CSS variables, never hardcoded colors or slate utilities.** Canonical tokens in `frontend/app/globals.css:30-65` (`:root`) and `:67-97` (`.dark`): `--background`, `--surface`, `--surface-secondary`, `--surface-elevated`, `--foreground`, `--muted-foreground`, `--border`, `--primary`, `--accent`, `--success`, `--warning`, `--danger`, `--signal`, `--panel`, `--radius`. Reference as `var(--surface-secondary)`, `var(--foreground)`, `border-[var(--border)]`.
- **Banned:** `bg-slate-*`, `text-slate-*`, `border-slate-*` (incl. `dark:` variants) and arbitrary hex `bg-[#...]`/`text-[#...]`/`border-[#...]` — CI fails via `pnpm run check:banned-classes` (`frontend/package.json:14`, `.github/workflows/ci.yml:100`). Tailwind layout utilities (`flex`, `grid`, `gap-2`, `p-3.5`, `rounded`, `text-xs`) are fine; only color utilities are gated.
- **Per-component CSS files** co-located with the component (`ProfileCard.css`, `Stepper.css`, `Counter.css`, `star-portal/styles.css`) use `pc-` prefixed classes (`.pc-card-wrapper`, `.pc-behind`, `.pc-card-shell` in `ProfileCard.tsx:344-346`).
- **`'use client'` directive** is the first line of every interactive component (`ProfileCard.tsx:1`, `EvidenceDrawer.tsx:1`, `ErrorState.tsx:1`).
- **Accessibility:** dialogs carry `role="dialog" aria-modal="true" aria-label=...` (`EvidenceDrawer.tsx:89-96`); errors `role="alert" aria-live="assertive"`; icon buttons always have `aria-label`.

## Commit / Branch Conventions

- **Branches:** `feature/*` (new feature), `fix/*` (bug), `refactor/*`, `security/*`, `docs/*` per `docs/rules/DEVELOPMENT_WORKFLOW.md:9-14`. Observed: `feature/phase-12-hackathon-mvp`, `feature/phase-11-productionization`, `fix/concerns-md-audit-fixes`. **NEVER push directly to `main`** — always PR from short-lived branches (`AGENTS.md` rule 3, `DEVELOPMENT_WORKFLOW.md:16`).
- **Commits:** atomic, conventional-prefix style — `fix:`, `docs:`, `docs(readme):`, `docs(pitch):`, `fix(ui):`, `fix(scheduler):`, `fix(codebase):`, `fix(ui, auth):` (see `git log --oneline`). Never commit `.env`, keys, or credentials (`AGENTS.md` rule 7, `docs/rules/SECURITY_STANDARDS.md:5`).
- **DoD footer on every phase:** typecheck + lint + build + pytest + contract sync + security + docker + CI + docs + git-safety checkboxes per `docs/rules/DEFINITION_OF_DONE.md:5-16`. If any gate cannot be verified, status is **BLOCKED**.

---

*Convention analysis: 2026-09-19*
