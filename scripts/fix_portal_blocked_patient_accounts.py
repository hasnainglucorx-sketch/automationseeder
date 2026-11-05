"""Replace workbook-dependent Patient blockers with reusable portal fixtures.

This is deliberately limited to the Patient/data portion of the 7 October 2026
blocked run. Role provisioning and requirement-gap cases are not rewritten.
"""
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "output" / "console-update" / "PRT-0702-cases.json"

IDS = """
PAT-AUTH-002 PAT-HOME-004 PAT-HOME-009 PAT-OGP-CALC-001 PAT-OGP-CALC-002
PAT-OGP-DATA-002 PAT-OGP-DATA-003 PAT-OGP-DATA-004 PAT-HISTORY-004 PAT-HISTORY-005
PAT-HISTORY-DATA-001 PAT-HISTORY-DATA-003 PAT-HISTORY-CAL-001 PAT-SHARE-007
PAT-REPORT-DATA-004 PAT-REPORT-DATA-005 PAT-REPORT-DATA-006 PAT-ERROR-001 PAT-ERROR-002
PAT-ERROR-003 PAT-ERROR-004 PAT-EDGE-004 PAT-EDGE-005 PAT-DATA-ERROR-001 PAT-CALC-001
PAT-CALC-002 PAT-CALC-004 PAT-CALC-005 PAT-CALC-006 PAT-CALC-007 PAT-TIR-001
PAT-TIR-002 PAT-UNIT-001 PAT-COMPARE-DATA-001 PAT-COMPARE-DATA-002
PAT-COMPARE-DATA-003 PAT-COMPARE-DATA-004 PAT-COMPARE-DATA-005 PAT-COMPARE-DATA-008
PAT-EXPORT-DATA-001 PAT-EXPORT-DATA-002 PAT-TIMEZONE-001 PAT-EVENT-DATA-001
PAT-OVERVIEW-DATA-002 PAT-OVERVIEW-DATA-003 PAT-OVERVIEW-DATA-004
PAT-OVERVIEW-DATA-005 PAT-OVERVIEW-DATA-006 PAT-OVERVIEW-DATA-011
PAT-OVERVIEW-DATA-012 PAT-OVERVIEW-DATA-013 PAT-OVERVIEW-DATA-014
PAT-OVERVIEW-DATA-015 PAT-OVERVIEW-DATA-016 PAT-OVERVIEW-DATA-017
PAT-OVERVIEW-DATA-018 PAT-OVERVIEW-DATA-019 PAT-OVERVIEW-DATA-020
PAT-OVERLAY-DATA-001 PAT-DIDO-005 PAT-DIDO-016 PAT-DIDO-020 PAT-PERF-001 PAT-PERF-003
SUP-SEC-004
""".split()

REPLACEMENTS = {
    "QA_WEB_STATS_01": "QA-PORTAL-HISTORY-01",
    "QA_WEB_EDGE_01": "QA-PORTAL-SPARSE-01",
    "QA_WEB_QUALITY_01": "QA-PORTAL-QUALITY-01",
    "QA_WEB_MMOL_01": "QA-PORTAL-MMOL-01",
    "QA_WEB_SECOND_01": "QA-PORTAL-SECONDARY-01",
    "QA_WEB_FOL_01": "QA-PORTAL-SECONDARY-01",
    "QA_WEB_HCP_01": "QA-PORTAL-HCP-01",
    "TD-GLU-BASE-001.2": "the generated QA-PORTAL-HISTORY-01 fixture summary",
    "TD-GLU-BASE-001.3": "the generated QA-PORTAL-HISTORY-01 fixture summary",
    "TD-TIR-001.2": "the stored 70–180 mg/dL thresholds",
    "TD-TIR-001.3": "the generated QA-PORTAL-HISTORY-01 range summary",
    "TD-TIR-001.4": "the approved Portal rounding rule",
    "TD-CAL-001.2": "the controlled D0-3 09:30 calibration (156 mg/dL)",
    "TD-REPORT-PASS-001.2": "the last 7 days",
    "TD-EVT-001.2 to TD-EVT-001.5": "the four controlled events in the generated fixture summary",
    "TD-DEVICE-001.4": "the generated fixture session list",
    "TD-FAULT-001.1": "the case-specific Requestly rule",
    "TD-FAULT-001.2": "the case-specific Requestly rule",
    "TD-KC-SESSION-001.1": "the approved Keycloak idle timeout",
    "TD-TIR-001.5": "the generated range metrics, which list both supported calculation variants",
    "TD-TIR-001.6": "the approved sparse-data rule",
    "TD-FAULT-READING-001.1": "the case-specific modified QueryReadings response",
    "TD-GLU-BASE-001.5": "the controlled empty-today state",
    "TD-GLU-BASE-001.4": "the controlled high/low placement markers in the generated fixture summary",
    "TD-EVT-001.2": "the controlled carbohydrate event",
    "TD-EVT-001.3": "the controlled insulin event",
    "TD-EVT-001.4": "the controlled activity event",
    "TD-EVT-001.5": "the controlled sickness note",
    "TD-RUN-001.1 to TD-RUN-001.3": "the approved Portal service-domain list",
    "TD-PERF-001.1": "the stated Chrome and office-network measurement conditions",
    "TD-AUDIT-SOURCE-001.1": "the approved QA audit-log source",
    "TD-GLU-NONE-SINGLE-001.4": "the verified one-reading QA-PORTAL-SPARSE-01 fixture",
}


