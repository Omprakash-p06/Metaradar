# Phase 15 — Free-Tier Cloud Deployment: RESEARCH.md

**Researched:** 2026-10-01
**Domain:** Free-tier cloud deployment (Netlify + Render + hosted Postgres/pgvector + Upstash Redis + Gemini AI adapter)
**Confidence:** MEDIUM-HIGH (live docs verified 2026-10-01; quotas marked where unverified)

Locked targets (from 15-CONTEXT.md): Frontend → Netlify. Backend → Render free tier.
No Grok. No Ollama/Gemma on cloud. Cloud AI = provider-agnostic adapter, Gemini free tier
initial provider, `AI_PROVIDER=gemini`, server-side key only, degraded fallback.

---

## Q1. Netlify + Next.js 16.3 / React 19

**Finding:** Netlify supports Next.js 13.5+ via its OpenNext adapter (`@netlify/plugin-nextjs`),
auto-installed at build time — **do NOT pin it**. App Router, SSR, ISR, RSC, Server Actions,
Middleware (Edge Function), route handlers, and `next/image` (via Image CDN) are all fully
supported with zero config.

- Sources:
  - https://docs.netlify.com/build/frameworks/framework-setup-guides/nextjs/overview/ (pub. 2026-02-04)
  - https://opennext.js.org/netlify
  - https://www.netlify.com/knowledge-base/how-to-deploy-nextjs-astro-nuxt-or-sveltekit-to-netlify/ (pub. 2026-09-08)
- **Next.js 16.3 status: UNVERIFIED for this exact version.** Docs say the adapter is "thoroughly
  tested with every Next.js release" and covers "13.5 up to the latest stable," but no source
  explicitly names 16.x. Treat as *expected-compatible, verify at build time* — the tracer plan
  (REQ-P15-12, production `next build` on Netlify) is the verification step.
- **Monorepo config (repo root ≠ frontend root):** set `base` / base directory to `frontend/`
  in Netlify UI or `netlify.toml` (`[build] base = "frontend/"`), build command `next build`
  (repo script `build`, needs pnpm — set `packageManager`/Node version; engines require
  Node ≥20.9, `.nvmrc` pins 20), publish directory `.next`.
  Source: https://opennext.js.org/netlify ("suggested build command and publish directory:
  `next build` and `.next`").
