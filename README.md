# Grail — Luxury Biohacking Dashboard

**40 live biomarker orbs. 4 orbital rings. AI health synthesis.**

Grail is not a traditional health dashboard. It's a living visual system — a dark canvas with a central amber orb surrounded by 40 glowing biomarker nodes orbiting in real time. Each node represents a health marker. The whole thing breathes.

**Live:** [grailorbital.creativekonsoles.com](https://grailorbital.creativekonsoles.com)

---

## What It Does

- **40 biomarkers** tracked across 4 orbital rings — cardiovascular, hormonal, metabolic, recovery, and longevity markers
- **AI synthesis** — sends your full biomarker panel to GPT-4, Claude, and Gemini simultaneously, returns a unified health verdict
- **Live data ingest** — `/ingest` endpoint accepts real-time data from Apple Health, wearables, and manual entry
- **Scoring engine** — composite health score computed dynamically across all 40 nodes, updates every 4–13 seconds
- **Status system** — green / orange / red per marker with personalized diet, sleep, and exercise recommendations
- **Report panels** — Body, Mind, and Spirit logging with symptom tracking and meal logging

## Biomarker Rings

| Ring | Markers |
|------|---------|
| Inner (8) | Resting HR, HRV, SpO₂, Sleep Duration, Respiratory Rate, VO₂ Max, Wrist Temp, Fasting Glucose |
| Middle (12) | Active HR, Testosterone, CRP, Recovery Index, Cortisol, Vitamin D, Deep Sleep %, REM %, Steps, BP, Body Fat, Ferritin |
| Outer (10) | Magnesium, Omega-3 Index, Insulin Sensitivity, Uric Acid, B12, Zinc, Hydration, Grip Strength, Lactate Threshold, Muscle Mass |
| Outermost (10) | Albumin, ALT, DHEA-S, Free Testosterone, IGF-1, Homocysteine, ApoB, Fibrinogen, NAD+, TSH |

## Stack

```
Python · Flask · Vanilla Canvas JS · Claude (Anthropic) · GPT-4 (OpenAI) · Gemini (Google)
Railway · No external UI frameworks
```

## Run Locally

```bash
pip install -r requirements.txt
python app.py
# → http://127.0.0.1:5566
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ingest` | POST | Push live health data |
| `/api/data` | GET | Retrieve current biomarker state |
| `/api/grail-guide` | POST | Trigger AI synthesis across all 3 models |
| `/log/symptom` | POST | Log a body/mind/spirit symptom |
| `/log/meal` | POST | Log a meal |

---

*A Creative Konsoles project. Built for people who take their biology seriously.*
