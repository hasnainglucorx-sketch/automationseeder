"""
Update 4 cases confirmed by screenshots shared on 2026-10-05:
  - VP-APP-REPORT-001: fix state-only preconditions; name confirmed tabs Glucose, Week, AGP
  - VP-APP-HOME-008: update tile labels to exact app text (DAILY AVG, SEVERE EVENTS)
  - VP-APP-WARMUP-009: rewrite with confirmed "You're all set" screen details
  - VP-APP-REPORT-AGP-001: add numbered expected results (4 items); align to QA-HISTORY-01
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
ci = {x["id"]: x for x in compact}
ri = {x["id"]: x for x in full}

def n(*items):
    return "\n".join(f"{i}. {s}" for i, s in enumerate(items, 1))

FULL_MAP = {"t":"title","req":"requirement","pre":"preconditions",
            "proc":"procedure","exp":"expected","ev":"evidence"}

UPDATES = {}

# ── REPORT-001 ───────────────────────────────────────────────────────────────
# Screenshots confirm three tabs: Glucose, Week, AGP.
# Precondition contained action words ("Sign in", "navigate") and a backend
# patient UUID (patients/7edf711f-...) — both removed.
UPDATES["VP-APP-REPORT-001"] = dict(
    pre=(
        "Non-production QA only. QA-HISTORY-01 is the controlled historical "
        "account for this case; its password must not be recorded in the "
        "protocol. The account is configured for country PK, Asia/Karachi, "
        "mg/dL, Low 70 mg/dL and High 180 mg/dL. Its seeded history contains "
        "populated 24-hour, 3-day, 7-day, 15-day and 90-day selections, "
        "readings on more than three dates, and values below 70, within "
        "70–180 and above 180 mg/dL. Reports is reachable from the "
        "bottom navigation bar."
    ),
    proc=n(
        "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
        "Sign in with QA-HISTORY-01 and navigate to Reports from the bottom "
        "navigation.",
        "Observe the report area and identify the available tabs.",
        "Tap the Glucose tab and observe the displayed report content and the "
        "active tab indication.",
        "Tap each remaining tab — Week and then AGP — one at a time, "
        "observing the content and active indication after each tap.",
    ),
    exp=n(
        "QA-HISTORY-01 fixture confirmed current; sign-in succeeds and Reports "
        "is reachable.",
        "Reports opens without crash or blank state; three tabs are visible: "
        "Glucose, Week and AGP.",
        "The Glucose tab becomes active and displays Glucose report content "
        "without crash or stale content from a previous tab.",
        "The Week and AGP tabs each become active in turn and display their "
        "respective content; switching tabs does not leave stale content from "
        "the previously selected tab.",
    ),
    ev=(
        "Screenshot of Reports with all three tabs visible (Glucose, Week, AGP); "
        "screenshot of each tab’s content after selection; execution record."
    ),
)

# ── HOME-008 ─────────────────────────────────────────────────────────────────
# Screenshots confirm tile heading labels: TIME IN RANGE, DAILY AVG, GMI,
# SEVERE EVENTS. Procedure updated to use exact visible labels.
# Precondition already correct from pass3 — not changed.
UPDATES["VP-APP-HOME-008"] = dict(
    proc=n(
        "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
        "Sign in with QA-HISTORY-01 and open Home.",
        "Record the selected range and the TIME IN RANGE, DAILY AVG, GMI and "
        "SEVERE EVENTS tile values.",
        "Select a different approved Home range and record all four tile values "
        "again.",
        "Tap the TIME IN RANGE tile and verify the Time in Range detail screen "
        "opens; return to Home.",
        "Tap DAILY AVG, verify the daily average detail screen opens; return. "
        "Tap GMI, verify the GMI detail screen opens; return. "
        "Tap SEVERE EVENTS, verify the Severe Events detail screen opens; return.",
    ),
    exp=n(
        "QA-HISTORY-01 fixture confirmed current; sign-in succeeds and Home "
        "loads.",
        "All four tile values for the initial range are recorded.",
        "All four tile values update to reflect the newly selected range; no "
        "stale values from the previous range remain.",
        "Tapping TIME IN RANGE opens the Time in Range detail screen; returning "
        "restores Home.",
        "Each of the remaining three tiles (DAILY AVG, GMI, SEVERE EVENTS) "
        "opens its detail screen; returning each time restores Home without "
        "crash or blank state.",
    ),
    ev=(
        "Screenshots of both range tile sets showing tile labels TIME IN RANGE, "
        "DAILY AVG, GMI and SEVERE EVENTS; screenshot of each opened detail "
        "screen; execution record."
    ),
)

# ── WARMUP-009 ───────────────────────────────────────────────────────────────
# Screenshot (IMG_6xxx) confirms:
#   iOS notification: "Your sensor is ready" /
#                     "Warm-up is complete. Open the app to see your glucose readings."
#   Screen heading:   "You're all set"
#   Body text:        "Your sensor is on and warming up. Once warm-up finishes,
#                      your glucose readings appear on the Home screen — a new
#                      reading every minute."
#   Checklist (green checkmarks): Sensor paired / Notifications /
#                                 Low alert at 70 mg/dL / High alert at 180 mg/dL
#   Button: "View Home" (black)
UPDATES["VP-APP-WARMUP-009"] = dict(
    pre=(
        "QA-MAIN-01 is signed in and the CGM sensor session is in the "
        "warm-up phase. The warm-up countdown is visible on the app screen."
    ),
    proc=n(
        "Keep the app open with the warm-up countdown visible and allow "
        "warm-up to proceed until the countdown completes.",
        "Observe whether an iOS notification arrives at warm-up completion; "
        "record its title and body text.",
        "Open the app if it was backgrounded; observe and record the heading, "
        "body text, checklist items and action button shown on the completion "
        "screen.",
        "Tap the action button on the completion screen and observe the "
        "destination.",
    ),
    exp=n(
        "The warm-up countdown completes; the app does not crash and warm-up "
        "does not end solely because the displayed estimate reached zero.",
        "An iOS notification is delivered reading “Your sensor is ready” "
        "and “Warm-up is complete. Open the app to see your glucose "
        "readings.”",
        "The app displays a “You’re all set” screen with body "
        "text “Your sensor is on and warming up. Once warm-up finishes, "
        "your glucose readings appear on the Home screen — a new reading "
        "every minute.” and a checklist showing green checkmarks for: "
        "Sensor paired, Notifications, Low alert at 70 mg/dL and High "
        "alert at 180 mg/dL.",
        "Tapping “View Home” navigates to the live CGM Home screen "
        "for the active session.",
    ),
    ev=(
        "Screenshot of warm-up countdown before completion; screenshot of iOS "
        "notification at warm-up completion; screenshot of the "
        "“You’re all set” screen showing all checklist items and "
        "the “View Home” button; screenshot of live CGM Home screen "
        "after tapping “View Home”; execution record with warm-up "
        "start and completion times."
    ),
)

# ── REPORT-AGP-001 ───────────────────────────────────────────────────────────
# Screenshots confirm:
#   - AGP tab label is "AGP"
#   - Chart title format: "AGP · 15 DAYS" (period-dependent)
#   - Horizontal axis: 24-hour time-of-day scale (00 to 24)
#   - Chart shows a central line (median) with two shaded percentile bands
#   - Six statistic tiles below chart
# Run-order had legacy "QA_AGP_01 / D0 14:00-17:59" content — replaced with
# QA-HISTORY-01 and numbered 4-item expected results to match 4 procedure steps.
UPDATES["VP-APP-REPORT-AGP-001"] = dict(
    pre=(
        "Non-production QA only. QA-HISTORY-01 is the controlled historical "
        "account for this case; its password must not be recorded in the "
        "protocol. Its seeded history covers at least 7 days and contains "
        "sufficient readings to generate an AGP profile."
    ),
    proc=n(
        "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
        "Sign in with QA-HISTORY-01, navigate to Reports and tap the AGP tab.",
        "On first or fresh entry to AGP, record the selected period shown "
        "above the chart.",
        "Confirm the chart title identifies AGP and inspect the horizontal "
        "axis label and scale.",
        "Inspect the central profile line and the two surrounding shaded "
        "percentile ranges.",
    ),
    exp=n(
        "Reports opens and the AGP tab becomes active without crash or blank "
        "state.",
        "The period shown above the AGP chart is 7 Days on first or fresh "
        "entry; the selected period is recorded.",
        "The chart title contains “AGP” followed by the selected "
        "period (e.g. “AGP · 7 DAYS”); the horizontal axis "
        "is a 24-hour time-of-day scale running from 00 to 24.",
        "A central profile line (the 50th percentile median) is visible; two "
        "shaded regions surround it, representing the 25th–75th and "
        "10th–90th percentile ranges.",
    ),
    ev=(
        "Screenshot of the AGP view showing the chart title “AGP · "
        "[PERIOD]”, the 24-hour time-of-day axis and the percentile "
        "profile; screenshot confirming 7 Days is selected on first entry; "
        "execution record."
    ),
)

# ── Apply to compact and run_order ────────────────────────────────────────────
for cid, fields in UPDATES.items():
    assert cid in ci, f"Missing from compact: {cid}"
    assert cid in ri, f"Missing from run_order: {cid}"
    ci[cid].update(fields)
    ri[cid].update({FULL_MAP[k]: v for k, v in fields.items() if k in FULL_MAP})

# ── Re-embed compact array into HTML ──────────────────────────────────────────
html = HTML_PATH.read_text(encoding="utf-8-sig")
embedded = json.dumps(compact, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
html, count = re.subn(
    r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)",
    lambda m: m[1] + embedded + m[2], html, count=1, flags=re.S)
assert count == 1, f"Expected 1 substitution, got {count}"

COMPACT_PATH.write_text(json.dumps(compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
FULL_PATH.write_text(json.dumps(full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)

print(f"Updated: {sorted(UPDATES.keys())}")
print(f"Compact: {len(compact)}  Run-order: {len(full)}")
