"""
Re-arrange batches to match the confirmed 22-step onboarding flow from screenshots.

Changes (two independent moves):

MOVE 1 — Choose Application Site (SITE batch)
  Screenshots confirm Step 04/22 = Choose the application site,
  which is BEFORE Apple Health (Step 06) and all other permissions.
  Current position: runs 165-168 (after sensor scan / sensor prep)
  New position:     immediately after VP-APP-PROFILE-014 (last profile case)
                    and before VP-APP-HEALTH-001

MOVE 2 — Permission Summary / You're All Set (PERM-SUM-001..007)
  Step 11/22 = You're all set screen, which is AFTER Critical Alerts (Step 09/10)
  but BEFORE Set Low Glucose Alert (Step 12) and Set High Glucose Alert (Step 13).
  Current position: VP-APP-PERM-SUM-001..007 scattered at runs 210-214, 332-333
                    (all after LOW/HIGH alert threshold cases at runs 99-134)
  New position:     immediately after VP-APP-PERM-SUM-008 (run 98, last CRITICAL/onboarding case)
                    and before VP-APP-LOW-001 (first LOW alert setup case)

After both moves, renumber runs 1-500, re-embed and copy HTML.
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

EXPECTED_COUNT = 500
assert len(compact) == EXPECTED_COUNT, f"Compact: expected {EXPECTED_COUNT}, got {len(compact)}"
assert len(full)    == EXPECTED_COUNT, f"Full: expected {EXPECTED_COUNT}, got {len(full)}"

ri = {x["id"]: x for x in full}
ci = {x["id"]: x for x in compact}

# ── MOVE 1: SITE batch ────────────────────────────────────────────────────────
SITE_IDS = [
    "VP-APP-SITE-001",
    "VP-APP-SITE-002",
    "VP-APP-SITE-003",
    "VP-APP-SITE-004",
]
SITE_ANCHOR = "VP-APP-PROFILE-014"   # insert after this

# ── MOVE 2: PERM-SUM batch (all except PERM-SUM-008 which is already placed) ──
PERM_SUM_IDS = [
    "VP-APP-PERM-SUM-001",
    "VP-APP-PERM-SUM-002",
    "VP-APP-PERM-SUM-005",
    "VP-APP-PERM-SUM-006",
    "VP-APP-PERM-SUM-007",
    "VP-APP-PERM-SUM-003",
    "VP-APP-PERM-SUM-004",
]
PERM_SUM_ANCHOR = "VP-APP-PERM-SUM-008"   # insert after this

# Verify all IDs exist in run_order
for cid in SITE_IDS + PERM_SUM_IDS + [SITE_ANCHOR, PERM_SUM_ANCHOR]:
    assert cid in ri, f"Missing from run_order: {cid}"

MOVEABLE = set(SITE_IDS + PERM_SUM_IDS)

# Build new ordered list
final_full = []
for case in full:
    cid = case["id"]
    if cid in MOVEABLE:
        continue   # will be re-inserted at anchor
    final_full.append(case)
    if cid == SITE_ANCHOR:
        for insert_id in SITE_IDS:
            final_full.append(ri[insert_id])
    if cid == PERM_SUM_ANCHOR:
        for insert_id in PERM_SUM_IDS:
            final_full.append(ri[insert_id])

assert len(final_full) == EXPECTED_COUNT, f"Expected {EXPECTED_COUNT}, got {len(final_full)}"

# Renumber
for i, case in enumerate(final_full, 1):
    case["run"] = i

# Re-order compact to match
final_compact = []
for case in final_full:
    c = ci[case["id"]]
    c["r"] = case["run"]
    final_compact.append(c)

assert len(final_compact) == EXPECTED_COUNT

# ── Spot-check ────────────────────────────────────────────────────────────────
def spot_check(anchor_id, expected_ids, label):
    idx = next(i for i, c in enumerate(final_full) if c["id"] == anchor_id)
    print(f"\n{label}: After {anchor_id} (run {final_full[idx]['run']}):")
    for j, iid in enumerate(expected_ids):
        actual = final_full[idx + 1 + j]
        status = "OK" if actual["id"] == iid else f"WRONG (got {actual['id']})"
        print(f"  +{j+1}: {iid}  {status}")

spot_check(SITE_ANCHOR,     SITE_IDS,     "MOVE 1 - SITE batch")
spot_check(PERM_SUM_ANCHOR, PERM_SUM_IDS, "MOVE 2 - PERM-SUM batch")

# Verify SITE now precedes HEALTH
site_run    = next(c["run"] for c in final_full if c["id"] == "VP-APP-SITE-001")
health_run  = next(c["run"] for c in final_full if c["id"] == "VP-APP-HEALTH-001")
perms_run   = next(c["run"] for c in final_full if c["id"] == "VP-APP-PERM-SUM-001")
low_run     = next(c["run"] for c in final_full if c["id"] == "VP-APP-LOW-001")
print(f"\nOrder check:")
print(f"  SITE-001    run {site_run}")
print(f"  HEALTH-001  run {health_run}  (should be > {site_run})")
print(f"  PERM-SUM-001 run {perms_run}  (should be < LOW-001)")
print(f"  LOW-001     run {low_run}")
assert site_run < health_run, "SITE must precede HEALTH"
assert perms_run < low_run,   "PERM-SUM must precede LOW"
print("All order assertions passed.")

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

print(f"\nCompact: {len(final_compact)}  Run-order: {len(final_full)}")
print("Done.")
