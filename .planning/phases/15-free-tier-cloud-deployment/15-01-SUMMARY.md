# Phase 15 Plan 01 Summary: Free-Tier Foundation Tracer

**Phase:** 15 — Free-Tier Cloud Deployment
**Plan:** 01
**Status:** Completed & Verified
**Deliverables:**
- `netlify.toml`: Netlify build configuration for Next.js 16.3 / React 19 frontend
- `render.yaml`: Render Blueprint for FastAPI + Uvicorn backend with auto-run Alembic migrations
- `docs/DEPLOYMENT.md`: Complete zero-cost deployment runbook covering Supabase + Render + Netlify + Gemini API

---

### Executed Tasks

1. **Supabase & pgvector Configuration:**
   - Documented project setup with `CREATE EXTENSION IF NOT EXISTS vector;`.
   - Provided connection string format for Supabase IPv4-compatible Session Pooler (port `5432`).
   - Documented `alembic upgrade head` and seeding commands.

2. **Netlify Deployment Configuration (`netlify.toml`):**
   - Configured `base = "frontend"`, `publish = ".next"`, `command = "pnpm run build"`, `NODE_VERSION = "20"`.
   - Added standard security headers (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`).
   - Verified that `pnpm --dir frontend run build` completes cleanly.

3. **Render Blueprint Configuration (`render.yaml`):**
   - Configured Python 3.11.9 runtime with `pip install -r requirements.txt`.
   - Set `preDeployCommand: alembic upgrade head` to run migrations before process start.
   - Set `startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
   - Targeted `/api/v1/health` for DB-free liveness checking.
   - Configured all sensitive values with `sync: false` and auto-generated `SECRET_KEY`.

4. **Zero-Secret & Free-Tier Invariants:**
   - Verified 100% free-tier architecture (₹0 / $0).
   - Zero secrets committed to the repository.

---

### Verification
- `pnpm --dir frontend run build`: Exited 0, all routes compiled.
- `netlify.toml`, `render.yaml`, and `docs/DEPLOYMENT.md` validated.
