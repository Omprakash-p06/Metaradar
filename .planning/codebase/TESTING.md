# Testing Patterns

**Analysis Date:** 2026-09-19

## Test Framework

**Runner:**
- Backend: `pytest >= 8.0.0` with `pytest-asyncio >= 0.23.0`, `pytest-cov`, `pytest-httpx` (see `backend/requirements.txt`)
- Config: `pytest.ini` — `asyncio_mode = auto`, `testpaths = tests`, `python_files = test_*.py`, `python_classes = Test*`, `python_functions = test_*`, `pythonpath = backend .`, marker `live` for tests requiring live external services
- Frontend: no unit-test runner (no vitest/jest config). Frontend quality is enforced by `tsc --noEmit` + `eslint .` + `check:banned-classes` + `next build` — all defined in `frontend/package.json:9-15` and CI `.github/workflows/ci.yml:95-102`

**Assertion Library:**
- Plain `assert` statements (pytest style). Async HTTP assertions via `httpx.AsyncClient` + `ASGITransport(app=app)` — see `tests/test_security.py:28-47`, `scripts/test_e2e_vertical_slice.py:89-144`

**Run Commands:**
```bash
pytest -v                          # Full backend suite (CI command, .github/workflows/ci.yml:74)
python tests/test_foundation.py    # 5 capability checks incl. async provider/BART fallback (TESTING_STRATEGY.md gate 3)
python scripts/test_e2e_vertical_slice.py   # 6-function decision vertical slice (needs DB + app import)
python scripts/export_openapi.py   # Contract sync gate (CI diff-checks frontend/types/api.ts after)
cd frontend && pnpm exec tsc --noEmit   # Frontend typecheck (DoD gate, DEFINITION_OF_DONE.md:7)
cd frontend && pnpm lint            # = eslint . (DoD gate)
cd frontend && pnpm run check:banned-classes  # Vanilla-CSS token gate
cd frontend && pnpm build           # = next build production gate
docker compose config              # Container readiness gate (TESTING_STRATEGY.md gate 6)
```

## Test File Organization

**Location:**
- Backend tests live in repo-root `tests/` (35 files: `conftest.py` + 34 `test_*.py`), configured by `pytest.ini: testpaths = tests`
- Scripts-as-tests live in `scripts/` — `test_e2e_vertical_slice.py` (389 lines, 6/6 cross-functional harness), `test_live_ingestion_e2e.py`, `test_demo_scenarios_e2e.py`
- Frontend has no `__tests__/` or `*.test.*` files — contract file `frontend/types/api.ts` is verified indirectly by `tests/test_contract_drift.py`

**Naming:**
- `tests/test_<domain>.py` — `test_auth.py`, `test_rbac.py`, `test_security.py`, `test_privacy_boundary.py`, `test_signals_endpoints.py`, `test_signal_routing_workflow.py`, `test_review_state_machine.py`, `test_approval_workflow.py`, `test_contract_drift.py`, `test_foundation.py`, `test_config.py`, `test_providers_live.py` (marked `live`), etc.

**Structure:**
```
tests/
├── conftest.py                        # autouse cleanup fixture (DB row delete + engine.dispose)
├── test_foundation.py                 # 5 capability unit checks (domain config, dedup, PII, red-team, providers)
├── test_contract_drift.py             # OpenAPI route presence + TS interface presence gate
├── test_auth.py / test_rbac.py / test_security.py / test_login_credentials.py
├── test_signals_endpoints.py / test_api_endpoints.py / test_signal_*workflow*.py
├── test_review_state_machine.py / test_approval_workflow.py
├── test_ingestion.py / test_retrieval.py / test_providers_live.py (live)
└── ... (34 test modules total)
scripts/
├── export_openapi.py                  # contract exporter (CI runs + git diff gate)
├── test_e2e_vertical_slice.py         # 6-function decision E2E (Rev 11.2)
├── test_live_ingestion_e2e.py / test_demo_scenarios_e2e.py
contracts/openapi.json                 # exported FastAPI schema (committed)
frontend/types/api.ts                  # canonical TS contract (re-emitted template, committed)
```

