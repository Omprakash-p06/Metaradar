# MetaRadar Production Deployment Runbook (₹0 / $0 Free-Tier Stack)

This runbook details how to deploy MetaRadar end-to-end using strictly free-tier hosting for public demonstration (e.g. REACH 2026 Conclave).

---

## 1. System Architecture

```text
Netlify (Next.js 16.3 + React 19 Frontend)
   │
   │ HTTPS (Cross-Origin Credentials: SameSite=None; Secure)
   ▼
Render (FastAPI + Uvicorn Backend)
   │
   ├── Local FastEmbed: sentence-transformers/all-MiniLM-L6-v2 (CPU In-Memory)
   ├── In-Memory PII/PHI Redaction Gate (Strict Zero-Leak Boundary)
   │
   ├── LangGraph 10-Node Workflow
   │     ▼
   │   Google Gemini API (Free Tier: gemini-2.5-flash)
   │     - Server-side GEMINI_API_KEY only
   │     - Automatic fallback to BART degraded mode on 429 quota exhaustion
   │     - Strictly semantic interpretation only (GENERATE_ACTIONS disabled)
   │
   └── PostgreSQL 16 Connection (Session Pooler Port 5432, sslmode=require)
         ▼
       Supabase (Free Tier: PostgreSQL 16 + native pgvector)
         - 500 MB DB storage
         - 384-dimensional HNSW cosine vector search
```

---

## 2. Cost & Tier Breakdown

| Component | Provider | Plan / Tier | Cost | Limits / Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend** | Netlify | Free | **₹0** | 100 GB bandwidth/month, 300 build mins/month. Auto-deploys via `netlify.toml`. |
| **Backend** | Render | Free Web Service | **₹0** | 512 MB RAM, 750 free instance-hours/month. Sleeps after 15m idle (~50s spin-up). |
| **Database & Vector** | Supabase | Free | **₹0** | 500 MB database, native `pgvector` enabled. Pauses after 7 days inactivity. |
| **Cloud AI Adapter** | Google AI Studio | Free Tier | **₹0** | 15 RPM, 1,000,000 TPM, 1,500 RPD. Degrades to BART if quota exhausted. |
| **Embeddings** | FastEmbed | Local CPU | **₹0** | Runs in-process on Render CPU; no GPU or remote embeddings API needed. |
| **Redis** | In-Memory / Upstash | Optional | **₹0** | Backend boots and serves core flows with Redis disabled. Upstash free tier optional. |

---

## 3. Step-by-Step Deployment Instructions

