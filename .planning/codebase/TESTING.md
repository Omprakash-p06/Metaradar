# Testing Patterns

**Analysis Date:** 2026-10-01

## Test Frameworks

**Backend runner:**
- `pytest>=8.0.0` + `pytest-asyncio>=0.23.0` + `pytest-cov>=4.1.0` + `pytest-httpx>=0.30.0` (see `backend/requirements.txt`)
- Config: `pytest.ini` — `asyncio_mode = auto`, `testpaths = tests`, `python_files = test_*.py`, `python_classes = Test*`, `python_functions = test_*`, `pythonpath = backend .`, marker `live` for external-service tests
- Global fixture: `tests/conftest.py:cleanup_db_connections` (autouse, async) — clears `_auth_rate_buckets`, deletes fixture-titled `Signal` rows (`Test Signal%`, `FSM Lifecycle%`, `approval-fp-%`, …), disposes engine

**Frontend gates (no Jest/Vitest detected — typecheck + lint + build are the frontend suite):**
- TypeScript `5.7.3`, ESLint `^10.8.1` + `eslint-config-next` + `@next/eslint-plugin-next`, Next `16.3.0` (see `frontend/package.json`)
- Package manager: `pnpm@9.15.5`, Node `>=20.9.0` (CI uses Node 22 + pnpm 9)

## Run Commands (verified — do not invent alternatives)

All commands from `.github/workflows/ci.yml`, `docs/rules/TESTING_STRATEGY.md`, `docs/rules/DEFINITION_OF_DONE.md`, `.github/pull_request_template.md`:

```bash
pytest -v                                          # Full backend suite (CI canonical; PYTHONPATH=backend:. DATABASE_URL=… REDIS_URL=… LLM_PROVIDER=local)
python tests/test_foundation.py                    # Foundation/capability verification (5 checks: domain config, dedup, PII, red-team, provider fallback)
pytest tests/test_login_credentials.py -v          # Phase-12 per-role credentials gate (8+ tests expected)
pytest tests/test_approval_workflow.py -v          # Phase-12 approval E2E gate (12+ tests expected)
pytest tests/test_rbac.py tests/test_intelligence_nodes.py tests/test_retrieval.py -v   # Regression subset
python -m pytest tests/test_contract_drift.py -v  # Contract presence assertions (fast, no DB)
python scripts/export_openapi.py                   # Regenerate contracts/openapi.json + frontend/types/api.ts
git diff --exit-code frontend/types/api.ts         # Contract canonical-copy gate (fails CI if template edited without re-export)
docker compose config                             # Container readiness validation
alembic upgrade head                               # Migration verification (run from backend/ with DATABASE_URL set)
python backend/app/db/seed.py                      # CI seeding after migrate
python scripts/test_e2e_vertical_slice.py          # 6-function decision-intelligence E2E harness (needs live API + DB)
python scripts/test_live_ingestion_e2e.py          # Live ingestion E2E (needs external source access)
python scripts/test_demo_scenarios_e2e.py          # Demo-scenario E2E
```

```bash
pnpm exec tsc --noEmit        # Frontend typecheck, 0 errors required (run from frontend/)
pnpm lint                     # = eslint . (run from frontend/)
pnpm run check:banned-classes # = node ../scripts/check-banned-classes.mjs (Tailwind token gate)
pnpm build                    # = next build, strict production build (run from frontend/)
```

## Test File Organization

**Location:** separate top-level `tests/` dir (not co-located), 30+ files:
- `tests/test_foundation.py` — 5 capability checks (canonical smoke suite)
- `tests/test_contract_drift.py` — OpenAPI path presence + TS interface presence
- `tests/test_api_endpoints.py`, `tests/test_signals_endpoints.py` — endpoint coverage
- `tests/test_auth.py`, `tests/test_login_credentials.py`, `tests/test_rbac.py` — auth/RBAC
- `tests/test_review_state_machine.py`, `tests/test_signal_routing_workflow.py`, `tests/test_signal_decision_refinement.py`, `tests/test_approval_workflow.py` — FSM/workflows
- `tests/test_privacy_boundary.py`, `tests/test_security.py`, `tests/test_redteam_behavior.py` — security/privacy
- `tests/test_calibration_service.py`, `tests/test_e2e_calibration_scenario.py`, `tests/test_parity_matrix.py`, `tests/test_provider_matrix.py`, `tests/test_providers_live.py` (`live` marker) — intelligence/calibration
- `tests/test_ingestion.py`, `tests/test_retrieval.py`, `tests/test_confluence_semantics.py`, `tests/test_intelligence_nodes.py`, `tests/test_provenance.py`, `tests/test_observability.py`, `tests/test_connector_health.py`, `tests/test_config.py`, `tests/test_config_errors.py`, `tests/test_failure_injection.py`, `tests/test_truthfulness_and_invariants.py`, `tests/test_operational_workspaces.py`, `tests/test_codebase_concerns.py`, `tests/test_launchers.py`

