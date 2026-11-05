"""
Update the 8 now-executable hardware cases with clear QA procedure language.
Controls referenced as:
  - "transmitter power switch" (black On/Off switch on the transmitter)
  - "phone Bluetooth" (iOS Bluetooth toggle in Settings or Control Centre)
  - "the transmitter" (the CGM transmitter simulator)
"""
import json, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT  = ROOT / "output/console-update"
COMPACT_PATH = OUT / "PRT-0701-cases.json"
FULL_PATH    = OUT / "PRT-0701-run_order.json"
HTML_PATH    = OUT / "PRT-0701-Console-source.html"
ROOT_HTML    = ROOT / "PRT-0701-Console-source.updated.html"

compact = json.loads(COMPACT_PATH.read_text(encoding="utf-8-sig"))
full    = json.loads(FULL_PATH.read_text(encoding="utf-8-sig"))

def n(*items):
    return "\n".join(f"{i}. {s}" for i, s in enumerate(items, 1))

UPDATES = {}

# ── TX-PAIR-017 ──────────────────────────────────────────────────────────────
UPDATES["VP-APP-TX-PAIR-017"] = dict(
    pre=(
        "The transmitter-pairing screen is displayed and the transmitter is "
        "powered on and actively advertising. QA-MAIN-01 is unauthenticated "
        "or has not yet completed sensor setup."
    ),
    proc=n(
        "Start the direct-connection step for the selected transmitter and "
        "observe the loading state.",
        "While the direct connection or device-info loading is in progress, "
        "power off the transmitter using the transmitter power switch.",
        "Keep the screen visible and wait at least 5 seconds, observing whether "
        "the app makes one automatic reconnection attempt.",
        "Continue observing until the app either reconnects or returns to the "
        "transmitter-selection screen; record the outcome.",
    ),
    exp=n(
        "The direct-connection step starts and the app attempts to communicate "
        "with the transmitter.",
        "The connection is lost; the app detects the disconnection without "
        "crashing or showing an unhandled error.",
        "Exactly one automatic reconnection attempt fires after approximately "
        "5 seconds; the attempt is observable on screen.",
        "After the single retry fails, the app returns to the "
        "transmitter-selection screen; no second automatic retry or "
        "indefinite loading state occurs.",
    ),
    ev=(
        "Screen recording or timed screenshots showing: the direct-connection "
        "loading state, the disconnection detection, the single retry attempt "
        "and the return to transmitter selection; execution record with timestamps."
    ),
)

# ── WARMUP-008 ───────────────────────────────────────────────────────────────
UPDATES["VP-APP-WARMUP-008"] = dict(
    pre=(
        "QA-MAIN-01 is signed in and the CGM sensor session is in the warm-up "
        "phase with the warm-up progress visible. The debug warm-up bypass has "
        "NOT been used for this case. The transmitter is powered on."
    ),
    proc=n(
        "Record the warm-up remaining time shown on screen, then power off the "
        "transmitter using the transmitter power switch.",
        "Keep the app open and observe the screen state shown after the "
        "transmitter is powered off.",
        "Power on the transmitter using the transmitter power switch and allow "
        "the app to detect and reconnect to it.",
        "Observe and record the warm-up status displayed after reconnection "
        "and confirm whether Home is accessible.",
    ),
    exp=n(
        "The warm-up remaining time is recorded; the transmitter powers off "
        "without the app crashing.",
        "The app shows a connection-loss or STALE state; the warm-up session "
        "is not ended and a new 60-minute warm-up is not started solely because "
        "the transmitter was powered off.",
        "The transmitter powers on and the app reconnects without crash.",
        "Warm-up resumes from the transmitter-reported remaining time; "
        "a fresh 60-minute restart does not occur; Home remains accessible "
        "and is not trapped behind a full-screen warm-up block.",
    ),
    ev=(
        "Screenshot of warm-up remaining time before power-off; screenshot of "
        "connection-loss state; screenshot of warm-up resumed state after "
        "reconnection showing the remaining time; Home screen screenshot "
        "confirming accessibility; execution record."
    ),
)

