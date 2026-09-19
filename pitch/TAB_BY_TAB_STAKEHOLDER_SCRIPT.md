# MetaRadar: Master Stakeholder Presentation Script & Easy-Speech Walkthrough Guide

**Novo Nordisk GBS Hackathon 2026 — Problem Statement #3: Rare Disease Competitive Intelligence Radar**  
*Pilot Focus: Haemophilia A & Haemophilia B Competitive Surveillance*  
*Document Release Date: 2026-09-02 | Version: 5.1 Hardened Production Baseline*  
*Team: MS Ramaiah Institute of Technology (MSRIT), Bangalore*

---

## 🗣️ Presenter's Quick Pronunciation Cheat Sheet

Keep this box open while speaking. If you see a difficult word, use the easy phonetic sound in brackets:

| Difficult Biopharma / Tech Word | How to Say It (Phonetic) | Simple Plain-English Meaning |
|---------------------------------|--------------------------|------------------------------|
| **Haemophilia** | *[HEE-moh-FEEL-ee-uh]* | Rare bleeding disorder |
| **Mim8** | *[MIM-eight]* | Novo Nordisk's next-gen antibody shot |
| **Concizumab (Alhemo)** | *[kon-si-ZOO-mab] / [al-HEE-moh]* | Novo Nordisk's anti-TFPI antibody |
| **Emicizumab (Hemlibra)** | *[EM-i-SIZ-oo-mab] / [hem-LEE-bruh]* | Roche's competing weekly/monthly shot |
| **Altuviiio** | *[al-TOO-vee-oh]* | Sanofi's once-weekly factor replacement |
| **Roctavian** | *[rok-TAY-vee-un]* | BioMarin's AAV5 gene therapy |
| **Hemgenix** | *[hem-JEN-iks]* | CSL Behring's gene therapy for Haemophilia B |
| **Marstacimab** | *[mar-STAS-i-mab]* | Pfizer's competing anti-TFPI antibody |
| **Fitusiran** | *[fye-TOO-si-ran]* | Sanofi's siRNA therapy |
| **ABR** | *[A - B - R]* | Annual Bleed Rate (number of bleeds per year) |
| **PDUFA** | *[puh-DOO-fuh]* | FDA target approval deadline date |
| **BLA / MAA** | *[B - L - A] / [M - A - A]* | US / European drug approval applications |
| **CHMP / EPAR** | *[C - H - M - P] / [EE-par]* | European Medicine Agency review committee / report |
| **Gemma 3** | *[JEM-uh three]* | Google's local offline AI model |
| **BART-MNLI** | *[BART M-N-L-I]* | The AI model we use to check contradictions |
| **pgvector** | *[P-G-Vector]* | Database vector search tool |
| **WORM** | *[Worm]* | Write-Once-Read-Many (Tamper-proof storage) |
| **FastEmbed** | *[Fast-Embed]* | Fast local search embedding tool |

---

## 1. Master Pitch Strategy & 60-Second Hook

### 1.1 The 60-Second Opening Hook (Read Exactly as Written)

> *"Good morning, respected judges and leaders.  
> 
> **A regular AI just summarizes documents. MetaRadar builds a complete evidence story around a real-world development.**  
> 
> In rare diseases like **Haemophilia** [HEE-moh-FEEL-ee-uh], the market is moving very fast. Every month, pharma teams get hundreds of trial updates, FDA filings, and press releases.  
> 
> Today, this data is trapped in separate silos:  
> - **Medical teams** see trial readouts but miss the regulatory filing context.  
> - **Safety teams** miss early warning signs on rare side effects.  
> - **Market Access teams** get surprised by competitor pricing reports.  
> - **Leadership** has no single place to approve urgent action items.  
> 
> **MetaRadar solves this completely.** It monitors **8 trusted sources** 24/7, groups related news inside a **48-hour window**, uses AI to **catch conflicting claims**, and delivers clear **Four-Question Decision Briefs** directly to 6 team roles with full leadership sign-off."*

---

### 1.2 The 3-Step Demo Formula ("Show, Prove, Steer")

Whenever you show any screen, follow this simple 3-step rhythm:

1. **SHOW THE NEWS**: Point to the card and say what happened.
2. **PROVE THE FACTS**: Point to the source badge (PubMed, ClinicalTrials, FDA) and show that MetaRadar never makes up fake data.
3. **STEER THE ACTION**: Show the suggested team action and the leadership sign-off button.

---

## 2. Global Shell & Navigation Controls

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ [≡] MetaRadar | User: TM (Medical Affairs)  🟢 Local Gemma 3  [Ingest Data] [🔍 ⌘K] [🔔] [🌙/☀️]│
├──────────────┬────────────────────────────────────────────────────────────────────────────────┤
│ DECISION     │                                                                                │
│ • Overview   │                                                                                │
│ • Signals    │                             MAIN SCREEN DISPLAY                                │
│ • Athena     │                                                                                │
│ ──────────── │                                                                                │
│ DEEP DIVE    │                                                                                │
│ • Confluence │                                                                                │
│ • Lifecycles │                                                                                │
│ • Red Team   │                                                                                │
│ • Missing    │                                                                                │
│ • Develop    │                                                                                │
│ • Functions  │                                                                                │
│ ──────────── │                                                                                │
│ ADMIN/SYSTEM │                                                                                │
│ • Calibrate  │                                                                                │
│ • Sources    │                                                                                │
│ • Logs (WORM)│                                                                                │
│ • Settings   │                                                                                │
├──────────────┴────────────────────────────────────────────────────────────────────────────────┤
│ 🟢 Database: Live  |  🛡️ Privacy Scrubber: Active  |  🧠 Local Gemma 3 Reasoning Live        │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Top Bar & Header Buttons Glossary

