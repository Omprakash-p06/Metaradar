# Codebase Concerns

**Analysis Date:** 2026-10-01

## Risk Table

| Severity | Area | Evidence path | Mitigation hint |
|----------|------|---------------|-----------------|
| High | PII/PHI scrub is regex-only, no NER; bare person names / addresses / clinical narrative pass through | `backend/app/services/pii.py:5-26` (8 patterns; `patient_name` requires literal `Patient Name:`; `clinical_subject` requires ID keyword) | Add second-layer NER or deny-list pass; default `classify_payload()` `UNKNOWN` → quarantine (already default-deny); add adversarial EV-4 cases to `tests/test_privacy_boundary.py` |
| High (impact) / Low (likelihood) | Grok hosted transmission retains data ~30d for abuse auditing; any mislabel leaks off-local | `backend/app/providers/grok.py:63-96` (`validate_privacy_gate` allow-list `PUBLIC`/`SYNTHETIC` only; default param `UNKNOWN` blocked) | Keep gate synchronous and non-bypassable; never allow-list `INTERNAL`; retain `tests/test_privacy_boundary.py` + `tests/test_codebase_concerns.py::test_synthesis_evidence_pii_classification` |
| Medium | Dual PII label conventions: `CONFIDENTIAL` (PII service) vs `PATIENT_IDENTIFIABLE` (signals endpoint) | `backend/app/services/pii.py:71` vs `backend/app/api/v1/endpoints/signals.py:1654`; enum in `backend/app/providers/base.py:20` | Converge on one blocked label; gate blocks both today (good) but converge to avoid future allow-list mistake — needs verification that gate explicitly rejects `PATIENT_IDENTIFIABLE` |
| Medium | Demo credential defaults ship in source; boot guard checks only `SECRET_KEY` + `DEMO_MODE` | `backend/app/core/config.py:35-49` (8 `DEMO_PASSWORD_*` plaintext defaults, `SECRET_KEY` dev default); guard at `backend/app/core/config.py:140-149` | Extend guard to reject default `DEMO_PASSWORD_*` and localhost `DATABASE_URL`/`REDIS_URL` in production; rotate defaults before any shared deployment |
| Medium | `signals.py` monolith (1826 lines): CRUD + RBAC + review + Athena + audit in one module | `backend/app/api/v1/endpoints/signals.py` (1826 lines); `backend/app/schemas/__init__.py` (656 lines) | Split into `signals_crud.py` / `signals_review.py` / `athena.py` behind same prefix; split schemas package; keep `tests/test_contract_drift.py` green |
| Medium | Unpinned `>=` dependency floors allow install drift | `backend/requirements.txt` (`fastapi>=0.110.0`, `langgraph>=0.2.0`, `pgvector>=0.2.5`) | Freeze with lockfile; pin `langgraph` + `pgvector` first; re-run `tests/test_provider_matrix.py` + `tests/test_retrieval.py` on bump |
| Low | Free-text log redaction misses custom key names (`xai_key`, `newsapi_key`-style) | `backend/app/core/redact.py:9-21` (`SENSITIVE_KEYS` has `grok_key` but `_KV_RE`/`_QUOTED_RE` alternation lacks `xai_key`, `newsapi_key`, `ncbi`, `openfda`) — needs verification by test | Extend regex alternation to match every credential var in `backend/app/core/config.py`; add unit test in `tests/test_security.py` |
| Low | Audit WORM defense split across DB trigger + ORM listeners; static test only, no live-DB trigger assertion | `backend/alembic/versions/014_auditlog_user_correlation.py`, `backend/app/models/__init__.py`; test `tests/test_codebase_concerns.py::test_worm_audit_trigger_ddl_integrity` reads migration file text only | Add migration-drift test asserting `trg_block_audit_log_update_delete` exists in live DB (`pg_trigger` check); document superuser break-glass; never claim 21 CFR Part 11/GxP |
| Low | `.env.example` stale: documents no `SECRET_KEY`, `APP_ENV`, `DEMO_MODE`, scheduler vars that production guard depends on | `.env.example` (28 lines; only DB/LLM/NewsAPI/CORS keys) vs `backend/app/core/config.py:34-39,122-134` | Sync `.env.example` with all operator-relevant keys (names only, empty values); keep `.env` gitignored and never quoted |

