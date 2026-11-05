"""
Update VP-APP-SPLASH-001 from docx v33_new3 and remove VP-APP-SPLASH-002.

Changes from docx:
- SPLASH-001: preconditions simplified, procedure reduced from 3 to 2 steps,
  version check merged into step 1 expected result.
- SPLASH-002: removed entirely (was already marked as merged into SPLASH-001).
"""
import json
import sys
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPACT_PATH = os.path.join(BASE, "output", "console-update", "PRT-0701-cases.json")
RUN_ORDER_PATH = os.path.join(BASE, "output", "console-update", "PRT-0701-run_order.json")

# Load latest files
with open(COMPACT_PATH, "r", encoding="utf-8") as f:
    compact = json.load(f)
with open(RUN_ORDER_PATH, "r", encoding="utf-8") as f:
    run_order = json.load(f)

print(f"Loaded {len(compact)} compact cases, {len(run_order)} run-order cases")

# --- Update VP-APP-SPLASH-001 ---
new_pre = "App fully closed before launch."
new_proc = (
    "1. Launch Modus App and observe the splash presentation.\n"
    "2. Keep watching until the splash closes."
)
new_exp = (
    "1. The splash opens without blank or corrupt content, displays the GlucoRx CGMx™ 1 product identity "
    "without missing, substituted, distorted or clipped app-owned content, and shows the app version and "
    "build number matching the build recorded in the PROCESS table.\n"
    "2. The splash moves to the Welcome screen with no hang, crash, blank state or repeated splash loop."
)

found_compact_001 = False
found_ro_001 = False

for c in compact:
    if c["id"] == "VP-APP-SPLASH-001":
        c["pre"] = new_pre
        c["proc"] = new_proc
        c["exp"] = new_exp
        found_compact_001 = True
        print("Updated VP-APP-SPLASH-001 in compact")
        break

if not found_compact_001:
    print("ERROR: VP-APP-SPLASH-001 not found in compact cases", file=sys.stderr)
    sys.exit(1)

for r in run_order:
    if r["id"] == "VP-APP-SPLASH-001":
        r["preconditions"] = new_pre
        r["procedure"] = new_proc
        r["expected"] = new_exp
        found_ro_001 = True
        print("Updated VP-APP-SPLASH-001 in run-order")
        break

if not found_ro_001:
    print("ERROR: VP-APP-SPLASH-001 not found in run-order cases", file=sys.stderr)
    sys.exit(1)

# --- Remove VP-APP-SPLASH-002 ---
compact_before = len(compact)
compact = [c for c in compact if c["id"] != "VP-APP-SPLASH-002"]
if len(compact) == compact_before:
    print("WARNING: VP-APP-SPLASH-002 not found in compact cases")
else:
    print(f"Removed VP-APP-SPLASH-002 from compact (was {compact_before}, now {len(compact)})")

ro_before = len(run_order)
run_order = [r for r in run_order if r["id"] != "VP-APP-SPLASH-002"]
if len(run_order) == ro_before:
    print("WARNING: VP-APP-SPLASH-002 not found in run-order cases")
else:
    print(f"Removed VP-APP-SPLASH-002 from run-order (was {ro_before}, now {len(run_order)})")

# --- Renumber run positions after removal ---
for i, c in enumerate(compact):
    c["r"] = i + 1

for i, r in enumerate(run_order):
    r["run"] = i + 1

# Write back
with open(COMPACT_PATH, "w", encoding="utf-8") as f:
    json.dump(compact, f, indent=2, ensure_ascii=False)
    f.write("\n")
print(f"Wrote {len(compact)} compact cases")

with open(RUN_ORDER_PATH, "w", encoding="utf-8") as f:
    json.dump(run_order, f, indent=2, ensure_ascii=False)
    f.write("\n")
print(f"Wrote {len(run_order)} run-order cases")

print("\nDone. Now run: python scripts/generate_unified_console.py")
