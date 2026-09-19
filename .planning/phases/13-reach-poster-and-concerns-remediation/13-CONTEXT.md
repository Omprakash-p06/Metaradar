# Phase 13 — Context & Decisions (REACH 2026 Poster & Codebase Hardening)

## Phase Overview

**Phase Title:** REACH 2026 Scientific Poster Synthesis & Codebase Concerns Remediation  
**Phase Number:** 13  
**Depends On:** Phase 12 (Hackathon MVP — COMPLETED & VERIFIED)  
**Target Branch:** `feature/phase-13-reach-poster-and-concerns`  
**Date:** 2026-09-19  
**Source Master Authorities:**
1. `poster/Guidelines for Poster Presentation _ REACH 2026 _ Final.pdf`
2. `poster/Poster Presentation Competition.pdf`
3. `poster/REACH_2026_Conclave Brochure.pdf`
4. `poster/Dr. B V Basavaraj.pdf`
5. `.planning/codebase/CONCERNS.md`
6. `.planning/codebase/INTEGRATIONS.md`

**Priority Classification:**
- **P0 (Visual & Presentation):** Standalone master SVG poster (`poster/poster.svg`) and high-resolution PNG (`poster/poster.png`) combining architecture, dataflow, responsibility matrix, and REACH/ProClin logos into a 90 cm × 120 cm layout with a <250-word abstract and 5-min presentation flow.
- **P0 (Security & Privacy):** PII/PHI second layer (clinical trial subject/patient ID denial patterns) + connector source ID normalization (`et_pharma`, `fierce_pharma`, `biopharmadive`) + UNKNOWN quarantine.
- **P1 (Platform Hardening):** Production startup guard (`APP_ENV=production` refuses boot on default `SECRET_KEY` or `DEMO_MODE=true`).
- **P1 (Ingestion Robustness):** NewsAPI UTC date calculation (`datetime.now(timezone.utc)`) to eliminate clock-skew and day-boundary quota bugs.
- **P2 (Scheduler Configuration):** Explicit scheduler intervals for RSS connectors (`biopharmadive`, `fierce_pharma`, `et_pharma`) in `config.py` and `scheduler.py`.

---

## 1. REACH 2026 Poster Competition Specifications

| Criterion | Rule / Specification | Implementation in MetaRadar |
|:---|:---|:---|
| **Event & Host** | REACH 2026 Flagship Clinical Research Conclave (ProClin Research Pvt Ltd) | Hotel Green Park, Bengaluru · Oct 05, 2026 |
| **Theme** | *Generative AI & Decentralized Clinical Trials: Transforming Clinical Research* | MetaRadar autonomous intelligence for decentralized trials & pharmacovigilance |
| **Dimensions** | Width max 90 cm & Height 120 cm (Portrait 3:4 aspect ratio) | 3402 × 4536 px at 96 DPI / 3543 × 4724 px at 100 DPI |
| **Visual Position** | Main content positioned in upper section for optimal visibility | Prominent title, affiliations, abstract, and architecture in top 45% |
| **Language** | Entire poster must be in English | 100% English scientific and operational terminology |
| **Design Style** | High contrast, large fonts, clear and concise, "Louder and Deeper" | Dark slate background (`#0B0F19`), cyan/emerald/rose accents, clean typography |
| **Abstract Limit** | Strictly ≤ 250 words | Self-contained 245-word structured abstract included on poster & submission file |
| **Time Allocation**| Strictly limited to 5 minutes oral presentation | Structured 5-stage walkthrough: Problem → Architecture → Pipeline → Governance → Impact |
| **Combined Visuals**| Combine multiple photos/diagrams into 1 SVG and convert to PNG | Base64-embedded architecture, dataflow, responsibility matrix, and conference logos |
| **Collaborator** | Dr. B V Basavaraj (M. S. Ramaiah University of Applied Sciences) | Acknowledged academic collaboration & institutional affiliation |

---

## 2. Codebase Concerns & Integrations Scope

Based on systematic findings in `.planning/codebase/CONCERNS.md` and `INTEGRATIONS.md`:

### A. PII/PHI Second Layer & Connector Normalization (`backend/app/services/pii.py`)
- **Gap:** Regex scrubber lacks clinical subject/trial identifiers (`Subject ID`, `Participant ID`, `Screening #`, `Patient Name`).
- **Gap:** `classify_payload` only checked `"fiercepharma"` (missing underscore used in `source_id = "fierce_pharma"`) and missed `"et_pharma"`.
- **Remediation:** Add clinical trial identifier regexes, fix connector list to recognize all 8 active connectors (`pubmed`, `clinical_trials`, `fda`, `ema`, `newsapi`, `biopharmadive`, `fierce_pharma`, `et_pharma`), and default unverified payloads to `UNKNOWN` (blocked by Grok privacy gate).

### B. Production Startup Guard (`backend/app/core/config.py`)
- **Gap:** Dev defaults (`SECRET_KEY = "dev-secret-change-in-production"`, `DEMO_MODE = True`) can accidentally boot in production.
- **Remediation:** Add `validate_production_settings()` hook that raises `RuntimeError` if `APP_ENV=production` with default secret key or demo mode enabled.

### C. NewsAPI UTC Clock Robustness (`backend/app/connectors/newsapi.py`)
- **Gap:** `date.today().isoformat()` uses local host timezone, causing day-boundary drift against NewsAPI's UTC quota reset.
- **Remediation:** Use `datetime.now(timezone.utc).date().isoformat()` across `fetch()`, `_window_start()`, and cursor updates.

### D. Explicit Scheduler Intervals (`backend/app/core/config.py`, `backend/app/services/scheduler.py`)
- **Gap:** Trade-press RSS connectors (`biopharmadive`, `fierce_pharma`, `et_pharma`) fell back to a hardcoded 30-min constant.
- **Remediation:** Add `SCHEDULER_BIOPHARMA_DIVE_INTERVAL_MINUTES`, `SCHEDULER_FIERCE_PHARMA_INTERVAL_MINUTES`, and `SCHEDULER_ET_PHARMA_INTERVAL_MINUTES` to settings and wire them into `_init_job_states()`.

### E. Automated Verification
- Create `tests/test_codebase_concerns.py` to assert PII clinical identifier detection, production boot refusal, UTC date formatting, and WORM audit-trigger immutability.