## Test Structure

**Suite Organization:**
```python
# tests/test_foundation.py — plain functions, asyncio_mode=auto handles async
def test_domain_config_loader():
    config = get_domain_config()
    assert config.domain_config_version == "1.0.0"
    assert len(config.assets) >= 7

@pytest.mark.asyncio
async def test_provider_execution_and_degraded_bart_fallback():
    provider_factory.gemma._client = AsyncClient(transport=MockTransport(ollama_handler), base_url="http://ollama-test")
    result = await provider_factory.execute_task(
        required_capability=ProviderCapability.REASON,
        evidence=["Trial shows 80% reduction in ABR"],
        task="Evaluate efficacy durability",
        classification=DataClassification.PUBLIC,
    )
    assert result["model_metadata"]["reasoning_available"] is True
```

```python
# tests/test_security.py — ASGI transport pattern (no live server needed)
async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost:8000") as ac:
    res = await ac.get("/api/v1/health/ready")
    assert res.status_code == 200
    assert headers.get("X-Content-Type-Options") == "nosniff"
```

**Patterns:**
- Setup: `sys.path.insert(0, str(base_dir / "backend"))` preamble at top of every test module; `from app.main import app` for ASGI tests; `MockTransport` handler injection for LLM provider tests (no network)
- Teardown: autouse `cleanup_db_connections` fixture in `tests/conftest.py:15-46` — clears `_auth_rate_buckets`, deletes `Signal` rows matching test title/fingerprint patterns (`%Test Signal%`, `FSM Lifecycle%`, `approval-fp-%`, `Deterministic E2E Acceptance%`, …), commits, then `await engine.dispose()`
- Assertion: status-code-first (`assert res.status_code == 200, f"...: {res.text}"`), then payload invariants, then audit-trail presence (`assert any(a["action"] == "SIGNAL_ESCALATED" for a in audits)`)

## Mocking

**Framework:** `httpx.MockTransport` + `httpx.ASGITransport(app=app)` — no `unittest.mock`/`pytest-mock` dependency. Rate-bucket reset via `from app.api.deps import _auth_rate_buckets; _auth_rate_buckets.clear()` before auth tests.

**Patterns:**
```python
# tests/test_foundation.py:66-82 — mock the Ollama/Gemma HTTP layer
def ollama_handler(request):
    return Response(200, json={"model": "gemma3:4b", "response": json.dumps({...}), "done": True})
provider_factory.gemma._client = AsyncClient(transport=MockTransport(ollama_handler), base_url="http://ollama-test")
```

```python
# scripts/test_e2e_vertical_slice.py:89-111 — in-process ASGI client (real DB, real app, no TCP)
transport = httpx.ASGITransport(app=app)
self.client = httpx.AsyncClient(transport=transport, base_url=base_url, timeout=30.0, headers={"Origin": self.origin})
```

**What to Mock:**
- External LLM HTTP (Ollama/Gemma) via `MockTransport` — deterministic `gemma3:4b` JSON payloads
- Nothing else in unit scope — DB-backed tests use the real async engine + fixture cleanup

**What NOT to Mock:**
- FastAPI app itself — always use `ASGITransport(app=app)` so routing/middleware/auth execute for real
- Auth cookies/CSRF — perform real `POST /auth/demo-login` with `Origin` header and propagate `metaradar_session`/`metaradar_csrf` cookies + `X-CSRF-Token` header (see `AuthenticatedDecisionClient.demo_login` / `_get_csrf_header`)
- Audit trail — assert real `SIGNAL_REVIEWED` / `SIGNAL_ESCALATED` / `ESCALATION_RESOLVED` rows via `GET /signals/{id}/audit-history`

## Fixtures and Factories

