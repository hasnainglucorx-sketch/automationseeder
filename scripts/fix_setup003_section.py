"""
Fix VP-APP-SETUP-003 (Step 05/22 — Permissions overview) section tag.

Problem: SETUP-003 sits at run 89 (after SITE batch, before HEALTH batch)
but still carries sec = "Batch 8 - 22-Step Setup - Setup Guide", which
causes Batch 8 to appear twice in the console.

Fix: give it its own section name "Onboarding Permissions Overview Screen",
then re-run full sequential batch renumbering so every section is Batch 1..N
in run order.
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

# ── Step 1: fix SETUP-003 sec ─────────────────────────────────────────────────
NEW_SEC_003 = "Onboarding Permissions Overview Screen"
fixed = False
for c in compact:
    if c["id"] == "VP-APP-SETUP-003":
        print(f"VP-APP-SETUP-003 run {c['r']}")
        print(f"  old sec: {c['sec']}")
        c["sec"] = NEW_SEC_003
        print(f"  new sec: {c['sec']}")
        fixed = True
        break
assert fixed, "VP-APP-SETUP-003 not found"

# ── Step 2: re-number ALL sections sequentially in run order ──────────────────
seen = {}
for c in compact:
    sec = c.get("sec", "")
    if sec and sec not in seen:
        seen[sec] = c["r"]

ordered = sorted(seen.items(), key=lambda x: x[1])

BATCH_RE = re.compile(r"^Batch \d+[a-z]? - (.+)$")

def descriptive_name(label):
    m = BATCH_RE.match(label)
    return m.group(1) if m else label

old_to_new = {}
for position, (old_label, _) in enumerate(ordered, 1):
    name = descriptive_name(old_label)
    old_to_new[old_label] = f"Batch {position} - {name}"

print(f"\nTotal sections: {len(ordered)}")

# Print the new sequence
for pos, (old_label, run) in enumerate(ordered, 1):
    new = old_to_new[old_label]
    flag = " *" if new != old_label else "  "
    print(f"  {flag} {pos:>2}  run {run:>3}  {new}")

# ── Step 3: apply to compact ──────────────────────────────────────────────────
cases_updated = 0
for c in compact:
    old = c.get("sec", "")
    new = old_to_new.get(old, old)
    if new != old:
        c["sec"] = new
        cases_updated += 1

print(f"\nCases updated: {cases_updated}")

# ── Step 4: write + re-embed ─────────────────────────────────────────────────
COMPACT_PATH.write_text(
    json.dumps(compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
FULL_PATH.write_text(
    json.dumps(full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

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
