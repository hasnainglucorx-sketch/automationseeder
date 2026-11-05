"""
Add/update cases from the 6 screenshots shared 2026-10-05 — batch 2.

Updates:
  VP-APP-HOME-002  — expected item 3: add STALE badge (orange) and
                     'Updated N minutes ago' exact text format
  VP-APP-HOME-012  — fix exp from 1 unnumbered item to 4 numbered items;
                     add OFFLINE badge (red, replaces SENSOR ON)

New cases (added to compact + run_order):
  VP-APP-HOME-RANGE-004  — < > historical navigation + Now button on Home
  VP-APP-REPORT-GLUCOSE-001 — fullscreen Glucose chart (Glucose / 3 Days /
                               X close / mini scrollbar with period markers)
  VP-APP-REPORT-DAILY-001   — DAILY CHARTS section (scrollable per-day chart
                               list below the six stat tiles in Reports)
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

FULL_MAP = {"t": "title", "req": "requirement", "pre": "preconditions",
            "proc": "procedure", "exp": "expected", "ev": "evidence"}

# ── Updates to existing cases ─────────────────────────────────────────────────

UPDATES = {}

# VP-APP-HOME-002: exp item 3 — add confirmed STALE badge name, orange colour
# and "Updated X minutes ago" staleness text (verified from screenshot 3).
# Procedure unchanged (6 steps). Only exp item 3 is changed.
_h002_exp_items = [
    "The LIVE status and latest reading time are recorded.",
    "Turning Bluetooth off does not crash or navigate away from Home.",
    (
        "While Bluetooth is OFF, the reading shows a STALE badge (orange) and "
        "the reading time area displays “Updated [N] minutes ago”; "
        "the reading is not presented as fresh/LIVE and the app displays "
        "understandable recovery guidance; the exact status indicator, staleness "
        "text and recovery instruction are recorded."
    ),
    "Restoring Bluetooth does not crash or produce an error screen.",
    "The app attempts automatic reconnection without requiring manual "
    "intervention.",
    "After fresh sensor data is received the app returns to LIVE; the final "
    "status, glucose value and update time are recorded.",
]
UPDATES["VP-APP-HOME-002"] = dict(
    exp=n(*_h002_exp_items),
)

# VP-APP-HOME-012: fix expected from 1 unnumbered item to 4 numbered items
# matching the 4 existing procedure steps; add OFFLINE badge (red) description.
UPDATES["VP-APP-HOME-012"] = dict(
    exp=n(
        "The current Home reading and status while online are recorded.",
        "Disabling Wi‑Fi and mobile internet does not crash or navigate "
        "away from Home; the SENSOR ON badge is replaced by an OFFLINE badge "
        "(red) in the top-right status area.",
        "During the offline period, Bluetooth CGM readings continue to arrive "
        "and display on Home; the sensor session is not corrupted and no "
        "connectivity-loss crash occurs.",
        "Re‑enabling internet returns Home to its normal online state; "
        "the OFFLINE badge is replaced by the appropriate online session status.",
    ),
)

for cid, fields in UPDATES.items():
    assert cid in ci
    assert cid in ri
    ci[cid].update(fields)
    ri[cid].update({FULL_MAP[k]: v for k, v in fields.items() if k in FULL_MAP})

# ── New cases ─────────────────────────────────────────────────────────────────

# Scheduling defaults for new HOME-RANGE case (match HOME-RANGE-003 block)
_range_sched = {
    "day": "Day 9 (= D0; TIR-001, TAR-002, TBR-002 between 14:00 and 17:59)",
    "est": "10",
    "phase": "Phase 5",
    "recovery": "R5",
    "section": "Home Time Range Selector",
}

# Scheduling defaults for new HOME and REPORT cases
_home_sched = {
    "day": "Day 7",
    "est": "8",
    "phase": "Phase 4A",
    "recovery": "R4",
    "section": "Home Screen",
}

_report_sched = {
    "day": "Day 9 (= D0; TIR-001, TAR-002, TBR-002 between 14:00 and 17:59)",
    "est": "8",
    "phase": "Phase 5",
    "recovery": "R5",
    "section": "Reports Overview and View Navigation",
}

# ── VP-APP-HOME-RANGE-004 ─────────────────────────────────────────────────────
# Screenshot 4 confirms: when a historical range is displayed on Home (e.g.
# 12 Hours showing "Thu 30 Jul · 12:00–00:00"), < and > arrows and a
# "Now" button are visible for navigating between periods.
NEW_COMPACT = []
NEW_FULL    = []

def new_case(cid, title, req, pre, proc, exp, ev, sched, run_num):
    c_obj = {
        "id": cid, "t": title, "req": req,
        "pre": pre, "proc": proc, "exp": exp, "ev": ev,
    }
    r_obj = {
        "id": cid, "title": title, "requirement": req,
        "preconditions": pre, "procedure": proc, "expected": exp,
        "evidence": ev, "run": run_num,
    }
    r_obj.update(sched)
    NEW_COMPACT.append(c_obj)
    NEW_FULL.append(r_obj)

new_case(
    cid="VP-APP-HOME-RANGE-006",
    title=(
        "Navigate Home chart to a historical period and return to current "
        "time using arrow controls and Now"
    ),
    req="",
    pre=(
        "Non-production QA only. QA-HISTORY-01 is the controlled historical "
        "account for this case; its password must not be recorded in the "
        "protocol. Its seeded history contains populated data across multiple "
        "dates accessible via a short range such as 12 Hours."
    ),
    proc=n(
        "Confirm QA-HISTORY-01 fixture is current; if stale request a "
        "re-seed. Sign in with QA-HISTORY-01 and open Home.",
        "Select 12 Hours from the Home range selector and record the date "
        "header shown (format: “Dow DD Mon · HH:00–HH:00”) "
        "and whether < >, and Now controls are visible.",
        "Tap the < arrow and record the updated date header.",
        "Tap the > arrow and record the updated date header.",
        "Tap Now and record the destination shown.",
    ),
    exp=n(
        "QA-HISTORY-01 fixture confirmed current; sign-in succeeds and Home "
        "loads.",
        "The 12 Hours range is active; a date header showing the current or "
        "most-recent period is displayed; < and > navigation arrows and a "
        "Now button are visible.",
        "Tapping < moves the view to the previous 12-hour period; the date "
        "header updates to reflect the earlier interval.",
        "Tapping > moves the view forward; the date header updates to the "
        "next period.",
        "Tapping Now navigates to the current 12-hour period; the date "
        "header reflects the current date and time range.",
    ),
    ev=(
        "Screenshot of Home showing the date header, < >, and Now controls "
        "on 12 Hours; screenshot after tapping <; screenshot after tapping "
        "Now showing current date; execution record."
    ),
    sched=_range_sched,
    run_num=492,
)

# ── VP-APP-REPORT-GLUCOSE-001 ─────────────────────────────────────────────────
# Screenshot 5 (time 1:53) confirms a fullscreen Glucose chart with:
#   Title "Glucose", subtitle "3 Days", X close button,
#   mini scrollbar at bottom with period markers (Aug, Sep, Today).
# This is distinct from the AGP fullscreen (VP-APP-REPORT-AGP-006).
new_case(
    cid="VP-APP-REPORT-GLUCOSE-001",
    title="Expand Glucose chart to fullscreen and close to return to Reports",
    req="",
    pre=(
        "Non-production QA only. QA-HISTORY-01 is the controlled historical "
        "account for this case; its password must not be recorded in the "
        "protocol. Its seeded history contains sufficient data to populate "
        "the Glucose chart in Reports."
    ),
    proc=n(
        "Confirm QA-HISTORY-01 fixture is current; if stale request a "
        "re-seed. Sign in with QA-HISTORY-01, navigate to Reports and select "
        "the Glucose tab.",
        "Locate and tap the chart expand control on the Glucose chart.",
        "Inspect the fullscreen chart: record the title, subtitle, close "
        "button, and the mini scrollbar visible at the bottom.",
        "Tap the X close button to exit fullscreen.",
    ),
    exp=n(
        "QA-HISTORY-01 fixture confirmed current; sign-in succeeds; Reports "
        "opens with the Glucose tab active.",
        "The fullscreen Glucose chart opens without crash.",
        "The fullscreen chart shows the title “Glucose”, a subtitle "
        "matching the selected period (e.g. “3 Days”), an X close "
        "button, and a mini timeline scrollbar at the bottom with historical "
        "period markers.",
        "Tapping X closes the fullscreen chart and returns to Reports without "
        "crash or loss of the active tab and period selection.",
    ),
    ev=(
        "Screenshot of Reports showing the Glucose chart expand control; "
        "screenshot of the fullscreen Glucose chart showing title "
        "“Glucose”, subtitle, X button and mini scrollbar with "
        "period markers; screenshot of Reports after closing fullscreen; "
        "execution record."
    ),
    sched={**_report_sched, "section": "Reports - Glucose View"},
    run_num=493,
)

# ── VP-APP-REPORT-DAILY-001 ───────────────────────────────────────────────────
# Screenshots 1 and 2 both confirm a "DAILY CHARTS · [PERIOD]" section
# below the six statistic tiles in the Glucose and AGP tabs. Each entry shows
# a date label (e.g. "Today · Monday 5 October") and a mini daily chart.
new_case(
    cid="VP-APP-REPORT-DAILY-001",
    title=(
        "Daily Charts section shows a scrollable per-day glucose list in "
        "Reports"
    ),
    req="",
    pre=(
        "Non-production QA only. QA-HISTORY-01 is the controlled historical "
        "account for this case; its password must not be recorded in the "
        "protocol. Its seeded history contains populated data across multiple "
        "calendar dates for a period of at least 15 days."
    ),
    proc=n(
        "Confirm QA-HISTORY-01 fixture is current; if stale request a "
        "re-seed. Sign in with QA-HISTORY-01, navigate to Reports and select "
        "the Glucose tab.",
        "Select a period covering multiple days (for example, 15 Days) using "
        "the period selector.",
        "Scroll down past the six statistic tiles and locate the DAILY CHARTS "
        "section header.",
        "Record the section header text and inspect the individual daily "
        "chart entries visible without scrolling.",
        "Scroll within the DAILY CHARTS section to view additional days and "
        "record the number of entries visible.",
    ),
    exp=n(
        "QA-HISTORY-01 fixture confirmed current; sign-in succeeds; Reports "
        "opens with the Glucose tab active.",
        "The selected period becomes active and the Glucose chart and six "
        "statistic tiles update for that period.",
        "A DAILY CHARTS section header reading “DAILY CHARTS · "
        "[PERIOD]” (e.g. “DAILY CHARTS · 15 DAYS”) is "
        "visible below the six stat tiles.",
        "Individual daily chart entries are displayed; each entry shows a "
        "date label (e.g. “Today · Monday 5 October”) and a "
        "mini glucose trace for that day.",
        "Scrolling reveals additional daily chart entries for the remaining "
        "days in the selected period without crash or layout break.",
    ),
    ev=(
        "Screenshot of the DAILY CHARTS section header (e.g. "
        "“DAILY CHARTS · 15 DAYS”) with at least two daily "
        "chart entries visible; screenshot after scrolling showing further "
        "entries; execution record."
    ),
    sched={**_report_sched, "section": "Reports - Daily Charts"},
    run_num=494,
)

# ── Validate new IDs don’t already exist ───────────────────────────────
for obj in NEW_COMPACT:
    assert obj["id"] not in ci, f"ID already exists in compact: {obj['id']}"
    assert obj["id"] not in ri, f"ID already exists in run_order: {obj['id']}"

compact.extend(NEW_COMPACT)
full.extend(NEW_FULL)

# ── Write JSON ────────────────────────────────────────────────────────────────
COMPACT_PATH.write_text(json.dumps(compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
FULL_PATH.write_text(json.dumps(full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ── Re-embed compact array into HTML ──────────────────────────────────────────
html = HTML_PATH.read_text(encoding="utf-8-sig")
embedded = json.dumps(compact, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
html, count = re.subn(
    r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)",
    lambda m: m[1] + embedded + m[2], html, count=1, flags=re.S)
assert count == 1
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)

print("Updated:", sorted(UPDATES.keys()))
print("New cases:", [x["id"] for x in NEW_COMPACT])
print(f"Compact: {len(compact)}  Run-order: {len(full)}")
