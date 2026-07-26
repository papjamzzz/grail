# Apple Health → Grail via Shortcuts

> **STATUS: WORKING as of 2026-07-26.** Shortcut `Grail Sync` on Jeremiah's iPhone
> posted a real heart rate (70 bpm) to `/ingest`, verified server-side against a
> deliberately implausible 99.0 baseline. Currently sends `heart_rate` only.

## Gotchas that actually cost time building it (read before editing the Shortcut)
1. **`Get Details of Health Sample` does not exist** — searching for it adds
   *Get Details of **Files***, whose detail list is File Path / File Size. Wrong action.
   Instead: reference the **Health Samples** variable directly in the value field and
   tap it — `Value` is already the default selected property. No extra action needed.
2. **The value field silently stays empty.** Inserting the variable is a separate tap
   from creating the field, and any interruption (permission prompt, URL edit) drops
   it. An empty value posts `""`, which `/ingest` rejects. **Always confirm the blue
   chip is in the field before running.** This broke two runs in a row.
3. **The permission prompt wipes the action's config.** After granting Health access,
   re-check Type / Sort by / Order / Limit — they revert.
4. **URL, exactly:** `https://ailiv.health/ingest`
   - `ailiv` — no trailing "e". `ailive.health` was bought but never wired: **no DNS at all.**
   - `ingest` — G not J. `/injest` 404s.
   - `https`, not `http` — Shortcuts defaults to `http://`, and a POST body can be
     dropped on the redirect.
5. **`Sort by: Start Date` + `Order: Latest First` + `Limit 1` are mandatory.** Without
   them the action returns every sample as a list, not a number.


Pushes **current** (not live) Apple Health values from the iPhone to Grail's
`/ingest`. No Xcode, no dev pairing, no provisioning expiry — this is why it
exists: the Apple Watch dev path is permanently blocked (see `~/pulse/CLAUDE.md`).

Data flows: **Watch → Apple Health on iPhone (automatic) → Shortcut → `/ingest` → Grail.**
The Watch never talks to Grail directly. Nothing needs to be installed on the Watch.

- **Endpoint:** `https://ailiv.health/ingest`
- **Method:** POST, `Content-Type: application/json`
- **Never put health values in the URL/query string** — body only.

---

## Build it once (iPhone → Shortcuts app)

### Step 1 — Start with TWO metrics only
Do not build all fields on the first pass. Prove the pipe works, then add more.

New Shortcut → name it `Grail Sync`.

### Step 2 — Get heart rate
1. Add action **Find Health Samples**
2. Set it to: type **Heart Rate**, **Sort by** Date, **Order** Latest First, **Limit** 1
3. Add action **Get Details of Health Sample** → detail **Value**
4. Rename that variable (long-press → Rename) to `hr`

### Step 3 — Get HRV
Repeat Step 2 exactly, but type **Heart Rate Variability**. Rename to `hrv`.

### Step 4 — Build the payload
Add action **Dictionary**, with these keys (Text values = the variables above):

| Key | Value |
|-----|-------|
| `heart_rate` | `hr` |
| `hrv` | `hrv` |

### Step 5 — Send it
Add action **Get Contents of URL**
- URL: `https://ailiv.health/ingest`
- Method: **POST**
- Request Body: **JSON**
- Body: the **Dictionary** from Step 4

Run it. Grail should return `{"ok": true, ...}`.

### Step 6 — Confirm it landed
Open `https://ailiv.health/api/data` — `heart_rate` and `hrv` should match, and
`age_seconds` should be a few seconds with `stale: false`.

---

## FULL BIOMARKER AUDIT (2026-07-26)

Grail's `DEFAULT_HEALTH` has 33 value keys. Not all are reachable from Apple Health,
and the ones that are split into three different Shortcut recipes. Getting the recipe
wrong produces a plausible-looking wrong number, not an error.

### Tier 1 — point-in-time. Uses the EXACT pattern already built.
`Find Health Samples` → Type → last 1 day → Sort **Start Date** / **Latest First** / **Limit 1**
→ insert variable. Four taps each.

| Grail key | Apple Health type | Caveat |
|-----------|-------------------|--------|
| `heart_rate` | Heart Rate | ✅ already wired. Updates every few min when worn. |
| `resting_hr` | Resting Heart Rate | Computed once daily |
| `walking_hr` | Walking Heart Rate Average | Daily average |
| `hrv` | Heart Rate Variability (SDNN) | Apple's own schedule, mostly overnight. **Equil refuses this as live — Grail only.** |
| `spo2` | Blood Oxygen Saturation | ⚠️ **Disabled on US Apple Watches** (patent dispute). Expect nothing unless from older data or another device. |
| `respiratory_rate` | Respiratory Rate | ⚠️ **Sleep only** — no daytime samples |
| `temperature` | Wrist Temperature | ⚠️ **Sleep only**, Series 8+/Ultra |
| `vo2_max` | VO2 Max | Occasional, needs outdoor workouts |
| `walking_speed` | Walking Speed | Periodic |
| `cardio_recovery` | Cardio Recovery | Only after qualifying workouts |
| `weight` | Body Mass | Manual or smart scale |
| `body_fat` | Body Fat Percentage | Manual or smart scale |
| `lean_mass` | Lean Body Mass | Manual or smart scale |
| `systolic_bp` | Blood Pressure Systolic | Manual / cuff |
| `diastolic_bp` | Blood Pressure Diastolic | Manual / cuff |
| `waist_cm` | Waist Circumference | Manual |
| `glucose` | Blood Glucose | Manual or CGM |

