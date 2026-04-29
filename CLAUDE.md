# Grail — Re-Entry Brief
*Paste this entire file into a new Claude session to resume immediately.*

---

## What This Is
**Grail** is a luxury biohacking dashboard. Dark canvas, no traditional UI. A central amber orb (the user) surrounded by 40 glowing biomarker orbs in 4 orbital rings. Feels alive, not clinical.

- **Folder:** `~/grail`
- **Port:** 5566
- **Stack:** Flask + vanilla canvas JS
- **GitHub:** not yet pushed (local only)
- **Start:** `cd ~/grail && python3 app.py`
- **View:** http://127.0.0.1:5566

---

## Files
| File | Purpose |
|------|---------|
| `index.html` | Entire frontend — canvas engine, all panels, all JS |
| `app.py` | Flask backend — ingest, meals, symptoms, 5i synthesis |
| `health_data.json` | Live health metrics (written by /ingest) |
| `symptoms.json` | Body/mind/spirit log entries |
| `meals.json` | Meal log entries |
| `requirements.txt` | Just `flask` + `requests` |

---

## Architecture

### Center Orb
- Amber shiny sphere, lighthouse pulse (`Math.pow(sin,3)` — long dark, sharp bright)
- `coreBase = Math.min(W,H) * 0.056` (50% of original)
- Score displayed at center, updates every 4–13 seconds
- Positioned at `oy` (computed between topbar and grail word)

### 40 Node Orbs — 4 Rings
| Ring | Count | Orbit multiplier | Speed |
|------|-------|-----------------|-------|
| 1 (inner) | 8 | 0.50 | 0.042 |
| 2 (middle) | 12 | 0.76 | 0.030 |
| 3 (outer) | 10 | 1.04 | 0.021 |
| 4 (outermost) | 10 | 1.34 | 0.014 |

Each node has: `id`, `label`, `angle`, `ringLevel`, `color`, `glow`, `system`, `unit`, `pct`, `currentPct`, `targetPct`, `minPct`, `maxPct`, `calcValue`, `insight`, `source`, `phase`, `nextChange`, `rec`

The `rec` object has: `diet`, `sleep`, `exercise`, `green` (funny message shown when status is green)

### Status System
`getStatus(n)`: green ≥ 68%, orange ≥ 38%, red < 38%  
Higher `currentPct` = better for ALL nodes (already inverted for CRP, resting HR, etc.)

### 40 Biomarkers
**Ring 1:** Resting HR, HRV, SpO₂, Sleep Duration, Respiratory Rate, VO₂ Max, Wrist Temp, Fasting Glucose  
**Ring 2:** Active HR, Testosterone, CRP, Recovery Index, Cortisol, Vitamin D, Deep Sleep %, REM Sleep %, Daily Steps, Systolic BP, Body Fat %, Ferritin  
**Ring 3:** Magnesium, Omega-3 Index, Insulin Sensitivity, Uric Acid, B12, Zinc, Hydration, Grip Strength, Lactate Threshold, Muscle Mass  
**Ring 4:** Serum Albumin, ALT Liver Enzyme, DHEA-S, Free Testosterone, IGF-1, Homocysteine, ApoB, Fibrinogen, NAD+, TSH/Thyroid

### Scoring
`Math.round(NODES.reduce((s,n) => s + n.currentPct, 0) / NODES.length)`  
Updates every 4–13 seconds. Recovery node is a weighted composite of HRV/resting HR/sleep/resp.

### Simulation
Nodes lerp toward `targetPct` each frame at `*= 0.0007`. Every 9–21 seconds a new random target is chosen (only if no live data for that field).

### Live Data
`GET /api/data` polls every 30s. `applyLiveData()` maps JSON fields → node targetPcts.  
`POST /ingest` body fields: `heart_rate`, `resting_hr`, `hrv`, `spo2`, `sleep_hours`, `respiratory_rate`, `vo2_max`, `temperature`, `glucose`, `testosterone`, `crp`

---

## Visual Engine (canvas)

### Intro Sequence
1. Black screen — `introPhase = 'waiting'`, `burstMult = 0`
2. Golden italic text slides down from top: *"Add Days to Your Life after Adding Life to Your Days"*
3. After 3.4s text fades/scrolls out
4. At 4.15s: `introPhase = 'pop'`, `burstMult = 5.0` → decays to 1.3 over 1.2s
5. Settles at `burstMult = 1.3` forever

