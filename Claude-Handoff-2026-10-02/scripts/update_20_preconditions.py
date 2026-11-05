"""Rewrite the 20 seeded-data test-case preconditions with executable fixtures."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"
CASES_PATH = OUT / "PRT-0701-cases.json"
RUN_PATH = OUT / "PRT-0701-run_order.json"
HTML_PATH = OUT / "PRT-0701-Console-source.html"
AUDIT_PATH = OUT / "precondition-update-20.json"

MAIN = "QA-HISTORY-01"
EMPTY = "QA-NODATA-01"
REGIONAL = "QA-REGION-US-01"

MAIN_BASE = (
    f"Non-production QA only. Sign in with the controlled historical account {MAIN}; do not place its password in the protocol. "
    "The account is verified and uses patient patients/7edf711f-273d-4a07-a598-2f25995a992f, country PK, Asia/Karachi, "
    "mg/dL, Low 70 mg/dL and High 180 mg/dL. Its seeded history contains populated 24-hour, 3-day, 7-day, 15-day and "
    "90-day selections, readings on more than three dates, and values below 70, within 70-180 and above 180 mg/dL. "
)

PRECONDITIONS = {
    "VP-APP-HOSTED-SIGNIN-012": (
        f"Req: DI-825 / DO-916. Non-production QA only. Use the verified account {MAIN}; do not record its password. "
        "Before execution, remove the app or clear its local data so the controlled server records are absent locally, then leave the user logged out. "
        "The server fixture was verified at 1 October 2026 13:48:37 PKT and contains: 2 July 2026 13:48:37 PKT = 98 mg/dL "
        "(91 days old), 3 July 2026 13:48:37 PKT = 100 mg/dL (exactly 90 days old), and 4 July 2026 13:48:37 PKT = "
        "102 mg/dL (89 days old). Expected destination: restored glucose history/Journal for this account. If execution occurs after that "
        "reference time, refresh the 89/90/91-day fixture immediately before execution and record the new timestamps and values."
    ),
    "VP-APP-HOSTED-SIGNIN-014": (
        f"Req: DI-285 / DO-673. Non-production QA only. The user is logged out. Use active, verified regional account {REGIONAL}; "
        "do not record its password. Controlled expected values are Country/region = United States (US), timezone = America/New_York, "
        "glucose unit = mg/dL, Low = 70 mg/dL, High = 180 mg/dL, and supported/fallback language = English. Onboarding must be complete "
        "before execution. Record these expected values, then verify them in User Profile, a glucose/threshold screen, and Settings > Language."
    ),
    "VP-APP-HOME-006": (
        MAIN_BASE +
        "Use the 24 Hours range containing 1 October 2026. The documented discontinuity has no readings from 07:23 through 08:07 PKT; "
        "the reading immediately before is 125.45 mg/dL at 07:22 PKT and the first reading after is 128.16 mg/dL at 08:08 PKT. "
        "Backend read-back verified zero readings within the gap. Quality/Test Engineering approval of this controlled synthetic gap is recorded."
    ),
    "VP-APP-HOME-007": (
        MAIN_BASE +
        "Use the known plotted point on 1 October 2026 at 07:22 PKT with API value 125.45 mg/dL; record the app's displayed whole-number "
        "rounding. Select a Home range that includes that point and enough surrounding history to pan and zoom."
    ),
    "VP-APP-HOME-008": (
        MAIN_BASE +
        "Use two populated Home ranges, 24 Hours and 7 Days. Record Time in Range, Daily Average, GMI and Severe Events before changing "
        "the range. The case verifies refresh and navigation; the numerical acceptance of GMI/Severe Events remains within their dedicated cases."
    ),
    "VP-APP-REPORT-001": (
        MAIN_BASE +
        "The account is synchronized on the test device and Reports is reachable from bottom navigation. Use the populated history to open "
        "and switch through every top-level report view presented by the build."
    ),
    "VP-APP-REPORT-002": (
        MAIN_BASE +
        "Reports is open. Use at least the populated 24 Hours, 7 Days and 15 Days selections and record the active selection before each change."
    ),
    "VP-APP-REPORT-005": (
        MAIN_BASE +
        "While online, open Reports and select the populated 7 Days period; wait for it to load and record one visible value/date so the local "
        "cache is established. Internet can then be disabled and restored using normal phone controls."
    ),
    "VP-APP-REPORT-016": (
        MAIN_BASE +
        "Open Reports on the populated 15 Days period, which contains varied readings across the configured Low/High bands. Record the six "
        "summary metrics before inspecting Key Insights and Focus Area. Any clinical-selection logic still lacking an approved requirement is observation only."
    ),
    "VP-APP-REPORT-DAY-004": (
        f"Req: DI-44 / DO-689. Non-production QA only. Use {MAIN}. Quality/Test Engineering approval for the backend-seeded fixture is recorded. "
        "Open Reports > Day for 1 October 2026 and select 24 Hours. There are no readings from 07:23 through 08:07 PKT; the API reading "
        "immediately before is 125.45 mg/dL at 07:22 PKT and the first reading after is 128.16 mg/dL at 08:08 PKT. Backend read-back "
        "verified zero readings inside the interval. Record app rounding and do not record the account password."
    ),
    "VP-APP-REPORT-WEEK-002": (
        MAIN_BASE +
        "Select a Week period containing readings on at least 27, 28 and 29 September 2026. Before opening Week, record one visible Day-reading "
        "timestamp from each of those dates so their chronological order can be compared."
    ),
    "VP-APP-TAR-001": (
        MAIN_BASE +
        "Open Time Above Range from Reports. Use the seeded 24 Hours, 3 Days, 7 Days, 15 Days and 90 Days selections; the 15/90-day history "
        "contains readings above the configured 180 mg/dL threshold."
    ),
    "VP-APP-TAR-002": (
        MAIN_BASE +
        "Open Time Above Range on the populated 15 Days period. The period contains readings above 180 mg/dL so Above readings, Above %, "
        "Peak, Total, Tracked and Recent Days can be checked. Record the displayed counts before calculating Above readings / Total readings x 100."
    ),
    "VP-APP-TAR-004": (
        f"Non-production QA only. Sign in with controlled no-data account {EMPTY}; do not record its password. Backend verification on "
        "1 October 2026 confirmed 217 varied readings in the 3 Days window, including 72 readings above 180 mg/dL, while 24 Hours contains "
        "no readings; the latest seeded reading is 30 September 2026 07:58 PKT. Open Time Above Range, first confirm populated 3 Days content, "
        "then select 24 Hours for the empty state."
    ),
    "VP-APP-TBR-001": (
        MAIN_BASE +
        "Open Time Below Range from Reports. Use the seeded 24 Hours, 3 Days, 7 Days, 15 Days and 90 Days selections; the 15/90-day history "
        "contains readings below the configured 70 mg/dL threshold."
    ),
    "VP-APP-TBR-002": (
        MAIN_BASE +
        "Open Time Below Range on the populated 15 Days period. The period contains readings below 70 mg/dL so Below readings, Below %, "
        "Lowest, Total, Tracked and Recent Days can be checked. Record the displayed counts before calculating Below readings / Total readings x 100."
    ),
    "VP-APP-TBR-004": (
        f"Non-production QA only. Sign in with controlled no-data account {EMPTY}; do not record its password. Backend verification on "
        "1 October 2026 confirmed 217 varied readings in the 3 Days window, including 37 readings below 70 mg/dL, while 24 Hours contains "
        "no readings; the latest seeded reading is 30 September 2026 07:58 PKT. Open Time Below Range, first confirm populated 3 Days content, "
        "then select 24 Hours for the empty state."
    ),
    "VP-APP-VAR-001": (
        MAIN_BASE +
        "Open Variability from Reports. Use the seeded 24 Hours, 3 Days, 7 Days, 15 Days and 90 Days selections. The controlled readings vary "
        "across the selected periods and are suitable for observing chart refresh."
    ),
    "VP-APP-VAR-002": (
        MAIN_BASE +
        "Open Variability on the populated 15 Days period. Record the displayed variability result, supporting statistics, Tracked range and "
        "Recent Days values before performing any independent check."
    ),
    "VP-APP-VAR-004": (
        f"Non-production QA only. Sign in with controlled no-data account {EMPTY}; do not record its password. Backend verification on "
        "1 October 2026 confirmed 217 varied readings in the 3 Days window, while 24 Hours contains no readings; the latest seeded reading is "
        "30 September 2026 07:58 PKT. Open Variability, first confirm populated 3 Days content, then select 24 Hours for the empty state."
    ),
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_records(records, field: str, require_all: bool = True):
    by_id = {record.get("id"): record for record in records}
    missing = sorted(set(PRECONDITIONS) - set(by_id))
    if missing and require_all:
        raise RuntimeError(f"Missing cases: {missing}")
    audit = []
    for case_id, new_text in PRECONDITIONS.items():
        if case_id not in by_id:
            continue
        record = by_id[case_id]
        audit.append({"id": case_id, "old": record.get(field, ""), "new": new_text})
        record[field] = new_text
    return audit


def add_missing_console_cases(cases, run_order):
    """Add target cases that existed in run_order but were absent from the console."""
    existing = {case["id"] for case in cases}
    run_by_id = {row["id"]: row for row in run_order}
    added = []
    new_cases = {}
    for case_id in PRECONDITIONS:
        if case_id in existing:
            continue
        row = run_by_id[case_id]
        new_cases[case_id] = {
            "r": 0,
            "sec": row["section"],
            "id": row["id"],
            "t": row["title"],
            "method": "Manual - Real Device",
            "req": row["requirement"],
            "pre": row["preconditions"],
            "proc": row["procedure"],
            "exp": row["expected"],
            "ev": row["evidence"],
        }
        added.append(case_id)

    def insert_after(anchor_id, records):
        index = next(i for i, case in enumerate(cases) if case["id"] == anchor_id) + 1
        cases[index:index] = records

    if "VP-APP-REPORT-016" in new_cases:
        insert_after("VP-APP-REPORT-015", [new_cases["VP-APP-REPORT-016"]])
    detail_cases = []
    for prefix in ("TAR", "TBR", "VAR"):
        for suffix in ("001", "002", "004"):
            case = new_cases.get(f"VP-APP-{prefix}-{suffix}")
            if case:
                detail_cases.append(case)
    if detail_cases:
        insert_after("VP-APP-TIR-007", detail_cases)

    for number, case in enumerate(cases, 1):
        case["r"] = number
    return added


def update_embedded_html(html: str, cases) -> str:
    embedded = json.dumps(cases, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    pattern = re.compile(r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)", re.DOTALL)
    updated, count = pattern.subn(lambda m: m.group(1) + embedded + m.group(2), html, count=1)
    if count != 1:
        raise RuntimeError("Could not replace the embedded case list")
    return ensure_account_reference_table(updated)


def ensure_account_reference_table(html: str) -> str:
    """Add one editable mapping table while keeping case text alias-only."""
    if 'id="account-reference-table"' not in html:
        table = '''    <div class="help-block" id="account-reference-table">
      <h4>Controlled test account references</h4>
      <div class="desc">Test cases use these stable references. Change an email here when an account is replaced; never put passwords in this table.</div>
      <div class="account-table-wrap"><table class="codes-table account-table">
        <thead><tr><th>Reference</th><th>Purpose</th><th>Current email</th></tr></thead>
        <tbody>
          <tr><td><code>QA-HISTORY-01</code></td><td>Historical, reports and restoration</td><td><input type="text" id="f-account-history" autocomplete="off"></td></tr>
          <tr><td><code>QA-NODATA-01</code></td><td>Empty 24 Hours / populated 3 Days</td><td><input type="text" id="f-account-nodata" autocomplete="off"></td></tr>
          <tr><td><code>QA-REGION-US-01</code></td><td>US regional configuration</td><td><input type="text" id="f-account-region" autocomplete="off"></td></tr>
        </tbody>
      </table></div>
    </div>
'''
        marker = '    <button class="primary-btn" id="setup-save">Save</button>'
        if marker not in html:
            raise RuntimeError("Could not locate setup Save button")
        html = html.replace(marker, table + marker, 1)

        css_marker = '  .codes-table td{padding:4px 6px; border-bottom:1px solid var(--border);}'
        css = css_marker + '''
  .account-table-wrap{overflow-x:auto; margin-bottom:12px;}
  .account-table{min-width:620px;}
  .account-table th{padding:5px 6px; text-align:left; color:var(--text-faint); font-size:11px; text-transform:uppercase; letter-spacing:.04em; border-bottom:1px solid var(--border);}
  .account-table td:nth-child(1){width:150px;}
  .account-table td:nth-child(2){width:210px;}
  .account-table input{min-width:230px; padding:7px 8px;}'''
        if css_marker not in html:
            raise RuntimeError("Could not locate table CSS")
        html = html.replace(css_marker, css, 1)

        meta_marker = '  var meta = {};'
        meta_code = '''  var meta = {};
  var ACCOUNT_DEFAULTS = {
    accountHistory: "rekod43112@maxtanie.com",
    accountNoData: "similoh324@caps7.com",
    accountRegion: "362qq@aristocrtic.live"
  };
  try { meta = JSON.parse(localStorage.getItem("prt0701-run-meta") || "{}"); } catch(e) { meta = {}; }'''
        if meta_marker not in html:
            raise RuntimeError("Could not locate meta declaration")
        html = html.replace(meta_marker, meta_code, 1)

        fill_marker = '    document.getElementById("f-mailbox").value = meta.mailbox || "";'
        fill_code = fill_marker + '''
    document.getElementById("f-account-history").value = meta.accountHistory || ACCOUNT_DEFAULTS.accountHistory;
    document.getElementById("f-account-nodata").value = meta.accountNoData || ACCOUNT_DEFAULTS.accountNoData;
    document.getElementById("f-account-region").value = meta.accountRegion || ACCOUNT_DEFAULTS.accountRegion;'''
        if fill_marker not in html:
            raise RuntimeError("Could not locate setup form population")
        html = html.replace(fill_marker, fill_code, 1)

        init_marker = '    wireStaticUI();\n    render();'
        init_code = '    wireStaticUI();\n    fillSetupForm();\n    render();'
        if init_marker not in html:
            raise RuntimeError("Could not locate console initialization")
        html = html.replace(init_marker, init_code, 1)

        save_marker = '        mailbox: document.getElementById("f-mailbox").value.trim()'
        save_code = '''        mailbox: document.getElementById("f-mailbox").value.trim(),
        accountHistory: document.getElementById("f-account-history").value.trim(),
        accountNoData: document.getElementById("f-account-nodata").value.trim(),
        accountRegion: document.getElementById("f-account-region").value.trim()'''
        if save_marker not in html:
            raise RuntimeError("Could not locate setup form save payload")
        html = html.replace(save_marker, save_code, 1)

        persist_marker = '      meta = m;\n      updateSubtitle();'
        persist_code = '''      meta = m;
      try { localStorage.setItem("prt0701-run-meta", JSON.stringify(m)); } catch(e) { console.warn(e); }
      updateSubtitle();'''
        if persist_marker not in html:
            raise RuntimeError("Could not locate setup persistence")
        html = html.replace(persist_marker, persist_code, 1)
    return html


def main() -> None:
    cases = load_json(CASES_PATH)
    run_order = load_json(RUN_PATH)
    update_records(run_order, "preconditions")
    added = add_missing_console_cases(cases, run_order)
    audit = update_records(cases, "pre")

    assert len(PRECONDITIONS) == 20
    assert len(cases) == 450
    assert len(run_order) == 479
    for case_id, expected in PRECONDITIONS.items():
        assert next(c for c in cases if c["id"] == case_id)["pre"] == expected
        assert next(c for c in run_order if c["id"] == case_id)["preconditions"] == expected

    write_json(CASES_PATH, cases)
    write_json(RUN_PATH, run_order)
    HTML_PATH.write_text(update_embedded_html(HTML_PATH.read_text(encoding="utf-8"), cases), encoding="utf-8")
    write_json(AUDIT_PATH, audit)
    print(json.dumps({"updated": len(PRECONDITIONS), "added_to_console": added,
                      "console_cases": len(cases), "audit": str(AUDIT_PATH)}, indent=2))


if __name__ == "__main__":
    main()