**Test Data:**
```python
# scripts/test_e2e_vertical_slice.py:40-78 — deterministic per-role fixtures
for role in ["MEDICAL_AFFAIRS", "REGULATORY", "SAFETY", "MARKET_ACCESS", "COMMUNICATIONS", "LEADERSHIP"]:
    count = SELECT count WHERE relevant_function == role AND review_status == "UNREVIEWED"
    if count == 0:
        db.add(Signal(source_id="fda"|"pubmed", fingerprint=f"e2e-fixture-{role.lower()}-{uuid...}",
                       title=f"Deterministic E2E Acceptance Signal for {role}", ...))
```

**Location:**
- E2E fixtures seeded inline by `ensure_acceptance_fixtures()` (same file) — idempotent (only seeds when count == 0)
- Cleanup patterns centralized in `tests/conftest.py:23-39` (title `ilike` list + `fingerprint.ilike('approval-fp-%')`)
- Static domain data: `backend/app/data/synthetic_signals.json`, `data/synthetic_signals.json`

## Coverage

**Requirements:** No numeric threshold enforced in `pytest.ini` or CI. CI requires the full suite to pass (`pytest -v` exit 0) — "100% clean output" per `docs/rules/DEFINITION_OF_DONE.md:10`, which means zero failures/errors, not 100% line coverage.

**View Coverage:**
```bash
pytest --cov=backend/app --cov-report=term-missing   # pytest-cov is installed; no committed config
```

## Test Types

**Unit Tests:**
- `tests/test_foundation.py` — 5 capability checks runnable via `python tests/test_foundation.py` directly (has `run_tests()` + `__main__` runner at `:104-120`): domain config load, fingerprint/chunking, PII scrub + classification, red-team contradiction rules, provider execute + degraded-BART fallback
- `tests/test_config.py`, `tests/test_config_errors.py`, `tests/test_calibration_service.py`, `tests/test_privacy_boundary.py`, `tests/test_provenance.py`, `tests/test_truthfulness_and_invariants.py` — pure service/logic scope

**Integration Tests:**
- `tests/test_api_endpoints.py`, `tests/test_signals_endpoints.py`, `tests/test_auth.py`, `tests/test_rbac.py`, `tests/test_security.py`, `tests/test_approval_workflow.py`, `tests/test_review_state_machine.py`, `tests/test_signal_*workflow*.py`, `tests/test_ingestion.py`, `tests/test_retrieval.py`, `tests/test_connector_health.py`, `tests/test_observability.py` — ASGI transport against real app + Postgres/Redis (CI provisions `pgvector/pgvector:pg16` + `redis:7-alpine` services, runs `alembic upgrade head` + `seed.py` first — `.github/workflows/ci.yml:17-65`)
- `tests/test_providers_live.py`, `scripts/test_live_ingestion_e2e.py` — marked `live`, require external services

**E2E Tests:**
- `scripts/test_e2e_vertical_slice.py` (Rev 11.2) — full 6-function decision slice, 6/6 steps: Medical Affairs `UNREVIEWED→IN_REVIEW→REVIEWED` + audit; Safety escalate (`escalate=True` → `is_escalated=True` + `SIGNAL_ESCALATED`); Leadership summary visibility + resolve (`resolve_escalation` → `ACTIONED` + `ESCALATION_RESOLVED`); Market Access `ACTIONED` + 409 terminal-lock proof; Communications `DISMISSED`; Regulatory `ACTION_REQUIRED`; Leadership direct override. Exit 0 = pass. Requires DB (`AsyncSessionLocal`) + `METARADAR_API_URL`/`METARADAR_ORIGIN` envs (defaults `http://localhost:8000/api/v1`, `http://localhost:3000`)
- No Playwright/Cypress — browser-side E2E is manual demo-journey (`scripts/test_demo_scenarios_e2e.py`)

## Contract Sync Gate (OpenAPI → TypeScript)

