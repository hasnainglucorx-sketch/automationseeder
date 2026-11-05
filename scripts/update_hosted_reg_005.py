"""Update hosted-registration password cases with behavior verified in Keycloak."""
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"

UPDATES = {
    "VP-APP-HOSTED-REG-005": {
        "title": "Password format validation",
        "precondition": "Hosted Registration is open. Use valid details in all other required fields.",
        "procedure": (
            "1. Complete Email, Given name(s), Region and any other required field with valid test data.\n"
            "2. Enter the same password in Password and Confirm password using fewer than 12 characters. Include a number, lowercase letter, uppercase letter and special character.\n"
            "3. Enter matching passwords of at least 12 characters with no number.\n"
            "4. Repeat with no lowercase letter, then no uppercase letter, then no special character.\n"
            "5. Enter matching passwords of at least 12 characters containing a number, lowercase letter, uppercase letter and special character. Do not create the account."
        ),
        "expected": (
            "1. The other required fields accept the valid test data.\n"
            "2. Keycloak shows: Invalid password: minimum length 12.\n"
            "3. Keycloak shows: Invalid password: must contain at least 1 numerical digits.\n"
            "4. Keycloak shows the matching message for each missing character type: must contain at least 1 lower case characters; must contain at least 1 upper case characters; must contain at least 1 special characters.\n"
            "5. No password-format message is shown and Create an account becomes available. No account is created in this test."
        ),
        "evidence": "Password-format validation screenshots or recording; valid-password state screenshot; execution record.",
    },
    "VP-APP-HOSTED-REG-006": {
        "title": "Password confirmation validation",
        "precondition": "Hosted Registration is open. Use valid details in all other required fields.",
        "procedure": (
            "1. Complete Email, Given name(s), Region and any other required field with valid test data.\n"
            "2. Enter a valid-format password in Password.\n"
            "3. Enter a different valid-format password in Confirm password. Do not create the account."
        ),
        "expected": (
            "1. The other required fields accept the valid test data.\n"
            "2. Password remains masked by default.\n"
            "3. Keycloak shows: Password confirmation doesn't match. Create an account remains unavailable and no account is created."
        ),
        "evidence": "Password-confirmation validation screenshot; execution record.",
    },
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_cases(cases):
    for case_id, update in UPDATES.items():
        matches = [item for item in cases if item.get("id") == case_id]
        if len(matches) != 1:
            raise RuntimeError(f"Expected one {case_id} in cases data")
        matches[0].update({
            "t": update["title"],
            "pre": update["precondition"],
            "proc": update["procedure"],
            "exp": update["expected"],
            "ev": update["evidence"],
        })


def update_run_order(rows):
    for case_id, update in UPDATES.items():
        matches = [item for item in rows if item.get("id") == case_id]
        if len(matches) != 1:
            raise RuntimeError(f"Expected one {case_id} in run-order data")
        matches[0].update({
            "title": update["title"],
            "preconditions": update["precondition"],
            "procedure": update["procedure"],
            "expected": update["expected"],
            "evidence": update["evidence"],
        })


def main():
    cases_path = OUT / "PRT-0701-cases.json"
    run_path = OUT / "PRT-0701-run_order.json"
    html_path = OUT / "PRT-0701-Console-source.html"
    cases = read_json(cases_path)
    run_order = read_json(run_path)

    update_cases(cases)
    update_run_order(run_order)
    write_json(cases_path, cases)
    write_json(run_path, run_order)

    html = html_path.read_text(encoding="utf-8")
    embedded = json.dumps(cases, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    pattern = re.compile(r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)", re.DOTALL)
    html, count = pattern.subn(lambda match: match.group(1) + embedded + match.group(2), html, count=1)
    if count != 1:
        raise RuntimeError("Embedded console case list was not found")
    html_path.write_text(html, encoding="utf-8")
    shutil.copy2(html_path, ROOT / "PRT-0701-Console-source.updated.html")

    print(json.dumps({case_id: data["title"] for case_id, data in UPDATES.items()}, indent=2))


if __name__ == "__main__":
    main()