- **Env-var wiring:** `NEXT_PUBLIC_*` values are **inlined at build time** — any change needs a
  redeploy. Set `NEXT_PUBLIC_API_URL` in the Netlify UI/CLI (Builds scope), not only in
  `netlify.toml` (functions can't read `netlify.toml` vars at runtime).
  Source: Netlify knowledge-base article above (env injected at build time; redeploy required).
- **SSR/runtime caveats:**
  - SSR/ISR/API routes become Netlify Functions in the site's functions region; Middleware
    becomes an Edge Function. A **serverless-function cold start** applies on top of Render
    backend latency — keep pages that hit Render static where possible.
  - Edge-runtime SSR pages run in the functions region, not at the edge (no functionality missing).
  - **Remove any SPA catch-all redirect** (`/* /index.html 200`) — user redirects beat
    adapter routes and silently break SSR/API routes.
  - Runtime env access from SSR needs **Functions + Builds scopes**, not Builds alone.
- **Current `frontend/next.config.mjs`:** only `images.unoptimized: true` — compatible; Image CDN
  optimization stays off, which is fine (avoids extra function invocations).

## Q2. Render free web service for FastAPI/Uvicorn (Python 3.11)

- Sources: https://render.com/docs/free, https://render.com/docs/python-version,
  https://render.com/docs/blueprint-spec, https://render.com/docs/health-checks,
  https://render.com/docs/compute-plans.md
- **Free compute:** 0.1 CPU / **512 MB RAM**. 750 free instance-hours per workspace/month
  (a single always-on service consumes ~720–744 h/month — essentially the whole allowance;
  keep-alive pinging vs. letting it sleep is a real tradeoff, see Risks).
- **Sleep/spin-down:** spins down after **15 min** with no inbound traffic; spin-up takes
  **~1 min** (community reports 30–90 s for Python). Browsers see a Render loading page;
  **programmatic clients (the Netlify frontend fetch) with short timeouts will fail** — this is
  an intermittent outage for API consumers, not a cosmetic delay.
  Mitigation options: (a) document + frontend retry/loading UX on cold start, (b) external
  keep-alive ping every ~10–14 min to a cheap health route (**NOT** `/robots.txt` — Render
  answers that itself while spun down and it never wakes the service), (c) accept sleep for demo.
  Source: https://odown.com/blog/how-to-keep-a-render-free-service-from-sleeping/ (2026-08-18),
  https://runhooks.app/blog/eliminating-render-free-tier-cold-starts/ (2026-05-04).
- **Build/start commands (native Python runtime):**
  - Build: `pip install -r backend/requirements.txt` (rootDir `backend/`)
  - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` — **must bind `$PORT`**, not hardcoded 8000.
  - Codebase note: backend app lives in `backend/` with `app.main:app`; `backend/Dockerfile`
    already runs uvicorn — planner can choose `runtime: python` (simpler) or `runtime: docker`.
- **Python version pinning:** env var `PYTHON_VERSION` must be **fully qualified** (e.g.
  `PYTHON_VERSION=3.11.x` — exact patch; UNVERIFIED which 3.11.x patches Render offers, check
  dashboard at plan time). Default for recent services is 3.11+; explicit pin required for
  reproducibility. Source: https://render.com/docs/python-version
- **Health check:** Blueprint field `healthCheckPath` (default `/`). Recommend a **lightweight,
  DB-free liveness path** for both Render health checks and keep-alive pings. Codebase has
  `GET /api/v1/health` (liveness, no DB) vs `GET /api/v1/health/ready` (DB+Redis checks) —
  use `/api/v1/health` for `healthCheckPath`/pings so a sleeping DB-pool doesn't fail the check.
  (Verified in `backend/app/api/v1/endpoints/health.py:37-40` vs `:43-73`.)
- **Ephemeral disk:** all local filesystem changes lost on redeploy/restart/spin-down; **no
  persistent disks on free tier**. Impact: FastEmbed model cache re-downloads on each cold boot
  (adds seconds to first-embed latency — acceptable, but keep-alive/warmup should trigger one
  embedding at startup); file uploads, GGUF models, SQLite — none may live on disk.
- **Request timeout limit: UNVERIFIED.** No authoritative number found in Render free docs this
  session (commonly cited ~100 s upstream timeout is **[ASSUMED]** — planner must verify or
  design endpoints to respond well under 60 s; the Athena/synthesize path is the risk area).
- **Blueprint schema:** `render.yaml` at repo root; service fields: `type: web`,
  `runtime: python` (or `docker`), `rootDir: backend`, `buildCommand`, `startCommand`,
  `plan: free`, `region`, `healthCheckPath`, `envVars` (with `sync: false` for secrets),
  `preDeployCommand` available for `alembic upgrade head`. Schema:
  https://render.com/schema/render.yaml.json, ref https://render.com/docs/blueprint-spec.
- **Other free-tier limits:** no SSH/shell, no one-off jobs, no private networking for free
  services (can *send* to datastores in same region), restarts possible at any time, no SMTP
  ports (25/465/587), no reserved ports 18012/18013/19099.

## Q3. Hosted Postgres + pgvector: Neon (WINNER) vs Supabase (fallback)

**Recommendation: Neon free tier.** Decisive factor is idle behavior, which dominates a demo app:

| Dimension | Neon free | Supabase free |
|---|---|---|
| Storage | 0.5 GB/project | 500 MB DB + 1 GB file storage |
| Idle behavior | **Scales to zero after 5 min, auto-wakes on next connection in ~0.5–1 s** | **Pauses after 7 days idle; manual dashboard restore (minutes), connections fail until then** |
| Compute quota | 100 CU-hours/project/month, autoscale ≤2 CU | Dedicated Nano, always-on while active |
| Projects | up to 100 | 2 active |
| pgvector/HNSW | Yes (incl. 384-dim HNSW) | Yes (mature, well-documented) |
| Branching | 10 branches/project free, with data | Paid only |
| PG versions | 14–18 selectable | New projects PG17 (older majors until forced upgrade) |
| Price of exceeding | Compute suspends to next month; **data not deleted** | Paused; restorable ≤1 yr |

- Sources: https://neon.com/pricing, https://devops-daily.com/comparisons/neon-vs-supabase
  (2026-05-02), https://dev.to/devopsdaily/neon-vs-supabase-free-tiers-we-benchmarked-both-so-you-dont-have-to-hic
  (2026-06-22), https://stackmatchup.com/supabase-vs-supabase-vs-neon/ (2026-08-03).
- **Why Neon for MetaRadar:** auto-wake (~1 s) is invisible to the tracer flow; Supabase's
  7-day manual-restore pause breaks any demo shown monthly. 384-dim HNSW (`signals.embedding`)
  is a tiny index — 0.5 GB is ample. Alembic + asyncpg + SQLAlchemy work unchanged over the
  standard wire protocol (`postgresql+asyncpg://user:pass@<host>/<db>?sslmode=require`;
  pooled variant adds `-pooler` to endpoint hostname).
  Source: https://neon.com/docs/guides/python, https://neon.com/docs/connect/connection-pooling