## Privacy / Security Notes (key names only — zero secrets)

- **PII scrub second layer (Phase 13 applied):** `clinical_subject` + `patient_name` patterns added, per-pattern compiled flags (`COMPILED_PATTERNS`), `None` guard, `PUBLIC_SOURCES` normalized to all 8 connectors (`pubmed`, `clinical_trials`, `fda`, `ema`, `newsapi`, `biopharmadive`, `fierce_pharma` + alias `fiercepharma`, `et_pharma`), phantom `congress` removed, unrecognized source → `UNKNOWN` (blocked). Evidence: `backend/app/services/pii.py:5-77`.
- **Grok privacy gate (default-deny):** `validate_privacy_gate()` returns True only for `PUBLIC`/`SYNTHETIC`; missing key raises `GrokUnavailableError` → BART degraded fallback. Evidence: `backend/app/providers/grok.py:63-96`, `backend/app/providers/factory.py`, `backend/app/providers/base.py` (`DataClassification`).
- **Synthesis path (Phase 13 fixed CR-02):** evidence now classified dynamically via `PIIPHIScrubber.classify_payload()` instead of hardcoded `PUBLIC`. Evidence: `backend/app/workflows/nodes/synthesize.py:123-135`. Residual dual-label note above still applies.
- **NewsAPI ingestion (Phase 13 fixed WR-01/WR-04):** UTC quota dates at `backend/app/connectors/newsapi.py:75,161`; title scrubbed + nested `article` dict sanitized (covered by `test_newsapi_parse_article_scrubs_title_and_raw_article`) — implementation not re-read this pass, test presence verified in `tests/test_codebase_concerns.py:137-166`.
- **Boot guard (Phase 13 fixed CR-01):** `validate_production_settings()` defined in `backend/app/core/config.py:140-149`, invoked at top of `lifespan()` in `backend/app/main.py:34`, tested by `test_production_boot_guard` + `test_lifespan_wires_production_boot_guard`. `start.py` wiring claimed in `13-REVIEW.md` remediation table — not re-verified this pass (needs verification).
- **Secret handling:** `.env` present (gitignored, existence only — contents never read); `.env.example` contains key names with empty secret values; no `TODO`/`FIXME`/`XXX`/`HACK` markers in `backend/` (grep clean); `SecretScrubFilter` + structlog redaction in `backend/app/core/redact.py`, `backend/app/core/logging.py`.
- **Auth/session:** bcrypt + constant-time token compare (`backend/app/core/security.py`); session cookie `HttpOnly`/`SameSite=lax`, `Secure` auto-enforced in prod via `effective_session_cookie_secure` (`backend/app/core/config.py:60-63`, `backend/app/api/v1/endpoints/auth.py`); CSRF cookie intentionally JS-readable; login rate-limit + pre-auth origin gate. No new gaps asserted — needs verification by `tests/test_auth.py`, `tests/test_rbac.py`, `tests/test_security.py`.
- **Do NOT fabricate:** no live vulnerability test was executed; items marked "needs verification" were not behaviorally confirmed.

## What Phase 13 Fixed vs Still Open

**Fixed and code-verified this pass:**

