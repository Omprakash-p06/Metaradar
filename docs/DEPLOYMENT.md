# MetaRadar Production Deployment Guide (₹0 / $0 Free-Tier Stack)

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
   ├── Local Embeddings: sentence-transformers/all-MiniLM-L6-v2 (CPU FastEmbed)
   ├── In-Memory PII/PHI Redaction Gate (Strict Zero-Leak Boundary)
   │
   ├── LangGraph 10-Node Workflow
   │     ▼
   │   Google Gemini API (Free Tier: gemini-2.5-flash / gemini-1.5-flash)
   │     - Server-side GEMINI_API_KEY only
   │     - Automatic fallback to BART degraded mode on 429 quota exhaustion
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
| **Frontend** | Netlify | Free | **₹0** | 100 GB bandwidth/mo, 300 build mins/mo. Auto-build from GitHub via `netlify.toml`. |
| **Backend** | Render | Free Web Service | **₹0** | 512 MB RAM, 750 free instance-hours/mo. Spins down after 15m idle (takes ~50s to wake on first request). |
| **Database & Vector DB** | Supabase | Free | **₹0** | 500 MB database, native `pgvector` enabled. Pauses after 7 days inactivity. |
| **LLM Provider** | Google AI Studio | Free Tier | **₹0** | 15 RPM, 1,000,000 TPM, 1,500 RPD. Degrades gracefully if quota exhausted. |
| **Embeddings** | FastEmbed | Local CPU | **₹0** | Runs in-memory on Render CPU; no GPU needed. |
| **Redis** | In-Memory / Upstash | Optional | **₹0** | Backend boots and serves core flows with Redis disabled. |

---

## 3. Step-by-Step Deployment Instructions

### Step 1: Set Up Supabase (Database & pgvector)
1. Log into [database.new](https://database.new) (Supabase console) and create a new project (e.g. `metaradar-db`).
2. Choose a region close to your Render deployment (e.g. AWS `ap-south-1` Mumbai or `us-east-1` / `eu-central-1`).
3. Set a strong database password and copy it securely.
4. Navigate to **SQL Editor** in Supabase and run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
5. Navigate to **Project Settings** $\rightarrow$ **Database** $\rightarrow$ **Connection String**.
6. Select **URI** mode and copy the **Session Pooler** (port `5432` with IPv4 compatibility):
   ```text
   postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require
   ```
7. Run migrations and seed data from your machine:
   ```bash
   export DATABASE_URL="postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require"
   alembic upgrade head
   python backend/app/db/seed.py
   ```

---

### Step 2: Obtain Google Gemini API Key
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Generate an API Key under the **Free Tier**.
3. Confirm that the key is kept **server-side only** (injected into Render `GEMINI_API_KEY`). It must never be committed to git or exposed to the client.
4. Note on Privacy: MetaRadar's in-memory `PIIPHIScrubber` and `validate_privacy_gate()` strictly scrub clinical identifiers and patient data before payloads leave the server.

---

### Step 3: Deploy Backend on Render
1. Log into [dashboard.render.com](https://dashboard.render.com).
2. Click **New** $\rightarrow$ **Blueprint** (or **Web Service**) and connect your GitHub repository (`Omprakash-p06/Metaradar`).
3. Render will detect [`render.yaml`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/render.yaml) automatically.
4. In the Render Dashboard under **Environment Variables**, fill in the secrets marked `sync: false`:
   - `DATABASE_URL`: Your Supabase connection string (`postgresql+asyncpg://...:5432/postgres?sslmode=require`).
   - `CORS_ORIGINS`: Your Netlify site URL (e.g. `https://metaradar.netlify.app`).
   - `GEMINI_API_KEY`: Your Google AI Studio API key.
   - `APP_ENV`: `production`
   - `DEMO_MODE`: `false`
   - `SECRET_KEY`: Auto-generated 32+ character random string.
5. Deploy. The `preDeployCommand` (`alembic upgrade head`) will run automatically, and the health check will monitor `/api/v1/health`.
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
6. Copy your Netlify domain (e.g. `https://metaradar.netlify.app`) and ensure it matches the `CORS_ORIGINS` setting on Render.

---

## 4. Verification & Tracer Checklist

Verify the deployed stack end-to-end:

- [ ] **Liveness Check:** `curl https://<RENDER-SERVICE>.onrender.com/api/v1/health` returns `{"status":"ok"}` (HTTP 200).
- [ ] **Readiness & DB Check:** `curl https://<RENDER-SERVICE>.onrender.com/api/v1/health/ready` returns `{"status":"ready","database":true}`.
- [ ] **Vector Query Probe:** Test that 384-dimensional pgvector cosine search executes against Supabase without error.
- [ ] **CORS Verification:** Inspect response headers on Netlify: `Access-Control-Allow-Origin` matches your Netlify domain; `Set-Cookie` includes `SameSite=None; Secure`.
- [ ] **Cold-Start Behavior:** If Render has spun down after 15 minutes of inactivity, verify that the frontend displays the cold-start wake banner while the instance initializes.
- [ ] **Privacy Gate Assurance:** Verify that synthetic signals and public news are analyzed by Gemini, while any flagged sensitive records trigger BART degraded factual summaries.

---

## 5. Secret Rotation & Troubleshooting

- **Rotating `SECRET_KEY`:** Update `SECRET_KEY` in the Render dashboard. This will invalidate all active sessions and require users to log in again.
- **Rotating `GEMINI_API_KEY`:** Update `GEMINI_API_KEY` in Render. If omitted or expired, MetaRadar falls back to local BART degraded mode without breaking core functionality.
- **Database Re-pooling:** If connecting through Supabase Transaction Pooler (port `6543`), ensure `statement_cache_size=0` is set in asyncpg connection args. Using Session Pooler (port `5432`) is recommended to avoid prepared statement conflicts.
