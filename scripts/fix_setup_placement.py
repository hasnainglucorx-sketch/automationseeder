"""
Move 22-step setup cases from end-of-list to correct protocol positions.

SETUP-001..004 (section=Setup Guide):
  Overview of the 22-step guided setup flow -> insert BEFORE VIDEO-001
  Anchor: after VP-APP-HIGH-013 (run 128), which is the last case
  before the 'How to Apply Your Sensor' section starts.

VOICE-001/002 + APPLY-001..006 (section=Application Guidance):
  In-app voice guidance and physical application step guidance ->
  insert AFTER VP-APP-TX-ATTACH-003 (run 164, end of 'Attach the Transmitter').

After insertion, renumber all runs 1-500, re-embed and copy HTML.
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

MOVEABLE = {
    "VP-APP-SETUP-001", "VP-APP-SETUP-002", "VP-APP-SETUP-003", "VP-APP-SETUP-004",
    "VP-APP-VOICE-001", "VP-APP-VOICE-002",
    "VP-APP-APPLY-001", "VP-APP-APPLY-002", "VP-APP-APPLY-003",
    "VP-APP-APPLY-004", "VP-APP-APPLY-005", "VP-APP-APPLY-006",
}

INSERTIONS = {
    # anchor ID -> list of IDs to insert immediately after that anchor
    "VP-APP-HIGH-013":    ["VP-APP-SETUP-001", "VP-APP-SETUP-002",
                           "VP-APP-SETUP-003", "VP-APP-SETUP-004"],
    "VP-APP-TX-ATTACH-003": ["VP-APP-VOICE-001", "VP-APP-VOICE-002",
                              "VP-APP-APPLY-001", "VP-APP-APPLY-002",
                              "VP-APP-APPLY-003", "VP-APP-APPLY-004",
                              "VP-APP-APPLY-005", "VP-APP-APPLY-006"],
}

# ── Re-order run_order ────────────────────────────────────────────────────────
ri = {x["id"]: x for x in full}

# Verify all anchors and moveable IDs exist
for anchor, ids in INSERTIONS.items():
    assert anchor in ri, f"Anchor missing: {anchor}"
    for cid in ids:
        assert cid in ri, f"Moveable case missing from run_order: {cid}"

base = [x for x in full if x["id"] not in MOVEABLE]
final_full = []
for case in base:
    final_full.append(case)
    if case["id"] in INSERTIONS:
        for insert_id in INSERTIONS[case["id"]]:
            final_full.append(ri[insert_id])

assert len(final_full) == 500, f"Expected 500, got {len(final_full)}"

# Renumber
for i, case in enumerate(final_full, 1):
    case["run"] = i

# ── Re-order compact to match ─────────────────────────────────────────────────
ci_dict = {x["id"]: x for x in compact}
final_compact = []
for case in final_full:
    c = ci_dict[case["id"]]
    c["r"] = case["run"]
    final_compact.append(c)

assert len(final_compact) == 500

# ── Spot-check anchor placements ─────────────────────────────────────────────
for anchor, inserts in INSERTIONS.items():
    idx = next(i for i, c in enumerate(final_full) if c["id"] == anchor)
    print(f"After {anchor} (run {final_full[idx]['run']}):")
    for j, iid in enumerate(inserts):
        actual = final_full[idx + 1 + j]["id"]
        status = "OK" if actual == iid else f"WRONG ({actual})"
        print(f"  +{j+1}: {iid} -> {status}")

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
assert count == 1
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)

print(f"\nCompact: {len(final_compact)}  Run-order: {len(final_full)}")
print("SETUP-001 now at run:", next(c['run'] for c in final_full if c['id']=='VP-APP-SETUP-001'))
print("VOICE-001 now at run:", next(c['run'] for c in final_full if c['id']=='VP-APP-VOICE-001'))
print("APPLY-001 now at run:", next(c['run'] for c in final_full if c['id']=='VP-APP-APPLY-001'))
