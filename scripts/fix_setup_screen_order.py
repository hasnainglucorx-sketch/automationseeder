"""
Move SETUP cases to their correct protocol positions matching the 22-step flow.

Screenshots confirm:
  Step 01/22 = "Your setup" overview       → VP-APP-SETUP-001
  Step 02/22 = "Before you begin"          → VP-APP-SETUP-002
  Step 03/22 = "Tell us about you"         → PROFILE batch (already correct after RESET)
  Step 04/22 = "Choose application site"   → SITE batch (already moved)
  Step 05/22 = "A few permissions" overview→ VP-APP-SETUP-003
  Step 06–09 = individual permissions       → HEALTH / NOTIFY / BT-PERM / CRITICAL

Current (wrong) position: SETUP-001..004 at runs 146-149
                           (after HIGH alert cases)

New positions:
  SETUP-001, SETUP-002, SETUP-004 → immediately BEFORE VP-APP-PROFILE-001
                                     (anchor: VP-APP-RESET-013, the last reset/forgot-pwd case)
  SETUP-003                       → immediately BEFORE VP-APP-HEALTH-001
                                     (anchor: VP-APP-SITE-004, last site case)
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

EXPECTED = 500
assert len(compact) == EXPECTED and len(full) == EXPECTED

ri = {x["id"]: x for x in full}
ci = {x["id"]: x for x in compact}

# ── Placements ────────────────────────────────────────────────────────────────
# Group 1: Step 01, 02 + Skip case → before Profile (after last Reset case)
GROUP1_ANCHOR = "VP-APP-RESET-013"
GROUP1_IDS    = ["VP-APP-SETUP-001", "VP-APP-SETUP-002", "VP-APP-SETUP-004"]

# Group 2: Step 05 permissions overview → before HEALTH (after last SITE case)
GROUP2_ANCHOR = "VP-APP-SITE-004"
GROUP2_IDS    = ["VP-APP-SETUP-003"]

MOVEABLE = set(GROUP1_IDS + GROUP2_IDS)

for cid in GROUP1_IDS + GROUP2_IDS + [GROUP1_ANCHOR, GROUP2_ANCHOR]:
    assert cid in ri, f"Missing from run_order: {cid}"

# ── Build new order ───────────────────────────────────────────────────────────
final_full = []
for case in full:
    cid = case["id"]
    if cid in MOVEABLE:
        continue
    final_full.append(case)
    if cid == GROUP1_ANCHOR:
        for insert_id in GROUP1_IDS:
            final_full.append(ri[insert_id])
    if cid == GROUP2_ANCHOR:
        for insert_id in GROUP2_IDS:
            final_full.append(ri[insert_id])

assert len(final_full) == EXPECTED, f"Expected {EXPECTED}, got {len(final_full)}"

# Renumber
for i, case in enumerate(final_full, 1):
    case["run"] = i

# Re-order compact to match
final_compact = []
for case in final_full:
    c = ci[case["id"]]
    c["r"] = case["run"]
    final_compact.append(c)

assert len(final_compact) == EXPECTED

# ── Spot-check ────────────────────────────────────────────────────────────────
def spot(anchor, inserts, label):
    idx = next(i for i, c in enumerate(final_full) if c["id"] == anchor)
    print(f"{label}: After {anchor} (run {final_full[idx]['run']}):")
    for j, iid in enumerate(inserts):
        actual = final_full[idx + 1 + j]
        ok = "OK" if actual["id"] == iid else f"WRONG ({actual['id']})"
        print(f"  +{j+1}: {iid}  {ok}")

spot(GROUP1_ANCHOR, GROUP1_IDS, "Group 1 (Step 01/02 before Profile)")
spot(GROUP2_ANCHOR, GROUP2_IDS, "Group 2 (Step 05 before Health)")

# Verify key order
def run_of(cid):
    return next(c["run"] for c in final_full if c["id"] == cid)

s001 = run_of("VP-APP-SETUP-001")
s002 = run_of("VP-APP-SETUP-002")
s003 = run_of("VP-APP-SETUP-003")
prof = run_of("VP-APP-PROFILE-001")
site = run_of("VP-APP-SITE-001")
hlth = run_of("VP-APP-HEALTH-001")

print(f"\nOrder check:")
print(f"  SETUP-001 (Step 01)  run {s001}")
print(f"  SETUP-002 (Step 02)  run {s002}")
print(f"  PROFILE-001 (Step 03) run {prof}  > {s002}: {prof > s002}")
print(f"  SITE-001 (Step 04)   run {site}   > {prof}: {site > prof}")
print(f"  SETUP-003 (Step 05)  run {s003}   > {site}: {s003 > site}")
print(f"  HEALTH-001 (Step 06) run {hlth}   > {s003}: {hlth > s003}")
assert s001 < s002 < prof < site < s003 < hlth, "Order assertion failed"
print("All order assertions passed.")

# ── Write ─────────────────────────────────────────────────────────────────────
COMPACT_PATH.write_text(
    json.dumps(final_compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
FULL_PATH.write_text(
    json.dumps(final_full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

html = HTML_PATH.read_text(encoding="utf-8-sig")
embedded = (json.dumps(final_compact, ensure_ascii=False, separators=(",", ":"))
            .replace("<", "\\u003c"))
html, count = re.subn(
    r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)",
    lambda m: m[1] + embedded + m[2], html, count=1, flags=re.S)
assert count == 1
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)

print(f"\nCompact: {len(final_compact)}  Run-order: {len(final_full)}")
print("Done.")