def clean(text: str) -> str:
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    text = re.sub(r"\s*\(email and password in TD-ACC-PAT-001\.2\)", "", text)
    text = re.sub(r"\s*\(TD-ACC-PAT-001\.2\)", "", text)
    text = text.replace("Open tab QA-PORTAL-HISTORY-01 in the workbook.",
                        "The generated QA-PORTAL-HISTORY-01 verification values are available in Test Assets > Portal Fixtures.")
    text = text.replace("Open tab QA-PORTAL-HISTORY-01, section C in the workbook .",
                        "The generated QA-PORTAL-HISTORY-01 range values are available in Test Assets > Portal Fixtures.")
    text = text.replace("Open tab QA-PORTAL-HISTORY-01, section C (hourly OGP values, the generated QA-PORTAL-HISTORY-01 fixture summary).",
                        "The generated hourly OGP values are available in Test Assets > Portal Fixtures.")
    text = text.replace("Open tab QA-PORTAL-HISTORY-01, section C (hourly OGP values, the generated QA-PORTAL-HISTORY-01 fixture summary)",
                        "The generated hourly OGP values are available in Test Assets > Portal Fixtures")
    text = re.sub(r"tab QA-PORTAL-HISTORY-01(?:, section C)?", "the generated QA-PORTAL-HISTORY-01 fixture summary", text)
    text = re.sub(r"tab QA-PORTAL-QUALITY-01", "the approved QA-PORTAL-QUALITY-01 fixture summary", text)
    text = text.replace("in the workbook", "in Test Assets > Portal Fixtures")
    text = text.replace("on the workbook", "in Test Assets > Portal Fixtures")
    text = text.replace("summary, it matches", "summary it matches")
    text = text.replace(
        "(the tab gives one value for each common formula, the generated range metrics, which list both supported calculation variants)",
        "(both supported calculation variants are listed)"
    )
    text = text.replace(
        "The tab gives one value for each common formula (the generated range metrics, which list both supported calculation variants).",
        "Both supported calculation variants are listed."
    )
    text = text.replace("range summary and section C", "range summary")
    text = text.replace("fixture summary .", "fixture summary.")
    text = text.replace(
        "The Requestly extension is installed in Chrome. You switch the failure on yourself and off ; this checks how the Portal handles errors and does not change the server.",
        "The Requestly extension is installed in Chrome and no failure rule is enabled."
    )
    text = text.replace("Open the generated QA-PORTAL-HISTORY-01 fixture summary",
                        "The generated QA-PORTAL-HISTORY-01 fixture summary is available")
    text = text.replace("Use a browser with Developer Tools.",
                        "A browser with Developer Tools is available.")
    text = re.sub(r"Sign in as the Patient QA-PORTAL-HISTORY-01\s*\.",
                  "The Patient QA-PORTAL-HISTORY-01 is signed in.", text)
    text = re.sub(r"Sign in as the Patient QA-PORTAL-SPARSE-01\s*\.",
                  "The Patient QA-PORTAL-SPARSE-01 is signed in.", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Restore numbered-list line breaks after whitespace normalization.
    text = re.sub(r" (?=\d+\. )", "\n", text)
    return text


def main() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    by_id = {case["id"]: case for case in cases}
    missing = sorted(set(IDS) - set(by_id))
    if missing:
        raise RuntimeError(f"Missing intended cases: {missing}")
    before_ids = [case["id"] for case in cases]
    for case_id in IDS:
        case = by_id[case_id]
        for field in ("pre", "proc", "exp", "ev"):
            case[field] = clean(case[field])
    by_id["PAT-UNIT-001"]["pre"] = (
        "No sign-in is needed. These controlled mg/dL values are available: "
        "45, 50, 63, 70, 100, 120, 140, 154, 156, 180, 200, 240 and 300."
    )
    by_id["PAT-SHARE-007"]["pre"] = (
        "QA-PORTAL-HISTORY-01 is signed in and Share Management > Patient Management is open. "
        "QA-PORTAL-SECONDARY-01 is already listed as a follower. Both alias emails are available securely."
    )
    by_id["PAT-CALC-001"]["pre"] = (
        "QA-PORTAL-HISTORY-01 is signed in. Its generated fixture summary is available, "
        "including the D0-6 to D0-1 period."
    )
    by_id["PAT-COMPARE-DATA-001"]["pre"] = (
        "QA-PORTAL-HISTORY-01 is signed in. Its generated fixture summary contains expected values "
        "for D0-6 to D0-1 and D0-14 to D0-8."
    )
    by_id["PAT-AUTH-002"]["pre"] = (
        "QA-PORTAL-HISTORY-01 is signed in and Overview is open. Browser Developer Tools are available."
    )
    by_id["PAT-UNIT-001"]["proc"] = (
        "1. Divide each controlled mg/dL value by 18.0182 and round to one decimal place. "
        "Compare the results with 2.5, 2.8, 3.5, 3.9, 5.5, 6.7, 7.8, 8.5, 8.7, 10.0, 11.1, 13.3 and 16.6 mmol/L respectively."
    )
    by_id["PAT-TIMEZONE-001"]["pre"] = (
        "The computer time zone is UTC. The Patient QA-PORTAL-TIMEZONE-01 is signed in. "
        "The account contains fixed winter, summer and UK daylight-saving-boundary readings recorded in its generated fixture summary."
    )
    by_id["PAT-TIMEZONE-001"]["proc"] = (
        "1. In UTC, open History for each controlled timestamp and record the displayed date and time.\n"
        "2. Change the computer time zone to Europe/London, reopen the winter reading and record its displayed date and time.\n"
        "3. Reopen the summer reading and record its displayed date and time.\n"
        "4. Inspect the ordered readings across the UK spring and autumn clock changes.\n"
        "5. Restore the computer time zone to Asia/Karachi."
    )
    by_id["PAT-TIMEZONE-001"]["exp"] = (
        "1. In UTC, every displayed timestamp matches the UTC instant in the generated fixture summary.\n"
        "2. The winter reading uses GMT and keeps its source order and date boundary.\n"
        "3. The summer reading uses BST, one hour ahead of UTC, and keeps its source order and date boundary.\n"
        "4. The Portal does not duplicate, omit or reorder a reading because the clock changes.\n"
        "5. The computer returns to Asia/Karachi."
    )
    by_id["PAT-PERF-001"]["pre"] = (
        "Chrome is on the latest approved version and connected to the normal office network. "
        "Developer Tools > Network is open. QA-PORTAL-HISTORY-01 is available."
    )
    by_id["PAT-PERF-003"]["pre"] = (
        "Chrome is on the latest approved version and connected to the normal office network. "
        "Developer Tools > Network is open. QA-PORTAL-HISTORY-01 is signed in and its verified 90-day fixture is current."
    )
    by_id["SUP-SEC-004"]["pre"] = (
        "QA-PORTAL-HISTORY-01 and QA-PORTAL-HCP-01 are ready in separate private windows. "
        "The approved QA audit-log source is available."
    )
    if before_ids != [case["id"] for case in cases]:
        raise RuntimeError("Case order or IDs changed")
    CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {len(IDS)} blocked Patient/data cases")


if __name__ == "__main__":
    main()