- **Pooling decision (critical, planner must implement):**
  - Neon PgBouncer runs in **transaction mode** — `SET/RESET`, `LISTEN/NOTIFY`, SQL-level
    `PREPARE`, temp tables, and **session-level advisory locks are NOT supported** on pooled
    connections. Source: https://neon.com/docs/connect/connection-pooling
  - Codebase uses `pg_try_advisory_lock` in scheduler (`backend/app/db/session.py:43-60`) and
    engine `pool_size=10, max_overflow=20` (`session.py:10-17`).
  - Rule: **migrations/scheduler → direct (non-pooled) connection string; request runtime →
    pooled `-pooler` string.** asyncpg + PgBouncer transaction mode also typically needs
    prepared-statement cache disabled (`statement_cache_size=0` connect arg) — **[ASSUMED]**,
    verify against hosted DB in tracer (REQ-P15-03 `alembic upgrade head` + vector search probe).
  - Supabase fallback note: its Supavisor pooler has the same transaction-vs-session-mode
    caveat; same split-connection rule would apply.
- **pgvector enablement:** `CREATE EXTENSION IF NOT EXISTS vector;` once in the hosted DB
  SQL editor before migrations (pgvector ≥0.2.5 client already a dep).

## Q4. Redis: OPTIONAL-viable (prove it) + Upstash free as optional addon

**Codebase verdict (verified by reading source this session): Redis is NOT boot-required
and core flows already degrade gracefully.**

- `lifespan` (`backend/app/main.py:31-66`) never touches Redis: validates settings → loads
  domain config → seeds DB → starts scheduler. No Redis client at boot.
- `/health/ready` treats Redis as **non-blocking**: DB failure → `degraded`, Redis failure →
  `redis: false` + `redis_warning` string, still returns 200 (`health.py:43-73`).
- `POST /cache/clear` catches all Redis exceptions → `status="cache_unavailable"`
  (`cache.py:16-32`).
- Only 3 Redis touchpoints in backend: `health.py:59`, `cache.py:22`, `REDIS_URL` default in
  `config.py:31`. No rate-limit buckets, no session store, no queue depend on Redis
  (rate limits are in-process dicts in `deps.py:24-25`; sessions are Postgres rows).
- **Exactly what degrades without Redis:** (1) readiness reports `redis:false` + warning;
  (2) `/cache/clear` returns `cache_unavailable` (frontend CacheClearModal shows graceful
  message — planner should verify the toast path); (3) nothing else — auth, signals,
  search, pipeline, Athena all function.
- **Upstash free tier (if wired as addon):** 1 DB, 256 MB, **500K commands/month**, 10 GB
  bandwidth, TCP + REST both supported. Render free (long-lived Uvicorn) can use **TCP**
  with the existing `redis>=5.0.3` client unchanged; REST (`upstash-redis` SDK) is only
  needed for edge/serverless runtimes — NOT our case, so **no new dependency required**.
  Sources: https://upstash.com/docs/redis/overall/billing, https://upstash.com/docs/redis/features/restapi,
  https://github.com/upstash/redis-py/
- **Recommendation:** make Redis optional via config (`REDIS_URL` empty/unset → skip checks,
  log once), ship Phase 15 with **no Redis by default** (fewer free-tier moving parts), document
  Upstash as the optional addon (TCP URL format `rediss://...` + `?ssl_cert_reqs` per Upstash
  console — copy verbatim at setup time). Planner must add a task proving core flows pass with
  Redis down (REQ-P15-04).

