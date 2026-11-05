"""
Pull all scattered Hosted Sign In cases back into the batch in correct order.

Current state:
  runs 24-32: HOSTED-SIGNIN-001/002/003/004/006/010/011/013/007
  run 66:     HOSTED-SIGNIN-015  (misplaced)
  run 454:    HOSTED-SIGNIN-012  (misplaced)
  run 458:    HOSTED-SIGNIN-005A (misplaced)
  run 459:    HOSTED-SIGNIN-014  (misplaced)
  run 460:    HOSTED-SIGNIN-005B (misplaced)
  run 499:    HOSTED-SIGNIN-008  (misplaced)
  run 500:    HOSTED-SIGNIN-009  (misplaced)

Target order (immediately after VP-APP-REGISTER-CONSENT-005, run 23):
  001, 002, 003, 004, 005A, 005B, 006, 007, 008, 009, 010, 011, 012, 013, 014, 015
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

ANCHOR = "VP-APP-REGISTER-CONSENT-005"

ORDERED_BATCH = [
    "VP-APP-HOSTED-SIGNIN-001",
    "VP-APP-HOSTED-SIGNIN-002",
    "VP-APP-HOSTED-SIGNIN-003",
    "VP-APP-HOSTED-SIGNIN-004",
    "VP-APP-HOSTED-SIGNIN-005A",
    "VP-APP-HOSTED-SIGNIN-005B",
    "VP-APP-HOSTED-SIGNIN-006",
    "VP-APP-HOSTED-SIGNIN-007",
    "VP-APP-HOSTED-SIGNIN-008",
    "VP-APP-HOSTED-SIGNIN-009",
    "VP-APP-HOSTED-SIGNIN-010",
    "VP-APP-HOSTED-SIGNIN-011",
    "VP-APP-HOSTED-SIGNIN-012",
    "VP-APP-HOSTED-SIGNIN-013",
    "VP-APP-HOSTED-SIGNIN-014",
    "VP-APP-HOSTED-SIGNIN-015",
]

ri = {x["id"]: x for x in full}

# Verify all IDs exist
assert ANCHOR in ri, f"Anchor missing: {ANCHOR}"
for cid in ORDERED_BATCH:
    assert cid in ri, f"Missing from run_order: {cid}"

BATCH_SET = set(ORDERED_BATCH)

# Build new ordered list: everything except the batch, insert batch at anchor
final_full = []
for case in full:
    if case["id"] in BATCH_SET:
        continue   # will be re-inserted at anchor
    final_full.append(case)
    if case["id"] == ANCHOR:
        for batch_id in ORDERED_BATCH:
            final_full.append(ri[batch_id])

assert len(final_full) == 500, f"Expected 500, got {len(final_full)}"

# Renumber
for i, case in enumerate(final_full, 1):
    case["run"] = i

# Re-order compact to match
ci_dict = {x["id"]: x for x in compact}
final_compact = []
for case in final_full:
    c = ci_dict[case["id"]]
    c["r"] = case["run"]
    final_compact.append(c)

assert len(final_compact) == 500

# Spot-check
anchor_idx = next(i for i, c in enumerate(final_full) if c["id"] == ANCHOR)
print(f"Anchor {ANCHOR} at run {final_full[anchor_idx]['run']}")
print("Hosted Sign In batch:")
for j, cid in enumerate(ORDERED_BATCH):
    actual = final_full[anchor_idx + 1 + j]
    status = "OK" if actual["id"] == cid else f"WRONG ({actual['id']})"
    print(f"  run {actual['run']:>3}  {cid}  {status}")

# Write JSON
COMPACT_PATH.write_text(
    json.dumps(final_compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
FULL_PATH.write_text(
    json.dumps(final_full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Re-embed + copy
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
