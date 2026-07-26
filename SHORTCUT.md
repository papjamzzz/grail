# Apple Health → Grail via Shortcuts

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
