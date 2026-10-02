# Testing Patterns

**Analysis Date:** 2026-10-02

## Test Framework

**Runner:**
- `pytest>=8.0.0` with `pytest-asyncio>=0.23.0`, `pytest-cov>=4.1.0`, `pytest-httpx>=0.30.0` (`backend/requirements.txt`)
- Config: `pytest.ini` at repo root
  ```ini
  [pytest]
  asyncio_mode = auto
  testpaths = tests
  python_files = test_*.py
  python_classes = Test*
  python_functions = test_*
  pythonpath = backend .
  markers =
      live: mark test as requiring live external services
  ```

**Assertion Library:**
- Plain `assert` statements only. No `unittest.TestCase`, no `pytest.assume`, no custom assertion helpers.

**Run Commands:**
```bash
pytest -v                                   # full suite (as CI runs it)
pytest -v -m "not live"                     # exclude tests needing external services
pytest tests/test_gemini_provider.py -v     # single module (per-phase DoD gate)
pytest --cov=app --cov-report=term-missing  # coverage
```

**Frontend has no unit-test runner.** There is no Jest, Vitest, Playwright, or Cypress. The frontend "suite" is the CI gate chain:
```bash
cd frontend
pnpm exec tsc --noEmit            # type gate
pnpm run check:banned-classes     # style gate (scripts/check-banned-classes.mjs)
pnpm lint                         # eslint
pnpm build                        # Next.js 16 production build
```

**Script-based E2E harnesses (not pytest):**
```bash
python scripts/test_e2e_vertical_slice.py    # 6-function decision-intelligence E2E
python scripts/test_demo_scenarios_e2e.py    # demo journey scenarios
python scripts/test_live_ingestion_e2e.py    # real connector ingestion (network)
python scripts/generate_parity_matrix.py     # feature parity matrix
python scripts/export_openapi.py             # API contract export
```

## Test File Organization

**Location:**
- Separate top-level `tests/` directory (not co-located with source)
- `backend/tests/` contains **only** `__pycache__` — it is a vestigial directory with no test modules
- 36 `test_*.py` modules plus `tests/conftest.py`

**Naming:**
- One module per concern: `test_privacy_boundary.py`, `test_contract_drift.py`, `test_redis_optional.py`, `test_gemini_provider.py`
- Domain-scoped rather than source-file-scoped — most modules exercise a behaviour across several modules

**Structure:**
```text
tests/
├── conftest.py                          # global autouse cleanup fixture
├── test_foundation.py                   # (5)  core app wiring
├── test_config.py / test_config_errors.py       # (3/7) settings + connector config errors
├── test_api_endpoints.py                # (5)  root/health/business endpoints
├── test_signals_endpoints.py            # (3)  signal API surface
├── test_auth.py / test_login_credentials.py     # (8/4) auth + per-role creds
├── test_rbac.py                         # (3)  role enforcement
├── test_security.py                     # (16) CSRF, origin, rate limits, sessions
├── test_privacy_boundary.py             # (3)  PII scrubber + provider privacy gate
├── test_provider_matrix.py              # (6)  provider capability matrix
├── test_gemini_provider.py              # (13) Gemini client, retries, gate, JSON parsing
├── test_gemma_stream.py                 # (4)  local streaming
├── test_providers_live.py               # (1)  marked `live`
├── test_ingestion.py                    # (15) connectors + ingestion service
├── test_connector_health.py             # (7)  health telemetry + status enums
├── test_intelligence_nodes.py           # (17) LangGraph nodes
├── test_confluence_semantics.py         # (2)  confluence logic
├── test_redteam_behavior.py             # (3)  contradiction rules
├── test_retrieval.py                    # (12) vector search
├── test_provenance.py                   # (14) provenance resolution
├── test_signal_routing_workflow.py      # (3)  routing + escalation
├── test_signal_decision_refinement.py   # (8)  decision object refinement
├── test_review_state_machine.py         # (5)  review FSM
├── test_approval_workflow.py            # (4)  approval request lifecycle
├── test_calibration_service.py          # (7)  HITL calibration
├── test_e2e_calibration_scenario.py     # (1)  calibration E2E
├── test_observability.py                # (3)  activity/health endpoints
├── test_operational_workspaces.py       # (3)  workspace data endpoints
├── test_truthfulness_and_invariants.py  # (7)  no-fabrication invariants
├── test_codebase_concerns.py            # (9)  prior CONCERNS.md regressions
├── test_failure_injection.py            # (2)  degraded-path behaviour
├── test_redis_optional.py               # (6)  boots without Redis
├── test_launchers.py                    # (6)  setup.py / start.py
├── test_parity_matrix.py                # (3)  feature parity
└── test_contract_drift.py               # (1)  OpenAPI ↔ TS contract sync
```

**Total: 219 test functions across 36 modules.**

## Test Structure

**Suite Organization:**

Tests are flat module-level functions — **no test classes** anywhere, despite `pytest.ini:python_classes = Test*`. Async tests are plain `async def` decorated with `@pytest.mark.asyncio` (150 usages):