- Exporter: `scripts/export_openapi.py::export_contracts()` dumps live `app.openapi()` to `contracts/openapi.json` AND re-emits the hand-maintained template to `frontend/types/api.ts` (verbatim — NOT codegen; honesty note at `:14-23`)
- Drift test: `tests/test_contract_drift.py::test_contract_sync_drift` asserts 9 route prefixes (`/api/v1/health`, `/signals`, `/confluence`, `/lifecycles`, `/red-team`, `/missing-signals`, `/developments`, `/sources`, `/cache/clear`) exist in the live schema AND 11 `export interface` names exist in `frontend/types/api.ts`
- CI canonical-copy check (`.github/workflows/ci.yml:76-81`): runs exporter then `git diff --exit-code frontend/types/api.ts` — fails if anyone hand-edits the TS file instead of the template in `export_openapi.py`
- **To change the contract:** edit the `ts_content` template inside `scripts/export_openapi.py`, run `python scripts/export_openapi.py`, commit `contracts/openapi.json` + `frontend/types/api.ts` together

## Common Patterns

**Async Testing:**
```python
# asyncio_mode = auto — plain `async def test_*` works; explicit mark also used
@pytest.mark.asyncio
async def test_red_team_contradiction_service():
    redteam = RedTeamNLIService()
    flags = await redteam.evaluate_contradictions(claims)
    assert flags[0]["rule_id"] == "RULE_A_DOSING_CONTRADICTION"
```

**Error Testing:**
```python
# Terminal-state lock: mutating ACTIONED must 409 (scripts/test_e2e_vertical_slice.py:297-298)
res_reopen = await c_ma.submit_review(ma_id, {"status": "IN_REVIEW"})
assert res_reopen.status_code == 409, f"Expected 409 on mutating ACTIONED signal, got {res_reopen.status_code}"

# Auth gates: missing/spoofed Origin must 403 (tests/test_security.py:50-80)
res = await ac.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
assert res.status_code == 403
assert "Missing Origin/Referer" in res.json()["detail"]
```

**Security-header testing:**
```python
# tests/test_security.py:27-47 — every response must carry hardened headers
assert headers.get("X-Frame-Options") == "DENY"
assert "default-src 'self'" in csp  # + object-src/base-uri/frame-ancestors/form-action 'none'/'self'
```

## Full Gate Sequence (DoD order)

Per `docs/rules/DEFINITION_OF_DONE.md`, `docs/rules/TESTING_STRATEGY.md`, and `.github/workflows/ci.yml`, run in this order:

```bash
# 1. Backend suite (needs Postgres 16 + Redis 7; CI seeds via alembic + seed.py)
pytest -v
# 2. Foundation capability spot-check
python tests/test_foundation.py
# 3. Contract sync + drift
python scripts/export_openapi.py && git diff --exit-code frontend/types/api.ts
# 4. E2E vertical slice (needs DB + app importable)
python scripts/test_e2e_vertical_slice.py
# 5-8. Frontend gates (from frontend/)
cd frontend && pnpm exec tsc --noEmit && pnpm run check:banned-classes && pnpm lint && pnpm build
# 9. Container readiness
docker compose config
```

Reference baseline: **pytest 186 passed / 1 skipped; E2E vertical slice 6/6** (hackathon release benchmark). Any regression below this blocks merge per `AGENTS.md` rule 6 (executable verification required).

## Coverage Gaps

- **Frontend unit tests: none.** No vitest/jest/RTL; `ProfileCard` tilt engine (`ProfileCard.tsx:75-185`), `EvidenceDrawer` feedback flow, and `ErrorState` retry paths are only exercised manually + via `next build`. Adding `vitest` + `testing-library` for `components/common/` is the highest-value gap
- **Contract drift blind spot:** `export_openapi.py` re-emits a static TS template, so `test_contract_drift.py` only checks interface *names*, not field parity — schema↔TS field drift needs human review of `contracts/openapi.json` diffs until real codegen (`openapi-typescript`) lands
- **Live-provider tests** (`test_providers_live.py`, `test_live_ingestion_e2e.py`) are excluded from offline CI by the `live` marker — Grok fallback + real ingestion only verified on demand
- **Migration verification** (`alembic upgrade head`) runs in CI but has no dedicated test module — model↔migration skew (e.g. new `Column` without revision) surfaces only at CI seed time

---

*Testing analysis: 2026-09-19*
