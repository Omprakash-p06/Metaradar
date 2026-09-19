#!/usr/bin/env python3
"""
Generate the Master MetaRadar Pitch Deck (.pptx)
Novo Nordisk GBS Hackathon 2026 — Problem Statement #3: Rare Disease Competitive Intelligence Radar
Style: Swiss Professional High-Contrast Dark Theme with Pure Absolute Positioning
"""

import os
from pathlib import Path
import sys

try:
    import pptx
    from pptx.util import Inches, Pt
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
except ImportError:
    print("Error: python-pptx is required to generate the pitch deck.", file=sys.stderr)
    print("Please install python-pptx using: pip install python-pptx", file=sys.stderr)
    sys.exit(1)

# --- Color Constants ---
BG_COLOR = RGBColor(11, 15, 25)          # #0B0F19 - Deep Navy
CARD_BG = RGBColor(17, 24, 39)           # #111827 - Surface Dark Slate
CARD_BORDER = RGBColor(30, 41, 59)       # #1E293B - Card Border
CARD_HOVER = RGBColor(24, 33, 53)        # #182135 - Elevated Surface
ACCENT_RED = RGBColor(255, 59, 96)       # #FF3B60 - MetaRadar Red
ACCENT_ROSE = RGBColor(225, 29, 72)      # #E11D48 - Deep Red
TEXT_WHITE = RGBColor(248, 250, 252)     # #F8FAFC - Heading White
TEXT_MUTED = RGBColor(148, 163, 184)     # #94A3B8 - Slate Muted
TEXT_BODY = RGBColor(226, 232, 240)      # #E2E8F0 - Body Light Grey
SUCCESS_GREEN = RGBColor(16, 185, 129)   # #10B981 - Success Green
WARNING_AMBER = RGBColor(245, 158, 11)   # #F59E0B - Warning Amber
HIGHLIGHT_CYAN = RGBColor(6, 182, 212)   # #06B6D4 - Tech Cyan

FONT_HEADING = "Segoe UI"
FONT_BODY = "Segoe UI"

ROOT_DIR = Path(__file__).resolve().parent.parent
PITCH_DIR = ROOT_DIR / "pitch"
PNGS_DIR = PITCH_DIR / "pngs"

