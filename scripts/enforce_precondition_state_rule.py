"""Keep actions in procedures for hosted registration and sign-in cases."""

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"


UPDATES = {
    "VP-APP-HOSTED-SIGNIN-002": {
        "pre": "Hosted Sign In is open. A non-sensitive password is available.",
    },
    "VP-APP-HOSTED-SIGNIN-003": {
        "pre": "Hosted Sign In is open. A non-sensitive test email is available.",
    },
    "VP-APP-HOSTED-SIGNIN-004": {
        "pre": "Hosted Sign In is open. A non-sensitive password is available.",
    },
    "VP-APP-HOSTED-SIGNIN-010": {
        "pre": (
            "The user is unauthenticated, internet is available, and Hosted Sign In is displayed. "
            "The QA_ACTIVE_01 email and password are available in the QA Workbook, Test Data row TD-01.2."
        ),
        "proc": (
            "1. Enter the QA_ACTIVE_01 email in Email.\n"
            "2. Enter the QA_ACTIVE_01 password from the QA Workbook, Test Data row TD-01.2.\n"
            "3. Select Sign in twice rapidly."
        ),
        "exp": (
            "1. The email is displayed in Email.\n"
            "2. The password is masked.\n"
            "3. One sign-in completes and CGMx 1 shows one destination screen; no duplicate browser page, stacked app "
            "screen, error or corrupted authentication state appears."
        ),
        "ev": "Screen recording of the repeated sign-in action and resulting destination; execution record.",
    },
    "VP-APP-HOSTED-SIGNIN-015": {
        "pre": (
            "The user is unauthenticated, internet is available, and Hosted Sign In is displayed. "
            "At least one unused, never-onboarded account is available in the onboarding pool."
        ),
        "proc": (
            "1. Select the next unused onboarding-pool account, record its alias, and sign in using its credentials from "
            "the QA Workbook, Test Data row TD-13.3 or TD-13.4.\n"
            "2. Complete the first onboarding screen and select Continue.\n"
            "3. On the next onboarding screen, remove CGMx 1 using the TD-59.1 reset method, reinstall it and launch it.\n"
            "4. Open the hosted sign-in flow and sign in again with the same account."
        ),
        "exp": (
            "1. The selected alias is recorded, sign-in succeeds and the first onboarding screen is shown; its title is recorded.\n"
            "2. The next onboarding screen is shown.\n"
            "3. CGMx 1 opens on the Welcome screen in an unauthenticated state.\n"
            "4. Sign-in succeeds and onboarding starts again from the first screen recorded in Step 1; Home is not shown "
            "until onboarding is completed."
        ),
        "ev": "Recorded account alias; first onboarding screen before and after reinstall; execution record.",
    },
    "VP-APP-HOSTED-SIGNIN-012": {
        "pre": (
            "Req: DI-825 / DO-916. Non-production QA only. QA-HISTORY-01 is active and verified, its password is held "
            "outside the protocol, and the tester is logged out. The controlled fixture contains readings intended to be "
            "91, 90 and 89 days old at execution. The recorded reference values are 98, 100 and 102 mg/dL respectively."
        ),
        "proc": (
            "1. Check the fixture ages immediately before execution. If necessary, refresh the three controlled readings so "
            "they are 91, exactly 90 and 89 days old, then record their timestamps and values.\n"
            "2. Remove CGMx 1 or clear its local data, reinstall or relaunch it as applicable, and confirm the user is logged out.\n"
            "3. Sign in with QA-HISTORY-01 through the normal hosted sign-in flow.\n"
            "4. Complete the normal post-sign-in flow until Home is displayed without manually re-entering historical readings.\n"
            "5. Open the Home/Reports historical view that includes the boundary dates and check the controlled readings."
        ),
        "exp": (
            "1. The recorded fixture contains one reading more than 90 days old, one exactly 90 days old and one less than "
            "90 days old at the execution time.\n"
            "2. CGMx 1 starts in a fresh, logged-out state with no locally retained history.\n"
            "3. Sign-in succeeds and the account's server-held data is restored without data from another account.\n"
            "4. Home is displayed without the tester manually recreating the historical readings.\n"
            "5. The exactly-90-day and less-than-90-day readings are available in the supported historical view; the "
            "more-than-90-day reading is excluded."
        ),
        "ev": (
            "Recorded 91/90/89-day fixture timestamps and values; fresh-state evidence; restored Home/Reports boundary view; "
            "execution record."
        ),
    },
    "VP-APP-HOSTED-SIGNIN-014": {
        "pre": (
            "Req: DI-285 / DO-673. Non-production QA only. The user is logged out. Test Data provides two active, verified "
            "regional accounts with completed onboarding and different controlled region, glucose-unit and language mappings. "
            "Their passwords are held outside the protocol and the expected mapping for each account is recorded in Test Data."
        ),
        "proc": (
            "1. Sign in using Account A.\n"
            "2. Open Settings > User Profile.\n"
            "3. Open Home.\n"
            "4. Sign out using Settings > Account Security > Logout.\n"
            "5. Sign in using Account B.\n"
            "6. Open Settings > User Profile.\n"
            "7. Open Home.\n"
            "8. Open Settings > Language."
        ),
        "exp": (
            "1. Account A signs in successfully.\n"
            "2. Country/region matches Account A's controlled mapping.\n"
            "3. Home glucose values use Account A's controlled glucose unit.\n"
            "4. The user becomes unauthenticated.\n"
            "5. Account B signs in successfully.\n"
            "6. Country/region matches Account B and does not retain Account A's value.\n"
            "7. Home glucose values use Account B's controlled unit and do not retain Account A's unit.\n"
            "8. The language or fallback matches Account B where it is exposed by the app. Internal regional server routing "
            "is outside this manual case."
        ),
        "ev": (
            "Account A and Account B User Profile screenshots; Account A and Account B Home glucose-unit screenshots; "
            "Settings > Language screenshot where applicable; execution record."
        ),
    },
    "VP-APP-HOSTED-REG-005": {
        "pre": "Hosted Registration is open. Valid values for every other required field are available.",
    },
    "VP-APP-HOSTED-REG-006": {
        "pre": "Hosted Registration is open. Valid values for every other required field are available.",
    },
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    cases_path = OUT / "PRT-0701-cases.json"
    run_path = OUT / "PRT-0701-run_order.json"
    html_path = OUT / "PRT-0701-Console-source.html"
    cases = load(cases_path)
    run_order = load(run_path)

    compact_map = {row["id"]: row for row in cases}
    full_map = {row["id"]: row for row in run_order}
    missing = set(UPDATES) - compact_map.keys() | (set(UPDATES) - full_map.keys())
    if missing:
        raise RuntimeError(f"Missing cases: {sorted(missing)}")

    for case_id, update in UPDATES.items():
        compact = compact_map[case_id]
        full = full_map[case_id]
        compact["pre"] = update["pre"]
        full["preconditions"] = update["pre"]
        if "proc" in update:
            compact["proc"] = update["proc"]
            full["procedure"] = update["proc"]
        if "exp" in update:
            compact["exp"] = update["exp"]
            full["expected"] = update["exp"]
        if "ev" in update:
            compact["ev"] = update["ev"]
            full["evidence"] = update["ev"]

    save(cases_path, cases)
    save(run_path, run_order)

    html = html_path.read_text(encoding="utf-8")
    embedded = json.dumps(cases, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    pattern = re.compile(r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)", re.DOTALL)
    html, count = pattern.subn(lambda match: match.group(1) + embedded + match.group(2), html, count=1)
    if count != 1:
        raise RuntimeError("Embedded console case list was not found")
    html_path.write_text(html, encoding="utf-8")
    shutil.copy2(html_path, ROOT / "PRT-0701-Console-source.updated.html")
    print(f"Updated {len(UPDATES)} cases")


if __name__ == "__main__":
    main()
