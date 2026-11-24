# MetaRadar Agent Instructions

These are the canonical repository rules for Codex, Claude Code, Gemini CLI, Antigravity, and any agent working in MetaRadar. `GEMINI.md`, `CLAUDE.md`, and agent entry points refer here. These files guide agent behavior; they cannot guarantee that a host loaded or obeyed them.

All agents are strictly governed by the mandatory global process standards defined in `docs/rules/`:
- **[ENGINEERING_STANDARDS.md](docs/rules/ENGINEERING_STANDARDS.md)**: Absolute non-negotiable software quality, type safety, and honest execution telemetry.
- **[DEFINITION_OF_DONE.md](docs/rules/DEFINITION_OF_DONE.md)**: Complete DoD verification matrix required before declaring any task done.
- **[DEVELOPMENT_WORKFLOW.md](docs/rules/DEVELOPMENT_WORKFLOW.md)**: Strict branch workflow (`feature/*`, `fix/*`), atomic commits, and pull requests.
- **[ARCHITECTURE_RULES.md](docs/rules/ARCHITECTURE_RULES.md)**: Approved Next.js 16 + FastAPI + PostgreSQL 16 + Local Gemma stack.
- **[TESTING_STRATEGY.md](docs/rules/TESTING_STRATEGY.md)**: Mandatory executable testing gates (TSC, ESLint, Next build, pytest, contract sync).
- **[SECURITY_STANDARDS.md](docs/rules/SECURITY_STANDARDS.md)**: Zero secret leaks, PII/PHI scrubbing, and external LLM privacy gate.
- **[CI_CD_STANDARDS.md](docs/rules/CI_CD_STANDARDS.md)**: Automated CI pipeline standards.
- **[RELEASE_PROCESS.md](docs/rules/RELEASE_PROCESS.md)**: Release verification and deployment readiness.

---

## 1. Establish project and task context