| UI Element | Where It Is | What It Means | Easy Words to Say to Stakeholders |
|------------|-------------|---------------|-----------------------------------|
| **User Profile** | Top Left of Dock | Shows current logged-in role (e.g., Medical Lead). | *"Clicking here shows my role card and permissions."* |
| **Dock Toggle** | Top of Dock | Expands or collapses the left menu. | *"I can collapse the sidebar to get a wider workspace."* |
| **`Ingest Data`** | Top Right Bar | Runs an instant live pull across all 8 data feeds. | *"Clicking this button pulls live public data right now."* |
| **Search (`⌘ K`)** | Top Right Bar | Opens instant fast search across all signals. | *"Pressing Command-K lets us search any drug or trial ID instantly."* |
| **Notification Bell**| Top Right Bar | Alerts for pending executive sign-offs. | *"This bell alerts leaders when an urgent approval is waiting."* |
| **Theme Toggle** | Top Right Bar | Switches between Dark Mode and Light Mode. | *"We support clean Dark and Light themes for any boardroom screen."* |
| **Health Footer** | Bottom Bar | Shows database, privacy filter, and AI status. | *"Our bottom footer proves our database is live and privacy filters are active."* |

---

## 3. Tab-by-Tab Deep Dive & Word-by-Word Spoken Script

---

