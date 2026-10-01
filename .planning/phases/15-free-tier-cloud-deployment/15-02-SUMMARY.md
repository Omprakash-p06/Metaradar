# Phase 15 Wave 2: Split-Origin Auth & Frontend Cold-Start Hardening Summary

**Executed Date:** 2026-10-01  
**Plan:** `.planning/phases/15-free-tier-cloud-deployment/15-02-PLAN.md`  
**Status:** Completed  
**Branch:** `feature/phase-15-free-tier-cloud-deployment`

---

## 1. Key Accomplishments

### Task 1: Production Cookie & CORS Hardening for Split-Origin Deploy
- **`backend/app/core/config.py`**:
  - Added `SESSION_COOKIE_SAMESITE: Optional[str] = None` setting (defaults to `"none"` in production, `"lax"` in development).
  - Added `effective_session_cookie_samesite` property to resolve `"none"`, `"lax"`, or `"strict"`.
  - Hardened `effective_session_cookie_secure` to automatically enforce `Secure=True` whenever `effective_session_cookie_samesite == "none"` (per modern browser security requirements gating `SameSite=None` behind `Secure`).
  - Strengthened `validate_production_settings()` to reject wildcard CORS origins (`"*"`) in production.
- **`backend/app/api/v1/endpoints/auth.py`**:
  - Updated `_set_auth_cookies` to use `settings.effective_session_cookie_samesite` and `settings.effective_session_cookie_secure` for `metaradar_session` and `metaradar_csrf`.
  - Updated `_clear_auth_cookies` to pass `samesite` and `secure` so cross-origin cookies in the browser jar are matched and removed.
  - Updated CSRF bootstrap endpoint (`get_csrf_token`) to issue cookies with `settings.effective_session_cookie_samesite` and `settings.effective_session_cookie_secure`.
- **Automated Tests**:
  - Added `test_cookie_samesite_and_secure_flags_configuration` in `tests/test_security.py` verifying dev vs prod defaults, explicit configurations, and `SameSite=None` forcing `Secure=True`.
  - Added `test_split_origin_login_cookies_carry_samesite_none_and_secure` in `tests/test_security.py` testing cross-origin login from Netlify origin, asserting `Set-Cookie` headers carry `samesite=none`, `secure`, and `httponly`.
  - Extended `test_production_boot_guard` in `tests/test_codebase_concerns.py` to assert that wildcard CORS origin in production raises `RuntimeError("FATAL: Wildcard CORS origin is forbidden in production.")`.

### Task 2: Frontend Cold-Start Retry & Loading States for Render Sleep
- **`frontend/lib/api.ts`**:
  - Added `BackendColdStartState` interface and `onBackendColdStart(listener)` subscription pattern for frontend components.
  - Added bounded retry loop with exponential backoff on idempotent reads (`GET`, `HEAD`, `OPTIONS`) and cold-start designated calls when encountering 502, 503, 504, or network timeout/connection errors during Render container wake-up.
  - Added client-side timeout (60s) and bounded cold-start retry with backoff on `askAthena` and `streamAthena`.
  - Preserved `credentials: 'include'` on all fetch requests for cross-site cookie attachment.
  - Preserved canonical `NEXT_PUBLIC_API_URL` resolution and existing UI styles.

---

## 2. Verification Evidence

1. **Backend Tests:**
   - Command: `pytest tests/test_auth.py tests/test_rbac.py tests/test_security.py tests/test_codebase_concerns.py`
   - Result: 36 passed in 44.14s.
   - Command: `pytest tests/test_contract_drift.py`
   - Result: 1 passed, 0 drift.
2. **Frontend Typecheck & Lint:**
   - Command: `pnpm --dir frontend exec tsc --noEmit`
   - Result: 0 errors.
   - Command: `pnpm --dir frontend run check:banned-classes`
   - Result: 0 violations across 35 files.
   - Command: `pnpm --dir frontend lint`
   - Result: 0 lint errors.
   - Command: `pnpm --dir frontend run build`
   - Result: Production build compiled successfully with Next.js Turbopack.
