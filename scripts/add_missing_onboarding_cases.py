"""
Add two cases confirmed missing from the 22-step onboarding flow audit.

Case 1 — VP-APP-CRITICAL-022 (Step 10/22: Breaking through Do Not Disturb)
  Insert immediately after VP-APP-CRITICAL-002 (run 105),
  before VP-APP-PERM-SUM-008.
  iOS-specific: the screen text begins "On iPhone..."

Case 2 — VP-APP-SENSOR-REG-001 (Step 15/22: Sensor registered)
  Insert immediately after VP-APP-SENSOR-ID-007 (run 172 before insertion),
  before VP-APP-PREP-001.

After both insertions the total becomes 502, runs renumbered 1–502.
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

EXPECTED_BEFORE = 500
assert len(compact) == EXPECTED_BEFORE, f"Compact: expected {EXPECTED_BEFORE}, got {len(compact)}"
assert len(full)    == EXPECTED_BEFORE, f"Full: expected {EXPECTED_BEFORE}, got {len(full)}"

ci = {x["id"]: x for x in compact}
ri = {x["id"]: x for x in full}

# Verify anchors exist and new IDs are absent
ANCHORS = ["VP-APP-CRITICAL-002", "VP-APP-SENSOR-ID-007"]
NEW_IDS = ["VP-APP-CRITICAL-022", "VP-APP-SENSOR-REG-001"]
for cid in ANCHORS:
    assert cid in ri, f"Anchor missing from run_order: {cid}"
    assert cid in ci, f"Anchor missing from compact: {cid}"
for cid in NEW_IDS:
    assert cid not in ri, f"ID already in run_order: {cid}"
    assert cid not in ci, f"ID already in compact: {cid}"

# ── New case definitions ──────────────────────────────────────────────────────

NEW_FULL_CRITICAL_022 = {
    "id": "VP-APP-CRITICAL-022",
    "run": 0,   # will be renumbered
    "title": "Breaking through Do Not Disturb guidance screen",
    "requirement": "DI-372 / DO-715 and DI-719 / DO-822",
    "preconditions": (
        "The device is at the Breaking through Do Not Disturb screen "
        "(STEP 10/22). iOS device is used."
    ),
    "procedure": (
        "1. Read the screen title, body text and available controls.\n"
        "2. Tap Continue."
    ),
    "expected": (
        "1. The screen title is \"Breaking through Do Not Disturb\". "
        "The body text states: \"On iPhone, the way a severe low-glucose alert "
        "reaches you through Silent and Focus is Critical Alerts — you’ll "
        "enable that next. There is no separate per-app Do Not Disturb switch to "
        "turn on.\" Two controls are present: Continue and Not now.\n"
        "2. The app advances to STEP 11/22 (You’re all set)."
    ),
    "evidence": (
        "1. Screenshot of the Breaking through Do Not Disturb screen showing the "
        "title, body text and both controls.\n"
        "2. Screenshot of STEP 11/22 confirming onward navigation after tapping Continue."
    )
}

NEW_COMPACT_CRITICAL_022 = {
    "id": "VP-APP-CRITICAL-022",
    "r": 0,   # will be renumbered
    "sec": "Batch 14 - Critical Alerts / DND Override",
    "method": "Manual - Real Device",
    "t": "Breaking through Do Not Disturb guidance screen",
    "req": "DI-372 / DO-715 and DI-719 / DO-822",
    "pre": (
        "The device is at the Breaking through Do Not Disturb screen "
        "(STEP 10/22). iOS device is used."
    ),
    "proc": (
        "1. Read the screen title, body text and available controls.\n"
        "2. Tap Continue."
    ),
    "exp": (
        "1. The screen title is \"Breaking through Do Not Disturb\". "
        "The body text states: \"On iPhone, the way a severe low-glucose alert "
        "reaches you through Silent and Focus is Critical Alerts — you’ll "
        "enable that next. There is no separate per-app Do Not Disturb switch to "
        "turn on.\" Two controls are present: Continue and Not now.\n"
        "2. The app advances to STEP 11/22 (You’re all set)."
    ),
    "ev": (
        "1. Screenshot of the Breaking through Do Not Disturb screen showing the "
        "title, body text and both controls.\n"
        "2. Screenshot of STEP 11/22 confirming onward navigation after tapping Continue."
    )
}

NEW_FULL_SENSOR_REG_001 = {
    "id": "VP-APP-SENSOR-REG-001",
    "run": 0,
    "title": "Sensor registered confirmation screen",
    "requirement": "DI-716 / DO-819",
    "preconditions": (
        "The sensor has been identified (scanned or entered manually) and the app "
        "is at the Sensor registered screen (STEP 15/22)."
    ),
    "procedure": (
        "1. Read the screen title, body text and the sensor-details row.\n"
        "2. Confirm the sensor details row shows the transmitter serial number "
        "recorded during sensor identification.\n"
        "3. Tap Continue."
    ),
    "expected": (
        "1. The screen title is \"Sensor registered\". The body text is "
        "\"We’ve got your sensor’s details. Next we’ll put it on "
        "— then the app connects to it.\" A Sensor details saved row is present.\n"
        "2. The Sensor details saved row displays the transmitter serial number "
        "that was entered or scanned in the preceding step.\n"
        "3. The app advances to STEP 16/22 (Clean and dry your skin)."
    ),
    "evidence": (
        "1. Screenshot of the Sensor registered screen showing the title, body text "
        "and Sensor details saved row with the transmitter serial number.\n"
        "2. Screenshot of STEP 16/22 confirming onward navigation after tapping Continue."
    )
}

NEW_COMPACT_SENSOR_REG_001 = {
    "id": "VP-APP-SENSOR-REG-001",
    "r": 0,
    "sec": "Batch 20 - Manual Sensor ID Entry",
    "method": "Manual - Real Device",
    "t": "Sensor registered confirmation screen",
    "req": "DI-716 / DO-819",
    "pre": (
        "The sensor has been identified (scanned or entered manually) and the app "
        "is at the Sensor registered screen (STEP 15/22)."
    ),
    "proc": (
        "1. Read the screen title, body text and the sensor-details row.\n"
        "2. Confirm the sensor details row shows the transmitter serial number "
        "recorded during sensor identification.\n"
        "3. Tap Continue."
    ),
    "exp": (
        "1. The screen title is \"Sensor registered\". The body text is "
        "\"We’ve got your sensor’s details. Next we’ll put it on "
        "— then the app connects to it.\" A Sensor details saved row is present.\n"
        "2. The Sensor details saved row displays the transmitter serial number "
        "that was entered or scanned in the preceding step.\n"
        "3. The app advances to STEP 16/22 (Clean and dry your skin)."
    ),
    "ev": (
        "1. Screenshot of the Sensor registered screen showing the title, body text "
        "and Sensor details saved row with the transmitter serial number.\n"
        "2. Screenshot of STEP 16/22 confirming onward navigation after tapping Continue."
    )
}

# ── Build new run_order ───────────────────────────────────────────────────────
INSERTIONS = {
    "VP-APP-CRITICAL-002":  NEW_FULL_CRITICAL_022,
    "VP-APP-SENSOR-ID-007": NEW_FULL_SENSOR_REG_001,
}

final_full = []
for case in full:
    final_full.append(case)
    if case["id"] in INSERTIONS:
        final_full.append(INSERTIONS[case["id"]])

EXPECTED_AFTER = EXPECTED_BEFORE + len(NEW_IDS)
assert len(final_full) == EXPECTED_AFTER, f"Expected {EXPECTED_AFTER}, got {len(final_full)}"

# Renumber
for i, case in enumerate(final_full, 1):
    case["run"] = i

# ── Build matching compact ────────────────────────────────────────────────────
# Add new compact objects to lookup
ci["VP-APP-CRITICAL-022"]  = NEW_COMPACT_CRITICAL_022
ci["VP-APP-SENSOR-REG-001"] = NEW_COMPACT_SENSOR_REG_001

final_compact = []
for case in final_full:
    c = ci[case["id"]]
    c["r"] = case["run"]
    final_compact.append(c)

assert len(final_compact) == EXPECTED_AFTER

# ── Spot-checks ───────────────────────────────────────────────────────────────
def run_of_f(cid):
    return next(c["run"] for c in final_full if c["id"] == cid)

c022_run  = run_of_f("VP-APP-CRITICAL-022")
crit2_run = run_of_f("VP-APP-CRITICAL-002")
psm8_run  = run_of_f("VP-APP-PERM-SUM-008")
sreg_run  = run_of_f("VP-APP-SENSOR-REG-001")
sid7_run  = run_of_f("VP-APP-SENSOR-ID-007")
prep_run  = run_of_f("VP-APP-PREP-001")

print("Insertion check:")
print(f"  CRITICAL-002          run {crit2_run}")
print(f"  CRITICAL-022 (new)    run {c022_run}  (should be {crit2_run + 1})")
print(f"  PERM-SUM-008          run {psm8_run}  (should be {crit2_run + 2})")
assert c022_run == crit2_run + 1, f"CRITICAL-022 not immediately after CRITICAL-002"
assert psm8_run == crit2_run + 2, f"PERM-SUM-008 not immediately after CRITICAL-022"

print(f"  SENSOR-ID-007         run {sid7_run}")
print(f"  SENSOR-REG-001 (new)  run {sreg_run}  (should be {sid7_run + 1})")
print(f"  PREP-001              run {prep_run}  (should be {sid7_run + 2})")
assert sreg_run == sid7_run + 1, f"SENSOR-REG-001 not immediately after SENSOR-ID-007"
assert prep_run == sid7_run + 2, f"PREP-001 not immediately after SENSOR-REG-001"

print(f"\nTotal run_order: {len(final_full)}  Total compact: {len(final_compact)}")
print("All insertion assertions passed.")

# ── Write JSON ────────────────────────────────────────────────────────────────
COMPACT_PATH.write_text(
    json.dumps(final_compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
FULL_PATH.write_text(
    json.dumps(final_full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ── Re-embed + copy ───────────────────────────────────────────────────────────
html = HTML_PATH.read_text(encoding="utf-8-sig")
embedded = (json.dumps(final_compact, ensure_ascii=False, separators=(",", ":"))
            .replace("<", "\\u003c"))
html, count = re.subn(
    r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)",
    lambda m: m[1] + embedded + m[2], html, count=1, flags=re.S)
assert count == 1, "HTML embed pattern not found"
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)

print("\nDone. HTML re-embedded and root copy updated.")