### Step 1: Set Up Supabase (Database & pgvector)
1. Log into [database.new](https://database.new) (Supabase console) and create a new project (e.g. `metaradar-prod`).
2. Select a region close to your Render deployment (e.g. AWS `ap-south-1` Mumbai, `us-east-1`, or `eu-central-1`).
3. Set a strong database password and copy it securely.
4. Navigate to **SQL Editor** in Supabase and run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
5. Navigate to **Project Settings** $\rightarrow$ **Database** $\rightarrow$ **Connection String**.
6. Select **URI** mode and copy the **Session Pooler** (port `5432` with IPv4 compatibility):
   ```text
   postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?ssl=require
   ```
   > **Note on Connection Pooling:** Use the **Session Pooler (port 5432)** rather than Transaction Pooler (port 6543) for asyncpg and Alembic migrations. Transaction pooler requires `statement_cache_size=0` to prevent prepared statement conflicts.
7. Run migrations and seed data from your machine:
   ```bash
   export DATABASE_URL="postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?ssl=require"
   alembic upgrade head
   python backend/app/db/seed.py
   ```

---

### Step 2: Obtain Google Gemini API Key
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Generate an API Key under the **Free Tier**.
3. Confirm that the key is kept **server-side only** (injected into Render `GEMINI_API_KEY`). It must never be committed to git or exposed to the client.
4. **Privacy Gate Assurance:** MetaRadar's in-memory `PIIPHIScrubber` and `validate_privacy_gate()` strictly scrub clinical identifiers, MRNs, patient names, and private data before any payload is transmitted to Google. Payloads with `PATIENT_IDENTIFIABLE`, `CONFIDENTIAL`, `INTERNAL`, or `UNKNOWN` classifications are refused before external transmission.
5. **No Action Execution:** Cloud Gemini capabilities explicitly exclude `GENERATE_ACTIONS`. Semantic interpretation and intelligence reasoning only; all rules and actions remain deterministic in application code.

---

### Step 3: Deploy Backend on Render
1. Log into [dashboard.render.com](https://dashboard.render.com).
2. Click **New** $\rightarrow$ **Blueprint** and connect your GitHub repository (`Omprakash-p06/Metaradar`).
3. Render will detect [`render.yaml`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/render.yaml) automatically.
4. In the Render Dashboard under **Environment Variables**, fill in the secrets marked `sync: false`:
   - `DATABASE_URL`: Your Supabase connection string (`postgresql+asyncpg://...:5432/postgres?ssl=require`).
   - `CORS_ORIGINS`: Your Netlify site URL (e.g. `https://metaradar-reach.netlify.app` — exact scheme + host, no wildcard).
   - `GEMINI_API_KEY`: Your Google AI Studio API key.
   - `APP_ENV`: `production`
   - `DEMO_MODE`: `false`
   - `SECRET_KEY`: A cryptographically secure random 256-bit string (`python -c "import secrets; print(secrets.token_urlsafe(32))"`).
   - `SESSION_COOKIE_SAMESITE`: `none`
   - `SESSION_COOKIE_SECURE`: `true`
5. Deploy. The `startCommand` will run database migrations (`alembic upgrade head`) automatically before launching `uvicorn`, and the health check will monitor `/api/v1/health`.
6. Once deployed, note your public Render URL (e.g. `https://metaradar-api.onrender.com`).

---

### Step 4: Deploy Frontend on Netlify
1. Log into [app.netlify.com](https://app.netlify.com).
2. Click **Add new site** $\rightarrow$ **Import an existing project** from GitHub.
3. Select your repository. Netlify will detect [`netlify.toml`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/netlify.toml).
   - **Base directory:** `frontend`
   - **Build command:** `pnpm run build`
   - **Publish directory:** `.next`
4. Under **Site configuration** $\rightarrow$ **Environment variables**, add:
   - `NEXT_PUBLIC_API_URL`: `https://<YOUR-RENDER-SERVICE>.onrender.com/api/v1`
   - `NODE_VERSION`: `20`
5. Click **Deploy site**.
6. Copy your Netlify domain (e.g. `https://metaradar-reach.netlify.app`) and verify it matches the `CORS_ORIGINS` setting on Render.

---

## 4. Free-Tier Limits, Quotas & Accepted Behaviors

### Render Free Web Service
- **Spin-Down on Idle:** After 15 minutes without requests, Render spins down the free service. The first incoming request takes ~50-60 seconds to wake the service.
- **Frontend Cold-Start Handling:** The MetaRadar frontend includes an automatic retry loop with exponential backoff on idempotent reads (`GET`) and Athena calls. Rather than showing an error toast, it retries transparently until the backend wakes.
- **Monthly Instance Hours:** 750 free instance hours per calendar month across all free services on your Render account.
- **Keep-Alive Tradeoff:** A free external pinger (e.g. UptimeRobot or cron-job.org polling `/api/v1/health` every 10 minutes) can keep Render awake during demo hours. However, running a pinger 24/7 consumes ~744 hours/month (your entire monthly allowance). **Recommended:** Turn on pinging only during the 1-2 days of your presentation or conference!

### Supabase Free Tier
- **Storage Limit:** 500 MB database storage (ample for thousands of signals and vector embeddings).
- **Auto-Pause Policy:** Inactive projects are paused after 7 days of inactivity. An unpause button in the Supabase console restores the database in ~2 minutes with zero data loss.
- **Render PostgreSQL Comparison:** Render offers a free Postgres database, but **deletes it permanently after 90 days**. Supabase was chosen specifically to avoid database destruction.

### Google Gemini Free Tier
- **Rate Limits:** 15 Requests Per Minute (RPM), 1,000,000 Tokens Per Minute (TPM), 1,500 Requests Per Day (RPD).
- **Graceful Fallback:** If the free quota is exceeded (HTTP 429), MetaRadar's `GeminiProvider` transparently catches the error and degrades to BART factual summary mode. Core platform navigation, search, and workflows never crash.

---

## 5. Critical Small-Failure Checklist

Before public presentation, review these common deployment pitfalls:

1. **Dynamic `$PORT` Binding on Render:**
   Render assigns a random port per instance via the `$PORT` environment variable. The start command must be `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Never hardcode `8000` in production start commands.
2. **Fully-Qualified `PYTHON_VERSION`:**
   Render's native Python environment requires an exact version pin (`3.13.5`). Do not specify partial versions like `3.13` or `3`.
3. **`ssl=require` on Supabase:**
   Remote connections to Supabase require SSL. The `DATABASE_URL` must include `?ssl=require` (or `?sslmode=require`).
4. **`NEXT_PUBLIC_*` Variables Baked at Build Time:**
   Next.js inlines `NEXT_PUBLIC_*` environment variables during `pnpm run build`. If you change `NEXT_PUBLIC_API_URL` in the Netlify dashboard, you **must trigger a new deployment** (Deploy $\rightarrow$ Trigger deploy) for the changes to take effect in the browser JavaScript bundle.
5. **Exact-Origin CORS (No Wildcards):**
   Pre-auth origin validation strictly checks `Origin` / `Referer` headers. Wildcards (`"*"`) are rejected by the production boot guard. Ensure `CORS_ORIGINS` on Render matches your Netlify domain exactly (`https://metaradar-reach.netlify.app`), including `https://` and without trailing slashes.
6. **SameSite=None Cookie Security:**
   Cross-origin cookies between Netlify and Render require `SameSite=None; Secure`. Modern browsers strictly reject `SameSite=None` cookies that lack the `Secure` flag. `effective_session_cookie_secure` in `config.py` enforces this automatically.

---

## 6. Secret Rotation & Maintenance

- **Rotating `SECRET_KEY`:**
  Update `SECRET_KEY` in the Render dashboard. This immediately invalidates all active sessions and CSRF tokens; users will simply be prompted to log in again.
- **Rotating `GEMINI_API_KEY`:**
  Update `GEMINI_API_KEY` in the Render dashboard. If the key is rotated, missing, or invalid, MetaRadar falls back to local BART degraded mode without breaking core functionality.
- **Upstash Redis (Optional Add-on):**
  If low-latency distributed caching is desired, create a free database at [console.upstash.com](https://console.upstash.com), copy the `rediss://` URL, and set `REDIS_URL` in Render. If unset or disabled, MetaRadar runs cleanly without Redis.

---

## 7. Local Development Guarantee

All changes made for cloud deployment are strictly additive and backward-compatible:
- Running `python start.py` locally starts PostgreSQL, Redis, FastAPI, and Next.js exactly as before.
- Local tests (`pytest`) run and pass against SQLite or local PostgreSQL.
- Local LLM inference via Ollama / Gemma 3 4B remains the default local behavior (`LLM_PROVIDER=local`).
- Grok fallback code is preserved untouched for development environments (`ENABLE_GROK_FALLBACK=false` in cloud).
