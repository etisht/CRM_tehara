#!/usr/bin/env python3
"""
Push attendance (shifts) to Firebase for operator Ruth
"""

import json, ssl, urllib.request, time
from datetime import datetime, timezone, timedelta

FIREBASE_URL = "https://hanzaha-d558c-default-rtdb.europe-west1.firebasedatabase.app"
OPERATOR_ID   = "-Ot__lq3wJPtP2R8hPiQ"
OPERATOR_NAME = "רות"

# Israel Daylight Time = UTC+3 (May)
IDT = timezone(timedelta(hours=3))

ssl_ctx = ssl.create_default_context()  # uses system CAs – verifies Firebase cert

def to_ms(date_str, time_str):
    """'d/m/yy' + 'HH:MM'  →  Unix ms (Israel time)"""
    d, m, y = date_str.split("/")
    h, mn   = time_str.split(":")
    dt = datetime(2000+int(y), int(m), int(d), int(h), int(mn), tzinfo=IDT)
    return int(dt.timestamp() * 1000)

def push(record):
    url  = f"{FIREBASE_URL}/attendance.json"
    data = json.dumps(record, ensure_ascii=False).encode()
    req  = urllib.request.Request(url, data=data, method="POST",
                                   headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15, context=ssl_ctx) as r:
        return json.loads(r.read())["name"]

def make_record(date_str, clock_in_str, clock_out_str):
    ci = to_ms(date_str, clock_in_str)
    co = to_ms(date_str, clock_out_str)
    d, m, y = date_str.split("/")
    iso_date = f"20{y}-{int(m):02d}-{int(d):02d}"
    return {
        "operatorId":      OPERATOR_ID,
        "operatorName":    OPERATOR_NAME,
        "date":            iso_date,
        "month":           iso_date[:7],
        "clockIn":         ci,
        "clockOut":        co,
        "durationMinutes": (co - ci) // 60000,
        "createdAt":       ci,
    }

# ---------- SHIFTS ----------
# Format: (date, in1, out1 [, in2, out2])
SHIFTS = [
    ("3/5/26",  "8:30",  "17:30"),
    ("4/5/26",  "9:00",  "18:00"),
    ("5/5/26",  "8:30",  "17:30"),
    ("6/5/26",  "8:30",  "17:30"),
    ("7/5/26",  "10:00", "18:00"),
    ("10/5/26", "8:30",  "16:30", "17:30", "18:30"),
    ("11/5/26", "8:30",  "13:30", "14:30", "18:30"),
    ("12/5/26", "8:30",  "17:30"),
    ("13/5/26", "8:30",  "17:30"),
    ("14/5/26", "10:00", "17:00", "18:00", "19:00"),
    ("17/5/26", "8:30",  "17:30"),
    ("18/5/26", "9:00",  "18:00"),
    ("19/5/26", "8:30",  "16:30", "17:30", "18:30"),
]

def main():
    ok = 0
    for row in SHIFTS:
        date = row[0]
        sessions = [(row[1], row[2])]
        if len(row) == 5:
            sessions.append((row[3], row[4]))

        for ci, co in sessions:
            rec = make_record(date, ci, co)
            mins = rec["durationMinutes"]
            h, m = divmod(mins, 60)
            try:
                fid = push(rec)
                label = f"{ci}–{co} ({h}:{m:02d})"
                print(f"  ✅ {date:<10} {label:<20} → {fid}")
                ok += 1
            except Exception as e:
                print(f"  ❌ {date} {ci}–{co} → ERROR: {e}")

    print(f"\nסיכום: {ok} רשומות נדחפו לרות")

if __name__ == "__main__":
    main()