# ── HOME-014 ─────────────────────────────────────────────────────────────────
UPDATES["VP-APP-HOME-014"] = dict(
    pre=(
        "QA-MAIN-01 is signed in and an active CGM session is delivering live "
        "readings. Home shows the LIVE status and the current glucose value."
    ),
    proc=n(
        "On Home, record the current glucose value, its timestamp and the "
        "LIVE session status.",
        "Power off the transmitter using the transmitter power switch.",
        "Power on the transmitter using the transmitter power switch and "
        "allow the app to reconnect.",
        "Observe Home after reconnection; compare the session status and "
        "any backfilled readings against the values recorded in Step 1.",
    ),
    exp=n(
        "The current glucose value, timestamp and LIVE session status are recorded.",
        "The app shows a disconnection or STALE state without crashing or "
        "ending the current CGM session.",
        "The transmitter powers on and the app reconnects without crash.",
        "The same CGM session resumes and Home returns to LIVE; any readings "
        "from the power-off interval may backfill or be absent, but no duplicate "
        "session and no data corruption is introduced.",
    ),
    ev=(
        "Screenshot of LIVE state before power-off; screenshot of "
        "connection-loss state; screenshot of recovered LIVE state after "
        "reconnection; history or graph screenshot confirming the same session "
        "without duplicates; execution record."
    ),
)

# ── HOME-015 ─────────────────────────────────────────────────────────────────
UPDATES["VP-APP-HOME-015"] = dict(
    pre=(
        "QA-MAIN-01 is signed in and an active CGM session is delivering live "
        "readings. Home shows the LIVE status."
    ),
    proc=n(
        "Record the last glucose value, its timestamp and measurement index "
        "shown on Home.",
        "Turn phone Bluetooth OFF using the iOS Bluetooth toggle in Control "
        "Centre and keep it off for at least 10 minutes so the transmitter "
        "records multiple readings that the phone does not receive.",
        "Turn phone Bluetooth ON and allow the app to reconnect to the "
        "transmitter automatically.",
        "Keep the app open and observe whether missed readings from the "
        "disconnection period are retrieved.",
        "Navigate to the Home graph or history and review the readings "
        "covering the disconnection interval.",
    ),
    exp=n(
        "The last pre-disconnection glucose value, timestamp and index are recorded.",
        "Phone Bluetooth is off; the app shows a disconnection or STALE state "
        "without crashing; the disconnection duration is noted.",
        "Phone Bluetooth is turned on; the app reconnects automatically "
        "without requiring manual steps.",
        "Missed readings are retrieved and added without crashing or "
        "unintended navigation.",
        "The retrieved readings appear at their correct chronological timestamps "
        "in the Home graph or history; no duplicate session is created.",
    ),
    ev=(
        "Screenshot of LIVE state before disconnection; screenshot of STALE "
        "state; screenshot after reconnection; Home graph or history screenshot "
        "showing the backfilled readings in chronological order; execution record "
        "noting disconnection start and end times."
    ),
)

