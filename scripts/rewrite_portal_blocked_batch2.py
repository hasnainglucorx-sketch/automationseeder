"""Rewrite calibration, report, failure-injection and calculation blockers."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "output" / "console-update" / "PRT-0702-cases.json"


def failure_case(page: str, rpc: str, status: str, affected: str, recovery: str) -> dict:
    return {
        "pre": (
            f"QA-PORTAL-HISTORY-01 is signed in and {page} is open in Chrome. "
            "Developer Tools and Requestly are available. No Requestly rule is enabled."
        ),
        "proc": (
            f"1. Record the normal {recovery} shown on {page}.\n"
            f"2. In Developer Tools > Network, refresh {page}, identify the successful {rpc} "
            "request and copy its exact URL.\n"
            f"3. In Requestly, create and enable a rule for that exact URL that returns {status}.\n"
            f"4. Refresh {page} and observe {affected} and the rest of the page.\n"
            f"5. Disable the Requestly rule and refresh {page}."
        ),
        "exp": (
            f"1. The normal {recovery} is present and is recorded as the recovery baseline.\n"
            f"2. The successful {rpc} request and its exact URL are visible in the Network list.\n"
            f"3. The rule is enabled only for the captured {rpc} URL.\n"
            f"4. {affected} shows an understandable unavailable/error state. The Portal remains "
            "usable and does not show fabricated data, raw server details, a crash or a blank page.\n"
            f"5. The normal {recovery} returns and matches step 1."
        ),
        "ev": f"Normal {page}; captured {rpc} URL; Requestly rule; failure state; recovered {page}; execution record.",
    }


UPDATES: dict[str, dict] = {
    "PAT-HISTORY-CAL-001": {
        "t": "PAT-HISTORY-CAL-001 — History calibration matches the controlled record",
        "pre": (
            "QA-PORTAL-HISTORY-01 is signed in. Test Assets records its calibration at "
            "D0-3 09:30 with a reference value of 156 mg/dL."
        ),
        "proc": (
            "1. Open History and select a custom range containing D0-3.\n"
            "2. Find the 09:30 calibration and compare its Patient, time and reference value with Test Assets.\n"
            "3. Select 24 hours, which does not contain D0-3."
        ),
        "exp": (
            "1. History shows D0-3 data.\n"
            "2. One calibration is shown for QA-PORTAL-HISTORY-01 at 09:30 with 156 mg/dL; it is not duplicated or attached to another Patient.\n"
            "3. The D0-3 calibration is not shown in the 24-hour period."
        ),
        "ev": "D0-3 History; calibration Patient/time/value; 24-hour History; execution record.",
    },
    "PAT-SHARE-007": {
        "t": "PAT-SHARE-007 — Own-email and duplicate follower invitations",
        "pre": (
            "QA-PORTAL-HISTORY-01 is signed in and Share Management > Followers is open. "
            "QA-PORTAL-SECONDARY-01 is already listed as a follower. Both emails are available in Test Assets."
        ),
        "proc": (
            "1. Select Invite, enter the email of QA-PORTAL-HISTORY-01 and select Send Invite. Record the response and whether a row is created.\n"
            "2. Repeat the invitation with the email of the already-listed QA-PORTAL-SECONDARY-01."
        ),
        "exp": (
            "1. The implemented own-email behavior is recorded for requirement review; no acceptance rule is invented for this requirement gap.\n"
            "2. A second follower row is not created for QA-PORTAL-SECONDARY-01, and the existing relationship remains usable."
        ),
        "ev": "Own-email response; follower list before/after duplicate invite; execution record.",
    },
    "PAT-REPORT-DATA-004": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Its 7-day range calculations are visible in Test Assets.",
        "proc": "1. Open Assessment Report, select 7 days and compare every displayed glucose-range percentage with the 7-day Test Assets row.",
        "exp": "1. Severe Low, Low, In Range, High and Urgent High values match Test Assets after displayed rounding, and the displayed categories total 100% within rounding.",
        "ev": "Seven-day report range percentages; Test Assets row; execution record.",
    },
    "PAT-REPORT-DATA-005": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Its 7-day GMI and ADAG estimated A1c values are visible in Test Assets.",
        "proc": "1. Open Assessment Report, select 7 days and record the label and value of the displayed estimated A1c metric.",
        "exp": "1. The displayed label identifies the formula being reported, and the value matches the corresponding 7-day GMI or ADAG A1c value in Test Assets after displayed rounding.",
        "ev": "Estimated A1c label/value; Test Assets comparison; execution record.",
    },
    "PAT-REPORT-DATA-006": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Its 7-day advanced calculations are visible in Test Assets.",
        "proc": "1. Open Assessment Report, select 7 days and compare displayed average, SD, CV, average deviation, usage and estimated A1c values with Test Assets.",
        "exp": "1. Every displayed metric matches the corresponding 7-day Test Assets value after displayed rounding; the estimated A1c label identifies whether GMI or ADAG is used.",
        "ev": "Seven-day advanced metrics and Test Assets comparison; execution record.",
    },
    "PAT-DATA-ERROR-001": {
        "t": "PAT-DATA-ERROR-001 — A reading missing its glucose value is not shown as valid",
        "pre": (
            "QA-PORTAL-HISTORY-01 is signed in and History is open in Chrome. Developer Tools "
            "and Requestly are available. No Requestly rule is enabled."
        ),
        "proc": (
            "1. In Developer Tools > Network, refresh History, identify the successful QueryReadings request and copy its exact URL.\n"
            "2. In Requestly, create a Modify Response Body rule for that URL. Keep the first reading's timestamp and index, but remove only its glucoseCentiMgDl value.\n"
            "3. Enable the rule and refresh History. Find the time of the modified first reading.\n"
            "4. Inspect the affected row/point and the rest of History.\n"
            "5. Disable the rule and refresh History."
        ),
        "exp": (
            "1. The successful QueryReadings URL is captured.\n"
            "2. The rule changes only the first reading's glucose value.\n"
            "3. The modified response is used for the refreshed page.\n"
            "4. The missing value is not presented as a plausible glucose reading; History remains usable and shows an unavailable/error/quality state for the invalid item.\n"
            "5. The valid glucose value returns."
        ),
        "ev": "Captured QueryReadings URL; response rule; affected History item; recovered item; execution record.",
    },
    "PAT-TIR-001": {
        "t": "PAT-TIR-001 — Independent seven-day glucose-range calculation",
        "pre": "The QA-PORTAL-HISTORY-01 7-day reading counts and thresholds are visible in Test Assets. No Portal sign-in is required.",
        "proc": (
            "1. Using Low 70 mg/dL and High 180 mg/dL, calculate the percentage below range, in range and above range from the Test Assets counts.\n"
            "2. Compare the calculated percentages with the 7-day Test Assets percentages."
        ),
        "exp": (
            "1. The calculation gives 15.0% below range, 70.0% in range and 15.0% above range; 70 and 180 mg/dL are included in range.\n"
            "2. The independent results match Test Assets and total 100.0%."
        ),
        "ev": "Calculation worksheet or execution-record calculation and Test Assets comparison.",
    },
    "PAT-TIR-002": {
        "t": "PAT-TIR-002 — Assessment Report uses the Patient's stored thresholds",
        "pre": (
            "QA-PORTAL-HISTORY-01 is signed in. Its stored Low threshold is 70 mg/dL and High "
            "threshold is 180 mg/dL. Its 7-day range values are visible in Test Assets."
        ),
        "proc": "1. Open Assessment Report, select 7 days and compare its glucose-range percentages and displayed thresholds with Test Assets.",
        "exp": "1. The report uses 70–180 mg/dL and shows 15.0% below range, 70.0% in range and 15.0% above range after displayed rounding.",
        "ev": "Displayed thresholds and seven-day range percentages; Test Assets comparison; execution record.",
    },
}


UPDATES["PAT-ERROR-001"] = failure_case("History", "ListEvents and ListSessions", "HTTP 500", "events and sessions", "readings, events and session data")
UPDATES["PAT-ERROR-002"] = failure_case("Share Management", "ListGrants and ListIncomingGrants", "HTTP 500", "sharing relationships", "incoming and outgoing sharing relationships")
UPDATES["PAT-ERROR-003"] = failure_case("Settings", "GetPatientSettings", "HTTP 500", "Patient settings", "Patient settings")
UPDATES["PAT-ERROR-004"] = failure_case("History", "ListCalibrations", "HTTP 500", "calibration data only", "readings, events and calibration data")
UPDATES["PAT-EDGE-004"] = failure_case("Overview", "QueryReadings", "HTTP 503", "the glucose graph and reading-dependent values", "glucose graph and reading-dependent values")
UPDATES["PAT-EDGE-005"] = failure_case("Overview", "ListPatients", "an aborted/cancelled request", "the Patient context", "signed-in Patient Overview")


for case_id, days in {
    "PAT-CALC-002": 7,
    "PAT-CALC-004": 7,
    "PAT-CALC-005": 15,
    "PAT-CALC-006": 30,
    "PAT-CALC-007": 90,
}.items():
    UPDATES[case_id] = {
        "pre": f"QA-PORTAL-HISTORY-01 is signed in. Its {days}-day range calculations are visible in Test Assets.",
        "proc": (
            f"1. Open Overview and select {days} days.\n"
            f"2. Compare every displayed summary value with the {days}-day Test Assets row."
        ),
        "exp": (
            f"1. Overview updates to the {days}-day period.\n"
            f"2. Latest, average, minimum, maximum, range percentages, usage, SD, CV, average deviation and estimated A1c values that are displayed match Test Assets after displayed rounding; the estimated A1c label identifies its formula."
        ),
        "ev": f"{days}-day Overview summaries; Test Assets row; execution record.",
    }

UPDATES["PAT-CALC-001"] = {
    "t": "PAT-CALC-001 — Selected date boundaries include both endpoint days",
    "pre": "QA-PORTAL-HISTORY-01 is signed in. Test Assets shows complete daily data for D0-6 through D0-1.",
    "proc": "1. Open History and select a custom range from D0-6 through D0-1.\n2. Inspect the first and last displayed timestamps.",
    "exp": "1. History applies the requested start and end dates.\n2. D0-6 00:00 and D0-1 23:59 are included; no reading outside the selected dates is shown.",
    "ev": "Custom range and first/last timestamps; execution record.",
}


def main() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    original_ids = [case["id"] for case in cases]
    by_id = {case["id"]: case for case in cases}
    missing = sorted(set(UPDATES) - set(by_id))
    if missing:
        raise RuntimeError(f"Missing intended cases: {missing}")
    for case_id, fields in UPDATES.items():
        by_id[case_id].update(fields)
    if original_ids != [case["id"] for case in cases]:
        raise RuntimeError("Case IDs or order changed")
    CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Rewrote {len(UPDATES)} blocked-report cases")


if __name__ == "__main__":
    main()