### Tab 1: `/dashboard` — Executive Overview

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ DECISION INTELLIGENCE BRIEFING                                                                │
│ Executive Overview                                                                            │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🚨 ACTION REQUIRED: 2 Cross-Functional Escalations Waiting for Leadership Sign-Off [Review ->]│
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🔵 TODAY'S EXECUTIVE INTELLIGENCE SUMMARY                                                     │
│ 8 Sources Monitored · 3 Confluences Confirmed · 4 High-Urgency Signals Flagged                │
│ [Total: 24]  [High Priority: 4]  [Needs Review: 7]  [Leadership: 2]                           │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────────────────────────┤
│ Active Signals  │ Monitored Drugs │ Confluences     │ Live Sources                            │
│      24         │       8         │       3         │       8 Connected                       │
│   +12% this week│    Active       │ High Confidence │ 100% Operational                        │
├─────────────────┴─────────────────┴─────────────────┴─────────────────────────────────────────┤
│ WHAT DESERVES ATTENTION RIGHT NOW        │ ANALYTICS & CONFLUENCE                             │
│ [All (24)] [Critical (4)] [Review] [Lead]│ ┌────────────────────────────────────────────────┐ │
│ ┌──────────────────────────────────────┐ │ │ CONFLUENCE SCORE: 84 / 100                     │ │
│ │ 🔴 CRITICAL | Score: 84              │ │ │ 01 TRIAL READOUT | Mim8 Phase 3 Study Met      │ │
│ │ Roche Emicizumab Monthly Shot Readout│ │ │ 02 REGULATORY    | EMA Positive Opinion        │ │
│ │ Achieves 0.0 Median ABR in Inhibitors│ │ └────────────────────────────────────────────────┘ │
│ │ [FACT] Primary trial goal met with   │ │ ┌────────────────────────────────────────────────┐ │
│ │ zero bleeds in adult patient cohort. │ │ │ PORTFOLIO MOMENTUM (News Speed Trend)          │ │
│ └──────────────────────────────────────┘ │ │ [Chart: Today's Speed vs 30-Day Average]       │ │
│                                          │ └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────┴────────────────────────────────────────────────────┘
```

#### Plain-English Glossary for this Tab
- **Executive Overview**: The main dashboard where team leads start their day.
- **Confluence Score (0–100)**: How strongly multiple independent sources agree on the same news.
- **Portfolio Momentum**: A chart showing if competitor news is speeding up compared to last month.
- **Priority Score (0–100)**: A clear math score showing how urgent a piece of news is.

#### Spoken Presenter Script (Read Out Loud)

> *"Let us start with the **Executive Overview**. This is the single cockpit for Novo Nordisk leaders.  
> 
> Notice the top alert banner: MetaRadar immediately flags that we have **2 urgent team escalations waiting for executive approval**.  
> 
> Look at the 4 metric boxes:  
> - We have **24 active signals**, up 12% this week.  
> - We are tracking **8 core haemophilia drugs**.  
> - We have **3 multi-source news clusters**.  
> - All **8 data feeds** are live and healthy.  
> 
> Looking at our main feed, 'What Deserves Attention Right Now', MetaRadar ranks the most urgent news at the top. Look at this top card: **Roche's monthly shot trial data**. It gets a high Priority Score of **84 out of 100**.  
> 
> On the right side, our **Confluence Radar** shows a high score of 84 because both clinical trials and European regulatory updates confirm this news at the same time.  
> 
> Now, let us look at the full list of signals in the Signals tab."*

---

### Tab 2: `/signals` — Live Intelligence Feed

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ LIVE INTELLIGENCE STREAM                                                                      │
│ Signals                                                                                       │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ [▼ Click to Filter: Priority / Drug Name / Signal Type / Source / Date]                       │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🔴 CRITICAL | Priority Score: 84 | Published: 2 hours ago | 4 Sources                         │
│ Roche Emicizumab Phase 3 Readout Reports 0.0 Median Bleeds in Inhibitor Patients             │
│ Target: Factor 8 | Type: Bispecific Shot | Source: BioPharma Dive & ClinicalTrials.gov        │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🟠 HIGH | Priority Score: 76 | Published: 6 hours ago | 3 Sources                             │
│ FDA Grants Priority Review for Novo Nordisk's Concizumab in Haemophilia B with Inhibitors    │
│ Target: TFPI | Type: Anti-TFPI Shot | Source: OpenFDA Drugs@FDA                               │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🟡 MEDIUM | Priority Score: 58 | Published: 1 day ago | 2 Sources                             │
│ Altuviiio Real-World Study Shows High Clotting Protection Past 4 Days                         │
│ Target: Factor 8 | Type: Long-Acting Factor | Source: NCBI PubMed (PMID: 39102488)           │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Plain-English Glossary for this Tab
- **Signals**: Clean, validated pieces of competitive news.
- **Priority Math Formula**: 
  $$\text{Score} = \text{Novelty (0–25)} + \text{Clinical Value (0–30)} + \text{Regulatory Value (0–25)} + \text{Freshness (0–20)}$$
- **Freshness Half-Life**: Fresh news published today gets 20 points. As news gets older, points drop naturally every 3 days.

#### Spoken Presenter Script (Read Out Loud)

> *"Here in the **Signals** workspace, we see all competitive news ranked clearly by urgency.  
> 
> Every score is based on simple, open math—never black-box guesses. For example, this top Roche signal scored **84 points** because:  
> - It brings new data in vector space (**20 points**).  
> - It is a Phase 3 human trial (**25 points**).  
> - It affects drug approvals (**20 points**).  
> - It was published just 2 hours ago (**19 points**).  
> 
> I can use our filter bar to filter by drug name, priority level, or source.  
> 
> Now let us click into our AI reasoning tool, **Ask Athena**."*

---

### Tab 3: `/intelligence` — Ask Athena (AI Q&A)

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ GROUNDED CLINICAL Q&A                                                                         │
│ Ask Athena                                                                                    │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────┐ ┌─────────────────────────────────────────────┐ │
│ │ 🧠 ASK ANYTHING ABOUT THE DRUG LANDSCAPE  │ │ 🤖 ATHENA FACT-CHECKED ANSWER               │ │
│ │ Ask Athena searches our database, cleans  │ │ [Badge: Local Gemma 3 Reasoning]            │ │
│ │ all private data, and gives fact-checked  │ │                                             │ │
│ │ answers using local offline AI.           │ │ In Phase 3 clinical trials, Mim8           │ │
│ │                                           │ │ [MIM-eight] achieved zero bleeds in 95% of  │ │
│ │ ✨ Built from 24 Active Live Signals      │ │ patients on monthly subcutaneous shots...   │ │
│ │                                           │ │                                             │ │
│ │ [Click Prompt: 5-Year Gene Therapy Data..]│ │ ─────────────────────────────────────────── │ │
│ │ [Click Prompt: Mim8 Zero-Bleed Data...]   │ │ VERIFIED SOURCE LINKS (2)                   │ │
│ │ [Click Prompt: FDA Action Dates for TFPI..]│ │ ┌─────────────────────────────────────────┐ │ │
│ │                                           │ │ │ 🟢 LIVE SOURCE | ClinicalTrials NCT04869267│ │
│ │ [ Type a question...                    ] │ │ │ FRONTIER-2 Efficacy in Haemophilia A/B   │ │ │
│ │ [ Glowing Button: Ask Athena            ] │ │ └─────────────────────────────────────────┘ │ │
│ └───────────────────────────────────────────┘ └─────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Plain-English Glossary for this Tab
- **Ask Athena**: Our smart assistant that answers medical questions using only verified data.
- **Local Gemma 3**: Google's open AI model running privately inside our server without sending data to the public internet.
- **Word-by-Word Streaming**: The text appears smoothly on screen in real time with zero waiting lag.
- **Verified Source Links**: Direct clickable links to real trial IDs and scientific papers.

#### Spoken Presenter Script (Read Out Loud)

> *"This is **Ask Athena**—our clinical intelligence assistant.  
> 
> Unlike ChatGPT, Athena **never makes up fake trial IDs or false claims**. It runs on **Local Gemma 3** [JEM-uh three] completely offline inside our system.  
> 
> Let us click this prompt: *'How does Mim8 [MIM-eight] zero-bleed data compare with competitor factor shots?'*  
> 
> Watch how fast the answer streams on screen.  
> 
> Look at the bottom of the card: every sentence is backed by a **Verified Source Link**. I can click 'NCT04869267' to open the exact ClinicalTrials.gov record and check patient numbers myself."*

---

### Tab 4: `/confluence` — Confluence Alerts (News Clustering)

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ CROSS-SOURCE EVIDENCE CLUSTERING                                                              │
│ Confluence Alerts                                                                             │
├─────────────────────────────────┬─────────────────┬─────────────────┬─────────────────────────┤
│ Confluences Detected            │ Evidence Depth  │ Main Focus      │ Tracking Window         │
│               3                 │ 3.4 sources     │ Mim8 / Bleeds   │ 48 Hours                │
├─────────────────────────────────┴─────────────────┴─────────────────┴─────────────────────────┤
│ ⚡ CONFIRMED NEWS CLUSTER | 4 Independent Sources Agreed Within 48 Hours                       │
│ Topic: Mim8 Subcutaneous Prophylaxis in Haemophilia Patients with Inhibitors                  │
│ Score: 92/100 | Agreement: High | Detected: Today                                             │
│                                                                                               │
│ Converged Evidence Sources:                                                                   │
│ [CLINICAL TRIAL: Study NCT04869267]      [REGULATORY: European EMA Positive Notice]           │
│ [CONGRESS: ASH 2026 Abstract]            [INDUSTRY NEWS: BioPharma Dive Article]              │
│                                                                                               │
│ [Click to Inspect All 4 Source Links ->]                                                      │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Plain-English Glossary for this Tab
- **Confluence**: When 3 or more completely separate sources (e.g., a trial registry, an FDA notice, and a news article) all report the exact same news within 48 hours.
- **Evidence Depth**: How many separate sources back up the claim (average 3.4 sources).
- **48-Hour Window**: The time window we use to catch breaking news trends before they get old.

#### Spoken Presenter Script (Read Out Loud)

> *"In competitive intelligence, a single news article can be biased. But when a clinical trial update, a European FDA notice, a medical congress paper, and a biopharma journal all agree within 48 hours, that is a **Confirmed News Cluster**.  
> 
> Here on the **Confluence** tab, MetaRadar automatically groups related news. Look at this top cluster for **Mim8** [MIM-eight]: 4 separate sources confirmed this development within 48 hours.  
> 
> Now let us see how this drug is progressing through clinical trials in our **Lifecycles** tab."*

---

### Tab 5: `/lifecycles` — Drug Lifecycle Tracker

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ CLINICAL PIPELINE PROGRESSION                                                                 │
│ Drug Lifecycle Tracker                                                                        │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ DRUG: Mim8 [MIM-eight] (Next-Gen Antibody Shot) | Maker: Novo Nordisk                         │
│ Target: Haemophilia A & B with/without Inhibitors                                             │
│                                                                                               │
│ ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐  │
│ │ PRECLINICAL  │──>│   PHASE 1    │──>│   PHASE 2    │──>│   PHASE 3    │──>│  REGULATORY  │  │
│ │  Completed   │   │  Completed   │   │  Completed   │   │  ACTIVE [✓]  │   │  SUBMITTED   │  │
│ └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘  │
│                                                                                               │
│ Latest Milestone: Phase 3 primary trial completed; filing preparation started.                │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ DRUG: Concizumab [kon-si-ZOO-mab] / Alhemo [al-HEE-moh] | Maker: Novo Nordisk                 │
│ Status: Approved in Canada & Europe / Under FDA Review in the US                              │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Plain-English Glossary for this Tab
- **Drug Lifecycle**: The step-by-step path a drug takes from the lab to human trials to pharmacy shelves.
- **Phase 1, 2, 3**: Safety testing (Phase 1) $\rightarrow$ Dose finding (Phase 2) $\rightarrow$ Big patient trials (Phase 3).
- **Regulatory Submitted**: When the drug company officially hands their data to the FDA or European EMA for approval.

#### Spoken Presenter Script (Read Out Loud)

> *"On the **Lifecycles** tab, MetaRadar tracks each drug across its development stages.  
> 
> Here we see **Mim8** [MIM-eight] moving from Phase 3 into Regulatory Submission. Whenever a trial status changes on ClinicalTrials.gov, MetaRadar automatically advances this progress bar.  
> 
> But what happens if a competitor publishes data that clashes with their earlier trial results? That leads us to our next feature: the **Red-Team Contradiction Engine**."*

---

### Tab 6: `/red-team` — Red-Team Contradiction Engine

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ CONTRADICTION & FACT-CHECKING AUDIT                                                           │
│ Red-Team Contradictions                                                                       │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ Filters: [All Severities] [Critical] [High] [Medium]                                          │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🛡️ CRITICAL SEVERITY | Rule: Efficacy vs Real-World Baseline | AI Confidence: 94%             │
│ Conflict spotted between Phase 3 promotional claim and published real-world registry numbers │
│                                                                                               │
│ ┌───────────────────────────────────────────┐ ┌─────────────────────────────────────────────┐ │
│ │ PROVEN BASELINE (From Earlier Study)      │ │ NEW PROMOTIONAL CLAIM (From Press Release)  │ │
│ │ Source: HAVEN-6 Real-World Study          │ │ Source: HAVEN-7 Promotional Press Release   │ │
│ │ "Real-world data showed an average of     │ │ "Phase 3 monthly shot achieved zero bleeds  │ │
│ │ 0.8 bleeds per year in routine care."     │ │ (0.0 ABR) across 100% of adult patients."   │ │
│ └───────────────────────────────────────────┘ └─────────────────────────────────────────────┘ │
│                                                                                               │
│ AI Explanation: The claim of 0.0 bleeds in promotional media conflicts with earlier real-world │
│ study data showing 0.8 bleeds per year.                                                       │
│ Recommended Action: Alert Medical Affairs to prepare response slides for doctors.             │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Plain-English Glossary for this Tab
- **Red-Team Engine**: An automated fact-checker that spots when a competitor makes claims that clash with earlier scientific data.
- **BART AI Model**: The language AI we use to compare two statements and detect contradictions.
- **Confidence (e.g., 94%)**: How certain the AI is that the two statements disagree.

#### Spoken Presenter Script (Read Out Loud)

> *"This screen is one of our biggest innovations: the **Red-Team Contradiction Engine**.  
> 
> Pharma competitors often publish press releases with bold claims that leave out prior real-world data. MetaRadar catches these discrepancies automatically.  
> 
> Look at this Critical alert: A competitor's press release claims '100% bleed-free results with 0.0 bleeds'. Our AI compared this against the published study in PubMed, which showed a real-world average of **0.8 bleeds per year**.  
> 
> With **94% confidence**, MetaRadar flags this contradiction side-by-side and alerts Medical Affairs to prepare counter-briefings for field liaisons."*

---

### Tab 7: `/missing-signals` — Missing Signals (Silence Detector)

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ MISSING EVIDENCE & SILENCE DETECTOR                                                           │
│ Missing Signals                                                                               │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ Filters: [All Watch States] [Overdue] [Due Soon] [Within Window] [Satisfied]                  │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ 👁️ OVERDUE | Team: REGULATORY AFFAIRS | +180 Days Overdue                                      │
│ Drug: Pfizer Marstacimab [mar-STAS-i-mab] | Expected Event: Phase 3 Trial Data Disclosure     │
│                                                                                               │
│ Prior Event: Clinical trial NCT03938792 marked trial completion 6 months ago.                 │
│ Expected News: Under FDA rules, primary results are expected within 180 days.                 │
│ Why Silence Matters: A 6-month delay with zero news suggests a possible safety pause or       │
│ recalculated trial results.                                                                   │
│                                                                                               │
│ [Confirm Watch Item]  [Assign Task to Regulatory Team]                                        │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Plain-English Glossary for this Tab
- **Missing Signal**: An alert triggered when expected news does **not** appear on time.
- **180-Day Rule**: Standard US law requiring clinical trial results to be shared publicly within 6 months of trial completion.
- **Silence as a Signal**: When a competitor goes silent after completing a big trial, it often hints at unexpected safety holds or recalculations.

#### Spoken Presenter Script (Read Out Loud)

> *"Other tools only tell you what was published. MetaRadar is the first tool to tell you **what was NOT published**.  
> 
> Here on **Missing Signals**, our timer tracks overdue milestones. Look at this alert: Pfizer's trial finished 6 months ago. Under FDA rules, trial data should be disclosed within 180 days.  
> 
> That time has passed with zero public updates. MetaRadar flags this **180-day silence as an active Overdue alert**. This silence is an early warning that gives our strategy team weeks of lead time."*

---

### Tab 8: `/developments` — Competitor Program Registry

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ COMPETITOR DRUG TRACKER                                                                       │
│ Competitive Developments Registry                                                             │
├─────────────────────────────────┬─────────────────┬─────────────────┬─────────────────────────┤
│ Tracked Programs                │ Total Signals   │ Disease Area    │ Tracking Status         │
│               8                 │       24        │ Haemophilia     │ Active 24/7             │
├─────────────────────────────────┴─────────────────┴─────────────────┴─────────────────────────┤
│ ┌───────────────────────────────────────────┐ ┌─────────────────────────────────────────────┐ │
│ │ 🧪 Mim8 [MIM-eight] Program               │ │ 🧪 Concizumab [kon-si-ZOO-mab] Program      │ │
│ │ Maker: Novo Nordisk | Stage: Phase 3      │ │ Maker: Novo Nordisk | Stage: Approved / BLA │ │
│ │ Target: Haemophilia A/B with Inhibitors   │ │ Type: Anti-TFPI Antibody                    │ │
│ │ Evidence: 8 Linked Records                │ │ Evidence: 6 Linked Records                  │ │
│ └───────────────────────────────────────────┘ └─────────────────────────────────────────────┘ │
│ ┌───────────────────────────────────────────┐ ┌─────────────────────────────────────────────┐ │
│ │ 🧪 Roctavian [rok-TAY-vee-un]             │ │ 🧪 Altuviiio [al-TOO-vee-oh]                │ │
│ │ Maker: BioMarin | Stage: On Market        │ │ Maker: Sanofi / Sobi | Stage: On Market     │ │
│ │ Type: AAV5 Gene Therapy                   │ │ Type: Long-Acting Factor 8                  │ │
│ └───────────────────────────────────────────┘ └─────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Plain-English Glossary for this Tab
- **Developments Registry**: The master list of all 8 main drug programs we track.
- **Linked Records**: All trial records, news stories, and filings grouped under that specific drug.

#### Spoken Presenter Script (Read Out Loud)

> *"The **Developments** tab gives a clean overview of all 8 major competitive programs in haemophilia—from our assets like Mim8 [MIM-eight] and concizumab [kon-si-ZOO-mab], to competitor gene therapies like Roctavian [rok-TAY-vee-un].  
> 
> Each box opens the full history of trials, filings, and news for that single drug."*

---

### Tab 9: `/functions` — Team Alignment & Executive Approvals

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ CROSS-TEAM ACTION & APPROVALS                                                                 │
│ Functions Intelligence                                                                        │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ ⚡ EXECUTIVE APPROVAL QUEUE (Visible to Leadership & Admin)                                   │
│ ┌───────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ Signal: Mim8 Phase 3 Trial Readout                                                        │ │
│ │ Sent by: Medical Affairs Lead | Priority: CRITICAL (Score: 84)                             │ │
│ │ Proposed Action: "Approve global update to doctor slide decks and brief Market Access."   │ │
│ │ [ ✕ Reject ]   [ 💬 Request More Facts ]   [ ✓ Approve Official Directive ]                 │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────┘ │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ 6 TEAM PERFORMANCE TILES                                                                      │
│ ┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐                    │
│ │ MEDICAL AFFAIRS      │ │ REGULATORY AFFAIRS   │ │ SAFETY & PV          │                    │
│ │ 85% Approval Rate    │ │ 92% Approval Rate    │ │ 100% Approval Rate   │                    │
│ │ ★ 4.6 / 5.0 Rating   │ │ ★ 4.8 / 5.0 Rating   │ │ ★ 4.9 / 5.0 Rating   │                    │
│ └──────────────────────┘ └──────────────────────┘ └──────────────────────┘                    │
│ ┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐                    │
│ │ MARKET ACCESS & HEOR │ │ MEDICAL COMMS        │ │ EXECUTIVE LEADERSHIP │                    │
│ │ 78% Approval Rate    │ │ 88% Approval Rate    │ │ 95% Approval Rate    │                    │
│ │ ★ 4.2 / 5.0 Rating   │ │ ★ 4.4 / 5.0 Rating   │ │ ★ 4.7 / 5.0 Rating   │                    │
│ └──────────────────────┘ └──────────────────────┘ └──────────────────────┘                    │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Plain-English Glossary for this Tab
- **Executive Approval Queue**: The sign-off screen where Vice Presidents approve or reject urgent team recommendations.
- **Approve Official Directive**: Clicking this creates an unchangeable, tamper-proof record in our database.
- **6 Roles**: Medical Affairs, Regulatory, Safety, Market Access, Comms, Leadership.

#### Spoken Presenter Script (Read Out Loud)

> *"On the **Functions** tab, MetaRadar connects our 6 core biopharma departments.  
> 
> Look at the top panel: as Executive Leadership, I see an **Approval Queue**. Medical Affairs has sent an urgent Mim8 competitive update, requesting sign-off to update our doctor slide decks.  
> 
> With one click on **'Approve Official Directive'**, I sign off on this decision. The system immediately notifies the team and logs a permanent, tamper-proof record in our audit log.  
> 
> Below, we see live response scores across all 6 departments."*

---

### Tab 10: `/calibrate` — Smart Weight Tuning

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ SCORING WEIGHT TUNING                                                                         │
│ Calibration                                                                                   │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ Filters: [All Roles] [Regulatory] [Medical] [Safety] [Market Access]      [Run Calibration]   │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ ACTIVE SCORING WEIGHTS MATRIX                                                                 │
│ ┌─────────────────────┬──────────────────┬─────────────────┬────────────────────────────────┐ │
│ │ Factor Name         │ Starting Weight  │ Tuned by Users  │ Adjustment Direction           │ │
│ ├─────────────────────┼──────────────────┼─────────────────┼────────────────────────────────┤ │
│ │ Clinical Trials     │ 1.000            │ 1.250           │ +0.250 (↑ More Important)      │ │
│ │ Regulatory Filings  │ 1.000            │ 1.150           │ +0.150 (↑ More Important)      │ │
│ │ Novelty / Surprise  │ 1.000            │ 0.900           │ -0.100 (↓ Reduced Noise)       │ │
│ │ Freshness / Speed   │ 1.000            │ 1.050           │ +0.050 (↑ Speed Matters)       │ │
│ └─────────────────────┴──────────────────┴─────────────────┴────────────────────────────────┘ │
│                                                                                               │
│ System Status: Balanced | Total User Feedback Reviews: 42                                     │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Plain-English Glossary for this Tab
- **Calibration**: Teaching the system what news matters most based on 1-to-5 star user ratings.
- **Starting Weight**: The default score multiplier (1.0).
- **Tuned Weight**: The adjusted score multiplier (e.g., 1.25 for clinical trials) calculated from real user feedback without writing new code.

#### Spoken Presenter Script (Read Out Loud)

> *"On the **Calibrate** tab, MetaRadar gets smarter over time.  
> 
> When doctors and directors rate signals 1 to 5 stars in their daily work, MetaRadar tunes its scoring weights automatically.  
> 
> As you can see, based on 42 real user ratings, Clinical Trial importance tuned up from 1.0 to **1.25**, while random novelty noise tuned down to **0.90**."*

---

### Tab 11: `/sources` — Live Data Feeds & Latency

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ LIVE DATA CONNECTORS & HEALTH                                                                 │
│ Sources & Connectors                                                                          │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────────────────────────┤
│ Active Sources  │ Healthy Feeds   │ Records Saved   │ Background Schedule                     │
│        8        │ 8 (100% Live)   │      1,420      │ Runs automatically every 15 minutes     │
├─────────────────┴─────────────────┴─────────────────┴─────────────────────────────────────────┤
│ 8 LIVE DATA SOURCE TILES                                                                      │
│ ┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────────┐ │
│ │ 🟢 NCBI PUBMED            │ │ 🟢 CLINICALTRIALS.GOV     │ │ 🟢 OPENFDA DRUGS@FDA          │ │
│ │ Status: HEALTHY           │ │ Status: HEALTHY           │ │ Status: HEALTHY               │ │
│ │ Speed: 142 ms             │ │ Speed: 188 ms             │ │ Speed: 95 ms                  │ │
│ │ Saved: 420 records        │ │ Saved: 310 records        │ │ Saved: 180 records            │ │
│ └───────────────────────────┘ └───────────────────────────┘ └───────────────────────────────┘ │
│ ┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────────┐ │
│ │ 🟢 EMA EUROPEAN RSS       │ │ 🟢 BIOPHARMA DIVE         │ │ 🟢 FIERCE PHARMA NEWS         │ │
│ │ Status: HEALTHY           │ │ Status: HEALTHY           │ │ Status: HEALTHY               │ │
│ └───────────────────────────┘ └───────────────────────────┘ └───────────────────────────────┘ │
│ ┌───────────────────────────┐ ┌───────────────────────────┐                                   │
│ │ 🟢 ET PHARMA (ASIA)       │ │ 🟡 NEWSAPI GLOBAL         │                                   │
│ │ Status: HEALTHY           │ │ Status: RATE MANAGED      │                                   │
│ └───────────────────────────┘ └───────────────────────────┘                                   │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Plain-English Glossary for this Tab
- **8 Data Connectors**: PubMed, ClinicalTrials.gov, OpenFDA, European EMA, BioPharma Dive, FiercePharma, ET Pharma, and NewsAPI.
- **Speed (e.g., 142 ms)**: How fast the server talks to the external medical database (in thousandths of a second).
- **Records Saved**: The exact number of raw articles stored in our tamper-proof Bronze database.

#### Spoken Presenter Script (Read Out Loud)

> *"On the **Sources** tab, MetaRadar shows 100% honest, live system telemetry.  
> 
> We connect to **8 trusted public streams**: PubMed, ClinicalTrials.gov, OpenFDA, European EMA, BioPharma Dive, FiercePharma, ET Pharma, and NewsAPI.  
> 
> Every box shows live speed in milliseconds and total records saved. If an external API slows down, our built-in safety brakes prevent crashes."*

---

### Tab 12: `/observability` — Tamper-Proof Audit Trail (WORM Logs)

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ AUDIT TRAIL & SYSTEM LOGS                                                                     │
│ Observability & Ingestion Logs                                                                │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ Filters: [All Logs] [INFO] [WARNING] [ERROR]                              [Refresh Logs]      │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🟢 INFO | 08:42:15 | Duration: 42 ms | Trace ID: req_99a812bf                                  │
│ News cluster CONF-881 formed: 4 separate sources agreed on Mim8 trial data.                   │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🟢 INFO | 08:41:02 | Trace ID: req_77c104e1                                                   │
│ Executive Directive APPROVED by user test.leader for signal SIG-841920.                       │
│ Security Status: Locked by Database Trigger [Write-Once Tamper-Proof]                         │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Plain-English Glossary for this Tab
- **Audit Trail**: A timestamped log of every single action, AI summary, and leadership approval.
- **Tamper-Proof (WORM)**: A database lock that lets us write logs once, but blocks anyone from ever changing or deleting them.
- **Trace ID**: A tracking number attached to every piece of news from start to finish.

#### Spoken Presenter Script (Read Out Loud)

> *"For a healthcare leader like Novo Nordisk, audit safety is essential. This is our **Audit Trail**.  
> 
> Every pipeline step and executive approval is saved here with a unique tracking ID.  
> 
> Most importantly, this log is protected by a physical **tamper-proof database lock**. Even a database administrator cannot change or delete an executive sign-off record once saved."*

---

### Tab 13: `/settings` — User Personas & System Setup

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ USER ROLES & SYSTEM SETTINGS                                                                  │
│ Settings                                                                                      │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ CLICK A ROLE TO SWITCH DEMO VIEW                                                              │
│ [ 👨‍⚕️ Medical Affairs ]  [ ⚖️ Regulatory Affairs ]  [ 🛡️ Safety & PV ]                          │
│ [ 📊 Market Access ]     [ 📢 Medical Comms ]       [ 👔 Executive Leadership ]               │
│ [ 💻 Platform Engineer ] [ ⚙️ System Admin ]                                                  │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ THEME SELECTION                                                                               │
│ [ 🌙 Dark Mode (Default) ]   [ ☀️ Light Mode (High Contrast) ]                                 │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ SYSTEM ARCHITECTURE                                                                           │
│ • Web Frontend: Next.js 16 + React 19                                                         │
│ • API Backend:  FastAPI + Python 3.11                                                         │
│ • Database:     PostgreSQL 16 + Vector Search + Redis Cache                                   │
│ • AI Engine:    Local Gemma 3 (Running Privately on Server)                                   │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Plain-English Glossary for this Tab
- **User Roles**: Lets you switch between the 6 different team views with 1 click.
- **Local Gemma 3**: Proves the AI is running privately on local hardware with zero external data leaks.

#### Spoken Presenter Script (Read Out Loud)

> *"Finally, our **Settings** tab lets judges and stakeholders switch between our 8 pre-set roles with one click.  
> 
> You can see how the dashboard instantly customizes itself for a Medical Affairs lead versus an Executive Vice President."*

---

## 4. The Signal Detail Deep-Dive (The Four Questions)

When clicking any signal, the **Signal Detail View** opens with our clean **Four-Question Decision Brief**:

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🔴 CRITICAL | Priority Score: 84 / 100 | Published: 2 hours ago | Provenance: VERIFIED [✓]   │
│ Roche Emicizumab Phase 3 Readout: 0.0 Median Bleeds in Inhibitor Patients                     │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ THE FOUR-QUESTION DECISION BRIEF                                                              │
│                                                                                               │
│ Q1: WHAT CHANGED? (Pure Verified Fact)                                                        │
│ [FACT] Roche’s Phase 3 study reported that once-monthly shots achieved a median of 0.0 bleeds │
│ in 89 adult Haemophilia A patients without inhibitors.                                        │
│                                                                                               │
│ Q2: WHY DOES IT MATTER? (Strategic Impact on Novo Nordisk)                                    │
│ [INTERPRETATION] This directly challenges Mim8's [MIM-eight] once-monthly dosing narrative.   │
│ If emicizumab matches our convenience, Mim8’s main advantage will rely on higher efficacy in  │
│ difficult inhibitor patients.                                                                 │
│                                                                                               │
│ Q3: WHO SHOULD ACT? (Team Ownership)                                                          │
│ Primary Owner: MEDICAL AFFAIRS (95% Match) | Secondary: MARKET ACCESS (82% Match)             │
│ Urgency: EXECUTIVE LEADERSHIP SIGN-OFF REQUIRED                                               │
│                                                                                               │
│ Q4: WHAT SHOULD WE DO? (Actionable Recommendations)                                           │
│ [ACTION] 1. Update Global Medical Affairs slide decks for doctor advisory boards in 48 hours.  │
│ [ACTION] 2. Market Access to check payer pricing impact before the Q3 pricing committee.      │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🛡️ RED-TEAM CONTRADICTION SPOTLIGHT                                                           │
│ Clashes with Phase 4 study: Real-world registries showed 0.8 bleeds per year, not 0.0 bleeds. │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ VERIFIED SOURCE CITATIONS                                                                     │
│ [🔗 PubMed ID: 38291023]    [🔗 ClinicalTrials ID: NCT04023099]    [🔗 FDA Approval Dossier]  │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ TEAM ACTION BUTTONS                                                                           │
│ [ Mark as Reviewed ]    [ Escalate to Leadership ]    [ Request Cross-Team Approval ]         │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Spoken Presenter Script for a Signal Detail Walkthrough

> *"When a team member opens any signal, they see our **Four-Question Decision Brief**:  
> 
> - **Q1: What changed?** Strictly labeled **[FACT]**—Roche’s trial met its zero-bleed endpoint.  
> - **Q2: Why does it matter?** Labeled **[INTERPRETATION]**—it challenges Mim8's [MIM-eight] monthly dosing narrative.  
> - **Q3: Who should act?** Medical Affairs owns the response, with Market Access supporting.  
> - **Q4: What should we do?** Two clear actions: update doctor advisory decks within 48 hours, and review payer pricing before Q3.  
> 
> Notice the **Red-Team Contradiction** warning at the bottom, and the **3 clickable source links** that let any doctor verify the raw data in seconds."*

---

## 5. Fast 3-Minute Live Demo Sequence

Follow this exact 3-minute sequence during your live pitch:

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                              3-MINUTE LIVE DEMO SEQUENCE                                      │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ MINUTE 1 (0:00–1:00) — INGEST & DASHBOARD                                                     │
│ 1. Start on /dashboard. Point to the top alert: "2 items awaiting executive sign-off".        │
│ 2. Click [Ingest Data] in the top bar. Show that new public data syncs in seconds.           │
│ 3. Point to the top Critical signal (Score: 84).                                              │
│                                                                                               │
│ MINUTE 2 (1:00–2:00) — SIGNAL DEEP-DIVE & RED-TEAM CONTRADICTION                              │
│ 4. Click the top signal. Walk through Q1 [FACT], Q2 [INTERPRETATION], and Q4 [ACTION].        │
│ 5. Show the BART AI Red-Team contradiction (0.0 claimed bleeds vs 0.8 real-world baseline).   │
│ 6. Click "Escalate to Leadership".                                                            │
│                                                                                               │
│ MINUTE 3 (2:00–3:00) — EXECUTIVE SIGN-OFF & TAMPER-PROOF AUDIT                                │
│ 7. Switch persona to "Executive Leadership" in Settings.                                      │
│ 8. Open /functions. Click [Approve Official Directive].                                       │
│ 9. Open /observability. Show the permanent tamper-proof audit log entry with tracking ID.    │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Easy Q&A Defense (Simple Answers to Tough Questions)

| # | Tough Question from Judges | Your Simple, Confident Answer |
|---|---------------------------|-------------------------------|
| **1** | *"How do you prevent the AI from making up fake data?"* | *"MetaRadar separates facts from opinions. Facts are extracted directly from primary text and labeled `[FACT]`. Every statement in Athena has a clickable link to a real PubMed PMID or trial ID."* |
| **2** | *"Is private Novo Nordisk data safe from leaking to cloud AI?"* | *"100% safe. MetaRadar runs **Local Gemma 3** [JEM-uh three] completely offline on local hardware. No private data is ever sent to public AI servers."* |
| **3** | *"How is this different from a standard RSS news feed?"* | *"An RSS feed just dumps raw text. MetaRadar groups news across 8 sources in 48 hours, catches conflicting claims using AI, spots missing trial disclosures, and delivers Four-Question Decision Briefs with leadership approvals."* |
| **4** | *"Why did you use math for priority scoring instead of asking an AI?"* | *"AI scores change unpredictably every time you ask. Our 4-factor math formula (Novelty + Clinical + Regulatory + Freshness) is 100% transparent, explainable, and consistent."* |
| **5** | *"What happens if an external website goes down?"* | *"All connectors have automatic safety retries and rate governors. If a site is down, MetaRadar serves saved records without crashing."* |
| **6** | *"How fast is the AI answer?"* | *"Because we use vector search and local AI streaming, the first word appears in less than **80 milliseconds**, and full search takes under **250 milliseconds**."* |
| **7** | *"Can someone edit or delete the approval history?"* | *"No. Our database uses a physical **WORM [Worm] tamper-proof lock**. Even a database admin cannot edit or delete an approval record once saved."* |
| **8** | *"How does the system learn what news we care about?"* | *"When team members give 1 to 5-star ratings, MetaRadar automatically tunes its scoring weights so important clinical news ranks higher."* |

---

*Document Author: Team MetaRadar (MSRIT Bangalore) | Novo Nordisk GBS Hackathon 2026 Problem Statement #3*