## Q5. Gemini free-tier provider + provider-agnostic interface

- **Model choice:** `gemini-2.5-flash` as initial (`gemini-2.5-flash-lite` as documented
  quota-fallback). Free-tier quotas as of Mar 2026 (third-party extraction of official docs —
  **re-verify in AI Studio at implementation time, quotas change**):
  - 2.5 Flash: **10 RPM / 250 RPD** / 250K TPM, 1M context.
  - 2.5 Flash-Lite: **15 RPM / 1,000 RPD** / 250K TPM (highest free RPD — best fallback).
  - 2.5 Pro: 5 RPM / 100 RPD (too thin for default; document only).
  - Model `gemini-2.5-flash` GA'd 2026-06-17, retirement noted 2026-10-20 in one Cloud doc —
    **flag: confirm current stable model ID at build time.**
  - Sources: https://ai.google.dev/gemini-api/docs/rate-limits,
    https://ai.google.dev/gemini-api/docs/pricing,
    https://www.aifreeapi.com/en/posts/gemini-api-free-tier-complete-guide (2026-03-17).
- **SDK vs REST decision: REST via existing `httpx` (no new dependency).** Rationale:
  backend already uses `httpx.AsyncClient` for Grok (`grok.py:55-61`, `requirements.txt:11`
  `httpx>=0.27.0`); the official `google-genai` SDK (`google/genai`, `googleapis/python-genai`)
  would add a new dep with its own retry/timeout surface. REST endpoint
  `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=...`
  — URL shape **[ASSUMED]** (well-established, but verify against
  https://ai.google.dev/gemini-api/docs/models at implementation).
  - Official SDK facts usable if planner prefers SDK: `google-genai` supports
    `response_mime_type="application/json"` + `response_json_schema`/`response_schema`,
    `HttpOptions(timeout_ms)` + `HttpRetryOptions(attempts, initial_delay, …)` retrying
    408/429/5xx with exponential backoff+jitter (default 5 attempts).
    Sources: https://googleapis.github.io/python-genai/index.html,
    https://ai.google.dev/gemini-api/docs/troubleshooting.
- **Structured output via REST:** set `generationConfig: { responseMimeType: "application/json",
  responseSchema: {...} }` mirroring the existing intent keys (`what_changed`,
  `why_it_matters`, `primary_function`, `suggested_action`) — exact REST field names
  **UNVERIFIED this session**, validate with one live call in tracer.
- **Timeout/retry/429 pattern:** connect timeout 5 s / read timeout 60 s (match `grok.py:56-60`
  precedent); retry **only** 408/429/5xx with exponential backoff + jitter, max ~3–4 attempts,
  then raise provider-unavailable → factory falls through to degraded. RPD exhaustion (midnight
  PT reset) must surface as `fallback_reason` metadata, not an exception to the client.
- **Provider-agnostic interface sketch** (extends `backend/app/providers/factory.py:13-53`
  chain Local-Gemma → Gemini → degraded; Grok branch untouched but unreachable when
  `ENABLE_GROK_FALLBACK=false`):
  ```python
  # backend/app/providers/gemini.py (new)
  class GeminiUnavailableError(Exception): ...

  class GeminiProvider(LLMProvider):
      name = "gemini"
      capabilities = [SUMMARIZE, CLASSIFY, REASON, STRUCTURED_OUTPUT]  # NOT GENERATE_ACTIONS
      def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-flash",
                   timeout_s: float = 60.0, max_retries: int = 3): ...
      def validate_privacy_gate(self, classification) -> bool: ...  # PUBLIC/SYNTHETIC only (copy grok.py:63-74)
      async def generate_intelligence(self, evidence: list[str], task: str,
                                      classification=UNKNOWN) -> dict[str, Any]: ...
      # returns existing keys: what_changed, why_it_matters, primary_function,
      # suggested_action + model_metadata (ModelMetadataSchema, provider="gemini",
      # fallback_reason="gemma_unavailable", latency_ms)
  ```
  Config additions (`config.py`): `AI_PROVIDER: str = "auto"` (`auto|local|gemini|off`),
  `GEMINI_API_KEY`, `GEMINI_MODEL="gemini-2.5-flash"`, `GEMINI_TIMEOUT_S=60`,
  `GEMINI_MAX_RETRIES=3`. Factory rule: Gemini attempted only when
  `AI_PROVIDER in ("gemini","auto")` AND key present AND privacy gate passes; any
  `GeminiUnavailableError` → degraded (same contract as `GrokUnavailableError`).
  Cloud model handles semantic interpretation only; actions stay deterministic
  (matches `DegradedProvider` precedent: `reasoning_available/actions_available` flags +
  no `GENERATE_ACTIONS` capability on the cloud provider).
- **Privacy/compliance note:** free-tier Gemini **may use prompts/responses to improve Google
  products** (paid tier does not). The existing `validate_privacy_gate` (PUBLIC/SYNTHETIC only)
  plus PII scrubber already bounds this — keep the gate mandatory, document the tradeoff in
  deploy docs. Source: https://ai.google.dev/gemini-api/docs/pricing (free-tier rows).

## Q6. Split-origin auth (Netlify ↔ Render): CORS, cookies, CSRF

Verified against `backend/app/main.py:80-88`, `config.py:34-67`, `auth.py:45-70`, `deps.py`.

- **CORS:** `CORSMiddleware` with explicit `allow_origins=settings.cors_origins_list`,
  `allow_credentials=True` — correct shape already. Change required: `CORS_ORIGINS` env must
  list the exact Netlify origin(s) (`https://<site>.netlify.app`), **never `*`**
  (credentialed CORS forbids `*` anyway). `validate_exact_origin`/`require_preauth_origin`
  (`deps.py:38-65`) does exact scheme://host matching — Netlify origin must be added or
  **login/demo-login return 403 "Untrusted request origin"**.
- **Session cookie — MUST CHANGE for cross-origin:** `_set_auth_cookies` hardcodes
  `samesite="lax"` (`auth.py:47-64`). **SameSite=Lax cookies are NOT sent on cross-site
  `fetch` POSTs** (login POST, mutating API calls from Netlify origin to Render origin are
  cross-site). With `Lax`, the browser will not attach `metaradar_session` to API requests
  → every authenticated call 401s. **Required production change:** `SameSite=None; Secure`
  on both `metaradar_session` and `metaradar_csrf` when running split-origin
  (`Secure` already auto-true in production via `effective_session_cookie_secure`,
  `config.py:60-63` — `None` without `Secure` is rejected by browsers, so gate `None`
  behind the secure flag). Recommend a setting e.g. `SESSION_COOKIE_SAMESITE="none"` in
  production, `"lax"` locally.
- **CSRF cross-origin:** safe by design here — double-submit (cookie value == `X-CSRF-Token`
  header) + HMAC session binding (`deps.py:166-208`); CSRF cookie is `httponly=False` so the
  SPA can read and echo it. `credentials: "include"` already set in frontend client
  (per INTEGRATIONS.md §Inter-Service Contracts). No CSRF redesign needed once cookies flow.
- **Secret management:** session/CSRF signing uses `SECRET_KEY` — production guard already
  enforced (`config.py:140-149` raises on default key or `DEMO_MODE=true`); Render env must set
  a generated `SECRET_KEY`, `APP_ENV=production`, `DEMO_MODE=false` (REQ-P15-05). Same
  `SECRET_KEY` must be stable across deploys (rotating invalidates all sessions — acceptable,
  document it).
- **Bearer fallback exists:** `get_current_user`/`get_optional_user` accept
  `Authorization: Bearer` (`deps.py:96-99`) — useful tracer fallback, but cookies remain primary.

## Q7. Env-var ambiguity: canonical winner

**Winner: `NEXT_PUBLIC_API_URL`. Evidence (grep, 4 hits, 2026-10-01):**

| Location | Variable used |
|---|---|
| `frontend/lib/api.ts:171` | `process.env.NEXT_PUBLIC_API_URL \|\| 'http://localhost:8000/api/v1'` — **the only var the shipped client reads** |
| `frontend/components/metaradar.tsx:1107` | `process.env.NEXT_PUBLIC_API_URL` (error fallback text) |
| `start.py:283` | injects `NEXT_PUBLIC_API_URL` for local dev |
| `docker-compose.yml:102` | sets `NEXT_PUBLIC_API_BASE_URL` — **dead value, read by nothing** |

No other `NEXT_PUBLIC_API_BASE_URL` readers exist. **Deployment resolves to
`NEXT_PUBLIC_API_URL` pointing at the Render backend** (e.g.
`https://<svc>.onrender.com/api/v1`); `docker-compose.yml:102` should be corrected to the
canonical name as a drive-by so local compose matches production.

---

## RECOMMENDED SETUP

| Service | Tier / choice | Config pointer |
|---|---|---|
| Frontend | **Netlify**, free, OpenNext adapter auto (don't pin) | `netlify.toml`: `base=frontend/`, `command="pnpm build"` (or `npm run build` fallback), `publish=".next"`, Node 20; `NEXT_PUBLIC_API_URL=https://<render-svc>.onrender.com/api/v1` in Netlify env (redeploy after change) |
| Backend | **Render** free web service, `runtime: python`, `plan: free`, region Oregon (or nearest) | `render.yaml`: `rootDir: backend`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, `PYTHON_VERSION=3.11.x` (fully qualified), `healthCheckPath: /api/v1/health`, `preDeployCommand: alembic upgrade head` |
| Postgres + pgvector | **Neon** free (0.5 GB, 100 CU-h/mo, auto-wake) | `CREATE EXTENSION vector;` once; runtime `DATABASE_URL` = pooled `-pooler` asyncpg URL `?sslmode=require`; migrations/scheduler = direct URL; pgBouncer-tx caveats per Q3 |
| Redis | **None by default** (proven optional); Upstash free TCP as opt-in addon | `REDIS_URL` unset → skip-with-warning; optional `rediss://` Upstash URL, existing `redis` client unchanged |
| Cloud AI | **Gemini** `gemini-2.5-flash` via `httpx` REST, `AI_PROVIDER=gemini`, Lite as quota fallback | `GEMINI_API_KEY` server-side only; timeout 60 s; retry 408/429/5xx ≤3–4; JSON schema validation; failure → degraded payload |
| Auth/CORS | SameSite=None+Secure cookies; exact-origin allow-list | `CORS_ORIGINS=https://<site>.netlify.app`; `SECRET_KEY` generated; `APP_ENV=production`; `DEMO_MODE=false` |
| Fallback ranking | DB fallback: Supabase free. Backend: Render-only per locked decision; any alternative is planner-escalated only if Render proves unviable | — |

## RISKS / GOTCHAS

1. **Render sleep × Netlify fetch timeouts** — first request after 15 min idle takes ~60 s;
   frontend must show loading/retry state, not an error toast. Keep-alive ping (≤14 min interval,
   to `/api/v1/health`, never `/robots.txt`) consumes most of the 750 h/month allowance — one
   service kept awake 24/7 ≈ the whole budget.
2. **Next.js 16.3 on Netlify adapter** — expected-compatible, not explicitly confirmed; tracer
   build is the proof gate.
3. **Neon pooled-tx vs advisory locks/prepared statements** — wrong connection string choice
   breaks scheduler/migrations at runtime, not at import; tracer must exercise both paths.
4. **SameSite=Lax default breaks ALL cookie auth cross-origin** — the single highest-probability
   "deployed but login loops" bug; fix in first plan.
5. **Gemini free quotas are thin and mutable** (Flash 250 RPD; data used for product
   improvement) — degraded path is the norm under load, not the exception; 429/RPD-exhausted
   handling must be first-class. Re-verify quotas in AI Studio at build time.
6. **`$PORT` binding, fully-qualified `PYTHON_VERSION`, `?sslmode=require`** — three
   small misconfigurations that each cause total deploy failure; checklist them in deploy docs.
7. **Ephemeral disk** — FastEmbed cache re-download per cold boot; no uploads/models on disk.
8. **`NEXT_PUBLIC_*` baked at build** — pointing frontend at a new backend URL requires
   Netlify rebuild, not just env edit.
9. **Exact-origin pre-auth check** — missing Netlify origin in `CORS_ORIGINS` = 403 on login
   with a misleading "untrusted origin" message; include in smoke-test steps.
10. **Free-tier data-loss asymmetry** — Neon exceeding limits suspends compute (data kept);
    Supabase pause restores ≤1 yr; Render free Postgres (NOT chosen) deletes at day 91 —
    do not accept Render Postgres if offered in dashboard flows.

## OPEN QUESTIONS (genuine unknowns only)

1. **Render inbound request timeout value** — not found in official free docs this session.
   *Planner decides:* time-box a docs check; else design all endpoints <60 s and add a
   client-side timeout+retry on Athena calls.
2. **Exact Render-available `PYTHON_VERSION` 3.11.x patch + default version for new services** —
   dashboard-dependent. *Planner decides:* read at Blueprint creation, pin fully qualified.
3. **Gemini REST `responseSchema` field shape + current stable model ID / retirement dates** —
   re-verify at implementation with one live call; keep model ID in env (`GEMINI_MODEL`).
4. **asyncpg + Neon pooler prepared-statement behavior for our SQLAlchemy version** — verify in
   tracer with pooled URL; fallback is direct URL everywhere (simpler, slightly fewer
   connections).
5. **Netlify free-tier bandwidth/functions budget for this workload** — not researched (no
   requirement cited a limit). *Planner decides:* add docs note; revisit only if build warnings
   or bills appear.

## Sources (all fetched 2026-10-01)

- Netlify Next.js support: https://docs.netlify.com/build/frameworks/framework-setup-guides/nextjs/overview/
- Netlify OpenNext adapter: https://opennext.js.org/netlify
- Netlify SSR/env/redirect gotchas: https://www.netlify.com/knowledge-base/how-to-deploy-nextjs-astro-nuxt-or-sveltekit-to-netlify/
- Render free tier: https://render.com/docs/free
- Render Python version: https://render.com/docs/python-version
- Render Blueprint spec: https://render.com/docs/blueprint-spec (+ schema https://render.com/schema/render.yaml.json)
- Render health checks: https://render.com/docs/health-checks
- Render compute plans: https://render.com/docs/compute-plans.md
- Render sleep analysis: https://odown.com/blog/how-to-keep-a-render-free-service-from-sleeping/
- Render cold-start mitigation: https://runhooks.app/blog/eliminating-render-free-tier-cold-starts/
- Neon pricing/free: https://neon.com/pricing
- Neon pooling (transaction mode): https://neon.com/docs/connect/connection-pooling
- Neon SQLAlchemy/Neon Python: https://neon.com/docs/guides/sqlalchemy, https://neon.com/docs/guides/python
- Neon vs Supabase benchmarks: https://dev.to/devopsdaily/neon-vs-supabase-free-tiers-we-benchmarked-both-so-you-dont-have-to-hic, https://devops-daily.com/comparisons/neon-vs-supabase, https://stackmatchup.com/supabase-vs-supabase-vs-neon/
- Upstash billing/free: https://upstash.com/docs/redis/overall/billing
- Upstash REST vs TCP: https://upstash.com/docs/redis/features/restapi, https://github.com/upstash/redis-py/
- Gemini rate limits: https://ai.google.dev/gemini-api/docs/rate-limits
- Gemini pricing/free tier: https://ai.google.dev/gemini-api/docs/pricing
- Gemini models: https://ai.google.dev/gemini-api/docs/models
- Gemini SDK structured output/retry: https://googleapis.github.io/python-genai/index.html, https://ai.google.dev/gemini-api/docs/troubleshooting
- Codebase (read this session): `backend/app/main.py:31-88`, `backend/app/core/config.py`,
  `backend/app/core/security.py`, `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/auth.py:45-70`,
  `backend/app/api/v1/endpoints/health.py:37-73`, `backend/app/api/v1/endpoints/cache.py`,
  `backend/app/db/session.py:10-60`, `backend/app/providers/{base,factory,grok,degraded}.py`,
  `frontend/lib/api.ts:171`, `frontend/components/metaradar.tsx:1107`, `start.py:283`,
  `docker-compose.yml:102`, `frontend/next.config.mjs`, `.env.example`

## Metadata

- Standard stack: MEDIUM-HIGH — all service picks verified against live 2026 docs; three
  items explicitly unverified (Next 16.3 adapter naming, Render timeout, Gemini REST field shape).
- Architecture: HIGH — cookie/CORS/pooling findings verified by reading the actual source lines.
- Quotas: MEDIUM — free-tier numbers sourced from official docs/benchmarks but subject to
  provider change; each carries a re-verify pointer.
- **Valid until:** ~30 days (re-check Gemini quotas + Netlify adapter release notes before planning
  if stale).
