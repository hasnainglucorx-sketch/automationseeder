"""
Remove 'iOS' from section labels and generic cross-platform content.

Rules:
- Section label "iOS 22-step setup - *"  → "22-Step Setup - *"
- "Approved real iOS/Android device"      → "Approved real device"
- "approved real iOS or Android device"   → "approved real device"
- "approved iOS or Android device"        → "approved real device"
- "app/iOS version"                        → "app and OS version"
- "Existing iOS and Android setup-guide"  → "Existing platform setup-guide"
- Per-case targeted replacements in Welcome/SignIn/Consent reference notes
  and Warmup notification wording.

KEEP iOS where the test is genuinely iOS-specific:
  - SIGNIN-004B  (iOS background/resume)
  - HEALTH-001/003/009  (Apple Health)
  - REGISTER-CONSENT-005  (iOS SSO prompt)
  - PERMISSION-001 thru 006  (iOS Settings paths, iOS-only cases)
  - CRITICAL-005/016  (iOS Critical Alerts)
  - HOME-015, LOW-015, HIGH-015, REPORT-DAY-005  (iOS Control Centre BT toggle)
  - BLE-SCAN-002/004  (iOS BLE ordering)
  - HOSTED-SIGNIN-005B  (iOS Apple Health note)
  - LOW-005 / HIGH-005 proc  (explicit cross-platform comparison, both devices)
  - CRITICAL-003/006/009 / MEDIUM-001  ("iOS and Android devices" = both required)
  - MEDIUM-002  (iOS notification area/settings)
  - LANGUAGE-005  (reinstall on iOS specific step)
  - CRITICAL-006/009 pre  (need both devices)
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
ci = {x["id"]: x for x in compact}
ri = {x["id"]: x for x in full}

changed = []

# ── 1. Section label fix ──────────────────────────────────────────────────────
SEC_OLD_NEW = {
    "iOS 22-step setup - Setup Guide":          "22-Step Setup - Setup Guide",
    "iOS 22-step setup - Application Guidance": "22-Step Setup - Application Guidance",
}
for c in compact:
    old_sec = c.get("sec", "")
    if old_sec in SEC_OLD_NEW:
        c["sec"] = SEC_OLD_NEW[old_sec]
        if c["id"] not in changed:
            changed.append(c["id"])

# ── 2. Global content replacements (safe – cross-platform phrasing only) ───────
GLOBAL_SUBS = [
    # exact strings, in decreasing specificity so shorter patterns don't
    # accidentally match what the longer ones already fixed
    ("Approved real iOS/Android device",       "Approved real device"),
    ("approved real iOS/Android device",       "approved real device"),
    ("Approved real iOS or Android device",    "Approved real device"),
    ("approved real iOS or Android device",    "approved real device"),
    ("Approved iOS or Android device",         "Approved real device"),
    ("approved iOS or Android device",         "approved real device"),
    ("approved iOS or Android",                "approved"),           # fallback
    ("app/iOS version",                        "app and OS version"),
    ("Existing iOS and Android setup-guide",   "Existing platform setup-guide"),
]

COMPACT_FIELDS = ["pre", "proc", "exp", "ev"]
FULL_FIELDS    = ["preconditions", "procedure", "expected", "evidence"]

def apply_subs(text):
    for old, new in GLOBAL_SUBS:
        text = text.replace(old, new)
    return text

for c in compact:
    for fld in COMPACT_FIELDS:
        orig = c.get(fld, "")
        updated = apply_subs(orig)
        if updated != orig:
            c[fld] = updated
            if c["id"] not in changed:
                changed.append(c["id"])

for r in full:
    for fld in FULL_FIELDS:
        orig = r.get(fld, "")
        updated = apply_subs(orig)
        if updated != orig:
            r[fld] = updated

# ── 3. Per-case targeted fixes ────────────────────────────────────────────────
def patch_compact(cid, fld, old, new):
    assert cid in ci, f"Missing compact: {cid}"
    c = ci[cid]
    assert old in c[fld], f"{cid}.{fld} does not contain expected text:\n{c[fld]}"
    c[fld] = c[fld].replace(old, new)
    if cid not in changed:
        changed.append(cid)

def patch_full(cid, fld, old, new):
    assert cid in ri, f"Missing run_order: {cid}"
    r = ri[cid]
    assert old in r[fld], f"{cid}.{fld} does not contain expected text:\n{r[fld]}"
    r[fld] = r[fld].replace(old, new)

def patch_both(cid, compact_fld, full_fld, old, new):
    patch_compact(cid, compact_fld, old, new)
    patch_full(cid, full_fld, old, new)

# Welcome-001: "approved iOS Welcome reference" → "approved platform Welcome reference"
patch_both("VP-APP-WELCOME-001", "proc", "procedure",
           "approved iOS Welcome reference", "approved platform Welcome reference")

# SignIn-001: "approved iOS reference" → "approved platform reference"
patch_both("VP-APP-SIGNIN-001", "proc", "procedure",
           "approved iOS reference", "approved platform reference")
patch_both("VP-APP-SIGNIN-001", "ev", "evidence",
           "approved iOS reference", "approved platform reference")

# Register-Consent-001: "approved iOS reference" → "approved platform reference"
patch_both("VP-APP-REGISTER-CONSENT-001", "proc", "procedure",
           "approved iOS reference", "approved platform reference")

# VIDEO-001: compact pre has "approved iOS device"; run_order has different text — compact only
patch_compact("VP-APP-VIDEO-001", "pre",
              "approved iOS device", "approved device")

# WARMUP-003: "standard iOS navigation route" → "standard navigation route"
patch_both("VP-APP-WARMUP-003", "proc", "procedure",
           "standard iOS navigation route", "standard navigation route")

# WARMUP-009: iOS notification wording (cross-platform warm-up alert)
patch_both("VP-APP-WARMUP-009", "proc", "procedure",
           "an iOS notification arrives", "a platform notification arrives")
patch_both("VP-APP-WARMUP-009", "exp", "expected",
           "An iOS notification is delivered", "A platform notification is delivered")
patch_both("VP-APP-WARMUP-009", "ev", "evidence",
           "screenshot of iOS notification", "screenshot of platform notification")


# PROFILE-001: "approved real iOS or Android device" already covered by global,
# but if the global left a plain "approved real device" that's correct — no extra step.

# ── 4. Sync run_order preconditions for cases changed in compact ──────────────
# For cases where compact precondition changed, sync to run_order
for cid in changed:
    if cid in ci and cid in ri:
        ri[cid]["preconditions"] = ci[cid]["pre"]

# ── 5. Write JSON ─────────────────────────────────────────────────────────────
COMPACT_PATH.write_text(
    json.dumps(compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
FULL_PATH.write_text(
    json.dumps(full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ── 6. Re-embed + copy ────────────────────────────────────────────────────────
html = HTML_PATH.read_text(encoding="utf-8-sig")
embedded = (json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
            .replace("<", "\\u003c"))
html, count = re.subn(
    r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)",
    lambda m: m[1] + embedded + m[2], html, count=1, flags=re.S)
assert count == 1
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)

print(f"Changed {len(changed)} cases:")
for cid in changed:
    print(f"  {cid}")