```python
import pytest

@pytest.mark.asyncio
async def test_gemini_capabilities_exclude_actions():
    provider = GeminiProvider(api_key="mock-gemini-key")
    assert provider.supports(ProviderCapability.SUMMARIZE) is True
    # Crucial security guarantee: semantic interpretation only, never action execution
    assert provider.supports(ProviderCapability.GENERATE_ACTIONS) is False
```

Synchronous tests need no decorator:

```python
def test_pii_scrubber_patterns():
    s1, p1, _ = PIIPHIScrubber.scrub("Contact doc@hospital.org for details")
    assert p1 is True
    assert "[EMAIL_REDACTED]" in s1
```

**The universal test-file preamble** — every module starts by bootstrapping `sys.path` before any `app.*` import:

```python
import pytest
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.providers.gemini import GeminiProvider, GeminiUnavailableError
from app.core.config import settings
```

This mirrors `pytest.ini:pythonpath = backend .` but is repeated defensively so modules also run standalone.

**Patterns:**
- **Setup:** the global autouse fixture in `tests/conftest.py` clears `_auth_rate_buckets` before each test
- **Teardown:** the same fixture deletes rows whose titles match a hardcoded list of test-fixture patterns (`'%Test Signal%'`, `'FSM Lifecycle%'`, `'Deterministic E2E Acceptance%'`, `Signal.fingerprint.ilike('approval-fp-%')`, …) then calls `await engine.dispose()`
- **Assertion pattern:** granular, one behaviour per assert, with domain-language assertion messages where the invariant is security-critical
- **Docstring-free tests** — the test name carries the intent (`test_privacy_gate_external_bypass_prevention`)

## Mocking

**Framework:** `unittest.mock` (`AsyncMock`, `MagicMock`) for DB/object boundaries, and **`pytest-httpx` / `httpx.MockTransport`** for HTTP.

**Patterns:**

HTTP provider mocking — swap the client's transport (no network, no `responses` library):

```python
from httpx import AsyncClient, MockTransport, Response

def gemini_handler(request):
    assert "key=test-valid-key" in str(request.url)
    body = json.loads(request.content)
    assert "contents" in body
    return Response(200, json={"candidates": [{"content": {"parts": [
        {"text": json.dumps({"what_changed": "...", "why_it_matters": "..."})}
    ]}}]})

provider = GeminiProvider(api_key="test-valid-key", max_retries=1)
provider._client = AsyncClient(transport=MockTransport(gemini_handler))
```

API testing without a live server — ASGI transport against the real app:

```python
from httpx import AsyncClient, ASGITransport
from app.main import app

async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
    response = await ac.get("/api/v1/health")
assert response.status_code == 200
```

Dependency override for auth + DB:

```python
from app.db.session import get_db
from app.api.deps import get_current_user
app.dependency_overrides[get_db] = lambda: mock_db
app.dependency_overrides[get_current_user] = lambda: fake_user
```

Settings mutation via monkeypatch:

```python
monkeypatch.setattr(settings, "ENABLE_GROK_FALLBACK", True)
```

**What to Mock:**
- Outbound HTTP to any external provider or connector (`MockTransport`, `pytest-httpx`)
- Database sessions and result scalars (`AsyncMock` + `MagicMock().scalars().all.return_value`)
- Settings flags that gate optional providers
- `sys.path`/module import side effects where a provider would otherwise load a model

**What NOT to Mock:**
- `PIIPHIScrubber` — the privacy boundary is tested against the real regex implementation (`tests/test_privacy_boundary.py`)
- `validate_privacy_gate()` — tested as real logic, not stubbed, in `tests/test_privacy_boundary.py` and `tests/test_gemini_provider.py`
- Provider capability declarations — asserted against the real class attributes
- The FastAPI app object itself — tests use `ASGITransport(app=app)` rather than a re-built app

## Fixtures and Factories

**Test Data:**
- No factory library (`factory_boy`, `faker`) is used. Test data is inline literals.
- Deterministic UUIDs and fingerprints are constructed explicitly, e.g. `fingerprint="approval-fp-<n>"` so the conftest cleanup pattern can find them.
- The cleanup list in `tests/conftest.py` doubles as the registry of fixture titles — **if you add a test that inserts a `Signal`, add its title pattern there or the row leaks into later runs.**

**Location:**
- The only shared fixture is `cleanup_db_connections` in `tests/conftest.py` (autouse, async)
- All other fixtures are local to a module

**Deterministic seeding:**
- `backend/app/db/seed.py` (`seed_canonical_sources_if_needed`) and `backend/app/services/auth_service.py` (`seed_demo_users_if_needed`) are invoked at startup and by CI. Both are idempotent by design.
- `scripts/test_e2e_vertical_slice.py` seeds its own deterministic signals per role before exercising the full workflow.

## Coverage

**Requirements:** `pytest-cov>=4.1.0` is installed but **no coverage threshold is configured or enforced** — no `[tool.coverage]` section, no `.coveragerc`, no `--cov-fail-under` in CI.

