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


---

# ADDING SLEEP (2026-09-21)

Sleep is the last big gap: HAILO's Recovery screen and hypnogram are built on it,
and until it arrives they render `--h --m` over a ghosted chart. Grail's `/ingest`
already accepts `sleep_hours`, `deep_sleep_min` and `rem_sleep_min` as plain
numbers — **no server change is needed.** All the work is in the Shortcut.

## Why this is not a Tier-1 copy-paste

The Tier-1 recipe (Find Health Samples → Limit 1 → Value) cannot work here. Apple
stores sleep as a series of **stage intervals** — dozens of rows per night, each
with a start, an end and a stage — not one number. There is no single Value to read.

**Do NOT use the `Duration` property.** It serialises unpredictably and may or may
not be seconds depending on iOS version. Use start and end dates with
**Get Time Between Dates**, which is explicit about its unit.

## Before you touch anything — the gotchas that already cost two runs

- After the Health permission prompt, **re-check Type / Sort / Order / Limit.** The
  prompt wipes the action config.
- **Confirm the blue variable chip is actually in the field** before running. An
  empty field posts `""` and `/ingest` rejects it.
- URL is exactly `https://ailiv.health/ingest` — `ailiv` no trailing e, `ingest`
  with a G, `https` not `http`.

---

## STAGE 1 — total sleep only (do this first)

This alone un-ghosts the big `7h 42m` figure on HAILO's Recovery screen. It is the
smaller job and the bigger visible win, so it goes first.

1. Open `Grail Sync`.
2. Add **Find Health Samples**
   - Type: **Sleep Analysis**
   - Start Date: **is in the last** → **1 day**  (do NOT set Limit 1 — you want them all)
3. Add **Filter** (or set the filter inside the Find action if your iOS shows it there)
   - Keep only samples whose **Value** contains **Asleep**
   - This drops "In Bed" and "Awake", which would otherwise inflate the total.
4. Add **Repeat with Each** over the filtered samples. Inside the loop:
   - **Get Time Between Dates** — from the item's **Start Date** to its **End Date**,
     unit **Minutes**
   - **Add** that to a running total (Calculate → Add, or a `Set Variable` accumulator
     named `sleepMin`)
5. After the loop: **Calculate** `sleepMin ÷ 60` → rename the result `sleepHours`.
6. In your existing **Dictionary**, add one key:

   | Key | Value |
   |-----|-------|
   | `sleep_hours` | `sleepHours` |

7. Run it. Then check it landed:

   ```bash
   curl -s https://ailiv.health/api/data | python3 -m json.tool | grep -i sleep
   ```

   `sleep_hours` should be a number near last night's actual total.

**If your iOS build offers a unit selector on Find Health Samples** (some versions let
you pick Hours directly), you can skip the loop: set unit **Hours**, then
**Calculate Statistics → Sum**. Try that first — if the option is there, Stage 1 is
three actions instead of six.

---

## STAGE 2 — deep and REM (only after Stage 1 posts a sane number)

Same loop, twice more, with a different filter each time. The stage names Apple
uses are `Asleep Deep`, `Asleep REM` and `Asleep Core`.

- Duplicate the Stage 1 block. Change the filter to **Value is Asleep Deep**.
  Do NOT divide by 60 — Grail wants minutes. Rename the total `deepMin`.
- Duplicate again, filter **Value is Asleep REM**, rename `remMin`.
- Add to the Dictionary:

  | Key | Value |
  |-----|-------|
  | `deep_sleep_min` | `deepMin` |
  | `rem_sleep_min` | `remMin` |

Verify the same way. Sanity check: deep + REM should be **less than** total sleep,
and deep is usually 60-110 min on a normal night. If deep comes back larger than
total, the filter is matching "Asleep" as a substring of every stage — make it an
exact match, not "contains".

---

## Run it every morning

Sleep only changes once a day, and only after you wake. Shortcuts app →
**Automation** → **New** → **Time of Day** → around **08:00**, run `Grail Sync`,
and turn **Ask Before Running** OFF or it will silently never fire.

This also fixes the other half of the problem: as of 2026-09-21 the feed had gone
**25 hours stale** because the Shortcut is manual-run. A daily automation keeps
every field current, not just sleep.


---

# SLEEP: THE RECIPE THAT ACTUALLY WORKS (proven 2026-09-21)

Returned **41** for deep sleep minutes on the first clean run. Build this block once,
then duplicate it per stage.

## What does NOT work — do not retry these

