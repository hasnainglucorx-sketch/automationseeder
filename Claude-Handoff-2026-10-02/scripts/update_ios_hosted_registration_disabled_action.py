"""Hosted registration: 'Create an account' is disabled (HTML disabled attribute, still blue) until all required fields are valid.
No 'Please specify this field.' message appears on the empty form."""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"
LATEST = ROOT / "Claude-Handoff-2026-10-02" / "latest"

D = "Create an account is disabled and cannot be selected, even though it is shown in blue."
U = {
"VP-APP-HOSTED-REG-002": dict(
 proc=("1. Leave Given name(s) empty and complete Email, Password, Confirm password and Region with valid test data.\n"
       "2. Enter a value in Given name(s).\n"
       "3. Clear Given name(s) again."),
 exp=("1. Create an account remains unavailable while Given name(s) is empty. No Please specify this field. message is shown.\n"
      "2. Given name(s) accepts and retains the value, and Create an account becomes available.\n"
      "3. Create an account becomes unavailable again once Given name(s) is empty.")),
"VP-APP-HOSTED-REG-003": dict(
 proc=("1. Complete Email, Password, Confirm password, Given name(s) and Region with valid test data. Leave Family name(s) empty.\n"
       "2. Enter a value in Family name(s), then clear it.\n"
       "3. Do not create the account."),
 exp=("1. Create an account becomes available with Family name(s) empty. No required-field message is shown for Family name(s).\n"
      "2. Family name(s) accepts and retains the value, and Create an account stays available when the field is entered or cleared.\n"
      "3. No account is created.")),
"VP-APP-HOSTED-REG-004": dict(
 proc=("1. Complete Password, Confirm password, Given name(s) and Region with valid test data.\n"
       "2. Enter malformed text in Email.\n"
       "3. Replace it with a valid-format test email. Do not create the account."),
 exp=("1. Create an account remains unavailable while Email is empty.\n"
      "2. Keycloak shows Invalid email address. and Create an account remains unavailable.\n"
      "3. The message is removed and Create an account becomes available.")),
"VP-APP-HOSTED-REG-005": dict(
 proc=("1. Use valid details in Email, Given name(s) and Region.\n"
       "2. Enter matching passwords shorter than 12 characters that contain a number, lowercase letter, uppercase letter and special character.\n"
       "3. Enter matching passwords of at least 12 characters with no number.\n"
       "4. Repeat with no lowercase letter, then no uppercase letter, then no special character.\n"
       "5. Enter matching passwords of at least 12 characters containing a number, lowercase letter, uppercase letter and special character. Do not create the account."),
 exp=("1. Create an account remains unavailable until a password is entered.\n"
      "2. Keycloak shows Invalid password: minimum length 12.\n"
      "3. Keycloak shows Invalid password: must contain at least 1 numerical digits.\n"
      "4. Keycloak shows the matching message for each missing type: must contain at least 1 lower case characters; must contain at least 1 upper case characters; must contain at least 1 special characters.\n"
      "5. No password-format message is shown and Create an account becomes available. Create an account stays unavailable in steps 2 to 4.")),
"VP-APP-HOSTED-REG-006": dict(
 proc=("1. Use valid details in Email, Given name(s) and Region.\n"
       "2. Enter a valid-format password in Password.\n"
       "3. Enter a different valid-format password in Confirm password.\n"
       "4. Change Confirm password to match Password. Do not create the account."),
 exp=("1. Password remains masked by default.\n"
      "2. Create an account remains unavailable until Confirm password is entered.\n"
      "3. Keycloak shows Password confirmation doesn't match. and Create an account remains unavailable.\n"
      "4. The message is removed and Create an account becomes available.")),
"VP-APP-HOSTED-REG-008": dict(
 pre="Hosted Registration is open. Valid test values are available.",
 proc=("1. Inspect Create an account on the empty form.\n"
       "2. Complete all required fields with valid values.\n"
       "3. Clear Email, then restore it.\n"
       "4. Clear Password, then restore it.\n"
       "5. Clear Confirm password, then restore it.\n"
       "6. Clear Given name(s), then restore it.\n"
       "7. Clear Region, then restore it.\n"
       "8. With all required fields valid, leave Family name(s) empty. Do not create the account."),
 exp=("1. " + D + " No Please specify this field. message is shown on the empty form.\n"
      "2. Create an account becomes available only after Email, Password, Confirm password, Given name(s) and Region all contain acceptable values.\n"
      "3. Clearing any one required field makes Create an account unavailable again.\n"
      "4. Family name(s) can stay empty without making Create an account unavailable.")),
}
SUBS = {
"VP-APP-HOSTED-REG-001": {"exp": [("4. Create an account is enabled, and it and Back to sign in are shown below the notice.",
    "4. " + D + " It remains unavailable until every required field is complete and valid. Back to sign in is shown below it.")]},
"VP-APP-HOSTED-REG-009": {"exp": [("1. Create an account is enabled.", "1. Create an account becomes available when all required values are valid.")]},
}
RUN = {"exp": "expected", "proc": "procedure", "pre": "preconditions"}


def load(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def save(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    cp, rp, hp = OUT / "PRT-0701-cases.json", OUT / "PRT-0701-run_order.json", OUT / "PRT-0701-Console-source.html"
    cases, order = load(cp), load(rp)
    for rows, run in ((cases, False), (order, True)):
        seen = set()
        for r in rows:
            i = r["id"]
            if i in U:
                for k, v in U[i].items():
                    r[RUN[k] if run else k] = v
                seen.add(i)
            if i in SUBS:
                for k, subs in SUBS[i].items():
                    key = RUN[k] if run else k
                    for old, new in subs:
                        if old not in r[key]:
                            raise RuntimeError(f"{i}: not found: {old}")
                        r[key] = r[key].replace(old, new)
                seen.add(i)
        if seen != set(U) | set(SUBS):
            raise RuntimeError("missing cases")
    save(cp, cases)
    save(rp, order)
    html = hp.read_text(encoding="utf-8-sig")
    emb = json.dumps(cases, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    html, n = re.compile(r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)", re.S).subn(
        lambda m: m.group(1) + emb + m.group(2), html, count=1)
    if n != 1:
        raise RuntimeError("embedded case list not found")
    hp.write_text(html, encoding="utf-8")
    shutil.copy2(hp, ROOT / "PRT-0701-Console-source.updated.html")
    for name in ("PRT-0701-cases.json", "PRT-0701-run_order.json", "PRT-0701-Console-source.html"):
        shutil.copy2(OUT / name, LATEST / name)
    shutil.copy2(hp, LATEST / "PRT-0701-Console-source.updated.html")
    shutil.copy2(Path(__file__), LATEST.parent / "scripts" / Path(__file__).name)
    print("ok")


if __name__ == "__main__":
    main()