### Tier 2 — CUMULATIVE. The Tier 1 recipe gives a WRONG number here.
These accumulate across the day in many small samples. `Limit 1` returns only the **last
increment** — e.g. the last 12 steps, not today's 8,400. You must sum instead:

`Find Health Samples` → Type → **Start Date is in the last 1 day** → **Limit OFF**
→ then add **Calculate Statistics** → operation **Sum** → insert *that* result.

| Grail key | Apple Health type |
|-----------|-------------------|
| `daily_steps` | Steps |
| `walk_run_km` | Walking + Running Distance |
| `flights_climbed` | Flights Climbed |
| `active_calories` | Active Energy |
| `resting_calories` | Resting Energy |
| `exercise_minutes` | Apple Exercise Time |
| `stand_minutes` | Apple Stand Time |
| `daylight_minutes` | Time in Daylight |

### Tier 3 — needs duration maths. Skip unless genuinely wanted.
Stored as intervals/sessions, not numbers. Requires computing durations from start/end
dates inside the Shortcut, then summing.

| Grail key | Why |
|-----------|-----|
| `sleep_hours` | Sleep is stage intervals (awake/core/deep/REM), not a total |
| `deep_sleep_min` | Must filter to the Deep stage, then sum durations |
| `rem_sleep_min` | Must filter to the REM stage, then sum durations |
| `mindful_minutes` | Mindful Sessions are intervals |

### Tier 4 — NOT reachable. Manual entry only.
Not queryable HealthKit quantity types. Grail's schema keeps them for manual/lab entry.

`testosterone` · `crp` · `vitamin_d` · `ferritin` · `cortisol`

### Not in Grail's schema at all
**Stillness / motion.** Apple Health stores no accelerometer or Core Motion stream, so
Shortcuts cannot read it at any tier, and Grail has no key for it. Equil *does* accept
`motion`, but nothing in this pipeline can honestly supply it. Real options: an
iPhone-side Core Motion app, or a BLE chest strap. Step count is **not** a substitute —
it lags by design and would break Equil's `motion<0.2` coherence lock.

### Equil vs Grail
Equil's `/webhook` accepts **only** `heart_rate` and `motion`. It deliberately dropped
HRV, SpO2 and respiratory rate as live signals ("no fake numbers"). Every other field
above goes to the Grail action only.

## Then add the rest

Same Find Health Samples → Get Value → add a Dictionary row. Key names must match
**exactly** (these are Grail's `DEFAULT_HEALTH` keys — a typo is silently ignored,
`/ingest` only accepts keys it recognises):

| Grail key | Apple Health sample type |
|-----------|--------------------------|
| `heart_rate` | Heart Rate |
| `resting_hr` | Resting Heart Rate |
| `walking_hr` | Walking Heart Rate Average |
| `hrv` | Heart Rate Variability |
| `spo2` | Blood Oxygen Saturation |
| `respiratory_rate` | Respiratory Rate |
| `temperature` | Wrist Temperature |
| `daily_steps` | Steps |
| `walk_run_km` | Walking + Running Distance |
| `flights_climbed` | Flights Climbed |
| `active_calories` | Active Energy |
| `resting_calories` | Resting Energy |
| `exercise_minutes` | Exercise Minutes |
| `stand_minutes` | Stand Minutes |
| `vo2_max` | VO2 Max |
| `cardio_recovery` | Cardio Recovery |
| `walking_speed` | Walking Speed |
| `daylight_minutes` | Time in Daylight |
| `mindful_minutes` | Mindful Minutes |
| `sleep_hours` | Sleep (see note) |

**Sleep is not a plain number.** Apple stores sleep as stage intervals, not a
single value, so `sleep_hours` / `deep_sleep_min` / `rem_sleep_min` need duration
maths in the Shortcut rather than a straight Get Value. Leave these out of v1 —
partial honest data beats a wrong number.

Everything below the "Watch auto" line in `DEFAULT_HEALTH` (weight, body fat, BP,
glucose, labs) is **manual entry**, not available from Health automatically. Don't
wire those here.

---

## Make it run on its own

Shortcuts app → **Automation** tab → **New** → **Time of Day**.
- Pick a cadence that matches how fresh "current" needs to be (hourly is plenty).
- Turn **Ask Before Running OFF**, or it will prompt every single time and silently
  stop syncing when you miss the prompt.

Grail flags anything older than **1 hour** as `stale: true`, so pick an interval
under that or the dashboard will correctly call your data stale.

---

## Honesty constraint

This is **current, not live.** Values are as fresh as the last automation run, and
Apple Health itself only updates most of these periodically — HRV, SpO2,
respiratory rate and wrist temperature are computed on Apple's own schedule, not
on demand. Do not present this as real-time. `/api/data` returns `age_seconds`
and `stale` precisely so the UI can tell the truth about how old a reading is.
