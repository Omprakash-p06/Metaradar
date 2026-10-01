# Phase 15 — Free-Tier Cloud Deployment: CONTEXT.md

**Phase:** 15 — Free-Tier Cloud Deployment (Netlify + Render + Gemini AI adapter)
**Date:** 2026-10-01
**Source:** User decisions gathered during `/gsd-plan-phase` (no discuss-phase; decisions below are LOCKED)

---

## 1. Goal

Deploy MetaRadar on free hosting: frontend on **Netlify**, backend on **free backend hosting**
(winner pre-selected: **Render**), with a **provider-agnostic cloud AI adapter** (Gemini free tier
as the initial cloud provider). Produce all repo configs needed so deployment is repeatable
from a clean checkout without committing secrets.

## 2. LOCKED Decisions (user-stated, verbatim intent preserved)

### 2.1 Hosting targets
- **Frontend → Netlify.** Verify Next.js 16.3 + React 19 compatibility with the Netlify Next.js
  runtime; configure `NEXT_PUBLIC_API_URL` (canonical — see STACK.md env-var ambiguity note)
  to point at the Render backend.
- **Backend → Render free tier** (user locked Render; researcher ranks alternatives only as
  documented fallback, plan targets Render). Account for free-tier constraints: sleep/spin-down,
  ephemeral filesystem, RAM limits, request timeouts.
- **PostgreSQL + pgvector → managed free tier with pgvector support.** Researcher picks between
  Supabase / Neon (both support pgvector); plan implements the winner. Alembic migrations must
  run cleanly against the hosted DB (`alembic upgrade head`).
- **Redis → free managed (e.g. Upstash) OR prove optional.** Backend must boot and serve core
  flows even if Redis is unavailable (verify current boot path: `backend/app/main.py` lifespan).

### 2.2 Cloud AI adapter (user-specified architecture)
- **Do NOT use Grok** — user has no remaining Grok API credits. `ENABLE_GROK_FALLBACK` stays off
  in cloud; existing Grok provider code is untouched (local/dev path only).
- **Do NOT deploy Ollama/Gemma on the free backend tier** (~2.5 GB GGUF + RAM do not fit).
- **Local Qwen / llama.rn remains the primary offline/mobile AI.** Cloud AI is an **optional
  fallback/upgrade, never a hard dependency.**
- Backend exposes a **provider-agnostic AI provider interface** so Gemini can later be replaced
  by another provider without changing application/business logic
  (extends existing `backend/app/providers/factory.py` chain, which is currently
  Local Gemma → Grok → degraded).
- **Gemini API is the initial cloud provider**, using the Gemini free tier where available.
- **Gemini API key is server-side only** (`GEMINI_API_KEY` env var); never shipped in any client.
- If `GEMINI_API_KEY` is unavailable or the cloud provider fails, the backend returns a
  **controlled AI-unavailable/degraded response** — core app functionality must not break.
- All rules, behavior policies, command validation, permissions, and execution stay
  **deterministic in the application/rule engine**. The cloud model handles **only semantic
  interpretation / planning / explanation** — it must NOT execute arbitrary actions.
- Keep the API compatible with the **existing AI command/intent schema**.
- Adapter requires: **provider timeout, rate-limit handling, structured-output validation,
  logging, and fallback handling**.
- Cloud AI is **optional through configuration** (e.g. `AI_PROVIDER=gemini`; unset/off →
  existing local/degraded chain behaves exactly as today).

## 3. Scope Fences

- **Free tiers only.** No paid services introduced by this phase. Document limits accepted
  (Render sleep, DB row/storage caps, Gemini free-tier quotas) and what breaks when hit.
- **Zero secrets in repo.** All keys/URLs via env vars; `.env.example` updated, production boot
  guard (`SECRET_KEY`/`DEMO_MODE`, `backend/app/core/config.py:140-149`) must pass on Render.
- **No behavior change locally.** `python setup.py` / `python start.py` flows keep working;
  cloud configs are additive (`netlify.toml`, `render.yaml`, backend build/start commands,
  env templates, deploy docs).
- **Security invariants preserved:** server-side RBAC, CSRF, rate limiting, security headers,
  CORS allow-list updated for the Netlify origin (no `*` in production).
- **Contract sync unchanged:** `python scripts/export_openapi.py` still passes in CI; deployment
  does not fork the API surface.
- **Tracer-first:** first plan must be an end-to-end deploy-config slice verifiable without paid
  services (e.g. production `next build` + backend boot against hosted DB + one live request
  through Netlify → Render).

## 4. Known Codebase Facts (for researcher/planner — verify, don't assume)

- Frontend: Next.js `16.3.0`, React 19, pnpm 9 preferred, `frontend/Dockerfile` exists.
- Backend: FastAPI + Uvicorn, `backend/requirements.txt` (pip, no lockfile), `backend/Dockerfile`
  (`python:3.11-slim`, non-root `appuser`), Alembic async migrations, `asyncpg`.
- Providers: `backend/app/providers/{gemma,grok,degraded,factory}.py`; config in
  `backend/app/core/config.py` (`Settings`, env aliases); embeddings via FastEmbed ONNX CPU
  (works on free tier — no GPU needed).
- Env ambiguity (STACK.md): `NEXT_PUBLIC_API_BASE_URL` (compose) vs `NEXT_PUBLIC_API_URL`
  (code) — deployment must canonically resolve which the frontend honors.
- No existing deploy configs: no `netlify.toml`, `render.yaml`, `Procfile`, `vercel.json`.
- CI gate reference: `.github/workflows/ci.yml` (pytest, tsc, banned-classes, eslint, next build).

## 5. Open Questions for Researcher (answer in RESEARCH.md)

1. Netlify + Next.js 16.3: runtime version support, SSR/dynamic-route caveats, env-var wiring.
2. Render free web service for FastAPI: build/start commands, Python version pinning, health-check
   path, disk ephemerality impact, sleep behavior + UX/docs mitigation.
3. Supabase vs Neon free tier for PG16 + pgvector 384-dim HNSW + asyncpg + Alembic — pick one
   with quota evidence.
4. Redis: Upstash free vs making Redis optional — what breaks today if Redis is down?
5. Gemini free-tier API: model choice, quotas, Python SDK vs REST, structured-output approach,
   timeout/retry guidance — design the provider-agnostic interface around it.
6. CORS/CSRF/session-cookie implications of split-origin deploy (Netlify ↔ Render):
   `SameSite`/`Secure` cookie settings, allowed origins, signed-cookie secret management.
