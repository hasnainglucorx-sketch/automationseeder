"""
Renumber all "Batch N - ..." section labels sequentially based on their
actual first-run position.

Sections that have no "Batch N -" prefix (22-Step Setup guide/application,
Reports detail sub-sections, Reports Overview stand-alone) are left unchanged.
Only the leading "Batch N" number is updated; the descriptive name is kept.

After renumbering, both JSON files and both HTML files are updated.
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

TOTAL = len(compact)
assert len(full) == TOTAL

BATCH_PREFIX = re.compile(r"^Batch \d+[a-z]? - (.+)$")

# ── 1. Collect section labels in run order (first occurrence) ─────────────────
seen_sections = {}   # label → first run
for c in compact:
    sec = c.get("sec", "")
    if sec and sec not in seen_sections:
        seen_sections[sec] = c["r"]

ordered_sections = sorted(seen_sections.items(), key=lambda x: x[1])

# ── 2. Assign new sequential batch numbers to sections that have one ───────────
counter = 0
old_to_new = {}   # old label → new label

for old_label, _ in ordered_sections:
    m = BATCH_PREFIX.match(old_label)
    if m:
        counter += 1
        name = m.group(1)
        new_label = f"Batch {counter} - {name}"
        old_to_new[old_label] = new_label
    else:
        old_to_new[old_label] = old_label   # no change for non-numbered sections

# ── 3. Report the mapping ──────────────────────────────────────────────────────
print("Section label renumbering:")
for old_label, _ in ordered_sections:
    new_label = old_to_new[old_label]
    changed = "  *" if new_label != old_label else "   "
    print(f"{changed} run {seen_sections[old_label]:>3}  {old_label!r:60s}  ->  {new_label!r}")

print(f"\nTotal sections with batch prefix: {counter}")
changed_count = sum(1 for o, n in old_to_new.items() if o != n)
print(f"Sections whose label changes: {changed_count}")

# ── 4. Apply to compact JSON ──────────────────────────────────────────────────
cases_updated = 0
for c in compact:
    old = c.get("sec", "")
    new = old_to_new.get(old, old)
    if new != old:
        c["sec"] = new
        cases_updated += 1

print(f"Compact cases updated: {cases_updated}")
assert cases_updated > 0, "No cases were updated — check the mapping"

# ── 5. Write compact JSON ─────────────────────────────────────────────────────
COMPACT_PATH.write_text(
    json.dumps(compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# full (run_order) JSON does not carry the sec field — no change needed there
FULL_PATH.write_text(
    json.dumps(full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ── 6. Re-embed + copy HTML ───────────────────────────────────────────────────
html = HTML_PATH.read_text(encoding="utf-8-sig")
embedded = (json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
            .replace("<", "\\u003c"))
html, count = re.subn(
    r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)",
    lambda m: m[1] + embedded + m[2], html, count=1, flags=re.S)
assert count == 1, "HTML embed pattern not found"
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)

print("\nDone. HTML re-embedded and root copy updated.")