def create_presentation():
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    icon_path = str(PNGS_DIR / "icon.png")
    arch_path = str(PNGS_DIR / "architecture.png")
    dataflow_path = str(PNGS_DIR / "dataflow.png")
    resp_path = str(PNGS_DIR / "responsibility_flow.png")

    for name, p in [
        ("Icon", icon_path),
        ("Architecture", arch_path),
        ("Dataflow", dataflow_path),
        ("Responsibility Flow", resp_path),
    ]:
        if not os.path.exists(p):
            print(f"Warning: Diagram asset '{name}' not found at {p}. Slide cards will omit image.", file=sys.stderr)

    def add_slide_base(slide_num, eyebrow_text, title_text, badge_text="Problem Statement #3 · Rare Disease"):
        slide = prs.slides.add_slide(blank_layout)
        
        # 1. Dark Background Fill
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.fill.background()

        # 2. MetaRadar Logo in Header
        if os.path.exists(icon_path):
            slide.shapes.add_picture(icon_path, Inches(0.6), Inches(0.35), Inches(0.65), Inches(0.65))

        # 3. Slide Eyebrow & Title Frame
        title_box = slide.shapes.add_textbox(Inches(1.35), Inches(0.32), Inches(8.8), Inches(0.72))
        tf = title_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p_eye = tf.paragraphs[0]
        p_eye.text = eyebrow_text.upper()
        p_eye.font.name = FONT_HEADING
        p_eye.font.size = Pt(9.5)
        p_eye.font.bold = True
        p_eye.font.color.rgb = ACCENT_RED
        p_eye.space_after = Pt(2)

        p_title = tf.add_paragraph()
        p_title.text = title_text
        p_title.font.name = FONT_HEADING
        p_title.font.size = Pt(17.5)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_WHITE

        # 4. Top Right Track Badge
        badge_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10.25), Inches(0.42), Inches(2.48), Inches(0.38))
        badge_box.fill.solid()
        badge_box.fill.fore_color.rgb = CARD_BG
        badge_box.line.color.rgb = CARD_BORDER
        badge_box.line.width = Pt(1)
        tf_b = badge_box.text_frame
        tf_b.margin_left = tf_b.margin_top = tf_b.margin_right = tf_b.margin_bottom = 0
        p_b = tf_b.paragraphs[0]
        p_b.text = badge_text
        p_b.alignment = PP_ALIGN.CENTER
        p_b.font.name = FONT_HEADING
        p_b.font.size = Pt(8.5)
        p_b.font.bold = True
        p_b.font.color.rgb = TEXT_MUTED

        # 5. Header Divider Line
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.15), Inches(12.133), Inches(0.015))
        line.fill.solid()
        line.fill.fore_color.rgb = CARD_BORDER
        line.line.fill.background()

        # 6. Bottom Footer
        foot_box = slide.shapes.add_textbox(Inches(0.6), Inches(7.08), Inches(12.133), Inches(0.3))
        tf_f = foot_box.text_frame
        tf_f.margin_left = tf_f.margin_top = tf_f.margin_right = tf_f.margin_bottom = 0
        p_f = tf_f.paragraphs[0]
        p_f.text = f"MetaRadar v5.1 — Autonomous Competitive Intelligence Radar | MS Ramaiah Institute of Technology (MSRIT) Bangalore                                Slide {slide_num} of 7"
        p_f.font.name = FONT_BODY
        p_f.font.size = Pt(8.5)
        p_f.font.color.rgb = TEXT_MUTED

        return slide

    def add_card(slide, left, top, width, height, bg_rgb=CARD_BG, border_rgb=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = bg_rgb
        card.line.color.rgb = border_rgb
        card.line.width = Pt(1.2)
        return card

    # =========================================================================
    # SLIDE 1: Team & Project Overview
    # =========================================================================
    s1 = add_slide_base(1, "Novo Nordisk GBS Hackathon 2026 · Problem Statement #3", "MetaRadar: Autonomous Rare Disease Competitive Intelligence Radar")
    
    # Left Box: Institutional & Team Profile
    add_card(s1, 0.6, 1.35, 5.85, 5.55)
    t1_box = s1.shapes.add_textbox(Inches(0.85), Inches(1.55), Inches(5.35), Inches(5.15))
    tf1 = t1_box.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = tf1.margin_right = tf1.margin_bottom = 0

    def add_entry(tf, title, desc, title_color=ACCENT_RED, desc_color=TEXT_BODY, size=9.5, space=6):
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = title + ": "
        r1.font.bold = True
        r1.font.size = Pt(size)
        r1.font.color.rgb = title_color
        r1.font.name = FONT_HEADING
        
        r2 = p.add_run()
        r2.text = desc
        r2.font.size = Pt(size)
        r2.font.color.rgb = desc_color
        r2.font.name = FONT_BODY
        p.space_after = Pt(space)

    p_h = tf1.paragraphs[0]
    p_h.text = "INSTITUTIONAL & TEAM PROFILE"
    p_h.font.bold = True
    p_h.font.size = Pt(11.5)
    p_h.font.color.rgb = TEXT_WHITE
    p_h.space_after = Pt(10)

    add_entry(tf1, "Institution", "MS Ramaiah Institute of Technology (MSRIT), Bangalore", HIGHLIGHT_CYAN, TEXT_WHITE, 10, 6)
    add_entry(tf1, "Team Name", "Team MetaRadar", HIGHLIGHT_CYAN, TEXT_WHITE, 10, 6)
    add_entry(tf1, "Faculty Sponsor", "Faculty Advisory Board (Dept. of Pharmacy Practice & CSE, MSRIT)", TEXT_MUTED, TEXT_BODY, 9.5, 8)
    
    p_sep = tf1.add_paragraph()
    p_sep.text = "CORE MULTI-DISCIPLINARY ROSTER"
    p_sep.font.bold = True
    p_sep.font.size = Pt(10)
    p_sep.font.color.rgb = ACCENT_RED
    p_sep.space_after = Pt(6)

    add_entry(tf1, "Sanjana Rathore B. (Lead)", "B.Pharm Final Year — Domain & Medical Affairs Lead", TEXT_WHITE, TEXT_MUTED, 9.5, 4)
    add_entry(tf1, "Ishaaq Ahmed Khan", "B.Pharm — Treatment Maps & Clinical Lifecycles", TEXT_WHITE, TEXT_MUTED, 9.5, 4)
    add_entry(tf1, "Usha Rathore", "B.Pharm — Red-Team Contradictions & Regulatory Affairs", TEXT_WHITE, TEXT_MUTED, 9.5, 4)
    add_entry(tf1, "Omprakash Panda", "ISE / CSE — System Architecture & LangGraph Pipeline", TEXT_WHITE, TEXT_MUTED, 9.5, 4)
    add_entry(tf1, "Veerendra Desai", "ISE / CSE — Vector Search (pgvector) & Infrastructure", TEXT_WHITE, TEXT_MUTED, 9.5, 4)

    # Right Box: 1-Line Problem, Headline Outcome & Scope
    add_card(s1, 6.75, 1.35, 5.98, 5.55)
    t2_box = s1.shapes.add_textbox(Inches(7.0), Inches(1.55), Inches(5.48), Inches(5.15))
    tf2 = t2_box.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = 0

    p_h2 = tf2.paragraphs[0]
    p_h2.text = "PROBLEM & HEADLINE OUTCOME"
    p_h2.font.bold = True
    p_h2.font.size = Pt(11.5)
    p_h2.font.color.rgb = TEXT_WHITE
    p_h2.space_after = Pt(10)

    add_entry(tf2, "1-Line Problem Statement", "Pharma teams monitoring Haemophilia A & B spend 15+ hours/week manually sifting fragmented clinical feeds, missing critical signals, and receiving ungrounded AI summaries that cannot be verified or trusted.", ACCENT_RED, TEXT_WHITE, 10, 10)

    add_entry(tf2, "Headline Outcome", "MetaRadar compresses 15+ hours of cross-functional competitive surveillance into seconds — delivering 100% source-verified, epistemically tagged decision briefs directly to the right stakeholder at the right time.", SUCCESS_GREEN, TEXT_WHITE, 10, 12)

    p_sc = tf2.add_paragraph()
    p_sc.text = "PILOT SCOPE & COMPLIANCE GUARANTEE"
    p_sc.font.bold = True
    p_sc.font.size = Pt(10)
    p_sc.font.color.rgb = HIGHLIGHT_CYAN
    p_sc.space_after = Pt(6)

    add_entry(tf2, "Disease Focus", "Haemophilia A (FVIII deficiency) & Haemophilia B (FIX deficiency) with/without inhibitors", TEXT_WHITE, TEXT_MUTED, 9.5, 4)
    add_entry(tf2, "Key Modalities", "EHL Factors (Altuviiio), Bispecifics (Mim8 vs Hemlibra), Anti-TFPI (concizumab vs marstacimab), AAV5 Gene Therapy (Roctavian, Hemgenix)", TEXT_WHITE, TEXT_MUTED, 9.5, 4)
    add_entry(tf2, "Data Security", "100% Public Authoritative APIs (PubMed, ClinicalTrials.gov, FDA, EMA) — Zero proprietary or confidential data ingested", SUCCESS_GREEN, TEXT_MUTED, 9.5, 4)

    # =========================================================================
    # SLIDE 2: Problem & Innovation
    # =========================================================================
    s2 = add_slide_base(2, "Market Challenge & Core Differentiation", "The Problem: Critical Blindspots & Our Core Innovations")

    # Left Box: Problem & Impacted Stakeholders
    add_card(s2, 0.6, 1.35, 5.85, 5.55)
    t3_box = s2.shapes.add_textbox(Inches(0.85), Inches(1.55), Inches(5.35), Inches(5.15))
    tf3 = t3_box.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = tf3.margin_right = tf3.margin_bottom = 0

    p_p = tf3.paragraphs[0]
    p_p.text = "THE PROBLEM: 3 COMPOUNDING FAILURES"
    p_p.font.bold = True
    p_p.font.size = Pt(11.5)
    p_p.font.color.rgb = ACCENT_RED
    p_p.space_after = Pt(8)

    add_entry(tf3, "1. Information Fragmentation", "Clinical trials, FDA/EMA filings, safety alerts, and industry news live in isolated silos. No team sees the complete picture.", TEXT_WHITE, TEXT_BODY, 9.5, 5)
    add_entry(tf3, "2. Ungrounded AI Summaries", "Generic LLMs fabricate trial IDs, invent PMIDs, and exhibit hallucination risks incompatible with biopharma decisions.", TEXT_WHITE, TEXT_BODY, 9.5, 5)
    add_entry(tf3, "3. Zero Decision Governance", "Critical signals arrive without structured ownership assignment, review enforcement, or auditable sign-off trails.", TEXT_WHITE, TEXT_BODY, 9.5, 10)

    p_imp = tf3.add_paragraph()
    p_imp.text = "WHO IS IMPACTED? (6 ENTERPRISE ROLES)"
    p_imp.font.bold = True
    p_imp.font.size = Pt(10)
    p_imp.font.color.rgb = HIGHLIGHT_CYAN
    p_imp.space_after = Pt(6)

    add_entry(tf3, "• Medical Affairs", "Misses competitor trial readout context and ABR benchmarks.", TEXT_MUTED, TEXT_BODY, 9, 3)
    add_entry(tf3, "• Regulatory Affairs", "Blindsided by PDUFA shifts, BLA submissions, and CHMP opinions.", TEXT_MUTED, TEXT_BODY, 9, 3)
    add_entry(tf3, "• Safety / PV", "Delayed recognition of inhibitor development or TMA events.", TEXT_MUTED, TEXT_BODY, 9, 3)
    add_entry(tf3, "• Market Access", "Surprised by competitor ICER reports and reimbursement barriers.", TEXT_MUTED, TEXT_BODY, 9, 3)
    add_entry(tf3, "• Executive Leadership", "Lacks unified, auditable decision steering for cross-functional actions.", TEXT_MUTED, TEXT_BODY, 9, 3)

    # Right Box: Our Core Innovations
    add_card(s2, 6.75, 1.35, 5.98, 5.55)
    t4_box = s2.shapes.add_textbox(Inches(7.0), Inches(1.55), Inches(5.48), Inches(5.15))
    tf4 = t4_box.text_frame
    tf4.word_wrap = True
    tf4.margin_left = tf4.margin_top = tf4.margin_right = tf4.margin_bottom = 0

    p_in = tf4.paragraphs[0]
    p_in.text = "OUR CORE INNOVATIONS (WHAT'S CREATIVE)"
    p_in.font.bold = True
    p_in.font.size = Pt(11.5)
    p_in.font.color.rgb = SUCCESS_GREEN
    p_in.space_after = Pt(8)

    add_entry(tf4, "Innovation 1 — 48h Confluence + Missing Signal FSM", "Autonomous clustering of multi-source signals within a 48-hour rolling window into unified developments AND active monitoring of expected trial milestone silence (turning absence of evidence into an active alert).", HIGHLIGHT_CYAN, TEXT_WHITE, 9.8, 10)

    add_entry(tf4, "Innovation 2 — Zero-Shot NLI Red-Team Contradiction", "BART-Large-MNLI engine actively cross-examines incoming competitor claims against published trial baselines across 19 biopharma consistency rules — catching discrepancies before they reach executives.", HIGHLIGHT_CYAN, TEXT_WHITE, 9.8, 10)

    add_entry(tf4, "Innovation 3 — Deterministic 4-Factor Priority Math", "No black-box scoring. 100% explainable mathematical scoring (Novelty + Clinical + Regulatory + Recency with 72h exponential decay) dynamically tuned via Human-in-the-Loop online gradient recalibration.", HIGHLIGHT_CYAN, TEXT_WHITE, 9.8, 10)

    add_entry(tf4, "Innovation 4 — Four-Question Decision Briefs", "Transforms unstructured news into epistemically tagged [FACT] vs [SPECULATION] briefs (1. What Changed? 2. Why It Matters? 3. Who Acts? 4. Suggested Action?) with 1-click binding executive directives.", HIGHLIGHT_CYAN, TEXT_WHITE, 9.8, 4)

    # =========================================================================
    # SLIDE 3: Solution Summary & Decision Governance Flow
    # =========================================================================
    s3 = add_slide_base(3, "System Overview & Decision Delivery", "Solution Summary: From Multi-Source Feeds to Executive Steer")

    # Left Column: Summary & Benefits
    add_card(s3, 0.6, 1.35, 5.3, 5.55)
    t5_box = s3.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(4.9), Inches(5.25))
    tf5 = t5_box.text_frame
    tf5.word_wrap = True
    tf5.margin_left = tf5.margin_top = tf5.margin_right = tf5.margin_bottom = 0

    p_s3 = tf5.paragraphs[0]
    p_s3.text = "SOLUTION SUMMARY IN 2 SENTENCES"
    p_s3.font.bold = True
    p_s3.font.size = Pt(11)
    p_s3.font.color.rgb = ACCENT_RED
    p_s3.space_after = Pt(6)

    p_sol = tf5.add_paragraph()
    p_sol.text = "MetaRadar is an autonomous, evidence-grounded competitive intelligence platform that continuously ingests 8 authoritative biomedical feeds, synthesizes evidence into epistemically tagged Four-Question Decision Briefs, and enforces cross-functional decision governance."
    p_sol.font.size = Pt(9.5)
    p_sol.font.color.rgb = TEXT_WHITE
    p_sol.space_after = Pt(10)

    p_bf = tf5.add_paragraph()
    p_bf.text = "EXPECTED ENTERPRISE BENEFITS"
    p_bf.font.bold = True
    p_bf.font.size = Pt(10.5)
    p_bf.font.color.rgb = SUCCESS_GREEN
    p_bf.space_after = Pt(6)

    add_entry(tf5, "• Time Impact", "Synthesis time cut from 15+ hours to seconds; alert-to-action latency reduced from weeks to minutes.", TEXT_WHITE, TEXT_MUTED, 9, 3)
    add_entry(tf5, "• Cost Impact", "75% manual FTE reduction; eliminates costly strategy missteps from ungrounded summaries.", TEXT_WHITE, TEXT_MUTED, 9, 3)
    add_entry(tf5, "• Quality Impact", "100% primary source provenance (PMID/NCT/FDA links) with strict [FACT] separation.", TEXT_WHITE, TEXT_MUTED, 9, 3)
    add_entry(tf5, "• Outcomes Impact", "Anticipates competitor shifts 2–4 weeks ahead of quarterly reports with WORM audit logging.", TEXT_WHITE, TEXT_MUTED, 9, 3)

    # Right Column: Decision Governance Diagram
    add_card(s3, 6.1, 1.35, 6.633, 5.55)
    if os.path.exists(resp_path):
        s3.shapes.add_picture(resp_path, Inches(6.2), Inches(1.45), Inches(6.433), Inches(5.35))

    # =========================================================================
    # SLIDE 4: Technical Implementation & Architecture
    # =========================================================================
    s4 = add_slide_base(4, "Enterprise Engineering Baseline", "Technical Implementation: Medallion Architecture & 11-Node Pipeline")

    # Top Half: Full Architecture Diagram
    add_card(s4, 0.6, 1.3, 12.133, 3.4)
    if os.path.exists(arch_path):
        s4.shapes.add_picture(arch_path, Inches(0.7), Inches(1.38), Inches(11.933), Inches(3.24))

    # Bottom 3 Feature Boxes
    box_w = 3.9
    gap = 0.216

    # Box 1: Data & Storage
    b1_left = 0.6
    add_card(s4, b1_left, 4.85, box_w, 2.05)
    tb1 = s4.shapes.add_textbox(Inches(b1_left + 0.15), Inches(4.95), Inches(box_w - 0.3), Inches(1.85))
    tf_b1 = tb1.text_frame
    tf_b1.word_wrap = True
    tf_b1.margin_left = tf_b1.margin_top = tf_b1.margin_right = tf_b1.margin_bottom = 0
    p1 = tf_b1.paragraphs[0]
    p1.text = "1. INGESTION & DATA LAYER"
    p1.font.bold = True
    p1.font.size = Pt(10)
    p1.font.color.rgb = HIGHLIGHT_CYAN
    p1.space_after = Pt(4)
    add_entry(tf_b1, "8 Connectors", "PubMed, ClinicalTrials.gov v2, OpenFDA, EMA RSS, BioPharma Dive, Fierce, ET Pharma, NewsAPI.", TEXT_WHITE, TEXT_MUTED, 8.5, 2)
    add_entry(tf_b1, "Medallion Store", "Bronze (WORM raw append-only) -> Silver (normalized evidence) -> Gold (384-dim vector signals).", TEXT_WHITE, TEXT_MUTED, 8.5, 2)
    add_entry(tf_b1, "PostgreSQL 16", "pgvector HNSW index (<250ms search), Redis 7 cache.", TEXT_WHITE, TEXT_MUTED, 8.5, 2)

    # Box 2: AI & Reasoning
    b2_left = b1_left + box_w + gap
    add_card(s4, b2_left, 4.85, box_w, 2.05)
    tb2 = s4.shapes.add_textbox(Inches(b2_left + 0.15), Inches(4.95), Inches(box_w - 0.3), Inches(1.85))
    tf_b2 = tb2.text_frame
    tf_b2.word_wrap = True
    tf_b2.margin_left = tf_b2.margin_top = tf_b2.margin_right = tf_b2.margin_bottom = 0
    p2 = tf_b2.paragraphs[0]
    p2.text = "2. AI REASONING DAG"
    p2.font.bold = True
    p2.font.size = Pt(10)
    p2.font.color.rgb = SUCCESS_GREEN
    p2.space_after = Pt(4)
    add_entry(tf_b2, "11-Node LangGraph", "Ingest -> Validate -> Embed -> NLP -> Ontology -> Confluence -> Lifecycle -> RedTeam -> Missing -> Synthesize -> Calibrate.", TEXT_WHITE, TEXT_MUTED, 8.5, 2)
    add_entry(tf_b2, "Local Gemma 3 4B", "Offline private LLM via GGUF/Ollama + Grok fallback (gated by privacy gate).", TEXT_WHITE, TEXT_MUTED, 8.5, 2)
    add_entry(tf_b2, "BART-Large-MNLI", "Zero-shot NLI for 19 contradiction rules.", TEXT_WHITE, TEXT_MUTED, 8.5, 2)

    # Box 3: Frontend & Governance
    b3_left = b2_left + box_w + gap
    add_card(s4, b3_left, 4.85, box_w, 2.05)
    tb3 = s4.shapes.add_textbox(Inches(b3_left + 0.15), Inches(4.95), Inches(box_w - 0.3), Inches(1.85))
    tf_b3 = tb3.text_frame
    tf_b3.word_wrap = True
    tf_b3.margin_left = tf_b3.margin_top = tf_b3.margin_right = tf_b3.margin_bottom = 0
    p3 = tf_b3.paragraphs[0]
    p3.text = "3. GOVERNANCE & DELIVERY"
    p3.font.bold = True
    p3.font.size = Pt(10)
    p3.font.color.rgb = ACCENT_RED
    p3.space_after = Pt(4)
    add_entry(tf_b3, "Next.js 16 + React 19", "13 workspaces, ⌘K semantic search, 3D holographic persona cards.", TEXT_WHITE, TEXT_MUTED, 8.5, 2)
    add_entry(tf_b3, "WORM Trigger", "Physical PostgreSQL trigger blocking all UPDATE/DELETE on audit log table.", TEXT_WHITE, TEXT_MUTED, 8.5, 2)
    add_entry(tf_b3, "Quality Gate", "186 pytest tests passed (100%), 0 TypeScript errors, 0 ESLint warnings.", TEXT_WHITE, TEXT_MUTED, 8.5, 2)

    # =========================================================================
    # SLIDE 5: Results / Demo Highlights & Concrete Walkthrough
    # =========================================================================
    s5 = add_slide_base(5, "Verification & Demo Walkthrough", "Results & Demo Highlights: Concrete Signal-to-Action Walkthrough")

    # Left Column: What Works & Benchmarks
    add_card(s5, 0.6, 1.35, 5.35, 5.55)
    t6_box = s5.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(4.95), Inches(5.25))
    tf6 = t6_box.text_frame
    tf6.word_wrap = True
    tf6.margin_left = tf6.margin_top = tf6.margin_right = tf6.margin_bottom = 0

    p_r1 = tf6.paragraphs[0]
    p_r1.text = "WHAT WORKS RIGHT NOW (DEMO PROOF)"
    p_r1.font.bold = True
    p_r1.font.size = Pt(11)
    p_r1.font.color.rgb = SUCCESS_GREEN
    p_r1.space_after = Pt(6)

    add_entry(tf6, "✓ Live 8-Connector Ingestion", "Real-time background polling with circuit breakers and SHA-256 deduplication.", TEXT_WHITE, TEXT_MUTED, 9, 2)
    add_entry(tf6, "✓ Priority Score Hover Explainer", "0–100 deterministic score breaking down 4 exact mathematical factors.", TEXT_WHITE, TEXT_MUTED, 9, 2)
    add_entry(tf6, "✓ Athena Copilot Streaming", "Sub-80ms TTFB token streaming with clickable verified source citations.", TEXT_WHITE, TEXT_MUTED, 9, 2)
    add_entry(tf6, "✓ Red-Team Contradiction Engine", "Detects trial vs claim discrepancies with BART-Large-MNLI confidence scores.", TEXT_WHITE, TEXT_MUTED, 9, 2)
    add_entry(tf6, "✓ Executive Sign-Off Queue", "1-click binding directives with WORM audit log enforcement.", TEXT_WHITE, TEXT_MUTED, 9, 6)

    p_r2 = tf6.add_paragraph()
    p_r2.text = "EMPIRICAL BENCHMARKS & METRICS"
    p_r2.font.bold = True
    p_r2.font.size = Pt(10)
    p_r2.font.color.rgb = HIGHLIGHT_CYAN
    p_r2.space_after = Pt(4)

    add_entry(tf6, "• Automated Tests", "186 passed, 0 failed (pytest, full test suite)", TEXT_WHITE, TEXT_BODY, 8.5, 2)
    add_entry(tf6, "• Type & Build Quality", "0 errors (tsc --noEmit), 0 ESLint warnings, Next.js build clean", TEXT_WHITE, TEXT_BODY, 8.5, 2)
    add_entry(tf6, "• Search & Stream Speed", "pgvector semantic search <250ms P95; Athena SSE TTFB <80ms", TEXT_WHITE, TEXT_BODY, 8.5, 2)
    add_entry(tf6, "• NLI Precision", "100% precision on curated ABR/inhibitor contradiction fixture pairs", TEXT_WHITE, TEXT_BODY, 8.5, 2)

    # Right Column: Concrete Example & Dataflow Diagram
    add_card(s5, 6.15, 1.35, 6.583, 5.55)
    t7_box = s5.shapes.add_textbox(Inches(6.35), Inches(1.48), Inches(6.183), Inches(2.2))
    tf7 = t7_box.text_frame
    tf7.word_wrap = True
    tf7.margin_left = tf7.margin_top = tf7.margin_right = tf7.margin_bottom = 0

    p_ex = tf7.paragraphs[0]
    p_ex.text = "CONCRETE EXAMPLE: ROCHE EMICIZUMAB HAVEN-7"
    p_ex.font.bold = True
    p_ex.font.size = Pt(10.5)
    p_ex.font.color.rgb = ACCENT_RED
    p_ex.space_after = Pt(4)

    add_entry(tf7, "Input (T+0)", "Competitor Phase 3 readout: monthly subcutaneous shot achieves median ABR 0.0 in non-inhibitors.", TEXT_WHITE, TEXT_MUTED, 8.5, 2)
    add_entry(tf7, "Pipeline Processing", "Deduplicated -> FastEmbed novelty 0.82 -> Priority Score 84 (CRITICAL) -> Red-Team flags conflict with HAVEN-6 Phase 4 (real-world ABR 0.8) -> 48h Confluence links to 3 prior signals.", TEXT_WHITE, TEXT_MUTED, 8.5, 2)
    add_entry(tf7, "Output Brief", "[FACT] HAVEN-7 met primary endpoint (n=89) | [INTERPRETATION] Direct threat to Mim8 monthly narrative | [ACTION] Update Medical Affairs advisory deck in 48h; Market Access to review pricing.", SUCCESS_GREEN, TEXT_WHITE, 8.5, 2)

    if os.path.exists(dataflow_path):
        s5.shapes.add_picture(dataflow_path, Inches(6.35), Inches(3.75), Inches(6.183), Inches(3.0))

    # =========================================================================
    # SLIDE 6: Feasibility, Roadmap & Risk Mitigation
    # =========================================================================
    s6 = add_slide_base(6, "Enterprise Readiness & Risk Governance", "Feasibility & Roadmap: 4-Milestone Enterprise Deployment")

    # Left Column: Roadmap
    add_card(s6, 0.6, 1.35, 5.85, 5.55)
    t8_box = s6.shapes.add_textbox(Inches(0.85), Inches(1.55), Inches(5.35), Inches(5.15))
    tf8 = t8_box.text_frame
    tf8.word_wrap = True
    tf8.margin_left = tf8.margin_top = tf8.margin_right = tf8.margin_bottom = 0

    p_rd = tf8.paragraphs[0]
    p_rd.text = "POST-HACKATHON 4-MILESTONE ROADMAP"
    p_rd.font.bold = True
    p_rd.font.size = Pt(11.5)
    p_rd.font.color.rgb = HIGHLIGHT_CYAN
    p_rd.space_after = Pt(8)

    add_entry(tf8, "Milestone 1 — Enterprise SSO & RBAC (M 1–2)", "SAML 2.0 / Okta / Azure AD integration for automated persona provisioning across 6 functional roles with fine-grained approval permissions.", TEXT_WHITE, TEXT_MUTED, 9.2, 6)

    add_entry(tf8, "Milestone 2 — Internal Data Lake Mirroring (M 2–3)", "Direct connectors to Novo Nordisk internal clinical data lake mirrors and historical congress slide repositories for enriched baseline comparisons.", TEXT_WHITE, TEXT_MUTED, 9.2, 6)

    add_entry(tf8, "Milestone 3 — Indication Expansion (M 3–4)", "Extend disease ontology beyond Haemophilia A/B to Sickle Cell Disease, Beta-Thalassemia, and Ultra-Rare Coagulopathies with multi-asset tracking.", TEXT_WHITE, TEXT_MUTED, 9.2, 6)

    add_entry(tf8, "Milestone 4 — GxP Validation & Audit Hardening (M 4–6)", "Formal Computerized System Validation (CSV) under 21 CFR Part 11 for electronic signatures, disaster recovery, and multi-region read replicas.", TEXT_WHITE, TEXT_MUTED, 9.2, 4)

    # Right Column: Risks & Mitigations
    add_card(s6, 6.75, 1.35, 5.98, 5.55)
    t9_box = s6.shapes.add_textbox(Inches(7.0), Inches(1.55), Inches(5.48), Inches(5.15))
    tf9 = t9_box.text_frame
    tf9.word_wrap = True
    tf9.margin_left = tf9.margin_top = tf9.margin_right = tf9.margin_bottom = 0

    p_rk = tf9.paragraphs[0]
    p_rk.text = "DEPENDENCIES, RISKS & MITIGATIONS"
    p_rk.font.bold = True
    p_rk.font.size = Pt(11.5)
    p_rk.font.color.rgb = WARNING_AMBER
    p_rk.space_after = Pt(8)

    add_entry(tf9, "Risk 1: Public API Outages & Rate Limits", "Mitigation: SourceScheduler advisory locking, exponential backoff retries, and cached Bronze fallback fixtures ensure zero downtime.", TEXT_WHITE, TEXT_MUTED, 9.2, 6)

    add_entry(tf9, "Risk 2: AI Hallucinations in High Stakes", "Mitigation: Strict epistemic labeling ([FACT] vs [SPECULATION]), zero ungrounded generation, and 100% clickable primary citation URLs.", TEXT_WHITE, TEXT_MUTED, 9.2, 6)

    add_entry(tf9, "Risk 3: Information Security & Data Leaks", "Mitigation: Local Gemma 3 4B offline execution + mandatory PII/PHI scrubber + validate_privacy_gate blocking non-public payloads.", TEXT_WHITE, TEXT_MUTED, 9.2, 6)

    add_entry(tf9, "Risk 4: Regulatory Decision Compliance", "Mitigation: Physical PostgreSQL WORM trigger prevents any mutation or deletion of audit logs, guaranteeing tamper-proof compliance.", TEXT_WHITE, TEXT_MUTED, 9.2, 4)

    # =========================================================================
    # SLIDE 7: Business Impact, Value Proposition & Key Takeaways
    # =========================================================================
    s7 = add_slide_base(7, "Strategic Value & Executive Summary", "Business Impact: Why MetaRadar Matters for Novo Nordisk")

    # Left Column: Business & Healthcare Value
    add_card(s7, 0.6, 1.35, 5.85, 5.55)
    t10_box = s7.shapes.add_textbox(Inches(0.85), Inches(1.55), Inches(5.35), Inches(5.15))
    tf10 = t10_box.text_frame
    tf10.word_wrap = True
    tf10.margin_left = tf10.margin_top = tf10.margin_right = tf10.margin_bottom = 0

    p_bi = tf10.paragraphs[0]
    p_bi.text = "QUANTIFIED VALUE PROPOSITION"
    p_bi.font.bold = True
    p_bi.font.size = Pt(11.5)
    p_bi.font.color.rgb = SUCCESS_GREEN
    p_bi.space_after = Pt(8)

    add_entry(tf10, "• Time Savings", "Compresses 15+ hours/week of manual competitive monitoring per user down to seconds (75% FTE effort reduction).", TEXT_WHITE, TEXT_BODY, 9.5, 5)
    add_entry(tf10, "• Strategic Lead Time", "Anticipates competitor trial readouts, PDUFA dates, and CHMP opinions 2 to 4 weeks ahead of quarterly reports.", TEXT_WHITE, TEXT_BODY, 9.5, 5)
    add_entry(tf10, "• Cost Avoidance", "Prevents multi-million dollar strategy missteps caused by unverified AI summaries or blindsided payer pricing shifts.", TEXT_WHITE, TEXT_BODY, 9.5, 5)
    add_entry(tf10, "• Decision Governance", "Enforces cross-functional accountability with 1-click binding directives and permanent WORM audit logs.", TEXT_WHITE, TEXT_BODY, 9.5, 10)

    p_ad = tf10.add_paragraph()
    p_ad.text = "LOW-FRICTION ADOPTION PATHWAY"
    p_ad.font.bold = True
    p_ad.font.size = Pt(10)
    p_ad.font.color.rgb = HIGHLIGHT_CYAN
    p_ad.space_after = Pt(4)
    add_entry(tf10, "Phase 1 (W 1–4)", "Pilot with Rare Blood Disorders Medical Affairs team (15 users).", TEXT_MUTED, TEXT_BODY, 8.8, 2)
    add_entry(tf10, "Phase 2 (W 5–8)", "Expand to Regulatory, Safety/PV, and Market Access teams.", TEXT_MUTED, TEXT_BODY, 8.8, 2)
    add_entry(tf10, "Phase 3 (W 9–12)", "Enterprise executive sign-off integration and global rollout.", TEXT_MUTED, TEXT_BODY, 8.8, 2)

    # Right Column: 3 Key Takeaways for Judges
    add_card(s7, 6.75, 1.35, 5.98, 5.55)
    t11_box = s7.shapes.add_textbox(Inches(7.0), Inches(1.55), Inches(5.48), Inches(5.15))
    tf11 = t11_box.text_frame
    tf11.word_wrap = True
    tf11.margin_left = tf11.margin_top = tf11.margin_right = tf11.margin_bottom = 0

    p_tk = tf11.paragraphs[0]
    p_tk.text = "3 KEY TAKEAWAYS FOR JUDGES"
    p_tk.font.bold = True
    p_tk.font.size = Pt(11.5)
    p_tk.font.color.rgb = ACCENT_RED
    p_tk.space_after = Pt(8)

    add_entry(tf11, "1. Autonomous, Not Just a Chatbot", "MetaRadar is a 24/7 autonomous 11-node intelligence pipeline that actively monitors 8 sources, clusters 48h confluences, and spots missing trial disclosures without requiring manual prompts.", HIGHLIGHT_CYAN, TEXT_WHITE, 9.8, 10)

    add_entry(tf11, "2. 100% Grounded & Epistemically Honest", "Every claim is strictly tagged [FACT] vs [SPECULATION] with clickable links to PubMed PMIDs, NCT IDs, and FDA dossiers. Runs privately on Local Gemma 3 with zero hallucination risk.", HIGHLIGHT_CYAN, TEXT_WHITE, 9.8, 10)

    add_entry(tf11, "3. Complete Decision Governance", "Intelligence without action is useless. MetaRadar delivers Four-Question Decision Briefs with role-scoped ownership and an immutable WORM executive sign-off queue.", HIGHLIGHT_CYAN, TEXT_WHITE, 9.8, 4)

    # Save output
    PITCH_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PITCH_DIR / "MetaRadar_Pitch_Deck.pptx"
    prs.save(str(output_path))
    print(f"Presentation saved successfully to {output_path}")

if __name__ == "__main__":
    create_presentation()
