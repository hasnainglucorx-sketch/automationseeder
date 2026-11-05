"""Rewrite remaining executable Patient/data blockers from the portal run."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "output" / "console-update" / "PRT-0702-cases.json"
UPDATES: dict[str, dict] = {}


UPDATES["PAT-UNIT-001"] = {
    "t": "PAT-UNIT-001 — Independent mg/dL-to-mmol/L conversions",
    "ev": "Recorded calculations for all 13 controlled values.",
}

for case_id, left, right in (
    ("PAT-COMPARE-DATA-001", 7, 15),
    ("PAT-COMPARE-DATA-002", 15, 30),
):
    UPDATES[case_id] = {
        "pre": f"QA-PORTAL-HISTORY-01 is signed in. Its {left}-day and {right}-day calculations are visible in Test Assets.",
        "proc": f"1. Open Compare. Set Range A to {left} days and Range B to {right} days.\n2. Compare every displayed value in each panel with its Test Assets row.",
        "exp": f"1. Compare keeps the {left}-day and {right}-day populations separate.\n2. Latest, average, minimum, maximum, range percentages, usage, SD, CV, average deviation and estimated A1c values that are displayed match the corresponding Test Assets row after displayed rounding.",
        "ev": f"Range A ({left} days), Range B ({right} days), Test Assets comparisons and execution record.",
    }

UPDATES.update({
    "PAT-COMPARE-DATA-003": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Its 7-day SD, CV and average-deviation values are visible in Test Assets.",
        "proc": "1. Open Compare, set one panel to 7 days and compare its SD, CV and average deviation with Test Assets.",
        "exp": "1. SD, CV and average deviation match the 7-day Test Assets values after displayed rounding.",
        "ev": "Seven-day Compare metrics and Test Assets comparison; execution record.",
    },
    "PAT-COMPARE-DATA-004": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Its 7-day range percentages are visible in Test Assets.",
        "proc": "1. Open Compare, set one panel to 7 days and compare every displayed glucose-range percentage with Test Assets.",
        "exp": "1. Severe Low, Low, In Range, High and Urgent High values match Test Assets after displayed rounding and total 100% within rounding.",
        "ev": "Seven-day Compare range percentages; Test Assets comparison; execution record.",
    },
    "PAT-COMPARE-DATA-005": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Its 90-day calculations are visible in Test Assets.",
        "proc": "1. Open Compare, set one panel to 90 days and compare every displayed statistic and glucose-range percentage with Test Assets.",
        "exp": "1. The panel uses the complete 90-day fixture. Every displayed value matches the 90-day Test Assets row after displayed rounding.",
        "ev": "Ninety-day Compare values; Test Assets comparison; execution record.",
    },
    "PAT-COMPARE-DATA-008": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Its 7-day daily History and controlled markers are visible in Test Assets.",
        "proc": "1. Open Compare, select 7 days and inspect Overlay mode.\n2. Switch to History mode and compare its daily values with Test Assets.",
        "exp": "1. Overlay contains only D0-6 through D0-1.\n2. History contains the same six days; each day starts at 00:00, ends at 23:59 and has the expected 50–240 mg/dL range.",
        "ev": "Seven-day Overlay and History modes; Test Assets comparison; execution record.",
    },
    "PAT-EXPORT-DATA-001": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Its 7-day calculations are visible in Test Assets. Browser downloads are allowed.",
        "proc": "1. Open Assessment Report and select 7 days.\n2. Download and open the report.\n3. Compare its date range and displayed values with Test Assets.",
        "exp": "1. The report shows the 7-day fixture period.\n2. The downloaded report opens successfully.\n3. Its date range and displayed glucose calculations match Test Assets after displayed rounding.",
        "ev": "Selected report period; downloaded report; Test Assets comparison; execution record.",
    },
    "PAT-EXPORT-DATA-002": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Its 7-day calculations and daily values are visible in Test Assets. Browser downloads are allowed.",
        "proc": "1. Open Assessment Report, select 7 days and download the PDF.\n2. Open the PDF and inspect the date range, unit, statistics, range percentages and chart.\n3. Compare representative chart points and every printed statistic with Test Assets.",
        "exp": "1. One PDF is downloaded for the selected period.\n2. The PDF identifies the 7-day period and mg/dL and contains the expected report sections.\n3. Printed statistics match Test Assets after displayed rounding, and representative chart points use D0-6 through D0-1 only.",
        "ev": "Downloaded PDF, date/unit/statistics/chart comparisons and execution record.",
    },
    "PAT-TIMEZONE-001": {
        "pre": "The computer time zone is UTC. QA-PORTAL-TIMEZONE-01 is signed in. Its UTC and Europe/London timestamps are visible in Test Assets.",
        "ev": "UTC, GMT, BST and clock-change History timestamps; restored Asia/Karachi setting; execution record.",
    },
    "PAT-EVENT-DATA-001": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Test Assets lists four events: sickness D0-3 07:00, activity D0-2 18:00, carbohydrate D0-1 08:00 and insulin D0-1 08:05.",
        "proc": "1. Open History and select 15 days.\n2. Find each of the four controlled events and inspect its time, type and details.\n3. Check their displayed order.",
        "exp": "1. History includes D0-14 through D0-1.\n2. Exactly one of each controlled event is shown at its Test Assets time: sickness note, 30-minute moderate walking activity, 40 g carbohydrate and 2.0-unit bolus insulin.\n3. The four events are ordered consistently by event time and are not duplicated.",
        "ev": "Four controlled History events with times/details/order; execution record.",
    },
})


metric_cases = {
    "PAT-OVERVIEW-DATA-002": "average_mg_dl",
    "PAT-OVERVIEW-DATA-003": "minimum_mg_dl",
    "PAT-OVERVIEW-DATA-004": "maximum_mg_dl",
}
for case_id, metric in metric_cases.items():
    label = metric.replace("_mg_dl", "").replace("_", " ").title()
    UPDATES[case_id] = {
        "pre": f"QA-PORTAL-HISTORY-01 is signed in. Test Assets shows the {label.lower()} for 7, 15, 30 and 90 days.",
        "proc": f"1. On Overview, select 7, 15, 30 and 90 days in turn. For each range, compare the displayed {label.lower()} with Test Assets.",
        "exp": f"1. The displayed {label.lower()} matches the corresponding Test Assets value for every range after displayed rounding.",
        "ev": f"Four Overview {label.lower()} values and Test Assets comparison; execution record.",
    }

for case_id, days in (("PAT-OVERVIEW-DATA-005", 30), ("PAT-OVERVIEW-DATA-006", 90)):
    UPDATES[case_id] = {
        "pre": f"QA-PORTAL-HISTORY-01 is signed in. Its {days}-day calculations are visible in Test Assets.",
        "proc": f"1. On Overview, select {days} days and compare every displayed summary value with Test Assets.",
        "exp": f"1. Every displayed {days}-day value uses the correct fixture population and matches Test Assets after displayed rounding.",
        "ev": f"{days}-day Overview values and Test Assets comparison; execution record.",
    }

for case_id, label, field in (
    ("PAT-OVERVIEW-DATA-011", "standard deviation", "SD"),
    ("PAT-OVERVIEW-DATA-012", "coefficient of variation", "CV"),
    ("PAT-OVERVIEW-DATA-013", "average deviation", "average deviation"),
    ("PAT-OVERVIEW-DATA-014", "estimated A1c", "GMI or ADAG A1c"),
):
    UPDATES[case_id] = {
        "pre": f"QA-PORTAL-HISTORY-01 is signed in. Its 7-day {label} value is visible in Test Assets.",
        "proc": f"1. On Overview, select 7 days and compare the displayed {label} with Test Assets.",
        "exp": f"1. The displayed {label} matches the Test Assets {field} value after displayed rounding; any formula choice is identified by its UI label.",
        "ev": f"Displayed {label}, label/formula and Test Assets comparison; execution record.",
    }

UPDATES.update({
    "PAT-OVERVIEW-DATA-015": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Its 7-day row in Test Assets shows 8,640 one-minute readings across D0-6 through D0-1.",
        "proc": "1. On Overview, select 7 days and inspect the reading count, date span and data-sufficiency wording.",
        "exp": "1. The page identifies the 7-day selection, reports 8,640 readings for the populated six days, and does not describe the empty D0 day as populated. Any cadence/completeness wording is recorded exactly.",
        "ev": "Seven-day count/span/sufficiency wording and Test Assets comparison; execution record.",
    },
    "PAT-OVERVIEW-DATA-016": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Its four controlled events and times are visible in Test Assets.",
        "proc": "1. On Overview, select 7 days and inspect Events & Notes.\n2. Compare every displayed event with Test Assets.",
        "exp": "1. Events & Notes is shown for the selected period.\n2. Sickness, activity, carbohydrate and insulin events match their controlled dates, times, types and values, with no unexplained missing or extra event.",
        "ev": "Events & Notes and four Test Assets comparisons; execution record.",
    },
    "PAT-OVERVIEW-DATA-017": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Its 7-day device-usage value is visible in Test Assets.",
        "proc": "1. On Overview, select 7 days and compare CGM device usage with Test Assets.",
        "exp": "1. Device usage matches 85.714% after displayed rounding.",
        "ev": "Displayed device usage and Test Assets comparison; execution record.",
    },
    "PAT-OVERVIEW-DATA-018": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Test Assets records a 300 mg/dL marker at D0-10 03:00–03:59 and a 45 mg/dL marker at D0-12 15:00–15:59.",
        "proc": "1. On Overview, select 15 days and open Daily Patterns.\n2. Find both controlled markers and inspect their day/date and local-hour placement.",
        "exp": "1. Daily Patterns uses the selected 15-day population.\n2. The 300 mg/dL marker is at D0-10 03:00–03:59 and the 45 mg/dL marker is at D0-12 15:00–15:59, with no day or hour shift.",
        "ev": "Fifteen-day Daily Patterns and both controlled marker positions; execution record.",
    },
    "PAT-OVERVIEW-DATA-019": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. D0-6 through D0-1 each contain the same controlled 7-day distribution: 15% below, 70% in and 15% above range.",
        "proc": "1. On Overview, select 7 days and inspect Time in Range by Day for D0-6 through D0-1.",
        "exp": "1. Each of the six populated days shows 15% below range, 70% in range and 15% above range after displayed rounding; no value is shown for D0 as if it were populated.",
        "ev": "Time in Range by Day for all six populated days; execution record.",
    },
    "PAT-OVERVIEW-DATA-020": {
        "pre": "No one is signed in. QA-PORTAL-SPARSE-01 and QA-PORTAL-HISTORY-01 are available in Test Assets.",
        "proc": "1. Sign in as QA-PORTAL-SPARSE-01, open Overview and select 7 days. Record the AGP sufficiency state.\n2. Log out, sign in as QA-PORTAL-HISTORY-01, open Overview and select 15 days. Record the AGP sufficiency state.",
        "exp": "1. One reading is not presented as a reliable AGP; a clear insufficient-data state is shown.\n2. The full minute-reading fixture produces the AGP/profile state without reusing the sparse account's message or data.",
        "ev": "Sparse and populated AGP sufficiency states; execution record.",
    },
    "PAT-OVERLAY-DATA-001": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Its empty days and controlled high marker are visible in Test Assets.",
        "proc": "1. Open Overlays and select 7 days.\n2. Select 15 days and inspect the added dates and controlled marker.",
        "exp": "1. Only D0-6 through D0-1 are included.\n2. D0-14 through D0-8 are added, D0-7 remains empty, the D0-10 03:00–03:59 300 mg/dL marker is included, and nothing older than D0-14 is shown.",
        "ev": "Seven-day and 15-day Overlay populations and controlled marker; execution record.",
    },
    "PAT-DIDO-005": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. History is open and Test Assets shows no readings on D0 but complete D0-1 readings.",
        "proc": "1. Select 24 hours and inspect the first/last timestamps and empty portion of the rolling period.",
        "exp": "1. History includes only readings newer than the rolling 24-hour boundary, does not fabricate D0 readings, and does not include older D0-1 readings outside the boundary.",
        "ev": "Rolling 24-hour boundary, first/last timestamps and empty current-day portion; execution record.",
    },
    "PAT-DIDO-020": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Chrome Developer Tools is available. Approved QA service domains are frontend.grxdiscovery.link, modapi.grxdiscovery.link and keycloak.dev.platform.glucorx.co.uk.",
        "proc": "1. In Developer Tools > Network, clear the request list. Open Overview, History, Assessment Report, Share Management, Profile and Export.\n2. Group requests by domain and inspect URLs, request payloads and response headers for Patient identity, clinical data and tokens.\n3. Trigger one safe required-field validation error and repeat the domain/payload inspection.",
        "exp": "1. The normal Patient journeys complete.\n2. Patient identity, clinical data, access tokens and refresh tokens are not placed in URLs/browser history or sent to a domain outside the approved QA list.\n3. The validation error does not send that protected information to an unapproved domain.",
        "ev": "Network domain list and inspected URLs/payloads for normal and validation-error flows; execution record.",
    },
    "PAT-PERF-001": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in. Chrome is on the approved version and connected to the normal office network. Developer Tools > Network is open with Preserve log off.",
        "proc": "1. Enable Disable cache. Perform 10 hard reloads of Overview and record the Load time shown in the Network panel for each run.\n2. Disable Disable cache. Perform 10 normal reloads and record each Load time.\n3. For each set, sort the 10 times from fastest to slowest and take the ninth value as p90.",
        "exp": "1. Ten first-load measurements are recorded under the same conditions.\n2. Ten cached-load measurements are recorded under the same conditions.\n3. First-load p90 is no more than 2.5 seconds and cached-load p90 is no more than 1.5 seconds.",
        "ev": "Chrome/browser/network conditions, 20 recorded Load times and both p90 calculations.",
    },
    "PAT-PERF-003": {
        "pre": "QA-PORTAL-HISTORY-01 is signed in and its 90-day fixture is current. Chrome is on the approved version and connected to the normal office network. Chrome Performance recording or a frame-accurate screen recording is available.",
        "proc": "1. Measure 10 renders after selecting 15 days, from selection until the report finishes drawing. Record every time.\n2. Measure 10 renders after selecting 90 days using the same start/end points.\n3. Sort each set from fastest to slowest and take the ninth value as p90.",
        "exp": "1. Ten comparable 15-day render times are recorded.\n2. Ten comparable 90-day render times are recorded.\n3. The 15-day p90 is no more than 3 seconds and the 90-day p90 is no more than 5 seconds.",
        "ev": "Measurement method, browser/network conditions, 20 render times and both p90 calculations.",
    },
})


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
