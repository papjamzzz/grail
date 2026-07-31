# AILIV — Luxury Biohacking Dashboard

> **Your biology, visualized.**

A high-resolution health monitoring dashboard featuring 40 live biomarker orbs across 4 orbital rings, AI synthesis across GPT, Claude, and Gemini, and a clinical-grade aesthetic built for serious biohackers.

**Live:** [ailiv.health](https://ailiv.health)

---

## What It Is

AILIV translates your biomarker data into a living, breathing visualization — orbital rings of health intelligence that update in real time and converge into a single AI synthesis verdict.

Built as a clinical-precision tool for people who track their biology seriously.

---

## Features

- **40 biomarker orbs** — organized across 4 orbital rings by health domain
- **4 orbital rings** — Metabolic, Cardiovascular, Hormonal, Recovery
- **Status lights** — green/amber/red per biomarker, calibrated to clinical ranges
- **AI synthesis** — GPT, Claude, and Gemini read your full panel and synthesize a verdict
- **Breath sync orb** — animated respiration guide integrated into the dashboard
- **Luxury aesthetic** — dark theme, precision typography, no noise

---

## Health Domains

| Ring | What It Tracks |
|------|---------------|
| Metabolic | Glucose, HbA1c, insulin sensitivity, lipids, liver panels |
| Cardiovascular | Blood pressure, heart rate, cholesterol, CRP, homocysteine |
| Hormonal | Testosterone, cortisol, thyroid (T3/T4/TSH), DHEA, estrogen |
| Recovery | Sleep quality, HRV, VO2 max, inflammation markers, oxidative stress |

---

## Stack

Python · Flask · Vanilla JS · Railway

---

## Setup

```bash
git clone https://github.com/papjamzzz/grail.git
cd grail
cp .env.example .env
# Fill in ANTHROPIC_API_KEY (labs import + Ask AILIV) and, if you use
# WHOOP sync, WHOOP_CLIENT_ID / WHOOP_CLIENT_SECRET / WHOOP_REDIRECT_URI.
# DATABASE_URL is optional — without it, the 24h Circadian Ring history
# is disabled but the live snapshot (/api/data) still works.
pip install -r requirements.txt
python app.py
```

---

## Part of AILIV / Creative Konsoles

Designed by Christian Seeber and Jeremiah Smith.

Built by [Creative Konsoles](https://creativekonsoles.com) — tools built using thought.

**[creativekonsoles.com](https://creativekonsoles.com)** &nbsp;·&nbsp; support@creativekonsoles.com

<!-- repo maintenance: 2026-05-12 -->
