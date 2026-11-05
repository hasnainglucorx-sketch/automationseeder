"""
Safe mechanical fixes — no content invention required.

PASS A: Actionable preconditions (29 compact + 5 run_order violations)
  Pattern 1: Remove "; record app build, OS, device and test-kit/transmitter identifiers"
             from the standard device-test-state preconditions.
  Pattern 2: Remove individual "Record X." sentences and recording clauses.
  Pattern 3: State-word replacement (action verb -> state phrasing).
  Special:   GUIDE-002 run_order pre synced to compact (compact is already state-only).

PASS B: Missing IDs (39 cases) — copy each case to the file that lacks it.
  run_order -> compact (36 IDs): map title/requirement/preconditions/procedure/expected/evidence
  compact -> run_order (3 IDs): SIGNIN-004A, SIGNIN-004B, WELCOME-003/004/005
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

changed_pre = []

# ═══════════════════════════════════════════════════════════════════════════════
# PASS A — Precondition cleanup
# ═══════════════════════════════════════════════════════════════════════════════

def set_pre(cid, new_pre, source="compact"):
    """Update precondition in compact and/or run_order without touching other fields."""
    if source in ("compact", "both") and cid in ci:
        ci[cid]["pre"] = new_pre
    if source in ("run_order", "both") and cid in ri:
        ri[cid]["preconditions"] = new_pre
    changed_pre.append(cid)


# ── Pattern 1: "; record app build, OS, device and test-kit/transmitter identifiers" ──
# These compact preconditions all follow the form:
#   "Approved real iOS/Android device; record app build, OS, device and
#    test-kit/transmitter identifiers. Reach X in a controlled test state[. ...]"
# Fix: strip the recording clause, keep the rest.
RECORD_DEVICE_IDS = [
    "VP-APP-BT-PERM-003", "VP-APP-BT-PERM-005", "VP-APP-BT-PERM-007",
    "VP-APP-BT-PERM-008", "VP-APP-BT-PERM-010",
    "VP-APP-HEALTH-002",  "VP-APP-HEALTH-008",
    "VP-APP-HIGH-002",    "VP-APP-HIGH-003",    "VP-APP-HIGH-004",
    "VP-APP-HIGH-005",    "VP-APP-HIGH-011",    "VP-APP-HIGH-012",
    "VP-APP-HIGH-013",    "VP-APP-HIGH-014",
    "VP-APP-LOW-002",     "VP-APP-LOW-003",     "VP-APP-LOW-004",
    "VP-APP-LOW-005",     "VP-APP-LOW-011",     "VP-APP-LOW-012",
    "VP-APP-LOW-013",     "VP-APP-LOW-014",
]
RECORD_CLAUSE = "; record app build, OS, device and test-kit/transmitter identifiers"

for cid in RECORD_DEVICE_IDS:
    assert cid in ci, f"Missing from compact: {cid}"
    new = ci[cid]["pre"].replace(RECORD_CLAUSE, "")
    set_pre(cid, new, source="compact")

# ── Pattern 2a: NOTIFY-002 — "; record app build and OS" ──
assert "VP-APP-NOTIFY-002" in ci
set_pre("VP-APP-NOTIFY-002",
        ci["VP-APP-NOTIFY-002"]["pre"].replace("; record app build and OS", ""),
        source="compact")

# ── Pattern 2b: Single "Record X." sentences at end of precondition ──
RECORD_SENTENCE = {
    "VP-APP-HOSTED-SIGNIN-007": " Record the account identifier in the execution record.",
    "VP-APP-MYCGM-005":         " Record Transmitter ID before the test.",
    "VP-APP-PERM-SUM-001":      " Record app build, OS and device.",
}
for cid, clause in RECORD_SENTENCE.items():
    assert cid in ci
    set_pre(cid, ci[cid]["pre"].replace(clause, ""), source="compact")

# ── Pattern 2c: MYCGM-008 — embedded recording clause ──
assert "VP-APP-MYCGM-008" in ci
set_pre("VP-APP-MYCGM-008",
        ci["VP-APP-MYCGM-008"]["pre"].replace(
            " Record account/session/transmitter and latest reading before update.", ""),
        source="compact")

# ── Pattern 2d: PROFILE-014 run_order — "(record its title)" inline ──
assert "VP-APP-PROFILE-014" in ri
set_pre("VP-APP-PROFILE-014",
        ri["VP-APP-PROFILE-014"]["preconditions"].replace("(record its title) ", ""),
        source="run_order")

# ── Pattern 3: CRITICAL-008 compact — "Put ... and record ..." -> state phrasing ──
# run_order is already state-only; compact has two action clauses.
assert "VP-APP-CRITICAL-008" in ci
_c008_old = ci["VP-APP-CRITICAL-008"]["pre"]
# Remove the action sentence and replace with state equivalent
_c008_new = _c008_old.replace(
    "Put the phone in DND/Focus using the platform setting approved for this test "
    "and record the state before triggering the alarm.",
    "The phone is in DND/Focus mode using the platform setting approved for this test."
)
set_pre("VP-APP-CRITICAL-008", _c008_new, source="compact")

# ── GUIDE-002 run_order: sync to compact's already-correct state-only pre ──
# compact: "User Guide guided tutorial flow is open."  (state-only, correct)
# run_order: "...Before you open the User Guide...Then open the User Guide." (actions)
assert "VP-APP-GUIDE-002" in ci
assert "VP-APP-GUIDE-002" in ri
set_pre("VP-APP-GUIDE-002", ci["VP-APP-GUIDE-002"]["pre"], source="run_order")

# ═══════════════════════════════════════════════════════════════════════════════
# PASS B — Missing ID reconciliation
# ═══════════════════════════════════════════════════════════════════════════════

# All run_order-only → add compact entry (field mapping)
RO_ONLY = [
    "VP-APP-CLINIC-001", "VP-APP-CLINIC-002", "VP-APP-CLINIC-003",
    "VP-APP-CLINIC-004", "VP-APP-CLINIC-005", "VP-APP-CLINIC-006",
    "VP-APP-DELETE-006",
    "VP-APP-GMI-001",    "VP-APP-GMI-002",    "VP-APP-GMI-003",
    "VP-APP-GMI-004",    "VP-APP-GMI-005",    "VP-APP-GMI-006",
    "VP-APP-HOME-RANGE-004", "VP-APP-HOME-RANGE-005",
    "VP-APP-HOSTED-REG-021",
    "VP-APP-JOURNAL-003",
    "VP-APP-REMINDER-002",
    "VP-APP-SEVERE-001", "VP-APP-SEVERE-002", "VP-APP-SEVERE-003",
    "VP-APP-SEVERE-004", "VP-APP-SEVERE-005", "VP-APP-SEVERE-006",
    "VP-APP-SHARE-009",
    "VP-APP-SIGNIN-004",
    "VP-APP-TAR-003",    "VP-APP-TBR-003",    "VP-APP-VAR-003",
    "VP-APP-TX-PAIR-030",
    "VP-APP-WELCOME-NAV-001", "VP-APP-WELCOME-NAV-002",
    "VP-APP-WELCOME-NAV-003", "VP-APP-WELCOME-NAV-004",
]

new_compact_entries = []
for cid in RO_ONLY:
    assert cid not in ci, f"Already in compact: {cid}"
    assert cid in ri,    f"Missing from run_order: {cid}"
    r = ri[cid]
    new_compact_entries.append({
        "id":  cid,
        "t":   r["title"],
        "req": r.get("requirement", ""),
        "pre": r["preconditions"],
        "proc": r["procedure"],
        "exp": r["expected"],
        "ev":  r["evidence"],
    })

compact.extend(new_compact_entries)
ci = {x["id"]: x for x in compact}   # rebuild index

# All compact-only → add run_order entry
# SIGNIN-004A / 004B: use SIGNIN-004 scheduling as reference
_signin_sched = {k: ri["VP-APP-SIGNIN-004"].get(k, "")
                 for k in ["day", "est", "phase", "recovery", "section"]}

# WELCOME-003/004/005: use WELCOME-NAV-001 scheduling as reference
_welcome_sched = {k: ri["VP-APP-WELCOME-NAV-001"].get(k, "")
                  for k in ["day", "est", "phase", "recovery", "section"]}

CO_ONLY = {
    "VP-APP-SIGNIN-004A": (_signin_sched, 496),
    "VP-APP-SIGNIN-004B": (_signin_sched, 497),
    "VP-APP-WELCOME-003": (_welcome_sched, 498),
    "VP-APP-WELCOME-004": (_welcome_sched, 499),
    "VP-APP-WELCOME-005": (_welcome_sched, 500),
}

new_full_entries = []
for cid, (sched, run_num) in CO_ONLY.items():
    assert cid not in ri, f"Already in run_order: {cid}"
    assert cid in ci,    f"Missing from compact: {cid}"
    c = ci[cid]
    entry = {
        "id":            cid,
        "title":         c["t"],
        "requirement":   c.get("req", ""),
        "preconditions": c["pre"],
        "procedure":     c["proc"],
        "expected":      c["exp"],
        "evidence":      c["ev"],
        "run":           run_num,
    }
    entry.update(sched)
    new_full_entries.append(entry)

full.extend(new_full_entries)
ri = {x["id"]: x for x in full}   # rebuild index

# ═══════════════════════════════════════════════════════════════════════════════
# Write + re-embed
# ═══════════════════════════════════════════════════════════════════════════════

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

print(f"Pass A — preconditions fixed: {len(changed_pre)} cases")
print(f"Pass B — run_order->compact: {len(new_compact_entries)} | compact->run_order: {len(new_full_entries)}")
print(f"Compact: {len(compact)}  Run-order: {len(full)}")
