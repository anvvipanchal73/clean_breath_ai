# CleanBreath AI: Family Smog & Urban Pollution Defense

A production-grade, mobile-first GenAI assistant that empowers households and community groups to navigate severe winter smog and urban air pollution with grounded, location-specific guidance, indoor air hacks, and deterministic, peer-reviewed impact tracking.

---

## 🏛️ Architecture Overview

```text
+-------------------------------------------------------------------------+
|                  CleanBreath Mobile PWA Client                          |
|  - Glassmorphic UI with dynamic AQI gradient aura & particle simulation |
|  - Animated SVG Arc Gauge, 48h Forecast Best-Window Highlighting        |
|  - 8-Step Profile Wizard, Sourced Impact Counters (zero hallucinations) |
|  - Voice Input, WhatsApp Card Export, Confetti Gamification & Pledges   |
|  - Bilingual (English + Hindi) with WCAG AA compliance                  |
+-----------------------------------+-------------------------------------+
                                    | REST / JSON
                                    v
+-------------------------------------------------------------------------+
|                    FastAPI Backend Engine (Port 8000)                   |
|  ├── Air Quality Service: Open-Meteo API ingestion (primary & fallback) |
|  ├── Risk Classifier: 5 Tiers (Green..Maroon) + 1-Tier Sensitive Shift  |
|  ├── Daily Plan Engine: 5-Stage Time-Blocked Routine (Do vs Avoid)      |
|  ├── Impact Engine: Deterministic Factor Table (impact_factors.v1.json) |
|  └── Gemini Chat Agent: Tool Calling, Knowledge Grounding & Citations   |
|                         + Urgent Clinical Triage Escalation Guardrails  |
+-----------------------------------+-------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|            Sourced Knowledge Base (/knowledge) & Factor Config          |
|  - WHO Global Air Quality Guidelines 2021 (ISBN 978-92-4-003422-8)      |
|  - CPCB National AQI Advisories (2014) & BS-VI Vehicular Standards     |
|  - AHAM AC-1-2015 Purifier Standards & Bliss et al. 2021 DIY Corsi Box |
|  - CDC NIOSH Respirator Guidance & Lindsley et al. 2021 (JAMA)          |
+-------------------------------------------------------------------------+
```

---

## 🚀 Quick Run Guide

### 1. Prerequisites Installed in Environment
- **Node.js**: `v20.18.0` & `npm 10.8.2` (configured in `~/.gemini/antigravity/bin`)
- **Python**: `3.15.2` with `uv` (`0.13.10`)
- **Backend Port**: `http://localhost:8000`
- **Frontend Port**: `http://localhost:3000`

### 2. Running Backend (FastAPI)
```bash
cd backend
export PYTHONPATH=.
python3 -m uvicorn app.main:app --port 8000 --host 0.0.0.0
```

### 3. Running Frontend (Next.js / Standalone PWA)
```bash
# Preview server
python3 -m http.server 3000 --directory frontend-preview

# Or full Next.js development server
cd frontend
npm install
npm run dev
```

### 4. Running Verification Test Suite
```bash
cd backend
PYTHONPATH=. python3 -m pytest tests/ -v
```
**Results**: `48 passed, 0 failed` across models, risk classification, and deterministic impact calculations.

---

## 📋 Comprehensive Changelog & Upgrades

### Section 0: Toolchain & Grounding Bug Fixes
- **Node.js 20 installed and symlinked**: Node 20.18.0 and npm 10.8.2 installed to `~/.local/node` and symlinked to user binaries. `uv` installed for rapid virtual environment dependency resolution.
- **Fixed "Walk saves ₹0" & unsourced numbers**: Removed static mock values. Connected calculations directly to `impact_factors.v1.json`. For walking and zero-emission actions, zero monetary savings are explicitly suppressed or labelled as passive.
- **Corrected N95 filtration overclaim**: Fixed to reflect actual NIOSH particulate efficiency (95% against fine aerosols with proper nasal seal, noting leakage on cloth/surgical masks).

### Section 1: End-to-End Functional Features
- **Live Open-Meteo Integration**: Real-time AQI, PM2.5, PM10, and thermal inversion risk fetched by coarse location. Includes cycleable Indian cities (Delhi Dwarka, Anand Vihar, Gurugram, Mumbai, Bengaluru, Kolkata) and manual simulation slider.
- **8-Step Household Onboarding Wizard**: Fully interactive modal capturing city, vulnerable members (asthma, children under 12, elderly), commute mode & distance, home structure, cooking fuel, heating method, and budget orientation.
- **Dynamic 7-Block Routine**: Time-blocked cards with explicit **DO** and **AVOID** markers, detailing the scientific reason and exposure avoidance.
- **Indoor Air Advisor**:
  - Interactive **CADR Purifier Sizing Calculator** using the AHAM AC-1 formula ($CADR \ge \text{Room Volume} \times 0.75$).
  - **DIY Corsi-Rosenthal Box Blueprint** (~300 m³/h CADR at ~₹1,650 vs ₹9,000+ commercial units).
  - **Ventilation Window Advisor** predicting next thermal window.
  - **Myth-Busters**: Explaining Cummings & Waring (2020) houseplant study and CDC mask seal physics.
- **Gemini Chat Agent with Grounded Tool Calling**:
  - Automatic keyword search across WHO, CPCB, and AHAM knowledge corpus.
  - Strict clinical symptom escalation for chest pain, acute breathlessness, or wheezing.
  - Inline source citations appended to every response.
  - Web Speech API voice input integration.
- **Community & Gamification**:
  - Interactive progress ring for collective neighbourhood pledges.
  - 4 pledge actions with instant confetti animation and progress ring advancement.
  - 1-click WhatsApp shareable impact summary.
- **Bilingual EN / Hindi Toggle**: Immediate in-place translation for all health directives, actions, and tabs.
- **Browser Push Notifications**: Service worker push registration prompt with threshold alerts.

### Section 2: Premium UI/UX Redesign
- **Glassmorphism Design Language**: Dark slate glass cards with 24px rounded corners and backdrop blur.
- **Dynamic Risk Aura & Particle Haze**: Ambient radial gradient that transitions from green to orange to maroon based on AQI. Background HTML5 canvas with floating smog particles whose speed and density scale with pollution levels.
- **Animated SVG Arc Gauge**: Precision mathematical arc with animated sweep and pulsing risk level badge.
- **48h Forecast Bar Chart**: Horizontal scrollable hourly forecast highlighting the safest outdoor window.
- **Micro-Interactions**: Confetti burst on pledge completion, spring transitions, and interactive slider feedback.
