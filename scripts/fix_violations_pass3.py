"""Pass 3: remove remaining action words from preconditions of the 13 still-failing cases."""
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

FIXTURE_BASE = (
    "Non-production QA only. QA-HISTORY-01 is the controlled historical account "
    "for this case; its password must not be recorded in the protocol. "
    "The account is configured for country PK, Asia/Karachi, mg/dL, "
    "Low 70 mg/dL and High 180 mg/dL. "
    "Its seeded history contains populated 24-hour, 3-day, 7-day, 15-day and "
    "90-day selections, readings on more than three dates, and values below 70, "
    "within 70–180 and above 180 mg/dL."
)

PRECONDITIONS = {
    "VP-APP-HOME-007": (
        FIXTURE_BASE + " The known plotted reference point is on 1 October 2026 "
        "at 07:22 PKT with API value 125.45 mg/dL."
    ),
    "VP-APP-HOME-008": (
        FIXTURE_BASE + " Both the 24 Hours and 7 Days selections are populated."
    ),
    "VP-APP-HOME-014": (
        "The approved real test kit supports a transmitter or CGM power-cycle "
        "during an active CGM session. QA-MAIN-01 is signed in with an active session."
    ),
    "VP-APP-REPORT-002": FIXTURE_BASE,
    "VP-APP-REPORT-005": (
        FIXTURE_BASE + " Internet connectivity can be disabled and restored using "
        "the normal phone controls."
    ),
    "VP-APP-REPORT-016": (
        FIXTURE_BASE + " Any clinical-selection logic lacking an approved "
        "requirement is observation only."
    ),
    "VP-APP-REPORT-WEEK-002": (
        FIXTURE_BASE + " The fixture contains readings on 27, 28 and 29 September 2026."
    ),
    "VP-APP-TAR-001": (
        "Non-production QA only. QA-HISTORY-01 is the controlled historical account "
        "for this case; its password must not be recorded in the protocol. "
        "Its seeded history contains populated 24-hour, 3-day, 7-day, 15-day and "
        "90-day selections; the 15-day and 90-day periods contain readings above "
        "the configured 180 mg/dL High threshold."
    ),
    "VP-APP-TAR-002": (
        "Non-production QA only. QA-HISTORY-01 is the controlled historical account "
        "for this case; its password must not be recorded in the protocol. "
        "The account is configured for mg/dL, Low 70 mg/dL and High 180 mg/dL. "
        "The 15 Days selection is populated with readings above 180 mg/dL. "
        "Expected seeded values: Above readings 750; Total 10020 − (minutes "
        "since midnight at execution time)."
    ),
    "VP-APP-TBR-001": (
        "Non-production QA only. QA-HISTORY-01 is the controlled historical account "
        "for this case; its password must not be recorded in the protocol. "
        "Its seeded history contains populated 24-hour, 3-day, 7-day, 15-day and "
        "90-day selections; the 15-day and 90-day periods contain readings below "
        "the configured 70 mg/dL Low threshold."
    ),
    "VP-APP-TBR-002": (
        "Non-production QA only. QA-HISTORY-01 is the controlled historical account "
        "for this case; its password must not be recorded in the protocol. "
        "The account is configured for mg/dL, Low 70 mg/dL and High 180 mg/dL. "
        "The 15 Days selection is populated with readings below 70 mg/dL. "
        "Expected seeded values: Below readings 1500; Total 10020 − (minutes "
        "since midnight at execution time)."
    ),
    "VP-APP-VAR-001": (
        "Non-production QA only. QA-HISTORY-01 is the controlled historical account "
        "for this case; its password must not be recorded in the protocol. "
        "Its seeded history contains populated 24-hour, 3-day, 7-day, 15-day and "
        "90-day selections with varied readings across all periods."
    ),
    "VP-APP-VAR-002": (
        "Non-production QA only. QA-HISTORY-01 is the controlled historical account "
        "for this case; its password must not be recorded in the protocol. "
        "The 15 Days selection is populated with varied readings."
    ),
}

for cid, pre in PRECONDITIONS.items():
    ci[cid]["pre"] = pre
    ri[cid]["preconditions"] = pre

COMPACT_PATH.write_text(json.dumps(compact, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
FULL_PATH.write_text(json.dumps(full, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

html = HTML_PATH.read_text(encoding="utf-8-sig")
embedded = json.dumps(compact, ensure_ascii=False, separators=(",",":")).replace("<","\\u003c")
html, count = re.subn(
    r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)",
    lambda m: m[1] + embedded + m[2], html, count=1, flags=re.S)
assert count == 1
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)
print("Pass 3 complete.")
