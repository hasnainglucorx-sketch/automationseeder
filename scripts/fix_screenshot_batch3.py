"""
Fix confirmed gaps from second screenshot review 2026-10-05:

1. VP-APP-REPORT-GLUCOSE-001 — WRONG SCREEN.  Screenshots 1 and 5 confirm the
   blue expand button (↙↗ circle) is on the HOME chart, not on Reports.  Screenshot 4
   (1:53) is the resulting fullscreen: title "Glucose", subtitle "3 Days", X button.
   The unconfirmed "mini scrollbar inside fullscreen" claim is removed; the slider
   lives below the Home chart (see new RANGE-007), not inside the fullscreen view.

2. VP-APP-HOME-RANGE-007 (new) — The horizontal timeline slider below the Home
   chart is confirmed in screenshots 1 (90 Days) and 5 (12 Hours): draggable
   position indicator with period markers | Aug · | Sep · Today.  This is separate
   from the < > arrow navigation tested in HOME-RANGE-006.
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

# ── 1. Fix VP-APP-REPORT-GLUCOSE-001 ─────────────────────────────────────────
# The fullscreen chart is reached from the Home chart expand button, not Reports.
# Screenshots 1 and 5 confirm: blue circular ↙↗ button top-right of the Home
# chart.  Screenshot 4 (1:53) confirms: fullscreen shows "Glucose" title,
# "3 Days" subtitle, X close button.  No mini scrollbar is visible inside the
# fullscreen; that scrollbar lives below the Home chart (covered by RANGE-007).

assert "VP-APP-REPORT-GLUCOSE-001" in ci
assert "VP-APP-REPORT-GLUCOSE-001" in ri

fix_glucose = dict(
    t=(
        "Expand the Home glucose chart to fullscreen using the expand button "
        "and close to return to Home"
    ),
    pre=(
        "Non-production QA only. QA-HISTORY-01 is the controlled historical "
        "account for this case; its password must not be recorded in the "
        "protocol. Its seeded history contains sufficient data to populate "
        "the glucose chart on the Home screen."
    ),
    proc=n(
        "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
        "Sign in with QA-HISTORY-01 and open Home.",
        "Select a range that shows historical data (for example, 3 Days or "
        "12 Hours) using the Home range selector; locate the blue circular "
        "expand button (↙↗ icon) in the top-right corner of the glucose chart.",
        "Tap the blue expand button and inspect the fullscreen chart; record "
        "the title, subtitle and the close control.",
        "Tap the X close button to exit fullscreen.",
    ),
    exp=n(
        "QA-HISTORY-01 fixture confirmed current; sign-in succeeds and Home "
        "loads with the glucose chart visible.",
        "The selected range is active and the chart updates; a blue circular "
        "button showing a resize/expand icon (diagonal arrows) is visible in the "
        "top-right corner of the Home glucose chart.",
        "The fullscreen Glucose chart opens without crash; the title Glucose "
        "and a subtitle matching the selected period (e.g. 3 Days) "
        "are displayed along with an X close button.",
        "Tapping X closes the fullscreen chart and returns to Home without "
        "crash or loss of the active range selection.",
    ),
    ev=(
        "Screenshot of the Home chart showing the blue expand button (diagonal arrows) "
        "visible in the top-right corner; screenshot of the fullscreen Glucose "
        "chart showing the title Glucose, the period subtitle and the X "
        "close button; screenshot of Home after closing fullscreen; "
        "execution record."
    ),
)

ci["VP-APP-REPORT-GLUCOSE-001"].update(fix_glucose)
ri["VP-APP-REPORT-GLUCOSE-001"].update(
    {FULL_MAP[k]: v for k, v in fix_glucose.items() if k in FULL_MAP}
)
# Also update scheduling section to Home Screen since this is now a Home case
ri["VP-APP-REPORT-GLUCOSE-001"]["section"] = "Home Screen"

# ── 2. New case VP-APP-HOME-RANGE-007 ────────────────────────────────────────
# Screenshots 1 (90 Days, 5:06) and 5 (12 Hours, 1:31) both confirm a horizontal
# timeline slider below the Home chart:
#   - A draggable rectangular position indicator that represents the current
#     chart viewport window.
#   - Period markers: | Aug · | Sep · Today
#   - In 90-Days view the track shows data-presence marks (coloured bars).
# Dragging this slider is a distinct interaction from tapping the < > arrows
# (VP-APP-HOME-RANGE-006); it allows direct pan to any historical period.

NEW_COMPACT = []
NEW_FULL    = []

def new_case(cid, title, req, pre, proc, exp, ev, sched, run_num):
    c_obj = {"id": cid, "t": title, "req": req,
             "pre": pre, "proc": proc, "exp": exp, "ev": ev}
    r_obj = {"id": cid, "title": title, "requirement": req,
             "preconditions": pre, "procedure": proc, "expected": exp,
             "evidence": ev, "run": run_num}
    r_obj.update(sched)
    NEW_COMPACT.append(c_obj)
    NEW_FULL.append(r_obj)

_range_sched = {
    "day": "Day 9 (= D0; TIR-001, TAR-002, TBR-002 between 14:00 and 17:59)",
    "est": "10",
    "phase": "Phase 5",
    "recovery": "R5",
    "section": "Home Time Range Selector",
}

new_case(
    cid="VP-APP-HOME-RANGE-007",
    title=(
        "Drag the timeline slider below the Home chart to navigate to a "
        "historical period and return to the current period"
    ),
    req="",
    pre=(
        "Non-production QA only. QA-HISTORY-01 is the controlled historical "
        "account for this case; its password must not be recorded in the "
        "protocol. Its seeded history contains populated data spanning multiple "
        "months, with data accessible via a short range such as 12 Hours and "
        "visible in the timeline slider period markers (e.g. | Aug, | Sep, Today)."
    ),
    proc=n(
        "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
        "Sign in with QA-HISTORY-01 and open Home; select 12 Hours from the "
        "range selector.",
        "Locate the horizontal timeline slider below the glucose chart; record "
        "the visible period markers and the current position of the slider "
        "indicator.",
        "Drag the slider indicator toward the left (earlier dates) and record "
        "the updated date header and chart content.",
        "Drag the slider indicator back toward the right (toward Today) and "
        "record the updated date header.",
        "Continue dragging to the Today position or tap Now, and confirm the "
        "chart returns to the current period.",
    ),
    exp=n(
        "QA-HISTORY-01 fixture confirmed current; sign-in succeeds; Home loads "
        "with 12 Hours active and the glucose chart visible.",
        "A horizontal timeline slider is visible below the glucose chart; it "
        "shows period markers (e.g. | Aug, | Sep, Today) and a draggable "
        "rectangular indicator reflecting the current chart viewport window.",
        "Dragging the slider left moves the chart view to an earlier period; "
        "the date header updates to reflect the earlier interval and the chart "
        "content changes accordingly.",
        "Dragging the slider right moves the chart view toward more recent data; "
        "the date header updates to the later interval.",
        "The chart returns to the current period; the date header reflects the "
        "current date and time range.",
    ),
    ev=(
        "Screenshot of Home showing the horizontal timeline slider below the "
        "chart with visible period markers (| Aug, | Sep, Today); screenshot "
        "after dragging left showing the earlier date header; screenshot after "
        "returning to the current period; execution record."
    ),
    sched=_range_sched,
    run_num=495,
)

# ── Validate new IDs don't already exist ──────────────────────────────────────
for obj in NEW_COMPACT:
    assert obj["id"] not in ci, f"ID already exists in compact: {obj['id']}"
    assert obj["id"] not in ri, f"ID already exists in run_order: {obj['id']}"

compact.extend(NEW_COMPACT)
full.extend(NEW_FULL)

# ── Write JSON ────────────────────────────────────────────────────────────────
COMPACT_PATH.write_text(
    json.dumps(compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
FULL_PATH.write_text(
    json.dumps(full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ── Re-embed compact array into HTML ──────────────────────────────────────────
html = HTML_PATH.read_text(encoding="utf-8-sig")
embedded = (json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
            .replace("<", "\\u003c"))
html, count = re.subn(
    r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)",
    lambda m: m[1] + embedded + m[2], html, count=1, flags=re.S)
assert count == 1
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)

print("Updated:", ["VP-APP-REPORT-GLUCOSE-001"])
print("New cases:", [x["id"] for x in NEW_COMPACT])
print(f"Compact: {len(compact)}  Run-order: {len(full)}")
