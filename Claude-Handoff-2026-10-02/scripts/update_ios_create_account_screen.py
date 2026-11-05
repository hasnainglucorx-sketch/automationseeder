"""Update native Create Account consent cases from IMG_6418.PNG."""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"

U = {
"VP-APP-REGISTER-CONSENT-001": {
"title": "Create your account screen content",
"pre": "The native Create your account screen is displayed and the user is signed out.",
"procedure": "1. Inspect the complete screen from top to bottom.\n2. Compare the image, text, controls and version with the approved iOS reference.",
"expected": (
"1. The screen shows the lifestyle image, CGMx 1 logo and Create your account heading.\n"
"2. The explanation states: It takes about a minute. You'll set your email and password on the secure GlucoRx page, then confirm your email address.\n"
"3. Separate Terms of Service and Privacy Policy consent controls and their Read links are shown.\n"
"4. Create account is disabled and Please accept both to continue. is shown while both controls are unchecked.\n"
"5. The security card reads Your health data is protected and Your information is encrypted in transit and at rest.\n"
"6. Already have an account? Sign in and the app version are visible. For IMG_6418.PNG the displayed reference is Version 1.0.4 (202609301). No content is missing, duplicated, clipped, overlapping or corrupted."
),
"evidence": "Full screen compared with IMG_6418.PNG; displayed version; execution record."},

"VP-APP-REGISTER-CONSENT-002": {
"title": "Terms and Privacy consent presentation",
"pre": "The native Create your account screen is displayed and the user is signed out.",
"procedure": "1. Inspect both consent controls before selecting either one.\n2. Inspect the legal text and link associated with each control.",
"expected": (
"1. Two separate controls are shown and both are unchecked by default.\n"
"2. The first control is associated with I agree to the Terms of Service and Read Terms of Service.\n"
"3. The second control is associated with I have read and accept the Privacy Policy and Read Privacy Policy.\n"
"4. No consent is preselected or implied by opening the screen."
),
"evidence": "Initial unchecked consent controls and associated text; execution record."},

"VP-APP-REGISTER-CONSENT-003": {
"title": "Create account consent gating",
"pre": "The native Create your account screen is displayed with both consent controls unchecked.",
"procedure": (
"1. Confirm Create account is unavailable and the helper message is displayed.\n"
"2. Select only the Terms of Service consent.\n"
"3. Select the Privacy Policy consent as well.\n"
"4. Deselect either consent."
),
"expected": (
"1. Create account is disabled and Please accept both to continue. is shown.\n"
"2. Create account remains disabled while only one consent is selected.\n"
"3. Create account becomes enabled when both consents are selected.\n"
"4. Deselecting either consent disables Create account again. No registration starts during these checks."
),
"evidence": "Zero, one, two and deselected consent states; execution record."},

"VP-APP-REGISTER-CONSENT-004": {
"title": "Terms of Service and Privacy Policy links",
"pre": "The native Create your account screen is displayed and internet is available.",
"procedure": (
"1. Select Read Terms of Service.\n"
"2. Return to Create your account.\n"
"3. Select Read Privacy Policy.\n"
"4. Return to Create your account."
),
"expected": (
"1. The GlucoRx Terms of Service resource opens without an error.\n"
"2. Returning restores Create your account; neither consent is selected automatically and registration does not start.\n"
"3. The GlucoRx Privacy Policy resource opens without an error.\n"
"4. Returning again restores Create your account without changing consent or account state."
),
"evidence": "Terms resource, Privacy resource and returned consent states; execution record."},

"VP-APP-REGISTER-CONSENT-005": {
"title": "Open hosted registration after consent",
"pre": "The native Create your account screen is displayed, both consent controls are selected and internet is available.",
"procedure": (
"1. Select Create account once.\n"
"2. If iOS shows a system sign-in confirmation, record its text and select Continue.\n"
"3. Observe the hosted destination.\n"
"4. Close the hosted view without submitting registration."
),
"expected": (
"1. The account action responds once.\n"
"2. Any iOS confirmation is handled once without opening duplicate views.\n"
"3. The hosted GlucoRx Create your account form opens with Email, Password, Confirm password, Given name(s), optional Family name(s) and required Region.\n"
"4. Closing the hosted view returns to the native Create your account flow without creating an account or authenticating the user."
),
"evidence": "Enabled Create account action, any iOS prompt, hosted registration form and returned native state; execution record."},
}


def load(path): return json.loads(path.read_text(encoding="utf-8"))
def save(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    cases_path = OUT / "PRT-0701-cases.json"
    run_path = OUT / "PRT-0701-run_order.json"
    html_path = OUT / "PRT-0701-Console-source.html"
    cases, run_order = load(cases_path), load(run_path)
    for rows, run in [(cases, False), (run_order, True)]:
        found = set()
        for row in rows:
            case_id = row.get("id")
            if case_id not in U: continue
            v = U[case_id]
            found.add(case_id)
            if run:
                row.update(title=v["title"], preconditions=v["pre"], procedure=v["procedure"], expected=v["expected"], evidence=v["evidence"])
            else:
                row.update(t=v["title"], pre=v["pre"], proc=v["procedure"], exp=v["expected"], ev=v["evidence"])
        if found != set(U): raise RuntimeError(f"Missing consent cases: {sorted(set(U)-found)}")
    save(cases_path, cases); save(run_path, run_order)
    html = html_path.read_text(encoding="utf-8")
    embedded = json.dumps(cases, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    pattern = re.compile(r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)", re.DOTALL)
    html, count = pattern.subn(lambda m: m.group(1) + embedded + m.group(2), html, count=1)
    if count != 1: raise RuntimeError("Embedded console case list was not found")
    html_path.write_text(html, encoding="utf-8")
    shutil.copy2(html_path, ROOT / "PRT-0701-Console-source.updated.html")
    print("Updated five native Create Account consent cases")


if __name__ == "__main__": main()