### Node Rendering (per frame)
```
pulse    = sin(time*1.9 + phase*8)*0.5 + 0.5         // individual beat
hbBoost  = hbFlash * 2.4                              // random heartbeat flash
nodeAlive= alive + hbBoost
nb       = (14 + pulse*6) * clamp(1 + burstMult*0.08)

haloStr  = (0.14 + pulse*0.18) * nodeAlive            // breathing halo
innerStr = (0.60 + pulse*0.22) * nodeAlive            // inner blob brightness
ring alpha = (0.30 + pulse*0.55) * nodeAlive          // outer ring punch
2nd ring   = (0.05 + pulse*0.18) * nodeAlive          // visible breath ring
```

### Hover Tooltip
Canvas tooltip above the orb: colored status dot + system name. No labels rendered on the orbs themselves.

### Click Panel (`#node-panel`)
Shows: status dot (green/orange/red) + label → system name → value → unit → range bar → insight → source → divider → funny green message (if green) → diet / sleep / move recommendations

---

## Top Bar (hover to reveal)
`Grail Guidance` | `Report-Body` | `Report-Mind` | `Report-Spirit` | `The Guide` | `Settings` | `API Keys` | `Export`

- **Grail Guidance** → POSTs to `/api/grail-guide` → sends everything to 5i at port 5562 → returns synthesis verdict + per-model results
- **Report-Body/Mind/Spirit** → log symptom panels (type field differentiates)
- **The Guide** → info panel explaining the whole system
- **Export** → downloads `grail-export.json`

---

## Backend (app.py)
- Port 5566, Flask
- `POST /ingest` — writes health fields to `health_data.json`
- `GET /api/data` — returns health_data.json
- `POST /log/symptom` — appends to symptoms.json (body: `text`, `severity`, `type`)
- `POST /log/meal` — appends to meals.json (body: `description`, `meal_type`)
- `GET /api/symptoms`, `GET /api/meals`
- `POST /api/grail-guide` — builds rich prompt from all data, POSTs to 5i at `http://127.0.0.1:5562/ask` with `{prompt, verdict:true, models:["claude","gpt","gemini"]}`, returns `{verdict, results, elapsed}`

---

## Key Design Rules
- No labels on orbs (hover only)
- No traditional dashboard layout
- Dark background (`#04040A` / canvas gradient)
- Gold/amber palette: `rgba(201,169,110,x)` throughout
- Font: Cormorant Garamond everywhere (score, grail word, panels, topbar)
- `#grail-word` fixed at `bottom: 22px` via CSS — never touch with JS
- `oy` = orbit center Y, computed in `resize()` from grail word top position
- All node positions use `oy` not `cy`

---

## Files
| File | Purpose |
|------|---------|
| `whoop_token.json` | WHOOP OAuth token (auto-created on connect) |

## WHOOP Integration
- OAuth 2.0 flow: `/whoop/connect` → WHOOP → `/whoop/callback`
- Syncs: resting HR, HRV, SpO2, respiratory rate, sleep hours, recovery score, skin temp, strain
- Routes: `GET /whoop/status`, `POST /whoop/sync`, `POST /whoop/disconnect`
- Settings panel shows Connect/Sync/Disconnect buttons + last sync time
- Requires `.env`: `WHOOP_CLIENT_ID`, `WHOOP_CLIENT_SECRET`, `WHOOP_REDIRECT_URI`
- Register app at: https://developer-dashboard.whoop.com (redirect URI: http://127.0.0.1:5566/whoop/callback)

## What's Done
- [x] 40 biomarker orbs, 4 rings, all orbiting at different speeds
- [x] Organic blob shapes (summed sine waves)
- [x] Lighthouse pulse center orb (shiny material)
- [x] Hover tooltip with status indicator (green/orange/red)
- [x] Click panel: full biomarker read + diet/sleep/exercise recs + funny green message
- [x] Intro phrase animation (scroll-in → hold → fade out → burst)
- [x] Top bar (hidden, reveals on hover) with 8 items
- [x] Grail Guidance (5i synthesis) with verdict + per-model results
- [x] Report-Body, Report-Mind, Report-Spirit logging
- [x] Meal logging
- [x] Live data ingest via /ingest endpoint
- [x] Score computed dynamically from all 40 node pcts
- [x] Apple Health export parsing (endpoint ready, parser not built yet)

## What's Next (ideas queue)
- [ ] Apple Health XML parser — drop export file, nodes go live
- [ ] Apple Shortcuts shortcut for live /ingest push from Watch
- [ ] Third click on node = full 5i synthesis just for that biomarker
- [ ] Timeline view — score over days
- [ ] Connecting nodes with visible tendrils (when two markers correlate)
- [ ] Push 5i verdict back to a specific marker's rec panel
- [ ] Mobile touch support
- [ ] GitHub push (papjamzzz/grail)

---

*Last updated: 2026-04-21 — 40 orbs, 4 rings, status system, rec panels, intro sequence all live*
