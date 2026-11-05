"""
Pass 2: Fix 42 remaining violations in the 43 changed cases.
  1. Synchronize titles between compact and run_order for 7 cases.
  2. Remove action words from preconditions (existing "Sign in with..." text).
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

# ── 1. Title synchronisation ────────────────────────────────────────────────
TITLE_SYNC = {
    # (compact_authoritative, run_order_authoritative) → pick winner
    "VP-APP-HOME-014":          "Recover the same session after approved transmitter power-cycle and replay",
    "VP-APP-HOSTED-SIGNIN-012": "Restore server-held account data at the 90-day boundary after sign-in",
    "VP-APP-MEDIUM-002":        "No-Data / Disconnection initial medium-priority alert",
    "VP-APP-SCAN-010":          "Expired sensor barcode is blocked before session start",
    "VP-APP-SENSOR-ID-006":     "Manual Sensor ID path requires packaging expiry check before installation",
    "VP-APP-SICK-005":          "Enforce the approved 3–256 character sickness free-text length",
    "VP-APP-TX-PAIR-024":       "Backend recall response enforced during CGM start or upload",
}
for cid, title in TITLE_SYNC.items():
    ci[cid]["t"] = title
    ri[cid]["title"] = title

# ── 2. Precondition action-word fixes ───────────────────────────────────────
# Pattern A: QA-HISTORY-01 cases — remove "Sign in with ... QA-HISTORY-01; ..." phrase
HISTORY_IDS = [
    "VP-APP-HOME-007","VP-APP-HOME-008",
    "VP-APP-REPORT-002","VP-APP-REPORT-005","VP-APP-REPORT-016",
    "VP-APP-REPORT-WEEK-002",
    "VP-APP-TAR-001","VP-APP-TAR-002",
    "VP-APP-TBR-001","VP-APP-TBR-002",
    "VP-APP-VAR-001","VP-APP-VAR-002",
]
HISTORY_PRE = (
    "Non-production QA only. QA-HISTORY-01 is the controlled historical account "
    "for this case; its password must not be recorded in the protocol."
)
for cid in HISTORY_IDS:
    # Extract any fixture-specific tail after the generic sign-in line
    existing = ci[cid]["pre"]
    # Strip the generic "Non-production QA only. Sign in with... password..." clause
    # and replace with state-only equivalent
    # Anything after the first sentence (which ends with "protocol.") is fixture state
    idx = existing.find("protocol.")
    if idx >= 0:
        tail = existing[idx + len("protocol."):].strip()
    else:
        tail = ""
    new_pre = HISTORY_PRE + (" " + tail if tail else "")
    ci[cid]["pre"] = new_pre
    ri[cid]["preconditions"] = new_pre

# Pattern B: REPORT-DAY-004 — "Open Reports..." and "Record app rounding..." are actions
RD004_PRE = (
    "Req: DI-44 / DO-689. Non-production QA only. "
    "QA-HISTORY-01 is the controlled historical account for this case; "
    "its password must not be recorded in the protocol. "
    "Quality/Test Engineering approval for the backend-seeded fixture is on record. "
    "The 1 October 2026 fixture contains no readings from 07:23 through 08:07 PKT; "
    "the reading immediately before the gap is 125.45 mg/dL at 07:22 PKT and the "
    "first reading after is 128.16 mg/dL at 08:08 PKT."
)
ci["VP-APP-REPORT-DAY-004"]["pre"] = RD004_PRE
ri["VP-APP-REPORT-DAY-004"]["preconditions"] = RD004_PRE

# Pattern C: REPORT-DAY-005 — "Record the last valid reading..." is an action
RD005_PRE = (
    "A physical sensor or transmitter session is active and producing normal readings. "
    "The test-account alias, sensor/transmitter/session identifier, expected reading "
    "frequency and approved out-of-range interruption method are established before "
    "execution begins. "
    "Acceptance requires either: (A) at least five consecutive measurement indexes "
    "remain missing after reconnection and are not backfilled; or (B) the timestamps "
    "surrounding the gap are more than 30 minutes apart. "
    "No backend reading is created, deleted or changed for this case."
)
ci["VP-APP-REPORT-DAY-005"]["pre"] = RD005_PRE
ri["VP-APP-REPORT-DAY-005"]["preconditions"] = RD005_PRE

# Pattern D: QA-NODATA-01 cases — remove "Sign in with controlled no-data account..."
NODATA_IDS = ["VP-APP-TAR-004", "VP-APP-TBR-004", "VP-APP-VAR-004"]
NODATA_PRE = (
    "Non-production QA only. QA-NODATA-01 is the controlled no-data account "
    "for this case; its password must not be recorded in the protocol. "
    "The fixture is expected to have no readings in 24 Hours and populated "
    "varied readings in 3 Days."
)
for cid in NODATA_IDS:
    ci[cid]["pre"] = NODATA_PRE
    ri[cid]["preconditions"] = NODATA_PRE

# ── 3. Write ─────────────────────────────────────────────────────────────────
COMPACT_PATH.write_text(json.dumps(compact, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
FULL_PATH.write_text(json.dumps(full, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

# Re-embed compact into HTML
html = HTML_PATH.read_text(encoding="utf-8-sig")
embedded = json.dumps(compact, ensure_ascii=False, separators=(",",":")).replace("<","\\u003c")
html, count = re.subn(
    r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)",
    lambda m: m[1] + embedded + m[2], html, count=1, flags=re.S)
assert count == 1
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)

print("Pass 2 complete.")
print(f"Compact: {len(compact)}  Run-order: {len(full)}")