| Review finding | Fix | Evidence |
|---|---|---|
| PII clinical identifiers + connector normalization (P0) | `clinical_subject`/`patient_name` regexes, 8-connector `PUBLIC_SOURCES`, `UNKNOWN` default | `backend/app/services/pii.py:12-13,28-38,77` |
| MRN / patient-name false positives (WR-02/WR-03) | MRN requires marker; `patient_name` case-sensitive with `Patient Name:` prefix | `backend/app/services/pii.py:9,13,25` |
| `scrub()` robustness + perf (IN-02) | `None` guard, module-level `COMPILED_PATTERNS` | `backend/app/services/pii.py:17-26,48-49` |
| Production boot guard (CR-01/WR-08) | Guard function + `lifespan()` wiring + wiring test | `backend/app/core/config.py:140-149`, `backend/app/main.py:34`, `tests/test_codebase_concerns.py:88-123` |
| NewsAPI UTC clock (WR-01/WR-07) | Both quota sites UTC + behavioral `_read_quota` test | `backend/app/connectors/newsapi.py:75,161`, `tests/test_codebase_concerns.py:126-134` |
| Scheduler explicit RSS intervals (P2/IN-03) | 3 new settings + exact-mapping test | `backend/app/core/config.py:128-130`, `tests/test_codebase_concerns.py:180-200` |
| Synthesis privacy bypass (CR-02) | Dynamic `classify_payload()` in synthesize node + test | `backend/app/workflows/nodes/synthesize.py:123-135`, `tests/test_codebase_concerns.py:169-177` |
| Phantom `congress` source (IN-01) | Removed from allow-list | `backend/app/services/pii.py:28-38` (no `congress`) |
| WORM trigger regression (new) | Static DDL integrity test for migration 014 | `tests/test_codebase_concerns.py:203-211` |

**Still open / residual (from prior CONCERNS.md + review):**

1. **NER-grade PII (High):** regex-only by design; adversarial names/addresses still pass — needs verification with adversarial suite.
2. **Boot guard scope (IN-04 residual):** `None` comparison removed (verified) but extended checks (default `DEMO_PASSWORD_*`, localhost DB URLs) not added — needs verification.
3. **`start.py` guard wiring:** claimed fixed, not re-read this pass — needs verification.
4. **Live-DB audit trigger assertion:** only static file-content test exists; add `pg_trigger` live check.
5. **Prod cookie-flag test:** no frontend/staging assertion that `Secure` is set under HTTPS — needs verification.
6. **Endpoint/schema split, lockfile, quota-clock hardening:** deferred per prior doc §Recommended Next Hardening Steps items 4–6; `signals.py` still 1826 lines, `requirements.txt` still `>=` floors.
7. **Poster/pitch generator hardening (WR-05/WR-06):** claimed fixed in review table (script-relative paths, fatal-on-missing, import guard); output regenerated — not re-executed this pass, Google Fonts `@import` offline reproducibility still needs verification.

## Tech Debt

- **Oversized `signals.py` (1826 lines):** merge-conflict and regression surface. Fix: split routers behind same prefix; move PII-scrub calls into shared dependency. Files: `backend/app/api/v1/endpoints/signals.py`.
- **Growing `schemas/__init__.py` (656 lines):** contract-drift surface with `frontend/types/api.ts`. Fix: split schemas package; keep `scripts/export_openapi.py` + `tests/test_contract_drift.py` gate green.
- **Synthetic/live coexistence:** provenance depends on `data_mode`/`is_synthetic` flags on every write path. Files: `backend/app/models/__init__.py`, `frontend/lib/mappers.ts`, `frontend/components/common/DataModeBadge.tsx`. Fix: enforce enum at model + mapper + badge; invariant tests in `tests/test_truthfulness_and_invariants.py`.
- **No TODO-debt:** grep for `TODO|FIXME|XXX|HACK` across `backend/` returns zero markers — healthy, no hidden stubs.

## Known Bugs

- **None open for hackathon MVP scope:** no reproducible crashers filed; failure-injection covers provider outage, quota exhaustion, stale-cache paths. Files: `tests/test_failure_injection.py`.

## Performance Bottlenecks

- **Local Gemma 3 4B CPU inference (~2–5 tok/s):** `backend/app/providers/gemma.py`, `backend/app/core/config.py:70-76`. Path: `LLM_DEVICE=cuda:0`, reduce context/output tokens; chain degrades Gemma → Grok (gated) → BART.
- **NewsAPI quota (100 req/day):** governor pauses auto-polling when `<15` remain with 90-min backoff. Files: `backend/app/connectors/newsapi.py`, `backend/app/services/scheduler.py`, `backend/app/core/domain_config.py`.

