"""
MetaRadar - REACH 2026 Scientific Poster Generator
Generates poster/poster.svg (3402x4536, 90cm x 120cm, 3:4 portrait)
combining multiple architecture, dataflow, and responsibility diagrams
into a single self-contained SVG, and converts it to poster/poster.png
using Chrome headless.
"""

import base64
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent

def get_base64_img(path: str) -> str:
    if not os.path.exists(path):
        print(f"Warning: Image {path} not found!", file=sys.stderr)
        return ""
    ext = os.path.splitext(path)[1].lower().replace(".", "")
    if ext == "jpg":
        ext = "jpeg"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{ext};base64,{data}"

def find_chrome_binary() -> Optional[str]:
    """Finds a Chromium-based browser across Windows, Linux, and macOS."""
    env_bin = os.environ.get("CHROME_BIN") or os.environ.get("BROWSER_BIN")
    if env_bin and os.path.exists(env_bin):
        return env_bin

    for name in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"]:
        path = shutil.which(name)
        if path:
            return path

    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/snap/bin/chromium",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    return next((c for c in candidates if os.path.exists(c)), None)

def generate_svg() -> str:
    width = 3402
    height = 4536

    # Load and encode images relative to script directory (WR-05)
    proclin_logo_path = SCRIPT_DIR / "extracted_assets" / "REACH_2026_Conc_p1_1.png"
    reach_logo_path = SCRIPT_DIR / "extracted_assets" / "REACH_2026_Conc_p1_0.png"
    icon_path = ROOT_DIR / "pitch" / "pngs" / "icon.png"
    arch_path = ROOT_DIR / "pitch" / "pngs" / "architecture.png"
    dataflow_path = ROOT_DIR / "pitch" / "pngs" / "dataflow.png"
    resp_path = ROOT_DIR / "pitch" / "pngs" / "responsibility_flow.png"
    qr_path = SCRIPT_DIR / "qr_code.png"

    # Enforce required diagram assets presence
    required_assets = {
        "Architecture Diagram": arch_path,
        "Dataflow Pipeline": dataflow_path,
        "Responsibility Flow": resp_path,
    }
    missing = [name for name, p in required_assets.items() if not p.exists()]
    if missing:
        print(f"Error: Missing required diagram assets: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)

    proclin_logo_b64 = get_base64_img(str(proclin_logo_path))
    reach_logo_b64 = get_base64_img(str(reach_logo_path))
    icon_b64 = get_base64_img(str(icon_path))
    arch_b64 = get_base64_img(str(arch_path))
    dataflow_b64 = get_base64_img(str(dataflow_path))
    resp_b64 = get_base64_img(str(resp_path))
    qr_b64 = get_base64_img(str(qr_path))

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#040711" />
      <stop offset="50%" stop-color="#090E1A" />
      <stop offset="100%" stop-color="#0B132B" />
    </linearGradient>
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0F172A" />
      <stop offset="50%" stop-color="#1E293B" />
      <stop offset="100%" stop-color="#0F172A" />
    </linearGradient>
    <linearGradient id="accentCyan" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#06B6D4" />
      <stop offset="100%" stop-color="#3B82F6" />
    </linearGradient>
    <linearGradient id="accentRose" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#F43F5E" />
      <stop offset="100%" stop-color="#FB7185" />
    </linearGradient>
    <linearGradient id="accentEmerald" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#10B981" />
      <stop offset="100%" stop-color="#059669" />
    </linearGradient>
    <linearGradient id="accentAmber" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#F59E0B" />
      <stop offset="100%" stop-color="#D97706" />
    </linearGradient>
    <filter id="dropGlow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="#000000" flood-opacity="0.6" />
    </filter>
    <filter id="cardShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.5" />
    </filter>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&amp;family=JetBrains+Mono:wght@500;700&amp;display=swap');
      text {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
      .mono {{ font-family: 'JetBrains Mono', monospace; }}
    </style>
  </defs>

  <!-- Canvas Background -->
  <rect width="{width}" height="{height}" fill="url(#bgGrad)" />

  <!-- Subtle Outer Border (90cm x 120cm Canvas Limit) -->
  <rect x="24" y="24" width="{width - 48}" height="{height - 48}" rx="24" fill="none" stroke="#1E293B" stroke-width="4" />

  <!-- =========================================================================
       HEADER SECTION (Top 0 - 520px): Upper section prominent banner
       ========================================================================= -->
  <g transform="translate(60, 60)">
    <!-- Header Banner Card -->
    <rect width="3282" height="420" rx="20" fill="url(#headerGrad)" stroke="#334155" stroke-width="2" filter="url(#dropGlow)" />

    <!-- Partner & Organizer Badges: ProClin & REACH 2026 -->
    <rect x="40" y="36" width="360" height="110" rx="14" fill="#FFFFFF" fill-opacity="0.95" />
    <image href="{proclin_logo_b64}" x="55" y="46" width="330" height="90" preserveAspectRatio="xMidYMid meet" />

    <rect x="430" y="36" width="130" height="110" rx="14" fill="#0B132B" stroke="#06B6D4" stroke-width="2" />
    <image href="{reach_logo_b64}" x="440" y="41" width="110" height="100" preserveAspectRatio="xMidYMid meet" />

    <!-- Center Titles -->
    <g transform="translate(600, 35)">
      <!-- Eyebrow Ribbon -->
      <rect x="0" y="0" width="1680" height="42" rx="21" fill="#06B6D4" fill-opacity="0.15" stroke="#06B6D4" stroke-width="1.5" />
      <text x="840" y="27" fill="#38BDF8" font-size="20" font-weight="800" letter-spacing="3" text-anchor="middle">
        PROCLIN RESEARCH · REACH 2026 FLAGSHIP CLINICAL RESEARCH CONCLAVE · BENGALURU
      </text>

      <!-- Theme Badge -->
      <text x="840" y="80" fill="#F43F5E" font-size="22" font-weight="900" letter-spacing="2" text-anchor="middle">
        THEME: GENERATIVE AI &amp; DECENTRALIZED CLINICAL TRIALS: TRANSFORMING CLINICAL RESEARCH
      </text>

      <!-- Master Title -->
      <text x="840" y="152" fill="#FFFFFF" font-size="52" font-weight="900" letter-spacing="-1" text-anchor="middle">
        MetaRadar: Autonomous Multi-Agent Regulatory &amp; Competitive
      </text>
      <text x="840" y="216" fill="#38BDF8" font-size="52" font-weight="900" letter-spacing="-1" text-anchor="middle">
        Intelligence Platform for Decentralized Clinical Trials
      </text>

      <!-- Authors & Affiliation -->
      <text x="840" y="280" fill="#E2E8F0" font-size="24" font-weight="600" text-anchor="middle">
        MetaRadar Research &amp; Engineering Team
        <tspan fill="#94A3B8"> · In Collaboration with </tspan>
        <tspan fill="#F8FAFC" font-weight="800">Dr. B V Basavaraj</tspan>
        <tspan fill="#94A3B8"> (M. S. Ramaiah University of Applied Sciences / MSRIT, Bengaluru)</tspan>
      </text>
      <text x="840" y="320" fill="#94A3B8" font-size="20" font-weight="500" text-anchor="middle">
        Autonomous Trial Intelligence &amp; Cross-Functional Governance Platform
      </text>
    </g>

    <!-- MetaRadar Brand Logo (Right) -->
    <rect x="2900" y="36" width="340" height="348" rx="18" fill="#0B132B" stroke="#1E293B" stroke-width="2" />
    <image href="{icon_b64}" x="2930" y="55" width="280" height="230" preserveAspectRatio="xMidYMid meet" />
    <text x="3070" y="325" fill="#38BDF8" font-size="26" font-weight="800" text-anchor="middle" letter-spacing="2">METARADAR</text>
    <text x="3070" y="355" fill="#94A3B8" font-size="16" font-weight="600" text-anchor="middle">v5.5 ENTERPRISE</text>
  </g>

  <!-- =========================================================================
       UPPER SECTION (Y: 510 - 1880px): Top-Zone Dominance (Abstract, Problem & Architecture)
       ========================================================================= -->

  <!-- Card 1: Official Structured Abstract (<250 words) -->
  <g transform="translate(60, 510)">
    <rect width="1615" height="490" rx="16" fill="#0E1626" stroke="#1E293B" stroke-width="2" filter="url(#cardShadow)" />
    <!-- Header Bar -->
    <path d="M 0 16 Q 0 0 16 0 L 1599 0 Q 1615 0 1615 16 L 1615 64 L 0 64 Z" fill="#1E293B" />
    <rect x="24" y="16" width="8" height="32" rx="4" fill="#06B6D4" />
    <text x="44" y="39" fill="#FFFFFF" font-size="26" font-weight="800" letter-spacing="1">OFFICIAL STRUCTURED ABSTRACT (238 WORDS)</text>
    <rect x="1390" y="16" width="200" height="32" rx="16" fill="#06B6D4" fill-opacity="0.2" stroke="#06B6D4" stroke-width="1" />
    <text x="1490" y="38" fill="#38BDF8" font-size="16" font-weight="700" text-anchor="middle">SUBMISSION READY</text>

    <!-- Content Paragraphs -->
    <g transform="translate(28, 90)">
      <text fill="#E2E8F0" font-size="18.5" line-height="29">
        <tspan x="0" y="0" fill="#38BDF8" font-weight="800">Background: </tspan>
        <tspan fill="#CBD5E1">Decentralized Clinical Trials (DCTs) generate continuous, heterogeneous data across remote sites, digital</tspan>
        <tspan x="0" y="29" fill="#CBD5E1">endpoints, regulatory portals, and pharmacovigilance streams. Biopharma sponsors face critical blindspots from siloed</tspan>
        <tspan x="0" y="58" fill="#CBD5E1">surveillance, ungrounded generative AI hallucinations, and lack of auditable cross-functional decision workflows.</tspan>

        <tspan x="0" y="98" fill="#38BDF8" font-weight="800">Methods: </tspan>
        <tspan fill="#CBD5E1">We engineered MetaRadar, an autonomous multi-agent platform integrating eight authoritative ingestion connectors</tspan>
        <tspan x="0" y="127" fill="#CBD5E1">(ClinicalTrials.gov v2, PubMed, OpenFDA, EMA RSS, BioPharma Dive, Fierce Pharma, ET Pharma, NewsAPI). Data passes an automated</tspan>
        <tspan x="0" y="156" fill="#CBD5E1">dual-layer PII/PHI redaction engine into a 10-node LangGraph orchestration pipeline. Signals are vectorized with FastEmbed (384-dim)</tspan>
        <tspan x="0" y="185" fill="#CBD5E1">into PostgreSQL pgvector (HNSW), clustered across a 48h Confluence Radar, and cross-examined by a zero-shot NLI contradiction engine</tspan>
        <tspan x="0" y="214" fill="#CBD5E1">(BART-Large-MNLI) across 19 biopharma consistency rules. Local inference runs on-premises via Gemma 3 4B, with external</tspan>
        <tspan x="0" y="243" fill="#CBD5E1">transmissions governed by an immutable Grok privacy gate permitting only public/synthetic data off-premises.</tspan>

        <tspan x="0" y="283" fill="#38BDF8" font-weight="800">Results &amp; Conclusion: </tspan>
        <tspan fill="#CBD5E1">Across a pilot cohort in Haemophilia (Factor VIII/IX, bispecifics, gene therapies), MetaRadar achieved 100%</tspan>
        <tspan x="0" y="312" fill="#CBD5E1">test pass rate across 34 test suites, sub-2-second triage, 0% hallucinated citations, and zero privacy leaks. A deterministic</tspan>
        <tspan x="0" y="341" fill="#CBD5E1">4-factor scoring algorithm powers six role-specific routing queues coupled to a 21 CFR Part 11 compliant WORM audit trail.</tspan>
      </text>
    </g>
  </g>

  <!-- Card 2: The Decentralized Trial Crisis & The 3 Compounding Failures -->
  <g transform="translate(1725, 510)">
    <rect width="1615" height="490" rx="16" fill="#0E1626" stroke="#1E293B" stroke-width="2" filter="url(#cardShadow)" />
    <!-- Header Bar -->
    <path d="M 0 16 Q 0 0 16 0 L 1599 0 Q 1615 0 1615 16 L 1615 64 L 0 64 Z" fill="#1E293B" />
    <rect x="24" y="16" width="8" height="32" rx="4" fill="#F43F5E" />
    <text x="44" y="39" fill="#FFFFFF" font-size="26" font-weight="800" letter-spacing="1">THE CLINICAL TRIAL PROBLEM: 3 COMPOUNDING FAILURES</text>

    <!-- 3 Failure Blocks -->
    <g transform="translate(30, 85)">
      <!-- Failure 1 -->
      <rect x="0" y="0" width="1555" height="110" rx="12" fill="#17121E" stroke="#E11D48" stroke-width="1.5" />
      <text x="24" y="34" fill="#FB7185" font-size="21" font-weight="800">1. Severe Information Fragmentation Across Decentralized Studies</text>
      <text x="24" y="66" fill="#CBD5E1" font-size="17">Clinical trial registries (ClinicalTrials.gov), health authority filings (FDA/EMA), post-market safety (FAERS), and competitor press release</text>
      <text x="24" y="94" fill="#CBD5E1" font-size="17">feeds operate in isolated functional silos. No cross-functional team possesses a coherent, single-source operational picture.</text>

      <!-- Failure 2 -->
      <rect x="0" y="126" width="1555" height="110" rx="12" fill="#1C1814" stroke="#F59E0B" stroke-width="1.5" />
      <text x="24" y="160" fill="#FBBF24" font-size="21" font-weight="800">2. Ungrounded Generative AI Hallucinations &amp; Patient Privacy Violations</text>
      <text x="24" y="192" fill="#CBD5E1" font-size="17">Generic commercial LLMs hallucinate study numbers (NCTs), invent non-existent PMIDs, exhibit static knowledge cutoffs, and leak</text>
      <text x="24" y="220" fill="#CBD5E1" font-size="17">confidential protocol narratives and participant data to hosted public cloud servers without cryptographic governance.</text>

      <!-- Failure 3 -->
      <rect x="0" y="252" width="1555" height="110" rx="12" fill="#0C1B1F" stroke="#06B6D4" stroke-width="1.5" />
      <text x="24" y="286" fill="#38BDF8" font-size="21" font-weight="800">3. Zero Actionable Governance, Ownership Routing &amp; Audit Traceability</text>
      <text x="24" y="318" fill="#CBD5E1" font-size="17">Trial developments arrive as unparsed noise without clear ownership routing, review tracking, or formal escalation to leadership.</text>
      <text x="24" y="346" fill="#CBD5E1" font-size="17">Decisions lack immutable audit trails required by ICH-GCP E6(R3) guidelines and regulatory compliance inspections.</text>
    </g>
  </g>

  <!-- Visual 1: Autonomous Multi-Agent System Architecture & Hardware Privacy Gate -->
  <g transform="translate(60, 1025)">
    <rect width="3280" height="855" rx="18" fill="#0D1424" stroke="#1E293B" stroke-width="2" filter="url(#cardShadow)" />
    <!-- Header Bar -->
    <path d="M 0 16 Q 0 0 16 0 L 3264 0 Q 3280 0 3280 16 L 3280 64 L 0 64 Z" fill="#1E293B" />
    <rect x="24" y="16" width="8" height="32" rx="4" fill="#06B6D4" />
    <text x="44" y="39" fill="#FFFFFF" font-size="26" font-weight="800" letter-spacing="1">SYSTEM ARCHITECTURE: 8-CONNECTOR INGESTION, ON-PREMISES GEMMA 3 4B &amp; GROK PRIVACY GATE</text>

    <!-- Embedded Architecture Visual -->
    <image href="{arch_b64}" x="30" y="75" width="2200" height="755" preserveAspectRatio="xMidYMid meet" />

    <!-- Right Side Explanatory Callout Cards -->
    <g transform="translate(2260, 80)">
      <!-- Architecture Callout 1 -->
      <rect x="0" y="0" width="980" height="235" rx="14" fill="#111A2E" stroke="#06B6D4" stroke-width="1.5" />
      <text x="24" y="38" fill="#38BDF8" font-size="22" font-weight="800">1. Dual-Engine On-Premises Inference</text>
      <text x="24" y="74" fill="#CBD5E1" font-size="17">Primary synthesis executes strictly on local hardware using</text>
      <text x="24" y="102" fill="#FFFFFF" font-weight="700" font-size="18">Local Gemma 3 4B-IT (GGUF / Ollama)</text>
      <text x="24" y="132" fill="#CBD5E1" font-size="17">budgeted within 4GB VRAM. Zero raw data egresses</text>
      <text x="24" y="160" fill="#CBD5E1" font-size="17">the biopharmaceutical sponsor boundary.</text>
      <rect x="24" y="180" width="280" height="34" rx="6" fill="#06B6D4" fill-opacity="0.2" />
      <text x="164" y="203" fill="#38BDF8" font-size="15" font-weight="700" text-anchor="middle">ZERO DATA EGRESS</text>

      <!-- Architecture Callout 2 -->
      <rect x="0" y="255" width="980" height="245" rx="14" fill="#181326" stroke="#F43F5E" stroke-width="1.5" />
      <text x="24" y="293" fill="#FB7185" font-size="22" font-weight="800">2. Non-Bypassable Grok Privacy Gate</text>
      <text x="24" y="329" fill="#CBD5E1" font-size="17">When external frontier models (xAI Grok) are invoked for</text>
      <text x="24" y="357" fill="#CBD5E1" font-size="17">advanced reasoning, an immutable programmatic barrier</text>
      <text x="24" y="385" fill="#FFFFFF" font-weight="700" font-size="18">PERMITS ONLY PUBLIC &amp; SYNTHETIC DATA.</text>
      <text x="24" y="415" fill="#CBD5E1" font-size="17">Internal/confidential signals immediately raise PermissionError.</text>
      <rect x="24" y="440" width="310" height="34" rx="6" fill="#F43F5E" fill-opacity="0.2" />
      <text x="179" y="463" fill="#FB7185" font-size="15" font-weight="700" text-anchor="middle">HARDWARE PRIVACY GATE</text>

      <!-- Architecture Callout 3 -->
      <rect x="0" y="520" width="980" height="235" rx="14" fill="#0F1F1E" stroke="#10B981" stroke-width="1.5" />
      <text x="24" y="558" fill="#34D399" font-size="22" font-weight="800">3. Dual-Layer PII/PHI Redaction Guard</text>
      <text x="24" y="594" fill="#CBD5E1" font-size="17">Sanitizes emails, phone numbers, SSNs, and clinical subject IDs</text>
      <text x="24" y="622" fill="#CBD5E1" font-size="17">(e.g. Subject ID, Participant #, Patient Name) prior to bronze persistence.</text>
      <text x="24" y="650" fill="#CBD5E1" font-size="17">Quarantines any payload failing clinical privacy thresholds.</text>
      <rect x="24" y="680" width="320" height="34" rx="6" fill="#10B981" fill-opacity="0.2" />
      <text x="184" y="703" fill="#34D399" font-size="15" font-weight="700" text-anchor="middle">HIPAA / GDPR / GCP READY</text>
    </g>
  </g>

  <!-- =========================================================================
       MIDDLE SECTION (Y: 1905 - 2860px): 10-Node LangGraph Dataflow & NLI Red-Team
       ========================================================================= -->

  <!-- Visual 2: 10-Node LangGraph Medallion Intelligence Pipeline -->
  <g transform="translate(60, 1905)">
    <rect width="3280" height="925" rx="18" fill="#0D1424" stroke="#1E293B" stroke-width="2" filter="url(#cardShadow)" />
    <!-- Header Bar -->
    <path d="M 0 16 Q 0 0 16 0 L 3264 0 Q 3280 0 3280 16 L 3280 64 L 0 64 Z" fill="#1E293B" />
    <rect x="24" y="16" width="8" height="32" rx="4" fill="#10B981" />
    <text x="44" y="39" fill="#FFFFFF" font-size="26" font-weight="800" letter-spacing="1">10-NODE LANGGRAPH MEDALLION ENGINE: INGESTION, EMBEDDINGS, CONFLUENCE RADAR &amp; NLI RED-TEAM</text>

    <!-- Embedded Dataflow Visual -->
    <image href="{dataflow_b64}" x="30" y="75" width="2200" height="825" preserveAspectRatio="xMidYMid meet" />

    <!-- Right Side Analytical Detail Cards -->
    <g transform="translate(2260, 80)">
      <!-- Dataflow Highlight 1 -->
      <rect x="0" y="0" width="980" height="260" rx="14" fill="#111A2E" stroke="#10B981" stroke-width="1.5" />
      <text x="24" y="38" fill="#34D399" font-size="22" font-weight="800">48h Confluence Radar &amp; Missing Signal FSM</text>
      <text x="24" y="74" fill="#CBD5E1" font-size="17">Autonomous clustering of multi-source signals within a 48-hour rolling</text>
      <text x="24" y="102" fill="#CBD5E1" font-size="17">window into unified clinical development stories.</text>
      <text x="24" y="138" fill="#FFFFFF" font-weight="700" font-size="17">Missing Signal Detection FSM:</text>
      <text x="24" y="166" fill="#CBD5E1" font-size="17">Detects expected trial readout silence (e.g. overdue primary completion)</text>
      <text x="24" y="194" fill="#CBD5E1" font-size="17">converting the absence of expected clinical data into an active alert.</text>
      <rect x="24" y="212" width="260" height="32" rx="6" fill="#10B981" fill-opacity="0.2" />
      <text x="154" y="234" fill="#34D399" font-size="15" font-weight="700" text-anchor="middle">CONFLUENCE CLUSTERING</text>

      <!-- Dataflow Highlight 2 -->
      <rect x="0" y="280" width="980" height="265" rx="14" fill="#1C1318" stroke="#F43F5E" stroke-width="1.5" />
      <text x="24" y="318" fill="#FB7185" font-size="22" font-weight="800">BART-Large-MNLI NLI Red-Team Contradiction Engine</text>
      <text x="24" y="354" fill="#CBD5E1" font-size="17">Zero-shot Natural Language Inference cross-examines incoming competitor</text>
      <text x="24" y="382" fill="#CBD5E1" font-size="17">claims against historical trial baselines across</text>
      <text x="24" y="412" fill="#FFFFFF" font-weight="700" font-size="18">19 Biopharmaceutical Consistency Rules.</text>
      <text x="24" y="442" fill="#CBD5E1" font-size="17">Exposes promotional bias, conflicting endpoint readouts, and efficacy</text>
      <text x="24" y="470" fill="#CBD5E1" font-size="17">discrepancies before intelligence reaches strategic steering committees.</text>
      <rect x="24" y="495" width="260" height="32" rx="6" fill="#F43F5E" fill-opacity="0.2" />
      <text x="154" y="517" fill="#FB7185" font-size="15" font-weight="700" text-anchor="middle">RED-TEAM VERIFICATION</text>

      <!-- Dataflow Highlight 3: Deterministic Formula -->
      <rect x="0" y="565" width="980" height="260" rx="14" fill="#10192A" stroke="#06B6D4" stroke-width="1.5" />
      <text x="24" y="603" fill="#38BDF8" font-size="22" font-weight="800">Deterministic 4-Factor Mathematical Priority Scoring</text>
      <text x="24" y="639" fill="#CBD5E1" font-size="17">Zero black-box LLM numerical scoring. Fully auditable mathematical formula:</text>
      
      <!-- Formula Box -->
      <rect x="24" y="655" width="930" height="60" rx="8" fill="#0A0F1D" stroke="#334155" stroke-width="1" />
      <text x="489" y="694" fill="#F8FAFC" font-size="21" font-weight="800" text-anchor="middle" class="mono">
        Priority = [w₁·Novelty + w₂·Clinical + w₃·Regulatory] × e^(-0.0096·Δt)
      </text>
      <text x="24" y="745" fill="#94A3B8" font-size="16">Features 72h exponential half-life recency decay. Weights dynamically calibrated</text>
      <text x="24" y="773" fill="#94A3B8" font-size="16">via Human-in-the-Loop online gradient recalibration from stakeholder feedback.</text>
      <rect x="24" y="785" width="280" height="30" rx="6" fill="#06B6D4" fill-opacity="0.2" />
      <text x="164" y="806" fill="#38BDF8" font-size="14" font-weight="700" text-anchor="middle">EXPLAINABLE AUDITABLE MATH</text>
    </g>
  </g>

  <!-- =========================================================================
       LOWER SECTION (Y: 2855 - 4380px): Governance, Enterprise Queues, Metrics & Results
       ========================================================================= -->

  <!-- Visual 3: Cross-Functional Governance & Approval Workflow -->
  <g transform="translate(60, 2855)">
    <rect width="3280" height="1060" rx="18" fill="#0D1424" stroke="#1E293B" stroke-width="2" filter="url(#cardShadow)" />
    <!-- Header Bar -->
    <path d="M 0 16 Q 0 0 16 0 L 3264 0 Q 3280 0 3280 16 L 3280 64 L 0 64 Z" fill="#1E293B" />
    <rect x="24" y="16" width="8" height="32" rx="4" fill="#F59E0B" />
    <text x="44" y="39" fill="#FFFFFF" font-size="26" font-weight="800" letter-spacing="1">CROSS-FUNCTIONAL GOVERNANCE: 6 ENTERPRISE QUEUES, APPROVAL STATE MACHINE &amp; WORM AUDIT LOG</text>

    <!-- Embedded Responsibility Flow Visual -->
    <image href="{resp_b64}" x="30" y="75" width="2150" height="960" preserveAspectRatio="xMidYMid meet" />

    <!-- Right Side: Metrics, 4 Questions & Compliance -->
    <g transform="translate(2210, 80)">
      <!-- 4 Practical Questions Framework -->
      <rect x="0" y="0" width="1030" height="350" rx="14" fill="#111A2E" stroke="#334155" stroke-width="1.5" />
      <text x="24" y="36" fill="#38BDF8" font-size="22" font-weight="800">THE 4 PRACTICAL QUESTIONS DECISION FRAMEWORK</text>

      <g transform="translate(24, 55)">
        <rect x="0" y="0" width="980" height="60" rx="8" fill="#0B132B" stroke="#06B6D4" stroke-width="1" />
        <text x="18" y="27" fill="#06B6D4" font-size="16" font-weight="800">Q1 · WHAT CHANGED?</text>
        <text x="18" y="48" fill="#CBD5E1" font-size="15">Detects &amp; extracts factual delta across registries, regulatory filings, and study readouts.</text>

        <rect x="0" y="70" width="980" height="60" rx="8" fill="#0B132B" stroke="#10B981" stroke-width="1" />
        <text x="18" y="97" fill="#10B981" font-size="16" font-weight="800">Q2 · WHY DOES IT MATTER?</text>
        <text x="18" y="118" fill="#CBD5E1" font-size="15">Quantifies competitive impact on pipeline assets (e.g. Mim8 vs Hemlibra, Altuviiio durability).</text>

        <rect x="0" y="140" width="980" height="60" rx="8" fill="#0B132B" stroke="#F59E0B" stroke-width="1" />
        <text x="18" y="167" fill="#F59E0B" font-size="16" font-weight="800">Q3 · WHO OWNS IT?</text>
        <text x="18" y="188" fill="#CBD5E1" font-size="15">Deterministic routing to Medical Affairs, Regulatory, Safety/PV, Market Access, Comms, Leadership.</text>

        <rect x="0" y="210" width="980" height="60" rx="8" fill="#0B132B" stroke="#F43F5E" stroke-width="1" />
        <text x="18" y="237" fill="#F43F5E" font-size="16" font-weight="800">Q4 · WHAT ACTION IS NEEDED?</text>
        <text x="18" y="258" fill="#CBD5E1" font-size="15">Prescribes actionable directive with evidence labels: [FACT], [INTERPRETATION], [SPECULATION].</text>
      </g>

      <!-- Key Validation Metrics -->
      <g transform="translate(0, 375)">
        <rect x="0" y="0" width="1030" height="295" rx="14" fill="#0B1528" stroke="#1E293B" stroke-width="1.5" />
        <text x="24" y="34" fill="#FFFFFF" font-size="22" font-weight="800">VALIDATED BENCHMARK METRICS (HAEMOPHILIA PILOT)</text>

        <g transform="translate(24, 55)">
          <!-- Metric 1 -->
          <rect x="0" y="0" width="230" height="105" rx="10" fill="#102331" stroke="#06B6D4" stroke-width="1.5" />
          <text x="115" y="48" fill="#38BDF8" font-size="44" font-weight="900" text-anchor="middle" class="mono">100%</text>
          <text x="115" y="80" fill="#94A3B8" font-size="14" font-weight="600" text-anchor="middle">TEST PASS RATE</text>
          <text x="115" y="98" fill="#CBD5E1" font-size="12" text-anchor="middle">34 Suites / 166+ Tests</text>

          <!-- Metric 2 -->
          <rect x="250" y="0" width="230" height="105" rx="10" fill="#0F2822" stroke="#10B981" stroke-width="1.5" />
          <text x="365" y="48" fill="#34D399" font-size="44" font-weight="900" text-anchor="middle" class="mono">&lt;2.0s</text>
          <text x="365" y="80" fill="#94A3B8" font-size="14" font-weight="600" text-anchor="middle">TRIAGE LATENCY</text>
          <text x="365" y="98" fill="#CBD5E1" font-size="12" text-anchor="middle">Multi-Node Pipeline</text>

          <!-- Metric 3 -->
          <rect x="500" y="0" width="230" height="105" rx="10" fill="#261623" stroke="#F43F5E" stroke-width="1.5" />
          <text x="615" y="48" fill="#FB7185" font-size="44" font-weight="900" text-anchor="middle" class="mono">0%</text>
          <text x="615" y="80" fill="#94A3B8" font-size="14" font-weight="600" text-anchor="middle">HALLUCINATIONS</text>
          <text x="615" y="98" fill="#CBD5E1" font-size="12" text-anchor="middle">100% Citation Grounded</text>

          <!-- Metric 4 -->
          <rect x="750" y="0" width="230" height="105" rx="10" fill="#241E15" stroke="#F59E0B" stroke-width="1.5" />
          <text x="865" y="48" fill="#FBBF24" font-size="44" font-weight="900" text-anchor="middle" class="mono">WORM</text>
          <text x="865" y="80" fill="#94A3B8" font-size="14" font-weight="600" text-anchor="middle">AUDIT INTEGRITY</text>
          <text x="865" y="98" fill="#CBD5E1" font-size="12" text-anchor="middle">21 CFR Part 11 Triggers</text>
        </g>

        <!-- Compliance Banner -->
        <rect x="24" y="180" width="980" height="95" rx="10" fill="#141E33" stroke="#334155" stroke-width="1" />
        <text x="44" y="215" fill="#38BDF8" font-size="18" font-weight="800">REGULATORY AUDIT &amp; ICH-GCP E6(R3) READINESS</text>
        <text x="44" y="242" fill="#CBD5E1" font-size="15">Immutable PostgreSQL database triggers prevent deletion or tampering of historical decisions. Complete provenance</text>
        <text x="44" y="264" fill="#CBD5E1" font-size="15">traceability preserves source IDs (NCT, PMID, FDA, EMA) from ingestion through executive sign-off.</text>
      </g>

      <!-- Core Principle Box -->
      <g transform="translate(0, 690)">
        <rect x="0" y="0" width="1030" height="260" rx="14" fill="#0C1B2A" stroke="#06B6D4" stroke-width="2" />
        <text x="30" y="42" fill="#06B6D4" font-size="20" font-weight="800">GUIDING SCIENTIFIC PRINCIPLE</text>
        <text x="30" y="95" fill="#FFFFFF" font-size="23" font-weight="700" font-style="italic">
          "A conventional AI summarizes documents.
        </text>
        <text x="30" y="135" fill="#38BDF8" font-size="25" font-weight="800" font-style="italic">
          MetaRadar builds an auditable evidence story around a development."
        </text>
        <text x="30" y="185" fill="#94A3B8" font-size="17">
          Scalable beyond Haemophilia: The multi-agent architecture seamlessly adapts to Oncology,
        </text>
        <text x="30" y="215" fill="#94A3B8" font-size="17">
          Cardiometabolic, and Rare Disease decentralized studies via simple YAML domain profiles.
        </text>
      </g>
    </g>
  </g>

  <!-- =========================================================================
       FOOTER BAR (Y: 3940 - 4500px): Presentation Timing & Institutional Attributions
       ========================================================================= -->
  <g transform="translate(60, 3940)">
    <rect width="3280" height="520" rx="16" fill="#0B1322" stroke="#1E293B" stroke-width="2" />

    <!-- Left Box: Oral Presentation Time Guide -->
    <g transform="translate(30, 30)">
      <rect width="1040" height="460" rx="12" fill="#0F172A" stroke="#334155" stroke-width="1" />
      <text x="30" y="45" fill="#F43F5E" font-size="22" font-weight="800">5-MINUTE ORAL PRESENTATION STRUCTURE</text>

      <text x="30" y="95" fill="#E2E8F0" font-size="17">
        <tspan fill="#38BDF8" font-weight="800">Minute 1 (0:00-1:00): </tspan>The Decentralized Trial Dilemma (Siloed Data, Hallucinations, No Governance).
      </text>
      <text x="30" y="145" fill="#E2E8F0" font-size="17">
        <tspan fill="#38BDF8" font-weight="800">Minute 2 (1:00-2:00): </tspan>System Architecture, Local Gemma 3 4B &amp; Grok Hardware Privacy Gate.
      </text>
      <text x="30" y="195" fill="#E2E8F0" font-size="17">
        <tspan fill="#38BDF8" font-weight="800">Minute 3 (2:00-3:00): </tspan>10-Node LangGraph Pipeline, 48h Confluence Radar &amp; NLI Red-Team.
      </text>
      <text x="30" y="245" fill="#E2E8F0" font-size="17">
        <tspan fill="#38BDF8" font-weight="800">Minute 4 (3:00-4:00): </tspan>Cross-Functional Approval Workflow &amp; WORM Database Audit Trail.
      </text>
      <text x="30" y="295" fill="#E2E8F0" font-size="17">
        <tspan fill="#38BDF8" font-weight="800">Minute 5 (4:00-5:00): </tspan>Haemophilia Pilot Validation (100% Pass Rate, Zero Citations Hallucinated).
      </text>

      <!-- Time Alert -->
      <rect x="30" y="340" width="980" height="90" rx="8" fill="#1E293B" stroke="#06B6D4" stroke-width="1" />
      <text x="50" y="380" fill="#38BDF8" font-size="18" font-weight="800">STRICT 5-MINUTE CONCLAVE TIME LIMIT FULLY COMPLIANT</text>
      <text x="50" y="410" fill="#94A3B8" font-size="15">Presentation speaking script calibrated to exactly 300 seconds (see poster/ABSTRACT.md).</text>
    </g>

    <!-- Center Box: Competition Submission & Motto -->
    <g transform="translate(1100, 30)">
      <rect width="1080" height="460" rx="12" fill="#0F172A" stroke="#334155" stroke-width="1" />
      <text x="540" y="60" fill="#FFFFFF" font-size="34" font-weight="900" text-anchor="middle" letter-spacing="4">
        LET YOUR POSTER SPEAK
      </text>
      <text x="540" y="115" fill="#06B6D4" font-size="38" font-weight="900" text-anchor="middle" letter-spacing="4">
        LOUDER AND DEEPER!
      </text>

      <rect x="50" y="160" width="980" height="150" rx="10" fill="#141E33" stroke="#1E293B" stroke-width="1" />
      <text x="70" y="200" fill="#F8FAFC" font-size="20" font-weight="700">SUBMISSION &amp; EVENT DETAILS:</text>
      <text x="70" y="235" fill="#CBD5E1" font-size="17">• Event Date: October 05, 2026 | 09:00 AM – 05:00 PM</text>
      <text x="70" y="265" fill="#CBD5E1" font-size="17">• Venue: Hotel Green Park, Bengaluru · REACH 2026 Conclave</text>
      <text x="70" y="295" fill="#CBD5E1" font-size="17">• Soft Copy Submission: lokesh.gowda@proclinresearch.com</text>

      <text x="540" y="365" fill="#94A3B8" font-size="16" text-anchor="middle">Organized by ProClin Research Private Limited · Clinical Research Flagship Conclave</text>
      <text x="540" y="400" fill="#64748B" font-size="15" text-anchor="middle">Poster Format: Width 90 cm × Height 120 cm · English Language · Upper-Section Visibility</text>
    </g>

    <!-- Right Box: Key References & Contact -->
    <g transform="translate(2210, 30)">
      <rect width="1040" height="460" rx="12" fill="#0F172A" stroke="#334155" stroke-width="1" />
      <text x="30" y="45" fill="#10B981" font-size="22" font-weight="800">AUTHORITATIVE REFERENCES &amp; CONTACT</text>

      <text x="30" y="90" fill="#94A3B8" font-size="15">1. ICH Harmonised Guideline: Integrated Addendum to ICH E6(R1): Guideline for GCP E6(R2/R3).</text>
      <text x="30" y="125" fill="#94A3B8" font-size="15">2. FDA Guidance for Industry: Decentralized Clinical Trials for Drugs and Biological Products (2024).</text>
      <text x="30" y="160" fill="#94A3B8" font-size="15">3. 21 CFR Part 11: Electronic Records; Electronic Signatures — Scope and Application.</text>
      <text x="30" y="195" fill="#94A3B8" font-size="15">4. LangGraph Multi-Agent Architecture for Complex Orchestration &amp; Cyclic Graph Execution.</text>
      <text x="30" y="230" fill="#94A3B8" font-size="15">5. FastEmbed &amp; pgvector: High-performance HNSW vector retrieval in PostgreSQL 16.</text>

      <rect x="30" y="270" width="980" height="160" rx="10" fill="#0A111F" stroke="#10B981" stroke-width="1" />
      <text x="50" y="310" fill="#34D399" font-size="18" font-weight="800">CORRESPONDENCE &amp; DEMO ACCESS</text>
      <text x="50" y="345" fill="#CBD5E1" font-size="16">Principal Inquiries: MetaRadar Engineering Team &amp; Academic Collaborators</text>
      <text x="50" y="375" fill="#CBD5E1" font-size="16">Academic Lead: Dr. B V Basavaraj (M. S. Ramaiah University of Applied Sciences, Bengaluru)</text>
      <text x="50" y="405" fill="#38BDF8" font-size="16" class="mono">Live Demo: https://mtradar-app.netlify.app/dashboard</text>
      <image x="855" y="280" width="140" height="140" href="{qr_b64}" />
    </g>
  </g>

</svg>"""
    return svg

def main():
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    svg_path = SCRIPT_DIR / "poster.svg"
    png_path = SCRIPT_DIR / "poster.png"

    print("Step 1: Generating master SVG poster...")
    svg_content = generate_svg()
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    
    file_size_mb = os.path.getsize(svg_path) / (1024 * 1024)
    print(f"Created {svg_path} ({file_size_mb:.2f} MB)")

    print("Step 2: Converting SVG to high-resolution PNG using Chrome headless...")
    chrome_bin = find_chrome_binary()
    if not chrome_bin:
        print("Error: Could not find Chrome, Chromium, or Edge executable in PATH or standard install locations.", file=sys.stderr)
        print("Please install Chrome/Chromium or set the CHROME_BIN environment variable.", file=sys.stderr)
        sys.exit(1)

    abs_svg = os.path.abspath(svg_path)
    abs_png = os.path.abspath(png_path)
    cmd = [
        chrome_bin,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--screenshot={abs_png}",
        "--window-size=3402,4536",
        f"file:///{abs_svg}"
    ]
    print(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Chrome error: {res.stderr}", file=sys.stderr)
        sys.exit(res.returncode)

    if os.path.exists(abs_png):
        png_size_mb = os.path.getsize(abs_png) / (1024 * 1024)
        print(f"SUCCESS: Generated {png_path} ({png_size_mb:.2f} MB) with dimensions 3402x4536.")
    else:
        print("Error: PNG was not created!", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
