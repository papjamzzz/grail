# AILIV — Dev Notes
*Jeremiah Smith + Christian Seeber | Internal*

---

## Asset List

### 01 Orbital-Live `LIVE` ★ AI INTEGRATED
**ailiv.health/**
Flagship view. 40 biomarker orbs across 4 orbital rings. Each orb reflects live health status via color, pulse, and glow. Includes real-time health scoring and AI synthesis panel.

- Flask route: `/`
- Canvas-rendered orbs via JS
- 4 orb states: optimal, warning, critical, inactive
- Right sidebar: scoring + detail panels | Status ring at top
- **AI:** `POST /api/grail-guide` → sends all biomarker data to 5i (port 5562) → returns synthesis verdict + per-model results from Claude, GPT, Gemini
- **AI trigger:** "Grail Guidance" button in top bar (hover to reveal)

---

### 02 Cells `LIVE`
**ailiv.health/cells**
Cellular-level visualization. 90 biomarker blobs in a physics-based organic cluster. More emotional, less structured than Orbital. Built for feel over precision.

- Flask route: `/cells`
- Physics simulation via JS
- Electric pastel color palette
- Same biomarker data model as Orbital
- **AI:** None

---

### 03 BioSurface `LIVE`
**ailiv.health/biosurface**
Living 3D terrain map of biological state. Biological systems rendered as a stress-to-optimal color-coded surface. Gives a spatial sense of the body as a landscape.

- Flask route: `/biosurface`
- 3D terrain rendering in-browser
- Color gradient: stress (red) → optimal (green)
- No external 3D lib — pure JS/CSS
- **AI:** None

---

### 04 Body Figure `LIVE`
**ailiv.health/bodyfigure**
Comprehensive system dashboard. Covers cardiovascular, metabolic, hormonal, and recovery metrics in a single view. Full-body read at a glance.

- Flask route: `/bodyfigure`
- Multi-system layout
- 4 biological domains rendered as grouped panels
- CSS variables for all state colors
- **AI:** None

---

### 05 Biobaseline `LIVE`
**ailiv.health/biobaseline**
Baseline visualization across 6 biological systems including metabolic, hormonal, and longevity metrics. Shows where the user sits relative to their personal baseline.

- Flask route: `/biobaseline`
- 6-system layout
- Baseline comparison logic
- Longevity markers included
- Static data for now
- **AI:** Sonar integration pending

---

### 06 Signal Bridge `LIVE`
**ailiv.health/signal-bridge**
Cross-platform correlation tool. Links Apple Health and WHOOP data across 4 time periods. Surfaces relationships between metrics that wouldn't be visible in either app alone.

- Flask route: `/signal-bridge`
- Apple Health + WHOOP data correlation
- 4 time windows
- Cross-device logic
- **AI:** Early Sonar proof of concept — correlation logic not yet AI-driven

---

### 07 Roots `LIVE`
**ailiv.health/rootcause**
Force-directed network map. Connects flagged labs to root causes to targeted protocols. Shows why something is off and what to do about it — not just what the number is.

- Flask route: `/rootcause`
- Force-directed graph (JS)
- Node types: lab marker → root cause → protocol
- Wearable data integration
- **AI:** None — strong candidate for AI-generated protocol recommendations

---

### 08 Centrifuge `LIVE`
**ailiv.health/ailiv**
Ambient biometric display. Designed for presentations and demonstrations. All biomarkers in a single spinning visual — more art than dashboard.

- Flask route: `/ailiv`
- Rotating/centrifuge animation
- Presentation mode — no interaction required
- Full-screen ambient display
- **AI:** None

---

### 09 Console `LIVE`
**ailiv.health/console**
Internal control panel. Shows biomarker data, system logs, and health metrics in a structured console interface. Admin and dev-facing.

- Flask route: `/console`
- System logs + health metrics
- Internal use only — not user-facing in v1
- **AI:** None

---

## AI Integration Summary

| Asset | AI Status | Details |
|-------|-----------|---------|
| Orbital-Live | ✅ Live | 5i synthesis via Grail Guidance — Claude + GPT + Gemini verdict |
| Biobaseline | ⏳ Pending | Sonar integration planned |
| Signal Bridge | ⏳ Prototype | Sonar proof of concept — correlation layer not yet AI |
| Roots | 💡 Candidate | Protocol recommendations — strong AI fit |
| Cells | — | None |
| BioSurface | — | None |
| Body Figure | — | None |
| Centrifuge | — | None |
| Console | — | None |

---

## Sonar
Sonar is the planned AI correlation layer for the platform. When live, it will power:
- Cross-metric pattern detection (Signal Bridge)
- Baseline deviation analysis (Biobaseline)
- Potentially: per-biomarker root cause reasoning (Roots)

---

*Last updated: 2026-05-04*