# ── MEDIUM-002 ───────────────────────────────────────────────────────────────
UPDATES["VP-APP-MEDIUM-002"] = dict(
    pre=(
        "QA-MAIN-01 is signed in and an active CGM session is delivering live "
        "readings. Notification permission is enabled and the app is not "
        "suppressed in iOS notification settings. Do Not Disturb or Focus mode "
        "is available on the test device."
    ),
    proc=n(
        "Confirm live readings are arriving and record the last reading time.",
        "Power off the transmitter using the transmitter power switch to stop "
        "all incoming readings.",
        "Keep the app open and observe the screen and the iOS notification "
        "area; record the wording and priority of the first no-data or "
        "disconnection alert that appears, before any critical escalation.",
        "Restore the transmitter to a live reading state, then enable "
        "Do Not Disturb or Focus on the phone; power off the transmitter "
        "again and observe whether the medium-priority alert appears and "
        "is audible with DND active.",
        "Power on the transmitter and allow normal readings to resume "
        "after evidence is captured.",
    ),
    exp=n(
        "Live readings are confirmed and the last reading time is recorded.",
        "The transmitter powers off and readings stop; the app does not crash.",
        "After the defined interval without readings, a medium-priority "
        "no-data or disconnection alert appears; the alert wording is recorded; "
        "critical-level escalation has not yet occurred at this stage.",
        "The medium-priority alert appears and is audible even with "
        "Do Not Disturb or Focus active; the DND-bypass behaviour is recorded.",
        "The transmitter powers on and live readings resume without crash.",
    ),
    ev=(
        "Screenshot of the medium-priority alert at Steps 3 and 4; "
        "screenshot confirming DND or Focus was active during Step 4; "
        "audio evidence or note confirming the alert was audible; "
        "execution record with alert timestamps."
    ),
)

# ── HIGH-015 ─────────────────────────────────────────────────────────────────
UPDATES["VP-APP-HIGH-015"] = dict(
    pre=(
        "QA-MAIN-01 is signed in and an active CGM session is delivering "
        "readings. Notification permission is enabled. The transmitter is "
        "configured to output High glucose values."
    ),
    proc=n(
        "Confirm at least one High glucose reading is visible on Home and "
        "record the reading index.",
        "Turn phone Bluetooth OFF using the iOS Bluetooth toggle in Control "
        "Centre and keep it off for at least 10 minutes while the transmitter "
        "continues recording High readings that the phone does not receive.",
        "Turn phone Bluetooth ON and allow the app to reconnect and retrieve "
        "the missed High readings.",
        "Check the iOS notification area and lock screen during and immediately "
        "after the backfill; record any notification that appears.",
        "Navigate to history or the Home graph and verify the backfilled "
        "High readings.",
    ),
    exp=n(
        "At least one High reading is confirmed on Home and the reading index "
        "is recorded.",
        "Phone Bluetooth is off; the app shows a disconnection state; "
        "the transmitter continues running and the disconnection duration "
        "is noted.",
        "Phone Bluetooth is turned on; the app reconnects and the missed "
        "High readings backfill without crashing.",
        "No new High threshold notification is generated for the backfilled "
        "historical High readings; any notification that appears is recorded "
        "for assessment.",
        "Backfilled High readings appear at their correct timestamps in "
        "history or the Home graph.",
    ),
    ev=(
        "Home screenshot confirming High output before disconnection; "
        "notification area screenshots during and immediately after backfill "
        "confirming no new High alert was raised; history or graph screenshot "
        "showing the backfilled High readings; execution record."
    ),
)

# ── LOW-015 ──────────────────────────────────────────────────────────────────
UPDATES["VP-APP-LOW-015"] = dict(
    pre=(
        "QA-MAIN-01 is signed in and an active CGM session is delivering "
        "readings. Notification permission is enabled. The transmitter is "
        "configured to output Critical Low glucose values."
    ),
    proc=n(
        "Confirm at least one Critical Low glucose reading is visible on "
        "Home and record the reading index.",
        "Turn phone Bluetooth OFF using the iOS Bluetooth toggle in Control "
        "Centre and keep it off for at least 10 minutes while the transmitter "
        "continues recording Critical Low readings that the phone does not receive.",
        "Turn phone Bluetooth ON and allow the app to reconnect and retrieve "
        "the missed Critical Low readings.",
        "Check the iOS notification area and lock screen during and immediately "
        "after the backfill; record any notification that appears.",
        "Navigate to history or the Home graph and verify the backfilled "
        "Critical Low readings.",
    ),
    exp=n(
        "At least one Critical Low reading is confirmed on Home and the "
        "reading index is recorded.",
        "Phone Bluetooth is off; the app shows a disconnection state; "
        "the transmitter continues running and the disconnection duration "
        "is noted.",
        "Phone Bluetooth is turned on; the app reconnects and the missed "
        "Critical Low readings backfill without crashing.",
        "No new Critical Low or Urgent Low notification is generated for "
        "the backfilled historical readings; any notification that appears "
        "is recorded for assessment.",
        "Backfilled Critical Low readings appear at their correct timestamps "
        "in history or the Home graph.",
    ),
    ev=(
        "Home screenshot confirming Critical Low output before disconnection; "
        "notification area screenshots during and immediately after backfill "
        "confirming no new Critical Low alert was raised; history or graph "
        "screenshot showing the backfilled Critical Low readings; execution record."
    ),
)

