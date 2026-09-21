#!/usr/bin/env python3
"""Pull sleep totals out of an Apple Health export.

Why this exists: summing sleep stage intervals inside the Shortcuts app is a
four-action Repeat loop per stage, it breaks in ways that are invisible from
outside the phone, and debugging it costs an hour. Apple's own export already
contains every interval. Parsing it here takes seconds and is debuggable.

Usage:
  1. iPhone Health app -> profile picture -> Export All Health Data
  2. AirDrop export.zip to the Mac, unzip it
  3. grep -a 'HKCategoryTypeIdentifierSleepAnalysis' export.xml > /tmp/sleep_records.xml
     (export.xml is ~2GB; grep first, then parse the few thousand matching lines)
  4. python3 scripts/parse_health_export.py
  5. POST the three numbers to /ingest

Grail's /api/parse-apple-health endpoint does the same thing server-side, but
it wants the whole multi-hundred-MB file uploaded. For a one-off, this is faster.
"""
import re, collections
from datetime import datetime, timedelta

ASLEEP = {'Asleep','AsleepCore','AsleepDeep','AsleepREM','AsleepUnspecified'}
rec = re.compile(r'startDate="([^"]+)"\s+endDate="([^"]+)"\s+value="HKCategoryValueSleepAnalysis(\w+)"')

nights = collections.defaultdict(lambda: collections.Counter())
for line in open('/tmp/sleep_records.xml', errors='ignore'):
    m = rec.search(line)
    if not m: continue
    s, e, val = m.groups()
    try:
        sd = datetime.strptime(s[:19], '%Y-%m-%d %H:%M:%S')
        ed = datetime.strptime(e[:19], '%Y-%m-%d %H:%M:%S')
    except ValueError:
        continue
    mins = (ed - sd).total_seconds() / 60
    if mins <= 0 or mins > 16*60: continue
    # a night is keyed by the morning you woke on
    night = ed.date()
    if val in ASLEEP:
        nights[night]['asleep'] += mins
        if val == 'AsleepDeep': nights[night]['deep'] += mins
        if val == 'AsleepREM':  nights[night]['rem']  += mins
    elif val == 'Awake':
        nights[night]['awake'] += mins

print(f"{'night of':<12}{'total':>9}{'deep':>8}{'rem':>8}{'awake':>8}")
print('-'*45)
for night in sorted(nights)[-7:]:
    c = nights[night]
    h, m = divmod(int(c['asleep']), 60)
    print(f"{night!s:<12}{f'{h}h {m}m':>9}{int(c['deep']):>7}m{int(c['rem']):>7}m{int(c['awake']):>7}m")

latest = max(nights)
c = nights[latest]
print(f"\nLATEST NIGHT ({latest}):")
print(f"  sleep_hours    = {round(c['asleep']/60, 2)}")
print(f"  deep_sleep_min = {round(c['deep'], 1)}")
print(f"  rem_sleep_min  = {round(c['rem'], 1)}")