- **Read Project Memory Before Acting**: Read `.planning/STATE.md` and confirm the task belongs to the active phase. Read `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, and the applicable phase's spec, plan, research, context, and verification artifacts before implementation. Read the relevant project specifications under `docs/`.
- **Master Plan Authority**: The sole canonical and authoritative specification for this repository is [METARADAR_MASTER_PLAN_v5.0.md](docs/METARADAR_MASTER_PLAN_v5.0.md). All other documentation files are secondary historical references and must not override the Master Plan.
- **Understand the Core Value & Pipeline**: MetaRadar builds an evidence story around every clinical development in rare diseases (haemophilia pilot: Factor VIII/IX, bispecifics emicizumab/mim8, anti-TFPI concizumab/marstacimab, RNAi fitusiran, and gene therapies Hemgenix/Roctavian/Beqvez). It runs an **11-node LangGraph workflow** (`INGEST → VALIDATE → UNDERSTAND → ANALYZE (Confluence, Lifecycle, Red-Team, Missing-Signal) → SYNTHESIZE → CALIBRATE → BRIEF`) feeding the **Four-Question Framework**:
  1. *What changed?* (Near-real-time signal feed, entity tags, multi-source confluence alerts)
  2. *Why does it matter?* (Relevance breakdown, lifecycle position, red-team contradiction analysis, competitive context)
  3. *Which enterprise function should review it?* (Calibrated role-routing badges with confidence scores)
  4. *What action may be required?* (AI-suggested actions prefaced "Suggested — requires human review")
- **Inspect Reality First**: Treat planned modules as plans, not proof that source code exists. Inspect actual repository files, schemas, and endpoints before writing code.
- **Narrow Goals**: State a clear, narrow goal and identify affected files, functions, callers/callees, data contracts, configuration, and side effects before modifying code.

---

## 2. Codebase inspection, impact review & contract verification

- **Contract Synchronization Gate**:
  - Pydantic v2 schemas (`backend/app/schemas/`) and TypeScript interfaces (`frontend/types/api.ts`) must remain 100% synchronized.
  - After modifying API schemas or endpoints, run `python scripts/export_openapi.py` to regenerate the OpenAPI specification and check contract drift.
- **Frontend Quality & Banned Classes Gate**:
  - Run `node scripts/check-banned-classes.mjs` before frontend commits to enforce design tokens and forbid arbitrary unvetted styling classes.
  - Run `tsc --noEmit` and `pnpm run build` to verify zero TypeScript errors and a clean Next.js 16 build.
- **Haemophilia Domain Knowledge Layer**:
  - Domain ontology, modalities, approved assets, and Red-Team evidence rules are housed in `config/haemophilia.yaml`. Any modification to clinical rules must preserve schema compatibility and clinical accuracy.
- **Database Migrations & ORM Models**:
  - Always check `backend/app/models/` and `alembic/versions/`.
  - Schema changes require a new Alembic migration (`alembic revision --autogenerate -m "..."`) and must be tested via `alembic upgrade head`.
  - Never alter existing historical migration files unless addressing a migration chain bug.

---

## 3. Make safe, scoped changes

- **Git Branching & PR Protocol (Mandatory Rule)**:
  - **NEVER push directly to `main`**.
  - All changes must be developed on a dedicated feature or fix branch (`feature/*`, `fix/*`).
  - Keep commits atomic with conventional commit syntax (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
  - Open a Pull Request for review and merge only after CI/CD test suite succeeds.
- **Preserve Rollback Path**: Use an isolated sandbox or worktree when available. Make the smallest reviewable change and preserve a clear rollback path. Do not overwrite or revert pre-existing user work.
- **Zero Secrets Policy**:
  - Never commit `.env` files, production database connection strings, API keys (`GEMINI_API_KEY`, `NEWS_API_KEY`), credentials, or private session keys.
  - Validate that secrets are injected exclusively via environment variables or secret managers (Render / Netlify).
- **No Destructive Git Actions**: Avoid destructive Git commands (including `reset --hard`, `clean -fd`, force-pushing `main`, or broad checkout/revert commands).

---

## 4. MetaRadar engineering constraints

- **Technology Stack**:
  - **Frontend**: Next.js 16 (App Router, React 19, TypeScript, TailwindCSS 4, TanStack Query v5, Recharts, Framer Motion).
  - **Backend**: FastAPI 0.110+ (Python 3.11/3.13, Uvicorn, asyncpg, SQLAlchemy 2.0 AsyncSession, Pydantic v2).
  - **Database & Vectors**: PostgreSQL 16 + native `pgvector` extension (384-dimensional cosine distance for `sentence-transformers/all-MiniLM-L6-v2`).
  - **AI & Reasoning Layer**:
    - Default local reasoning: **Gemma 3 4B Instruct** via local LLM runtime (`LLM_PROVIDER=local`).
    - Cloud deployment adapter: **Google Gemini 2.5 Flash** (`gemini-2.5-flash`) via `GeminiProvider` (`AI_PROVIDER=gemini`).
    - Local fallback: **BART (`facebook/bart-large-cnn`)** for factual summarization (CPU-friendly, never-crash degraded mode) and **BART MNLI (`facebook/bart-large-mnli`)** for zero-shot NLI contradiction detection.
    - **Factual Summarization vs Reasoning Separation**: BART provides factual summarization only; it is NEVER reasoning-equivalent. All action recommendations are deterministic in application code; external cloud LLMs have `GENERATE_ACTIONS` strictly disabled.
- **Mandatory Privacy Gate & PII/PHI Boundary**:
  - All clinical text must pass through the in-memory `PIIPHIScrubber` and `validate_privacy_gate()` before transmission to any external AI provider.
  - Payloads classified as `PATIENT_IDENTIFIABLE`, `CONFIDENTIAL`, `INTERNAL`, or `UNKNOWN` must be blocked with an immediate privacy rejection. Only public disclosures and synthetic benchmark data are permitted for external APIs.
- **WORM Audit Trail & Governance**:
  - Append-only `audit_logs` table protected by PostgreSQL triggers (`block_audit_log_mutation`). Never attempt `UPDATE` or `DELETE` on audit records.
  - All automated actions must be labeled "Suggested — requires human review".
- **Free-Tier Cloud Resilience (Netlify + Render + Supabase)**:
  - **Cross-Origin Authentication**: Enforce `SameSite=None; Secure` cookies for split-origin requests between Netlify frontend (`https://mtradar-app.netlify.app`) and Render backend (`https://metaradar-api.onrender.com`).
  - **Cold-Start Handling**: Accommodate Render's 50s free-tier spin-up with retry loops on idempotent reads and clear user feedback.
  - **Database Auto-Pause Awareness**: Supabase free-tier databases pause after 7 days of inactivity. Handle database connection failures gracefully with diagnostic messaging rather than silent failures.
  - **Optional Redis**: The backend must boot and operate cleanly when `REDIS_URL` is empty, disabled, or unset.

---

## 5. Verify and report honestly

- **Definition of Done (DoD) Verification Matrix**:
  Before declaring any task or phase complete, verify all mandatory quality gates:
  1. **Backend Tests**: `pytest tests/` (186+ automated tests passing, 0 failures).
  2. **TypeScript Compilation**: Strict `tsc --noEmit` with 0 type errors.
  3. **Frontend Production Build**: `pnpm run build` compiling cleanly with Turbopack / Next.js 16.
  4. **Contract Verification**: `python scripts/export_openapi.py` with 0 schema drift between backend and frontend.
  5. **Banned Classes Gate**: `node scripts/check-banned-classes.mjs` scanning clean with 0 violations.
  6. **Alembic Migrations**: Schema migrations verified and applied without drift.
- **No Fabricated Telemetry or Output**:
  - Never fabricate test logs, benchmark numbers, health statuses, or mock data.
  - If a check fails, report the exact error, classify root cause, fix it, and re-verify. If an external service is unavailable, report the limitation honestly.
- **No Disabling Tests or Suppressing Warnings**:
  - Never use `ignoreBuildErrors`, `@ts-ignore`, `eslint-disable`, or silent `except: pass` to mask compilation, linting, or test failures.

---

## 6. MetaRadar Comprehensive Command & Feature Reference

### 6.1 Application Startup & Orchestration
- `python start.py`: Unified local runner (boots PostgreSQL, Redis, FastAPI backend on `:8000`, and Next.js frontend on `:3000`).
- `python start.py --mock`: Boots the full platform with mock data connectors and synthetic haemophilia signals for offline demonstration.
- `python setup.py`: Environment setup wizard checking system dependencies, Python packages, Node.js, and database connectivity.
- `docker-compose up -d`: Boots local containerized PostgreSQL 16 (with pgvector) and Redis 7.

### 6.2 Database & Migrations
- `alembic upgrade head`: Applies all pending database migrations up to the latest revision.
- `alembic current`: Shows currently applied revision.
- `alembic revision --autogenerate -m "<description>"`: Generates a new migration revision based on SQLAlchemy ORM model changes.
- `python backend/app/db/seed.py`: Seeds canonical haemophilia data sources, baseline assets, and initial audit records.

### 6.3 Testing & Quality Verification
- `pytest -v`: Executes full automated backend test suite (connectors, LangGraph nodes, privacy invariants, auth, RBAC).
- `pytest tests/test_login_credentials.py -v`: Tests role credentials and login flows.
- `pytest tests/test_privacy_gate.py -v`: Validates strict PII/PHI scrubbing and zero-leak boundaries.
- `python scripts/test_e2e_vertical_slice.py`: Executes end-to-end multi-role stakeholder calibration test.
- `node scripts/check-banned-classes.mjs`: Scans frontend code for banned or arbitrary CSS classes.
- `python scripts/export_openapi.py`: Exports OpenAPI 3.1 schema and verifies TypeScript contract synchronization.

### 6.4 Frontend Tooling
- `pnpm --prefix frontend dev`: Starts Next.js development server on `http://localhost:3000`.
- `pnpm --prefix frontend build`: Produces optimized Next.js 16 production build.
- `pnpm --prefix frontend lint`: Runs ESLint across frontend components and pages.
- `npx tsc --noEmit` (inside `frontend/`): Performs strict TypeScript static type analysis.

### 6.5 Cloud Deployment & Infrastructure
- `docs/DEPLOYMENT.md`: Comprehensive free-tier cloud deployment runbook (Netlify + Render + Supabase + Google AI Studio).
- `netlify.toml`: Netlify build and header configuration for the Next.js 16 frontend.
- `render.yaml`: Infrastructure-as-Code Blueprint for the FastAPI backend service on Render.
- **Live Netlify Production URL**: `https://mtradar-app.netlify.app/`
- **Live Render API Service**: `https://metaradar-api.onrender.com/`
