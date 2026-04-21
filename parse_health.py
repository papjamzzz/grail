#!/usr/bin/env python3
"""
Parse Apple Health export.xml → grail/health_data.json
Run: python3 parse_health.py /path/to/apple_health_export/export.xml
"""

import xml.etree.ElementTree as ET
import json, sys, os
from datetime import datetime, timedelta
from collections import defaultdict

EXPORT = sys.argv[1] if len(sys.argv) > 1 else \
    os.path.expanduser("~/Desktop/apple_health_export/export.xml")

OUT = os.path.join(os.path.dirname(__file__), "health_data.json")

# ── Types we care about ───────────────────────────────────────────────────────
TARGETS = {
    "HKQuantityTypeIdentifierRestingHeartRate":        ("resting_hr",         "count/min"),
    "HKQuantityTypeIdentifierHeartRate":               ("heart_rate",          "count/min"),
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN":("hrv",                 "ms"),
    "HKQuantityTypeIdentifierOxygenSaturation":        ("spo2",                "%"),
    "HKQuantityTypeIdentifierRespiratoryRate":         ("respiratory_rate",    "count/min"),
    "HKQuantityTypeIdentifierVO2Max":                  ("vo2_max",             "mL/kg/min"),
    "HKQuantityTypeIdentifierBodyTemperature":         ("temperature",         "degC"),
    "HKQuantityTypeIdentifierBodyFatPercentage":       ("body_fat_pct",        "%"),
    "HKQuantityTypeIdentifierBodyMass":                ("body_mass_kg",        "kg"),
    "HKQuantityTypeIdentifierAppleWalkingSteadiness": ("walking_steadiness",  "%"),
    "HKQuantityTypeIdentifierWalkingAsymmetryPercentage":("walking_asymmetry","%" ),
    "HKQuantityTypeIdentifierWalkingSpeed":            ("walking_speed_kmh",   "km/hr"),
    "HKQuantityTypeIdentifierWaistCircumference":      ("waist_cm",            "cm"),
    "HKQuantityTypeIdentifierHeight":                  ("height_cm",           "cm"),
    "HKQuantityTypeIdentifierSixMinuteWalkTestDistance":("six_min_walk_m",     "m"),
    "HKQuantityTypeIdentifierWalkingHeartRateAverage": ("walking_hr",          "count/min"),
    "HKQuantityTypeIdentifierFlightsClimbed":          ("flights_climbed",     "count"),
    "HKQuantityTypeIdentifierTimeInDaylight":          ("daylight_min",        "min"),
    "HKQuantityTypeIdentifierPhysicalEffort":          ("physical_effort",     "MET"),
    "HKQuantityTypeIdentifierAppleSleepingBreathingDisturbances":
                                                       ("sleep_breath_dist",   "count/hr"),
}

print(f"Parsing {EXPORT} …")

# ── Streaming parse — file can be huge ───────────────────────────────────────
buckets = defaultdict(list)   # type → [(datetime, float)]
sleep_records = []            # (startDate, endDate, value) for sleep analysis

ctx = ET.iterparse(EXPORT, events=("start",))
for event, elem in ctx:
    tag = elem.tag
    if tag == "Record":
        t    = elem.get("type", "")
        val  = elem.get("value", "")
        sd   = elem.get("startDate", "")
        ed   = elem.get("endDate", "")

        if t == "HKCategoryTypeIdentifierSleepAnalysis" and val and sd and ed:
            try:
                s = datetime.strptime(sd[:19], "%Y-%m-%d %H:%M:%S")
                e = datetime.strptime(ed[:19], "%Y-%m-%d %H:%M:%S")
                sleep_records.append((s, e, val))
            except Exception:
                pass

        if t in TARGETS and val and sd:
            try:
                dt  = datetime.strptime(sd[:19], "%Y-%m-%d %H:%M:%S")
                fv  = float(val)
                buckets[t].append((dt, fv))
            except Exception:
                pass

        elem.clear()

# ── Most-recent value per type ────────────────────────────────────────────────
result = {}
for hk_type, (field, unit) in TARGETS.items():
    rows = buckets.get(hk_type, [])
    if rows:
        rows.sort(key=lambda x: x[0])
        dt, v = rows[-1]
        # convert % to 0-1 where Apple sends ratio
        if unit == "%" and v <= 1.0:
            v = round(v * 100, 1)
        elif unit == "%":
            v = round(v, 1)
        else:
            v = round(v, 2)
        result[field] = v
        result[field + "_date"] = dt.strftime("%Y-%m-%d")
        print(f"  {field:35s} = {v} ({dt.date()})")

# ── Daily step count — sum for most recent day that has data ─────────────────
step_rows = buckets.get("HKQuantityTypeIdentifierStepCount", [])
if step_rows:
    step_rows.sort(key=lambda x: x[0])
    latest_day = step_rows[-1][0].date()
    daily_steps = sum(v for dt, v in step_rows if dt.date() == latest_day)
    result["step_count"] = int(daily_steps)
    result["step_count_date"] = str(latest_day)
    print(f"  {'step_count':35s} = {int(daily_steps)} ({latest_day})")

# ── Sleep analysis — most recent night ───────────────────────────────────────
# HKCategoryValueSleepAnalysis: 0=InBed, 1=Asleep(any), 4=Core, 5=Deep, 6=REM, 7=Awake
if sleep_records:
    sleep_records.sort(key=lambda x: x[0])
    # most recent window = last 24h that contain sleep
    latest_end = sleep_records[-1][1]
    window_start = latest_end - timedelta(hours=24)
    recent = [(s,e,v) for s,e,v in sleep_records if e >= window_start]

    ASLEEP_VALS = {"HKCategoryValueSleepAnalysisAsleep",
                   "HKCategoryValueSleepAnalysisAsleepCore",
                   "HKCategoryValueSleepAnalysisAsleepDeep",
                   "HKCategoryValueSleepAnalysisAsleepREM"}
    DEEP_VALS   = {"HKCategoryValueSleepAnalysisAsleepDeep"}
    REM_VALS    = {"HKCategoryValueSleepAnalysisAsleepREM"}

    total_asleep = sum((e-s).total_seconds()/3600 for s,e,v in recent if v in ASLEEP_VALS)
    deep_sleep   = sum((e-s).total_seconds()/3600 for s,e,v in recent if v in DEEP_VALS)
    rem_sleep    = sum((e-s).total_seconds()/3600 for s,e,v in recent if v in REM_VALS)

    result["sleep_hours"]    = round(total_asleep, 2)
    result["deep_sleep_hrs"] = round(deep_sleep, 2)
    result["rem_sleep_hrs"]  = round(rem_sleep, 2)
    result["sleep_date"]     = latest_end.strftime("%Y-%m-%d")

    if total_asleep > 0:
        result["deep_sleep_pct"] = round(deep_sleep / total_asleep * 100, 1)
        result["rem_sleep_pct"]  = round(rem_sleep  / total_asleep * 100, 1)
    print(f"  {'sleep_hours':35s} = {result['sleep_hours']} hrs  "
          f"(deep {result.get('deep_sleep_pct','?')}%  rem {result.get('rem_sleep_pct','?')}%)")

result["last_updated"] = datetime.now().isoformat()

with open(OUT, "w") as f:
    json.dump(result, f, indent=2)

print(f"\n✓ Written → {OUT}")
print(f"  {len(result)} fields captured")
