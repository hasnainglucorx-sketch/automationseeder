"""Rewrite the first Patient Portal blocked-report cases against current fixtures."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "output" / "console-update" / "PRT-0702-cases.json"


UPDATES = {
    "PAT-AUTH-002": {
        "t": "PAT-AUTH-002 — Clearing Portal data keeps the user signed in until the Keycloak session is cleared",
        "pre": (
            "QA-PORTAL-HISTORY-01 is signed in and Overview is open in a supported desktop "
            "browser. The Overview protected-page address is available. The browser provides "
            "site-data controls that can remove data for one domain without clearing all browser data."
        ),
        "proc": (
            "1. Confirm that Overview belongs to QA-PORTAL-HISTORY-01, then copy the complete "
            "Overview address from the browser address bar.\n"
            "2. In the browser's site-data or developer tools, select frontend.grxdiscovery.link. "
            "Remove only that Portal domain's local storage, session storage, IndexedDB and cache. "
            "Do not remove data or cookies for the Keycloak sign-in domain and do not use a "
            "clear-all-browser-data action.\n"
            "3. Paste the copied Overview address into the address bar and open it.\n"
            "4. In the browser's site-data controls, remove the cookies and site data for "
            "keycloak.dev.platform.glucorx.co.uk. Then remove the Portal-domain storage listed "
            "in step 2 again.\n"
            "5. Paste the same protected Overview address into the address bar and open it again."
        ),
        "exp": (
            "1. The copied address is a protected QA-PORTAL-HISTORY-01 Overview address.\n"
            "2. The Portal-domain browser data is removed while the separate Keycloak session "
            "remains present.\n"
            "3. Keycloak recognises its existing session and returns to Overview without asking for "
            "the email or password. Overview still belongs to QA-PORTAL-HISTORY-01 and no other "
            "user's information appears.\n"
            "4. Both the Keycloak session data and the newly restored Portal-domain data are removed.\n"
            "5. The Keycloak sign-in page is shown. Overview and all other protected Patient Portal "
            "content remain hidden until a user signs in again."
        ),
        "ev": (
            "Portal-domain data selection; reopened Overview without credential entry; Keycloak-domain "
            "data selection; final Keycloak sign-in page; execution record."
        ),
    },
    "PAT-HOME-004": {
        "t": "PAT-HOME-004 — Overview handles a glucose-statistics request failure",
        "pre": (
            "QA-PORTAL-HISTORY-01 is signed in. Overview is open with 7 days selected. "
            "Chrome Developer Tools and Requestly are available. No Requestly rule is enabled."
        ),
        "proc": (
            "1. Record the Last, Average, Lowest and Highest values shown on Overview.\n"
            "2. In Developer Tools > Network, refresh Overview and identify the successful "
            "GetGlucoseStatistics request. Copy its request URL.\n"
            "3. In Requestly, create and enable an HTTP-status rule for that exact URL with "
            "status 500. Refresh Overview and observe the four widgets and the rest of the page.\n"
            "4. Disable the rule and refresh Overview again."
        ),
        "exp": (
            "1. The four widgets show values for the verified 7-day fixture.\n"
            "2. The successful request and its exact URL are visible in the Network list.\n"
            "3. The Portal shows an understandable unavailable/error state for the affected "
            "statistics, does not show fabricated values or raw server details, and remains usable.\n"
            "4. The four normal values return and match step 1."
        ),
        "ev": (
            "Normal widget values; Network request URL; Requestly 500 rule; failure state; "
            "recovered values; execution record."
        ),
    },
    "PAT-HOME-009": {
        "t": "PAT-HOME-009 — Patient Profile editable and read-only fields",
        "pre": (
            "QA-PORTAL-HISTORY-01 is signed in and Overview is open. Its expected profile "
            "values are available in Test Assets > Portal Fixtures."
        ),
        "proc": (
            "1. Open Profile and compare the displayed Patient values with "
            "QA-PORTAL-HISTORY-01 in Test Assets.\n"
            "2. Select Edit Profile. Record every enabled field and every read-only field.\n"
            "3. Change one enabled field that is not given name, family name or date of birth "
            "to a normal valid value. Save, reopen Profile and check the saved value.\n"
            "4. Restore the original value, save and reopen Profile."
        ),
        "exp": (
            "1. The displayed profile belongs to QA-PORTAL-HISTORY-01 and matches the Test Assets values.\n"
            "2. The execution record clearly identifies which fields are editable and read-only.\n"
            "3. The Portal accepts the supported change and shows the same value after Profile is reopened.\n"
            "4. The original value is restored and remains after Profile is reopened."
        ),
        "ev": "Profile values; edit state; saved value; restored value; execution record.",
    },
    "PAT-OGP-CALC-001": {
        "t": "PAT-OGP-CALC-001 — Seven-day OGP median values match the fixture",
        "pre": (
            "QA-PORTAL-HISTORY-01 is signed in. The 7-day hourly OGP table is available in "
            "Test Assets > Portal Fixtures."
        ),
        "proc": (
            "1. Open OGP and select 7 days. At 00:00, 03:00, 10:00, 15:00 and 23:00, "
            "read the median value from the chart or its accessible data table and compare it "
            "with P50 in the 7-day Test Assets table."
        ),
        "exp": (
            "1. Each checked median matches the corresponding P50 value in Test Assets, "
            "allowing only the rounding shown by the Portal."
        ),
        "ev": "Selected 7-day OGP; five displayed median values; Test Assets comparison; execution record.",
    },
    "PAT-OGP-CALC-002": {
        "t": "PAT-OGP-CALC-002 — Seven-day OGP percentile lines and bands match the fixture",
        "pre": (
            "QA-PORTAL-HISTORY-01 is signed in. The 7-day hourly OGP table is available in "
            "Test Assets > Portal Fixtures."
        ),
        "proc": (
            "1. Open OGP, select 7 days and identify the median line, inner band and outer band.\n"
            "2. At 00:00, 03:00, 10:00, 15:00 and 23:00, compare the chart or accessible "
            "table values with P10, P25, P50, P75 and P90 in Test Assets."
        ),
        "exp": (
            "1. The chart presents P50 as the median line, P25–P75 as the inner band and "
            "P10–P90 as the outer band.\n"
            "2. Every checked percentile matches Test Assets, allowing only displayed rounding."
        ),
        "ev": "OGP legend/bands; five hourly percentile comparisons; execution record.",
    },
    "PAT-OGP-DATA-002": {
        "t": "PAT-OGP-DATA-002 — Seven-day OGP contains the expected 24 hourly buckets",
        "pre": (
            "QA-PORTAL-HISTORY-01 is signed in. The 7-day hourly OGP table is available in "
            "Test Assets > Portal Fixtures."
        ),
        "proc": (
            "1. Open OGP, select 7 days and compare every local-hour bucket from 00:00 through "
            "23:00 with the 7-day Test Assets table."
        ),
        "exp": (
            "1. All 24 local-hour buckets are present. Each bucket's reading count and "
            "P10/P25/P50/P75/P90 values match Test Assets, allowing only displayed rounding."
        ),
        "ev": "Complete 24-hour OGP chart or accessible table; Test Assets comparison; execution record.",
    },
    "PAT-OGP-DATA-003": {
        "t": "PAT-OGP-DATA-003 — OGP does not present one reading as a reliable band",
        "pre": (
            "QA-PORTAL-SPARSE-01 is signed in. Test Assets shows its only reading at D0-3 "
            "12:00 with a value of 154 mg/dL."
        ),
        "proc": "1. Open OGP, select 7 days and inspect the 12:00 bucket and the sufficiency message.",
        "exp": (
            "1. The single reading is not presented as a reliable percentile band. The page "
            "shows an insufficient-data or equivalent clear state and remains usable."
        ),
        "ev": "Sparse fixture row in Test Assets; OGP 12:00 state; sufficiency message; execution record.",
    },
    "PAT-OGP-DATA-004": {
        "t": "PAT-OGP-DATA-004 — Ninety-day OGP buckets and bands match the fixture",
        "pre": (
            "QA-PORTAL-HISTORY-01 is signed in. The 90-day hourly OGP table is available in "
            "Test Assets > Portal Fixtures."
        ),
        "proc": (
            "1. Open OGP, select 90 days and compare every local-hour bucket from 00:00 "
            "through 23:00 with the 90-day Test Assets table."
        ),
        "exp": (
            "1. All 24 local-hour buckets are present. Each bucket's reading count and "
            "P10/P25/P50/P75/P90 values match Test Assets, allowing only displayed rounding."
        ),
        "ev": "Complete 90-day OGP chart or accessible table; Test Assets comparison; execution record.",
    },
    "PAT-HISTORY-004": {
        "t": "PAT-HISTORY-004 — History preset and custom date ranges",
        "pre": (
            "QA-PORTAL-HISTORY-01 is signed in and History is open. D0 is the fixture anchor "
            "shown in Test Assets. The fixture has no readings on D0, D0-7, D0-15, D0-30 or D0-90."
        ),
        "proc": (
            "1. Select 24 hours and record the first and last displayed reading.\n"
            "2. Select 7 days and record the first and last displayed reading.\n"
            "3. Select 15 days and confirm that the D0-10 03:00 high marker and D0-12 15:00 low marker are included.\n"
            "4. Select 30 days and confirm that both markers are included.\n"
            "5. Select 90 days and confirm that both markers are included.\n"
            "6. Select a custom range containing D0-3 only and inspect its readings and calibration."
        ),
        "exp": (
            "1. Only readings within the last 24 hours are shown; no D0 readings are fabricated.\n"
            "2. Only D0-6 through D0-1 readings are shown; no D0-7 reading is present.\n"
            "3. Only the 15-day range is shown and both controlled markers appear at their recorded times.\n"
            "4. Only the 30-day range is shown and both markers remain present.\n"
            "5. Only the 90-day range is shown and both markers remain present.\n"
            "6. Only D0-3 data is shown, including the 09:30 calibration of 156 mg/dL."
        ),
        "ev": "Each selected range; boundary readings; controlled markers; D0-3 calibration; execution record.",
    },
    "PAT-HISTORY-005": {
        "t": "PAT-HISTORY-005 — History shows the selected range without paging or sorting",
        "pre": "QA-PORTAL-HISTORY-01 is signed in and History is open.",
        "proc": (
            "1. Select 90 days and inspect the controls above, below and beside the History data.\n"
            "2. Scroll from the first available History data to the last available data for the selected range."
        ),
        "exp": (
            "1. History does not show page-number, next-page, previous-page or sort controls.\n"
            "2. The selected-range data remains available through the screen's implemented scrolling/view, "
            "without requiring an undocumented paging or sorting action."
        ),
        "ev": "History controls and beginning/end of selected-range data; execution record.",
    },
    "PAT-HISTORY-DATA-001": {
        "t": "PAT-HISTORY-DATA-001 — History values and calibration match the fixture",
        "pre": (
            "QA-PORTAL-HISTORY-01 is signed in. D0 and the controlled History values are "
            "available in Test Assets > Portal Fixtures."
        ),
        "proc": (
            "1. Open History and select a custom range containing D0-3 only.\n"
            "2. Check the readings at 00:00, 00:03, 00:09, 00:51 and 00:59.\n"
            "3. Find the calibration at 09:30."
        ),
        "exp": (
            "1. History shows D0-3 data only.\n"
            "2. The readings are 50, 63, 156, 240 and 240 mg/dL respectively.\n"
            "3. The calibration is shown at 09:30 with a reference value of 156 mg/dL."
        ),
        "ev": "D0-3 range; five controlled readings; calibration time/value; execution record.",
    },
    "PAT-HISTORY-DATA-003": {
        "t": "PAT-HISTORY-DATA-003 — Daily History boundaries and min/max match the fixture",
        "pre": (
            "QA-PORTAL-HISTORY-01 is signed in. The expected daily History values for D0-6 "
            "through D0-1 are available in Test Assets > Portal Fixtures."
        ),
        "proc": (
            "1. Open History, select 7 days and compare each displayed day's first time, last "
            "time, minimum and maximum with the daily History table in Test Assets."
        ),
        "exp": (
            "1. D0-6 through D0-1 each start at 00:00, end at 23:59, have a minimum of "
            "50 mg/dL and a maximum of 240 mg/dL. No extra day is included."
        ),
        "ev": "Seven-day History daily values and Test Assets comparison; execution record.",
    },
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
    CASES.write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Rewrote {len(UPDATES)} blocked-report cases")


if __name__ == "__main__":
    main()
