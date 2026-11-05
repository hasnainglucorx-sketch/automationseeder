"""Rewrite HCP cases verified against the live QA portal on 8 October 2026."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "output" / "console-update" / "PRT-0702-cases.json"


UPDATES = {
    "HCP-LIST-001": {
        "t": "HCP-LIST-001 — Patient List shows only currently shared Patients",
        "pre": "QA-PORTAL-HCP-01 is signed in and Patient List is displayed. QA-PORTAL-HISTORY-01 and QA-PORTAL-SECONDARY-01 have active shares with this HCP. QA-PORTAL-SPARSE-01 is not shared with this HCP.",
        "proc": "1. Compare the Total value and Patient rows with the three fixture states.\n2. Read the Patient Name, Status, Registered and Action columns for both displayed rows.",
        "exp": "1. Total is 2. QA Portal History and QA Portal Secondary are listed; QA Portal Sparse is not listed.\n2. Both displayed Patients have Active status, a registration date and a View control.",
    },
    "HCP-LIST-002": {
        "t": "HCP-LIST-002 — Patient List shows the empty state when no Patients are shared",
        "pre": "QA-PORTAL-HCP-EMPTY-01 is signed in and has no current Patient shares. Patient List is displayed.",
        "proc": "1. Inspect the Total value and the Patient table.",
        "exp": "1. Total is 0. The table shows “No patients found” and “No shared patient records are available for this HCP.” No Patient row is shown.",
    },
    "HCP-LIST-004": {
        "t": "HCP-LIST-004 — Patient List handles a controlled request failure and recovers",
        "pre": "QA-PORTAL-HCP-01 is signed in and has active shares from QA-PORTAL-HISTORY-01 and QA-PORTAL-SECONDARY-01. Browser request interception is available for the Patient List request.",
        "proc": "1. Open Patient List and allow it to finish loading.\n2. Configure the Patient List request to return HTTP 500, then reload Patient List.\n3. Remove the interception and reload Patient List.",
        "exp": "1. A loading state is shown while the request is pending. When loading finishes, Total is 2 and both active Patients are displayed.\n2. The Portal shows that Patient List could not be loaded, remains usable and does not present a finished empty list or previously loaded rows as a successful refresh.\n3. Patient List recovers without another sign-in. Total returns to 2 and both active Patients are displayed once.",
        "ev": "Screenshots of the loading, controlled-failure and recovered states; browser Network record showing the controlled HTTP 500 and successful retry; execution record",
    },
    "HCP-LIST-008": {
        "t": "HCP-LIST-008 — Search Patient List by name and clear the search",
        "pre": "QA-PORTAL-HCP-01 is signed in. Patient List shows QA Portal History and QA Portal Secondary.",
        "proc": "1. Enter Secondary in Search patients.\n2. Replace the search with No Such Patient.\n3. Clear Search patients.",
        "exp": "1. Total changes to 1 and only QA Portal Secondary is shown.\n2. Total changes to 0. The table shows “No patients found” and “No patients match your search.”\n3. Total returns to 2 and both shared Patients are shown.",
    },
    "HCP-LIST-014": {
        "t": "HCP-LIST-014 — Open a shared Patient and return to Patient List",
        "pre": "QA-PORTAL-HCP-01 is signed in. Patient List shows QA Portal History and QA Portal Secondary.",
        "proc": "1. Select View for QA Portal History.\n2. Select Patient List above the Patient Glucose Data page.",
        "exp": "1. Patient Glucose Data opens with the banner “Viewing patient QA Portal History” and shows that Patient's identity and clinical sections.\n2. Patient List returns and still shows both active shared Patients.",
    },
    "HCP-DATA-004": {
        "t": "HCP-DATA-004 — Patient identity changes correctly when another shared Patient is opened",
        "pre": "QA-PORTAL-HCP-01 is signed in. Patient List shows QA Portal History and QA Portal Secondary, which contain different glucose data.",
        "proc": "1. Select View for QA Portal History and read the viewing banner and Patient identity.\n2. Return to Patient List and select View for QA Portal Secondary. Read the same identity areas.",
        "exp": "1. The page identifies QA Portal History in the viewing banner, Patient identity and glucose heading.\n2. The page identifies QA Portal Secondary in the same areas. The previous Patient's name and clinical data are not presented as the selected Patient.",
    },
    "HCP-DATA-006": {
        "t": "HCP-DATA-006 — Preset ranges update the shared Patient period",
        "pre": "QA-PORTAL-HCP-01 is signed in and Patient Glucose Data is open for QA Portal History.",
        "proc": "1. Select 7 days, 15 days, 30 days and 90 days one at a time. After each selection, read the selected range, displayed dates and historical-data notice.",
        "exp": "1. Each selected control is highlighted and the heading, date period and historical-data notice change to that preset. The page keeps QA Portal History as the selected Patient and reloads the clinical sections for the selected period.",
    },
    "HCP-DATA-010": {
        "t": "HCP-DATA-010 — Custom Range applies a complete date period",
        "pre": "QA-PORTAL-HCP-01 is signed in and Patient Glucose Data is open for QA Portal History. Range is collapsed.",
        "proc": "1. Expand Range.\n2. Enter a complete valid Start Date and End Date from the seeded fixture period, then select Go.",
        "exp": "1. Start Date, End Date and Go are displayed. Both date fields use the dd/mm/yyyy format.\n2. The selected date period is shown in the range heading and historical-data notice, and the clinical sections reload for that period.",
    },
    "HCP-DATA-019": {
        "t": "HCP-DATA-019 — Patient detail handles a controlled readings failure and recovers",
        "pre": "QA-PORTAL-HCP-01 is signed in and has an active share from QA-PORTAL-HISTORY-01. Browser request interception is available for the QueryReadings request.",
        "proc": "1. Open QA Portal History and allow the 30-day Patient Glucose Data page to finish loading.\n2. Configure QueryReadings to return HTTP 500, then reload the Patient page.\n3. Remove the interception and reload the Patient page.",
        "exp": "1. The page identifies QA Portal History and displays the historical-data notice, Glucose Chart and calculated sections for the selected period.\n2. The page keeps the correct Patient identity, displays “Failed to fetch patient shared data” and shows “No glucose data available.” It does not fabricate readings or present previously loaded readings as a successful refresh.\n3. Patient Glucose Data recovers without another sign-in and displays the historical notice, chart and calculated sections for QA Portal History.",
        "ev": "output/hcp-data-019-failure.png; output/hcp-data-019-recovery.png; browser Network record showing the controlled HTTP 500 and successful retry; output/hcp-data-019-execution.json",
    },
    "HCP-DATA-021": {
        "t": "HCP-DATA-021 — Shared Patient data is clearly identified as historical",
        "pre": "QA-PORTAL-HCP-01 is signed in and Patient Glucose Data is open for QA Portal History with a completed date range.",
        "proc": "1. Read the notice above the Glucose Chart and the text immediately below it.",
        "exp": "1. The page states “Historical data — not live.” It shows the selected start and end times with the time zone and states that the figures are calculated over the selected period.",
    },
    "HCP-NFR-001": {
        "t": "HCP-NFR-001 — HCP navigation shows the correct role and permitted pages",
        "pre": "QA-PORTAL-HCP-01 is signed in to the HCP Portal.",
        "proc": "1. Inspect the account card and navigation.\n2. Open Patient List and Connect Code, then open and close Profile.",
        "exp": "1. The account card identifies HCP Portal. Navigation contains Patient List, Connect Code, Profile and Logout. Clinic Administrator, Admin and Super Admin controls are not shown.\n2. Each offered HCP page or window opens for the same signed-in HCP and the role does not change.",
    },
    "HCP-NFR-003": {
        "t": "HCP-NFR-003 — Profile shows the signed-in HCP account",
        "pre": "QA-PORTAL-HCP-01 is signed in to the HCP Portal.",
        "proc": "1. Select Profile and inspect the displayed fields.\n2. Close User Profile.",
        "exp": "1. User Profile shows First Name, Last Name, Gender, Date of Birth, Email, Phone Number, Address, Town and Post Code for the signed-in HCP.\n2. User Profile closes and the page that was open remains selected.",
    },
    "HCP-QR-001": {
        "t": "HCP-QR-001 — Connect Code opens confirmation for the intended HCP",
        "pre": "QA-PORTAL-HCP-01 has a Connect Code. QA-PORTAL-SPARSE-01 is signed in to the CGMx1 app and does not currently share data with this HCP.",
        "proc": "1. As QA-PORTAL-HCP-01, open Connect Code in the HCP Portal.\n2. As QA-PORTAL-SPARSE-01, open Clinic Connect and scan or enter the HCP Connect Code. Stop without selecting Share my data.",
        "exp": "1. Connect Code displays the code and explains that the Patient chooses what to share. No Patient data is shared by opening this page.\n2. The app displays “Share with this clinic?” and identifies Muhammad Hasnain as the recipient. It states that glucose readings, sensor sessions and logged events will be visible and that sharing can be stopped at any time. Cancel and Share my data are displayed. No share is created until Share my data is selected.",
        "ev": "Screenshot of the HCP Connect Code page; IMG_6494.PNG showing the Patient confirmation; execution record",
    },
    "HCP-QR-006": {
        "t": "HCP-QR-006 — Download QR and Printable Poster produce matching usable files",
        "pre": "QA-PORTAL-HCP-01 is signed in and Connect Code is open with code CG-HASN-AI01.",
        "proc": "1. Select Download QR and open the downloaded PNG.\n2. Select Printable Poster and open the downloaded PDF.\n3. Compare the code, HCP identity and sharing explanation in both files with the Connect Code page.",
        "exp": "1. The PNG opens and shows a readable QR, code CG-HASN-AI01, Muhammad Hasnain and the statement that nothing is shared until the Patient confirms in the app. Nothing is clipped or unreadable.\n2. The PDF opens as a clear one-page A4 poster. It shows the QR, code CG-HASN-AI01, Muhammad Hasnain, the HCP email and instructions to scan or enter the code. Nothing overlaps or is clipped.\n3. Both files identify the same code and HCP as the Connect Code page. Their text describes a Patient-controlled connection and does not state that downloading or scanning automatically shares data.",
        "ev": "connect-qr-CG-HASN-AI01 (1).png; connect-poster-CG-HASN-AI01 (1).pdf; screenshot of the HCP Connect Code page; execution record",
    },
    "HCP-QR-008": {
        "t": "HCP-QR-008 — Connect Code materials explain Patient choice and confirmation",
        "pre": "QA-PORTAL-HCP-01 has Connect Code CG-HASN-AI01. QA-PORTAL-SPARSE-01 is signed in to the CGMx1 app and does not currently share data with this HCP.",
        "proc": "1. As QA-PORTAL-HCP-01, open Connect Code and read the sharing explanation.\n2. Open the Printable Poster and downloaded QR files and read their sharing explanations.\n3. As QA-PORTAL-SPARSE-01, scan or enter CG-HASN-AI01 in Clinic Connect, inspect the confirmation, then select Cancel.",
        "exp": "1. Connect Code explains that the Patient controls what is shared and can stop sharing.\n2. The poster tells the Patient to check the clinic details and choose what to share and for how long. The downloaded QR states that nothing is shared until the Patient confirms in the app. Both identify CG-HASN-AI01 and Muhammad Hasnain.\n3. The app displays “Share with this clinic?”, identifies Muhammad Hasnain, lists glucose readings, sensor sessions and logged events, and states that sharing can be stopped at any time. Cancel and Share my data are displayed. Selecting Cancel closes the confirmation without creating a share.",
        "ev": "Screenshot of the HCP Connect Code page; connect-poster-CG-HASN-AI01 (1).pdf; connect-qr-CG-HASN-AI01 (1).png; IMG_6494.PNG showing the Patient confirmation; execution record",
    },
    "HCP-QR-010": {
        "t": "HCP-QR-010 — Local QR and poster export failures are reported",
        "pre": "QA-PORTAL-HCP-01 is signed in and Connect Code CG-HASN-AI01 is displayed. An approved browser test harness can force the local QR image export and poster PDF generation functions to fail without downloading a file. The export functions run in the browser; no server request is used.",
        "proc": "1. Enable the local QR image export failure, select Download QR, then remove the failure.\n2. Enable the local poster PDF generation failure, select Printable poster, then remove the failure.\n3. Select Download QR and Printable poster again without fault injection.",
        "exp": "1. The Portal shows “Could not export the QR image.” No PNG is downloaded and the Portal remains usable.\n2. The Portal shows “Could not build the poster PDF.” No PDF is downloaded and the Portal remains usable.\n3. The PNG and PDF are downloaded successfully after fault injection is removed and both identify CG-HASN-AI01 and Muhammad Hasnain.",
        "ev": "Screenshots of both controlled export errors and the recovered downloads; browser download record; execution record",
    },
    "HCP-PROFILE-UPDATE-001": {
        "t": "HCP-PROFILE-UPDATE-001 — Open HCP Edit Profile mode",
        "pre": "QA-PORTAL-HCP-01 is signed in and User Profile is open. The current profile values are recorded in the execution record.",
        "proc": "1. Select Edit Profile.\n2. Inspect the enabled and read-only profile controls.",
        "exp": "1. Edit mode opens and displays Save.\n2. First Name, Last Name, Gender, Date of Birth, Phone Number, Address, Town and Post Code are editable. Email remains read-only.",
    },
    "HCP-PROFILE-UPDATE-004": {
        "t": "HCP-PROFILE-UPDATE-004 — HCP email remains read-only in Edit Profile",
        "pre": "QA-PORTAL-HCP-01 is signed in and Edit Profile is open.",
        "proc": "1. Inspect the Email field and try to place the text cursor in it or change its value.",
        "exp": "1. Email displays the signed-in account address but remains disabled/read-only; its value cannot be edited in this form.",
    },
    "HCP-PROFILE-UPDATE-003": {
        "t": "HCP-PROFILE-UPDATE-003 — First Name and Last Name validation",
        "pre": "QA-PORTAL-HCP-01 is signed in and Edit Profile is open. Current profile values have been recorded. Test changes will be discarded unless a step explicitly requires Save.",
        "proc": "1. Test First Name and Last Name one at a time with an empty value, two characters and a value longer than 50 characters. Try Save after each value.\n2. Enter three spaces in both name fields, complete the other required fields with valid test values and try Save.\n3. Test names of 3–50 characters containing a hyphen and an apostrophe, then discard the changes.",
        "exp": "1. Empty values, values shorter than 3 characters and values longer than 50 characters are rejected before any profile update request is sent.\n2. Whitespace-only names are rejected as empty and no profile update request is sent.\n3. Names of 3–50 characters containing normal name punctuation are accepted by the field validation. Discarding the changes leaves the saved profile unchanged.",
        "ev": "Screenshots or recording of each validation result; browser Network record; execution record",
    },
    "HCP-PROFILE-UPDATE-005": {
        "t": "HCP-PROFILE-UPDATE-005 — Phone Number accepts only the supported format",
        "pre": "QA-PORTAL-HCP-01 is signed in and Edit Profile is open. Other required fields contain valid test values. Test changes will be discarded.",
        "proc": "1. Enter letters and then unsupported special characters in Phone Number. Try Save after each value.\n2. Enter an 8-digit number and then a 16-digit number. Try Save after each value.\n3. Enter a 9–15 digit number, first without and then with one leading +. Try Save, then discard the changes.",
        "exp": "1. Letters and unsupported special characters are rejected by Phone Number and no profile update request is sent.\n2. The 8-digit and 16-digit values are rejected and no profile update request is sent.\n3. A 9–15 digit number is accepted with or without one leading +. No other + position is accepted. Discarding the changes leaves the saved profile unchanged.",
        "ev": "Screenshots or recording of the phone validation results; browser Network record; execution record",
    },
    "HCP-PROFILE-UPDATE-006": {
        "t": "HCP-PROFILE-UPDATE-006 — Gender options and Date of Birth limits",
        "pre": "QA-PORTAL-HCP-01 is signed in and Edit Profile is open. Test changes will be discarded.",
        "proc": "1. Open Gender and inspect all options.\n2. Leave Gender unselected and try Save. Then select each offered option in turn.\n3. Enter a valid past Date of Birth, then enter a future date and try Save. Discard the changes.",
        "exp": "1. Gender offers Male, Female, Other and Prefer Not To Share, with Select a gender as the unselected prompt.\n2. Gender is required. An unselected value is rejected; each offered value can be selected.\n3. A valid past date is accepted. A date after the current date is rejected before any profile update request is sent. Discarding the changes leaves the saved profile unchanged.",
        "ev": "Screenshots of the Gender options and future-date rejection; browser Network record; execution record",
    },
    "HCP-PROFILE-UPDATE-008": {
        "t": "HCP-PROFILE-UPDATE-008 — Saved HCP profile values persist after refresh and sign-in",
        "pre": "QA-PORTAL-HCP-01 is signed in and Edit Profile is open. Current profile values have been recorded. A valid reversible test value is available for one editable field.",
        "proc": "1. Change one field to the reversible test value and select Save.\n2. Refresh the Portal, reopen Profile and inspect the saved field.\n3. Log out, sign in again and reopen Profile. Restore the original value and select Save.",
        "exp": "1. Profile reports a successful save and closes only after the update succeeds.\n2. The test value remains after refresh.\n3. The test value remains after a new sign-in. The original value is restored successfully at the end of the case.",
        "ev": "Screenshots before Save, after refresh, after sign-in and after restoration; execution record",
    },
    "HCP-PROFILE-UPDATE-009": {
        "t": "HCP-PROFILE-UPDATE-009 — Unsaved HCP profile changes are discarded",
        "pre": "QA-PORTAL-HCP-01 is signed in and Edit Profile is open. The saved First Name value has been recorded.",
        "proc": "1. Change First Name to UnsavedTest without selecting Save, then close User Profile.\n2. Reopen User Profile and inspect First Name.",
        "exp": "1. User Profile closes without reporting that the change was saved.\n2. First Name shows the previously saved value. UnsavedTest is not retained.",
        "ev": "output/hcp-profile-update-009.png; execution record",
    },
    "HCP-PROFILE-UPDATE-010": {
        "t": "HCP-PROFILE-UPDATE-010 — HCP profile Save failure remains recoverable",
        "pre": "QA-PORTAL-HCP-01 is signed in and Edit Profile is open with valid values in every required field. Browser request interception is available for the profile update request. Current saved values have been recorded.",
        "proc": "1. Change one field to a reversible test value.\n2. Configure the profile update request to return HTTP 500, select Save, then remove the interception.\n3. Confirm that the saved profile is unchanged, reopen Edit Profile if needed and save the test value normally. Restore the original value at the end.",
        "exp": "1. The valid test change remains visible in Edit Profile before Save.\n2. The Portal reports that Save failed, does not report success and keeps the test values available for correction or retry. No changed value is stored.\n3. The profile remains usable after the controlled failure. A normal retry succeeds, persists the test value and allows the original value to be restored.",
        "ev": "output/hcp-profile-save-failure.png; browser Network record showing the controlled failure and successful retry; execution record",
    },
    "HCP-DIDO-002": {
        "t": "HCP-DIDO-002 — Shared Patient view contains clinical review controls only",
        "pre": "QA-PORTAL-HCP-01 is signed in and Patient Glucose Data is open for QA Portal History.",
        "proc": "1. Inspect the Patient identity, range controls and all clinical sections on the page.\n2. Inspect the page and navigation for export, Patient comparison and device-management controls.",
        "exp": "1. The page provides Patient identity, Today, 7 days, 15 days, 30 days, 90 days, custom Range, Glucose Chart, CGM Summary, Time in Range, Glucose Distribution, Ambulatory Glucose Profile, Daily Patterns, Time in Range by Day and Events & Notes.\n2. Export, Patient comparison and device-management controls are not offered in the shared Patient view or HCP navigation.",
    },
}


def main() -> None:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    by_id = {case["id"]: case for case in cases}
    if len(by_id) != len(cases):
        raise RuntimeError("Duplicate PRT-0702 case IDs")
    missing = sorted(set(UPDATES) - set(by_id))
    if missing:
        raise RuntimeError(f"Missing case IDs: {missing}")
    for case_id, fields in UPDATES.items():
        by_id[case_id].update(fields)
    CASES_PATH.write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {len(UPDATES)} HCP cases")


if __name__ == "__main__":
    main()