# ── REPORT-DAY-005 ───────────────────────────────────────────────────────────
UPDATES["VP-APP-REPORT-DAY-005"] = dict(
    pre=(
        "QA-MAIN-01 is signed in and an active CGM session is delivering live "
        "readings on the current date. The Reports > Day view is accessible."
    ),
    proc=n(
        "Confirm a live reading is arriving and record its value, timestamp "
        "and measurement index.",
        "Turn phone Bluetooth OFF using the iOS Bluetooth toggle in Control "
        "Centre and keep it off for at least 30 minutes; note the disconnection "
        "start time.",
        "Turn phone Bluetooth ON and allow the app to reconnect; record the "
        "value, timestamp and index of the first reading received after "
        "reconnection.",
        "Confirm the gap qualifies: either at least 5 consecutive measurement "
        "indexes are absent and not backfilled, or the timestamps surrounding "
        "the gap are more than 30 minutes apart. If neither condition is met, "
        "repeat Steps 2 and 3 with a longer disconnection.",
        "Navigate to Reports > Day, select the current date and locate the "
        "time range covering the disconnection.",
        "Inspect the glucose graph line across the gap interval.",
    ),
    exp=n(
        "The last pre-gap glucose value, timestamp and index are recorded.",
        "Phone Bluetooth is off and the app shows a disconnection state; "
        "the disconnection start time is recorded.",
        "Bluetooth is restored and the app reconnects; the first post-gap "
        "reading is recorded with its value, timestamp and index.",
        "The gap meets the qualifying criteria; the missing indexes or the "
        "30-minute time span are confirmed and recorded.",
        "Reports > Day opens and the current date with the gap interval "
        "is reachable.",
        "A visible line break appears across the gap interval in the Day graph; "
        "the app does not draw a continuous glucose line across the gap; "
        "normal graphing resumes after the gap.",
    ),
    ev=(
        "Screenshot of last pre-gap reading on Home; screenshot of disconnection "
        "state; screenshot of first post-gap reading; Reports > Day screenshot "
        "clearly showing the line break across the gap interval; execution record "
        "with disconnection start time, end time and gap boundaries."
    ),
)

# ── Apply ────────────────────────────────────────────────────────────────────
FULL_MAP = {"t":"title","req":"requirement","pre":"preconditions",
            "proc":"procedure","exp":"expected","ev":"evidence"}

ci = {x["id"]: x for x in compact}
ri = {x["id"]: x for x in full}

for cid, fields in UPDATES.items():
    assert cid in ci, f"Missing from compact: {cid}"
    assert cid in ri, f"Missing from run_order: {cid}"
    ci[cid].update(fields)
    ri[cid].update({FULL_MAP[k]: v for k, v in fields.items() if k in FULL_MAP})

# Re-embed
html = HTML_PATH.read_text(encoding="utf-8-sig")
embedded = json.dumps(compact, ensure_ascii=False, separators=(",",":")).replace("<","\\u003c")
html, count = re.subn(
    r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)",
    lambda m: m[1] + embedded + m[2], html, count=1, flags=re.S)
assert count == 1

COMPACT_PATH.write_text(json.dumps(compact, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
FULL_PATH.write_text(json.dumps(full, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)

print(f"Updated: {len(UPDATES)} cases")
print(f"Compact: {len(compact)}  Run-order: {len(full)}")