**View Coverage:**
```bash
pytest --cov=app --cov-report=term-missing
```

`htmlcov/` and `.coverage` are gitignored.

## Test Types

**Unit Tests:**
- Scope: pure logic and single-class behaviour
- Approach: no DB, no network. Everything mocked. Examples: `tests/test_privacy_boundary.py`, `tests/test_gemini_provider.py`, `tests/test_confluence_semantics.py`, `tests/test_calibration_service.py`

**Integration Tests:**
- Scope: endpoints + services against a real Postgres (pgvector image in CI)
- Approach: `ASGITransport(app=app)` with real DB session, or `AsyncMock` DB where the assertion is about response shape. Examples: `tests/test_api_endpoints.py`, `tests/test_ingestion.py`, `tests/test_retrieval.py`, `tests/test_approval_workflow.py`
- Require the CI service containers (`pgvector/pgvector:pg16`, `redis:7-alpine`)

**E2E Tests:**
- Framework: **standalone Python scripts**, not a browser driver. No Playwright/Selenium.
- `scripts/test_e2e_vertical_slice.py` — logs in as each of the 6 functions, walks queue → evidence inspection → review state transitions → audit verification, and asserts terminal-state locking
- `scripts/test_demo_scenarios_e2e.py`, `scripts/test_live_ingestion_e2e.py` (network-dependent)

**Invariant / regression tests:**
- `tests/test_truthfulness_and_invariants.py` — asserts the system never fabricates data (data-mode and provenance honesty)
- `tests/test_codebase_concerns.py` — **encodes entries from `CONCERNS.md` as regression tests.** When you add a concern to CONCERNS.md, this is where its guard test belongs.
- `tests/test_failure_injection.py` — degraded-path behaviour when providers/DB fail
- `tests/test_redis_optional.py` — proves the app boots with `REDIS_URL=""` (this is the production Render posture)

**Contract tests:**
- `tests/test_contract_drift.py` plus the CI step `python scripts/export_openapi.py && git diff --exit-code frontend/types/api.ts`
- The contract's source of truth is the template **inside `scripts/export_openapi.py`**, which re-emits `frontend/types/api.ts` verbatim and writes `contracts/openapi.json`

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_privacy_gate_external_bypass_prevention(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_GROK_FALLBACK", True)
    grok = GrokProvider(api_key="mock-key")
    assert grok.validate_privacy_gate(DataClassification.PUBLIC) is True
    assert grok.validate_privacy_gate(DataClassification.CONFIDENTIAL) is False
```
`asyncio_mode = auto` means `pytest-asyncio` handles the event loop, but the explicit `@pytest.mark.asyncio` decorator is still applied for clarity on every async test.

**Error Testing:**
```python
with pytest.raises(PermissionError):
    await grok.generate_intelligence(
        evidence=["Patient record user@site.com"],
        task="Task",
        classification=DataClassification.CONFIDENTIAL,
    )
```
Typed exceptions are asserted by type; HTTP failures are asserted by status code on the `ASGITransport` response.

**Conditional/Skip:**
```python
pytest.mark.skipif(...)      # 1 usage
pytest.mark.live             # 1 usage — external services; declared in pytest.ini markers
```
Run the safe subset with `pytest -m "not live"`.

## Test Coverage Gaps

**Frontend behaviour:**
- What's not tested: every React component and all client-side logic. There is no component or interaction test of any kind.
- Risk: `frontend/lib/api.ts` (1,139 lines) performs runtime shape normalization in `frontend/lib/mappers.ts` against a hand-maintained contract; a mapper/contract divergence is only caught by `tsc`, not by behaviour.
- Priority: Medium

**Streaming (SSE) path:**
- What's not tested: `POST /api/v1/athena/stream` end-to-end. `tests/test_gemma_stream.py` covers 4 functions of local streaming, but the full Athena citation-streaming route (`backend/app/api/v1/endpoints/signals.py:1630`) has no test.
- Risk: the flagship demo surface could regress silently.
- Priority: High

**The production entrypoint's failure branch:**
- What's not tested: `backend/run.py` behaviour when `alembic upgrade head` fails — this branch is deliberately designed to still bind the port.
- `tests/test_launchers.py` covers `setup.py`/`start.py` but not this production path.
- Priority: Medium

**Scheduler backoff/jitter math:**
- What's not tested: `SourceScheduler._connector_worker_loop` timing, backoff growth, and the NewsAPI quota-preservation branch (`quota_remaining < 15`).
- Risk: quota exhaustion or hot-looping in production with no failing test.
- Priority: Medium

**Celery-style concurrency / multi-instance behaviour:**
- What's not tested: advisory-lock interaction across two concurrent scheduler instances. `try_advisory_lock` is exercised only in single-process tests.
- Priority: Low

**No coverage threshold:**
- What's not enforced: `pytest-cov` is installed but CI fails no build on coverage regression, so new untested code can land freely.
- Priority: Low

---

*Testing analysis: 2026-10-02*