**Naming:** `test_<domain>.py`; classes `Test*`, functions `test_*`
**E2E scripts:** `scripts/test_*_e2e*.py` + `scripts/generate_parity_matrix.py` (report generator, not a test)

## Test Structure

**Suite organization (exemplar `tests/test_foundation.py`):**
```python
import sys
from pathlib import Path
base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))  # required boilerplate in every test/script

def test_domain_config_loader():
    config = get_domain_config()
    assert config.domain_config_version == "1.0.0"

@pytest.mark.asyncio  # optional — asyncio_mode=auto already handles it
async def test_red_team_contradiction_service():
    redteam = RedTeamNLIService()
    flags = await redteam.evaluate_contradictions(claims)
    assert flags[0]["rule_id"] == "RULE_A_DOSING_CONTRADICTION"
```

**Patterns:**
- Setup: direct service instantiation + `httpx.MockTransport` injection for providers (see `test_provider_execution_and_degraded_bart_fallback`); DB-backed tests rely on `conftest.py` autouse cleanup, not per-test setup
- Teardown: `conftest.py` deletes known fixture titles + `await engine.dispose()`
- Assertions: plain `assert` with domain invariants (fingerprint format, scrub tokens like `[EMAIL_REDACTED]`, FSM terminal `409`, audit actions `SIGNAL_ESCALATED`/`ESCALATION_RESOLVED`)

## Contract-Sync Process (critical — read carefully)

Pipeline per `docs/rules/ARCHITECTURE_RULES.md` §5: FastAPI OpenAPI → `contracts/openapi.json` → `frontend/types/api.ts`.

1. Edit the TS template string **inside** `scripts/export_openapi.py:39-779` (the canonical source) AND/OR backend Pydantic schemas in `backend/app/schemas/`
2. Run `python scripts/export_openapi.py` (dumps live schema to `contracts/openapi.json`, re-emits template verbatim to `frontend/types/api.ts`)
3. Commit **both** files together; CI re-runs the script and fails on `git diff --exit-code frontend/types/api.ts` (see `ci.yml:76-81`)
4. **Known limitation (honesty note in `scripts/export_openapi.py:14-23`):** `api.ts` is NOT codegen'd from OpenAPI — the CI gate only detects direct edits to the canonical copy, NOT schema↔TS drift. Drift must be caught by human review of `contracts/openapi.json` diffs + `tests/test_contract_drift.py` presence assertions until `openapi-typescript`/`datamodel-code-generator` is adopted
5. `tests/test_contract_drift.py` asserts paths (`/api/v1/health`, `/signals`, `/confluence`, `/lifecycles`, `/red-team`, `/missing-signals`, `/developments`, `/sources`, `/cache/clear`) and TS interfaces (`Signal`, `HealthResponse`, `ModelMetadata`, `ConfluenceAlertItem`, `LifecycleTimelineItem`, `ContradictionItem`, `MissingSignalWatchItem`, `DevelopmentSummary`, `SourceRegistryItem`, `CacheClearResponse`, `SignalFilterParams`)

## Mocking

**Framework:** `httpx.MockTransport` / `httpx.ASGITransport(app=app)` (no `unittest.mock` proliferation observed)
```python
# Provider mock — tests/test_foundation.py:66-82
provider_factory.gemma._client = AsyncClient(transport=MockTransport(ollama_handler), base_url="http://ollama-test")
# In-process API client — scripts/test_e2e_vertical_slice.py:92
transport = httpx.ASGITransport(app=app)
```
**What to mock:** LLM provider HTTP (`gemma._client`), external connector fetches
**What NOT to mock:** PII scrubber, fingerprint/chunking, FSM transitions, audit trail — these are the invariants under test and must execute for real; `live`-marked tests (`tests/test_providers_live.py`) require real external services and are excluded from default CI

