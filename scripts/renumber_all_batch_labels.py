"""
Assign a sequential "Batch N - ..." label to EVERY section (64 total).

Sections previously missing a batch number are given one.
Sections that already have one get their number corrected to match run order.
The descriptive name after the number is preserved exactly.

Old label -> descriptive name extraction rules:
  "Batch N[a-z]? - NAME"  -> NAME
  "22-Step Setup - NAME"  -> 22-Step Setup - NAME  (keep full text as name)
  "Reports - NAME"        -> Reports - NAME
  "Reports Overview..."   -> Reports Overview...
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

# ── 1. Collect sections in run order ─────────────────────────────────────────
seen = {}
for c in compact:
    sec = c.get("sec", "")
    if sec and sec not in seen:
        seen[sec] = c["r"]

ordered = sorted(seen.items(), key=lambda x: x[1])   # [(label, first_run), ...]

# ── 2. Extract descriptive name from existing label ───────────────────────────
BATCH_RE = re.compile(r"^Batch \d+[a-z]? - (.+)$")

def descriptive_name(label):
    m = BATCH_RE.match(label)
    if m:
        return m.group(1)          # strip leading "Batch N - "
    return label                   # already has no batch prefix — keep as-is

# ── 3. Build old -> new mapping ───────────────────────────────────────────────
old_to_new = {}
for position, (old_label, _) in enumerate(ordered, 1):
    name = descriptive_name(old_label)
    new_label = f"Batch {position} - {name}"
    old_to_new[old_label] = new_label

# ── 4. Report ─────────────────────────────────────────────────────────────────
print("Section renumbering (all 64 batches):")
for pos, (old_label, run) in enumerate(ordered, 1):
    new_label = old_to_new[old_label]
    flag = "  *" if new_label != old_label else "   "
    print(f"{flag} {pos:>2}  run {run:>3}  {new_label}")

changed_sections = sum(1 for o, n in old_to_new.items() if o != n)
print(f"\nSections changed: {changed_sections} of {len(ordered)}")

# ── 5. Apply to compact ───────────────────────────────────────────────────────
cases_updated = 0
for c in compact:
    old = c.get("sec", "")
    new = old_to_new.get(old, old)
    if new != old:
        c["sec"] = new
        cases_updated += 1

print(f"Compact cases updated: {cases_updated}")

# ── 6. Write both JSON files ──────────────────────────────────────────────────
COMPACT_PATH.write_text(
    json.dumps(compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
FULL_PATH.write_text(
    json.dumps(full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ── 7. Re-embed + copy HTML ───────────────────────────────────────────────────
html = HTML_PATH.read_text(encoding="utf-8-sig")
embedded = (json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
            .replace("<", "\\u003c"))
html, count = re.subn(
    r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)",
    lambda m: m[1] + embedded + m[2], html, count=1, flags=re.S)
assert count == 1
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)

print("\nDone. HTML re-embedded and root copy updated.")
