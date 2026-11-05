"""
Reorder all 500 cases into correct protocol sequence and renumber run fields 1-500.

Steps:
1. Sort run_order by current `run` field (puts the 461 already-ordered cases right).
2. Remove the 9 misplaced appended cases (run 492-500) and re-insert each one
   directly after its anchor case.
3. Renumber run field 1-500.
4. Sort compact to match the same ID order; update `r`, `sec`, and `method`
   for cases that were added from run_order and are missing those fields.
5. Re-embed compact into HTML and copy to root.

Anchor placements (insert after):
  WELCOME-003/004/005         after VP-APP-WELCOME-002
  SIGNIN-004A / SIGNIN-004B   after VP-APP-SIGNIN-004
  HOME-RANGE-006 / 007        after VP-APP-HOME-RANGE-005
  REPORT-GLUCOSE-001          after VP-APP-HOME-RANGE-007 (Home chart expand)
  REPORT-DAILY-001            after VP-APP-REPORT-AGP-006 (end of Reports/AGP)
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

# ── Section → compact sec label mapping ──────────────────────────────────────
SEC_MAP = {
    "About":                                                    "Batch 56 - About",
    "Account Security":                                         "Batch 48 - Account Security",
    "Application Guidance":                                     "iOS 22-step setup - Application Guidance",
    "Attach the Transmitter":                                   "Batch 24 - Attach the Transmitter",
    "Average Glucose Detail":                                   "Batch 33 - Average Glucose Detail",
    "Bluetooth / Nearby Devices Permission":                    "Batch 12 - Bluetooth / Nearby Devices Permission",
    "Change Password / Re-authentication":                      "Batch 49 - Change Password / Re-authentication",
    "Choose the Application Site":                              "Batch 22 - Choose the Application Site",
    "Clinic Connect":                                           "Batch 46 - Clinic Connect",
    "Critical Alerts / DND Override":                          "Batch 14 - Critical Alerts / DND Override",
    "Delete Account":                                           "Batch 51 - Delete Account",
    "Emergency Contact":                                        "Batch 45 - Emergency Contact",
    "Forgot Password and Login Recovery":                       "Batch 8 - Forgot Password and Login Recovery",
    "Fresh Welcome Screen":                                     "Batch 2 - Welcome Screen",
    "GMI (Estimated A1C) Detail":                              "Batch 34 - GMI (Estimated A1C) Detail",
    "High Glucose Alert":                                       "Batch 17 - High Glucose Alert",
    "Home Screen":                                              "Batch 27 - Home Screen",
    "Home Time Range Selector":                                 "Batch 58 - Home Time Range Selector",
    "Hosted Registration":                                      "Batch 7 - Hosted Registration",
    "Hosted Sign In":                                           "Batch 6 - Hosted Sign In",
    "How to Apply Your Sensor / Instructional Video":           "Batch 18 - How to Apply Your Sensor / Instructional Video",
    "Insulin Event Entry":                                      "Batch 38 - Insulin Event Entry",
    "Journal":                                                  "Batch 41 - Journal",
    "Language":                                                 "Batch 52 - Language",
    "Log a New Event Sheet":                                    "Batch 36 - Log a New Event Sheet",
    "Logout":                                                   "Batch 50 - Logout",
    "Low Glucose Alert":                                        "Batch 16 - Low Glucose Alert",
    "Manual Sensor ID Entry":                                   "Batch 20 - Manual Sensor ID Entry",
    "Meal / Carbohydrate Event Entry":                          "Batch 37 - Meal / Carbohydrate Event Entry",
    "My CGM / Connected Device":                                "Batch 54 - My CGM / Connected Device",
    "Native Create Account and Consent":                        "Batch 5 - Native Create Account and Consent",
    "Native Sign In":                                           "Batch 4 - Native Sign In Screen",
    "Navigation Drawer":                                        "Batch 57 - Navigation Drawer",
    "Notification Permission and Notification Behaviour":       "Batch 13 - Notification Permission",
    "Permission Management":                                    "Batch 47 - Permission Management",
    "Permission Summary / Youâ\u0080\u0099re All Set":    "Batch 15 - Permission Summary / Youâ\u0080\u0099re All Set",
    "Permission Summary / You're All Set":                     "Batch 15 - Permission Summary / You're All Set",
    "Physical Activity Event Entry":                            "Batch 39 - Physical Activity Event Entry",
    "Platform Health Integration (Apple Health / Google Health)":"Batch 11 - Platform Health Integration (Apple Health / Google Health)",
    "Reminder Settings / Glucose Thresholds":                   "Batch 44 - Reminder Settings / Glucose Thresholds",
    "Remove the Sensor From the Box":                           "Batch 21 - Remove the Sensor From the Box",
    "Reports - AGP View":                                       "Batch 31 - Reports - AGP View",
    "Reports - Daily Charts":                                   "Batch 28b - Reports - Daily Charts",
    "Reports - Day View":                                       "Batch 29 - Reports - Day View",
    "Reports - Glucose View":                                   "Batch 27 - Home Screen",
    "Reports - Time Above Range Detail":                        "Reports - Time Above Range Detail",
    "Reports - Time Below Range Detail":                        "Reports - Time Below Range Detail",
    "Reports - Variability Detail":                             "Reports - Variability Detail",
    "Reports - Week View":                                      "Batch 30 - Reports - Week View",
    "Reports Overview and View Navigation":                     "Batch 28 - Reports Overview and View Navigation",
    "Scan Your Sensor and Camera Permission":                   "Batch 19 - Scan Your Sensor and Camera Permission",
    "Sensor Warm-up":                                           "Batch 26 - Sensor Warm-up",
    "Settings Overview":                                        "Batch 42 - Settings Overview",
    "Setup Guide":                                              "iOS 22-step setup - Setup Guide",
    "Severe Events Detail":                                     "Batch 35 - Severe Events Detail",
    "Share / Follow":                                           "Batch 55 - Share / Follow",
    "Sickness / Note Event Entry":                              "Batch 40 - Sickness / Note Event Entry",
    "Splash Screen":                                            "Batch 1 - Splash Screen",
    "Tell Us About You / Profile Setup":                        "Batch 10 - Tell Us About You / Profile Setup",
    "Theme":                                                    "Batch 53 - Theme",
    "Time in Range Detail":                                     "Batch 32 - Time in Range Detail",
    "Transmitter Discovery, Selection, Pairing & Recovery":     "Batch 25 - Transmitter Discovery, Selection, Pairing & Recovery",
    "Unscrew the Applicator Cap":                               "Batch 23 - Unscrew the Applicator Cap",
    "User Guide / IFU Access":                                  "Batch 59 - User Guide / IFU Access",
    "User Profile":                                             "Batch 43 - User Profile",
    "Welcome Navigation":                                       "Batch 2 - Welcome Screen",
}

# ── Anchors: insert the listed IDs (in order) after the anchor ID ─────────────
INSERTIONS = {
    "VP-APP-WELCOME-002":    ["VP-APP-WELCOME-003", "VP-APP-WELCOME-004", "VP-APP-WELCOME-005"],
    "VP-APP-SIGNIN-004":     ["VP-APP-SIGNIN-004A", "VP-APP-SIGNIN-004B"],
    "VP-APP-HOME-RANGE-005": ["VP-APP-HOME-RANGE-006", "VP-APP-HOME-RANGE-007",
                               "VP-APP-REPORT-GLUCOSE-001"],
    "VP-APP-REPORT-AGP-006": ["VP-APP-REPORT-DAILY-001"],
}

# IDs that are being moved from end-of-list to correct positions
MISPLACED = {cid for ids in INSERTIONS.values() for cid in ids}

ri = {x["id"]: x for x in full}

# ── Step 1: sort the non-misplaced cases by current run number ────────────────
base = sorted([x for x in full if x["id"] not in MISPLACED],
              key=lambda x: x.get("run", 9999))

# ── Step 2: insert misplaced cases at their anchor positions ──────────────────
final_full = []
for case in base:
    final_full.append(case)
    anchor_id = case["id"]
    if anchor_id in INSERTIONS:
        for insert_id in INSERTIONS[anchor_id]:
            final_full.append(ri[insert_id])

assert len(final_full) == 500, f"Expected 500, got {len(final_full)}"

# ── Step 3: renumber run field 1-500 ─────────────────────────────────────────
for i, case in enumerate(final_full, 1):
    case["run"] = i

# ── Step 4: sort compact to match the same ID order ──────────────────────────
order_map = {case["id"]: i for i, case in enumerate(final_full)}
ci_dict   = {x["id"]: x for x in compact}

final_compact = []
for case in final_full:
    cid = case["id"]
    c = ci_dict[cid]

    # Fill missing r / sec / method fields
    c["r"] = case["run"]
    if not c.get("sec"):
        ro_sec = case.get("section", "")
        c["sec"] = SEC_MAP.get(ro_sec, ro_sec)
    if not c.get("method"):
        c["method"] = "Manual - Real Device"

    # Update r to match new run number (even for cases that already had r)
    c["r"] = case["run"]

    final_compact.append(c)

assert len(final_compact) == 500

# ── Step 5: write JSON ────────────────────────────────────────────────────────
COMPACT_PATH.write_text(
    json.dumps(final_compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
FULL_PATH.write_text(
    json.dumps(final_full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ── Step 6: re-embed + copy ──────────────────────────────────────────────────
html = HTML_PATH.read_text(encoding="utf-8-sig")
embedded = (json.dumps(final_compact, ensure_ascii=False, separators=(",", ":"))
            .replace("<", "\\u003c"))
html, count = re.subn(
    r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)",
    lambda m: m[1] + embedded + m[2], html, count=1, flags=re.S)
assert count == 1
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)

print("Reorder complete.")
print(f"Compact: {len(final_compact)}  Run-order: {len(final_full)}")
print("First 15 IDs in new order:")
for c in final_full[:15]:
    print(f"  run={c['run']:>3}  {c['id']}")
print("...")
print("Spot-check anchors:")
for anchor, inserts in INSERTIONS.items():
    idx = next(i for i, c in enumerate(final_full) if c["id"] == anchor)
    for j, iid in enumerate(inserts):
        actual = final_full[idx + 1 + j]["id"]
        status = "OK" if actual == iid else f"WRONG ({actual})"
        print(f"  After {anchor} +{j+1}: {iid} -> {status}")