## Fixtures and Factories

- Deterministic signals seeded in-DB with `relevant_function` per role + `review_status="UNREVIEWED"` — see `scripts/test_e2e_vertical_slice.py:40-78` (`ensure_acceptance_fixtures`, fingerprint `e2e-fixture-<role>-<rand>`)
- Cleanup patterns in `tests/conftest.py:24-42` must be extended when adding new fixture title prefixes, otherwise test rows leak between runs
- Auth in E2E: `demo-login` per role + CSRF cookie (`metaradar_csrf` → `X-CSRF-Token`) + `Origin` header — see `AuthenticatedDecisionClient` (`scripts/test_e2e_vertical_slice.py:89-144`)

## Coverage

**Requirements:** no numeric threshold enforced in `pytest.ini` or CI; DoD requires "100% clean output" (0 failures), not a % number. `pytest-cov` is installed but no `--cov-fail-under` gate exists.
```bash
pytest --cov=backend/app --cov-report=term-missing -v   # ad-hoc coverage (not a CI gate)
```

## Test Types

**Unit/capability:** `tests/test_foundation.py` (5 checks, runnable via `python tests/test_foundation.py` directly thanks to `run_tests()` main)
**Contract:** `tests/test_contract_drift.py` + `scripts/export_openapi.py` + CI diff gate
**Integration (DB/Redis):** full `pytest -v` under CI services `pgvector/pgvector:pg16` + `redis:7-alpine` with `DATABASE_URL=postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar`
**E2E (decision workflows):** `scripts/test_e2e_vertical_slice.py` — 6/6 functions: Medical Affairs REVIEWED, Safety escalate → Leadership resolve, Market Access ACTIONED terminal-lock `409`, Communications DISMISSED, Regulatory ACTION_REQUIRED, Leadership direct override
**Frontend:** `tsc --noEmit` + `eslint .` + `check:banned-classes` + `next build` (no unit runner)
**Migration:** `alembic upgrade head` from `backend/` (migrations 013/014 baseline, 015 approval_requests)
**Container:** `docker compose config` validation only

## Common Patterns

**Async testing:** `asyncio_mode = auto` so `async def test_*` just works; explicit `@pytest.mark.asyncio` also present and harmless
**Error/terminal-state testing:**
```python
# Terminal lock — scripts/test_e2e_vertical_slice.py:296-298
res_reopen = await c_ma.submit_review(ma_id, {"status": "IN_REVIEW"})
assert res_reopen.status_code == 409
```
**Privacy testing:** `tests/test_privacy_boundary.py` + `tests/test_security.py`; scrub assertion exemplar:
```python
scrubbed, has_pii, counts = PIIPHIScrubber.scrub("Patient email patient@example.com, DOB: 05/12/1980")
assert has_pii is True
assert "[EMAIL_REDACTED]" in scrubbed
```

## Known Gates & Verified Baseline (from `.planning/STATE.md`, Phase 11 — do not regress)

- `alembic upgrade head` → migrations 013 + 014 clean (015 adds `approval_requests` per Phase 12)
- `pytest -v` → **166+ passed, 0 failed** (32 new tests added in Phase 11)
- `python scripts/test_e2e_vertical_slice.py` → **6/6 functions PASS**
- `python scripts/export_openapi.py` → contracts synchronized (auth endpoints present)
- `node scripts/check-banned-classes.mjs` → 0 violations
- `npm --prefix frontend run build` → Next.js 16 production build clean
- `npx tsc --noEmit` → 0 TypeScript errors
- Phase 12 matrix adds: `pytest tests/test_login_credentials.py -v` (8+), `pytest tests/test_approval_workflow.py -v` (12+), RBAC/retrieval regression subset, plus manual `/login` role-pill + approval-request UI checks

## PR Checklist (`.github/pull_request_template.md` — copy into every PR)

- [ ] Frontend `pnpm exec tsc --noEmit` passed / `pnpm lint` passed / `pnpm build` passed
- [ ] Backend `python tests/test_foundation.py` passed
- [ ] OpenAPI contract `python scripts/export_openapi.py` verified
- [ ] No secrets committed / PII scrubber verified / privacy gate verified
- [ ] Migrations verified (`alembic upgrade head`)
- [ ] Architecture docs updated if applicable + Known Limitations noted

---

*Testing analysis: 2026-10-01*