## Fragile Areas

- **Scheduler + backoff + quota interplay:** exponential backoff + jitter + advisory locks + `backoff_minutes`; single `Semaphore(4)` choke point. Tune only via `SCHEDULER_*` in `backend/app/core/config.py:122-134`; never bypass quota read-before-fetch in `backend/app/connectors/newsapi.py:74-85`. Coverage: `tests/test_ingestion.py`, `tests/test_failure_injection.py`, `tests/test_connector_health.py`.
- **pgvector 384-dim pin:** `sentence-transformers/all-MiniLM-L6-v2` revision pinned (`backend/app/core/config.py:97-100`); never change model/dimension without full backfill. Files: `backend/app/services/embeddings.py`, `backend/app/services/embeddings_backfill.py`, `backend/app/services/vector_query.py`.
- **LangGraph 11-node chain ordering:** scrub-before-persist, validate-before-embed. Files: `backend/app/workflows/state.py`, `backend/app/workflows/graph.py`, `backend/app/workflows/runner.py`, `backend/app/workflows/nodes/validate.py`, `backend/app/workflows/nodes/embed.py`. Coverage: `tests/test_intelligence_nodes.py`, `tests/test_signal_routing_workflow.py`.

## Scaling Limits

- **Postgres vector index:** thousands of rows OK; partition by domain + date past millions.
- **Scheduler concurrency:** 8-connector fan-out behind 4 slots; path is per-tier semaphores and per-source cadence.

## Dependencies at Risk

- **`llama-cpp-python` builds:** C++ extension risk on non-standard arch; fallback is Ollama sidecar (`OLLAMA_HOST`, `OLLAMA_MODEL` in `backend/app/core/config.py:93-94`).
- **Unpinned floors:** see risk table; generate lockfile.

## Missing Critical Features

- None for hackathon MVP scope; 35 test files present including `tests/test_auth.py`, `tests/test_rbac.py`, `tests/test_security.py`, `tests/test_privacy_boundary.py`, `tests/test_codebase_concerns.py` (9 tests), `tests/test_approval_workflow.py`, `tests/test_provider_matrix.py`.

## Test Coverage Gaps

- **Adversarial PII (High):** regex suite passes by construction; no NER/adversarial cases. Files: `backend/app/services/pii.py`.
- **Audit superuser bypass (Medium):** no DB-level negative test; static DDL test only. Files: `backend/alembic/versions/014_auditlog_user_correlation.py`.
- **Prod config assertions (Medium):** no test for `Secure` cookie flag under HTTPS or extended prod-guard (demo passwords, localhost URLs). Files: `backend/app/core/config.py:55-63`.
- **Stale STATE.md pointers (Low):** `.planning/STATE.md` marks Phase 13 completed on branch `feature/phase-13-reach-poster-and-concerns` with `total_phases: 17 / completed: 14`; re-verify branch merge status and phase counts before next planning cycle — needs verification.

## Environment Configuration (key names only — zero secrets)

- `.env` present, gitignored (existence only, never read). `.env.example` key names only, secret values empty — but stale (missing `SECRET_KEY`, `APP_ENV`, `DEMO_MODE`, scheduler vars).
- Required: `DATABASE_URL`, `REDIS_URL`. Conditionally required: `NEWSAPI_KEY` (no anonymous tier → `CONFIGURATION_ERROR` via `configuration_error_for()` in `backend/app/core/config.py:152-163`); `XAI_API_KEY` only when `ENABLE_GROK_FALLBACK=true`. Optional: `NCBI_API_KEY`, `OPENFDA_API_KEY`; aliases `GROK_API_KEY`, `NEWS_API_KEY` accepted.

---

*Concerns audit: 2026-10-01*