- **`Calculate Statistics` directly on the samples.** Fails with *"couldn't convert
  from Text to Number"*. Sleep samples' Value is text ("Deep", "Core"), not a number,
  and the action offers no Duration property to aggregate instead.
- **The `Duration` property.** Not reachable this way, and its units are inconsistent
  across iOS versions even when it is.
- **Searching the action list for "Sleep Analysis".** It is not an action. It is a
  value inside the **Type** field of **Find Health Samples**, and in current iOS it is
  called just **Sleep**.

## The block — four actions

1. **Find Health Samples**
   - Type **is** **Sleep**
   - Start Date **is in the last** **1** **day**
   - **Value** **contains** **Deep**   ← `contains`, not `is`. Exact stage spelling
     varies by iOS; `contains` sidesteps having to know it.
   - Sort by None, **Limit OFF** (you want every sample, not one)
2. **Repeat with each item in** *Health Samples*
3. *(inside the loop)* **Get Minutes between** *Repeat Item → **Start Date***
   **and** *Repeat Item → **End Date***
   - Both chips must carry a date property. A bare `Repeat Item` is the whole sample
     object and throws the same Text-to-Number error.
   - The action is added AFTER `End Repeat` by default — drag it inside the loop.
4. *(after `End Repeat`)* **Calculate the Sum of** *Repeat Results*
   - Shortcuts collects each iteration's output into `Repeat Results` automatically.
     No manual accumulator variable is needed.

Rename the Sum result (long-press → Rename) to `deepMin`.

## Then duplicate it per stage

| Filter value | Rename result | Grail key | Units |
|---|---|---|---|
| contains `Deep` | `deepMin` | `deep_sleep_min` | minutes |
| contains `REM`  | `remMin`  | `rem_sleep_min`  | minutes |
| total asleep (see below) | `sleepHours` | `sleep_hours` | **hours** — divide the sum by 60 |

**Total sleep:** try **Value contains `sleep`** first. If Apple's strings carry the
Asleep prefix (AsleepCore / AsleepDeep / AsleepREM) this catches all three stages
while excluding `Awake` and `In Bed`. If it returns 0, the strings are bare stage
names — in that case build three blocks (Core, Deep, REM) and add them together.

Sanity check before trusting it: **deep + REM must be less than total**, and total
should land near the hours you actually slept.


---

# STOP — READ THIS BEFORE BUILDING SLEEP IN SHORTCUTS (2026-09-21)

**Do not build sleep stage maths in the Shortcuts app.** It cost an hour and did
not finish. Use the Apple Health export instead — it took about five minutes and
produced all three numbers including REM.

Grail already had the parser the whole time: `/api/parse-apple-health` handles
`AsleepCore`, `AsleepDeep`, `AsleepREM` and writes sleep_hours / deep_sleep_min /
rem_sleep_min straight into the health file. Nobody checked before starting on the
Shortcut. Check what already exists first.

## The route that works

1. iPhone **Health app** -> profile picture -> **Export All Health Data** (takes a
   few minutes; the zip was 108MB and export.xml inside it was 2.3GB)
2. AirDrop to the Mac, unzip
3. `grep -a 'HKCategoryTypeIdentifierSleepAnalysis' export.xml > /tmp/sleep_records.xml`
   — grep first. Parsing 2.3GB of XML directly is pointless when ~15,000 lines match.
4. `python3 scripts/parse_health_export.py` — prints the last 7 nights
5. POST the three numbers to `/ingest`

Verified 2026-09-21: 7h 50m total, 37.5 min deep, 141.6 min REM. Landed in
`/api/data` and rendered in HAILO immediately.

## What the Shortcut attempt taught us anyway

- Stage values are **bare names** — `Core`, `Deep`, `REM`, `Awake`, `In Bed`. There
  is no "Asleep" prefix, so `Value contains sleep` matches nothing.
- Use `contains`, not `is`.
- The export also contains `AsleepUnspecified` (2036 records) — older watchOS, before
  stage tracking. Any total that ignores it will undercount historic nights.
- `Calculate Statistics` cannot aggregate health samples at all: "couldn't convert
  from Text to Number".
- The daily HR/HRV Shortcut still works and is untouched. Sleep is the only part
  that moves to the export route.

## Still open

The export is manual, so sleep will go stale until it is re-run. Options, roughly
in order of effort: re-export weekly; finish the Shortcut loop another day; or find
out why `Value contains REM` matched nothing on the phone when the export clearly
holds 1,353 REM records.
