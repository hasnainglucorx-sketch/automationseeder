"""Rewrite Hosted Registration cases for the current Keycloak form."""
import json
import re
import shutil
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"


def clean(value):
    return textwrap.dedent(value).strip()


def item(title, pre, procedure, expected, evidence):
    return {"title": title, "pre": clean(pre), "procedure": clean(procedure),
            "expected": clean(expected), "evidence": evidence}


U = {
"VP-APP-HOSTED-REG-001": item("Hosted registration page content", "Hosted Registration is open.", """
1. Inspect the page from top to bottom.
2. Open the Region list and the language list without making a selection.
""", """
1. The page shows Create your account, the required-fields note, Email, Password, Confirm password, Given name(s), Family name(s), Region, two password-visibility controls, Create an account, Back to sign in and the language selector.
2. Email, Password, Confirm password, Given name(s) and Region are marked required. Family name(s) is not marked required. Region offers United Kingdom and United States. The language selector offers English (UK), English (US), Cymraeg, العربية and Español.
3. The Region notice states that the selection determines where health data are stored and cannot be changed later.
4. Create an account is unavailable while required fields are incomplete.
""", "Full Hosted Registration page; Region and language lists; execution record."),

"VP-APP-HOSTED-REG-002": item("Given name required-field validation", "Hosted Registration is open.", """
1. Enter a value in Given name(s), then clear it.
2. Complete Email, Password, Confirm password and Region with valid test data, leaving Given name(s) empty.
""", """
1. Given name(s) accepts and retains the entered value, then becomes empty when cleared.
2. Keycloak shows Please specify this field. for Given name(s), and Create an account remains unavailable.
""", "Given name input and required-field validation; execution record."),

"VP-APP-HOSTED-REG-003": item("Family name is optional", "Hosted Registration is open.", """
1. Enter a value in Family name(s), then clear it.
2. Complete Email, Password, Confirm password, Given name(s) and Region with valid test data. Leave Family name(s) empty.
3. Do not create the account.
""", """
1. Family name(s) accepts and retains the entered value, then becomes empty when cleared.
2. No required-field message is shown for Family name(s).
3. With every required field valid, Create an account becomes available while Family name(s) remains empty.
""", "Optional Family name state and enabled Create an account action; execution record."),

"VP-APP-HOSTED-REG-004": item("Email format validation", "Hosted Registration is open.", """
1. Enter a valid-format test email in Email.
2. Replace it with malformed text.
3. Complete Password, Confirm password, Given name(s) and Region with valid test data. Do not create the account.
""", """
1. The valid-format email is accepted without an email-format message.
2. Keycloak shows Invalid email address. for malformed text.
3. Create an account remains unavailable while the email is malformed.
""", "Valid and malformed Email states; validation message; execution record."),

"VP-APP-HOSTED-REG-005": item("Password format validation", "Hosted Registration is open. Use valid details in all other required fields.", """
1. Enter matching passwords shorter than 12 characters that contain a number, lowercase letter, uppercase letter and special character.
2. Enter matching passwords of at least 12 characters with no number.
3. Repeat with no lowercase letter, then no uppercase letter, then no special character.
4. Enter matching passwords of at least 12 characters containing a number, lowercase letter, uppercase letter and special character. Do not create the account.
""", """
1. Keycloak shows Invalid password: minimum length 12.
2. Keycloak shows Invalid password: must contain at least 1 numerical digits.
3. Keycloak shows the matching message for each missing type: must contain at least 1 lower case characters; must contain at least 1 upper case characters; must contain at least 1 special characters.
4. No password-format message is shown and Create an account becomes available.
""", "Password-format messages and valid-password state; execution record."),

"VP-APP-HOSTED-REG-006": item("Password confirmation validation", "Hosted Registration is open. Use valid details in all other required fields.", """
1. Enter a valid-format password in Password.
2. Enter a different valid-format password in Confirm password. Do not create the account.
""", """
1. Password remains masked by default.
2. Keycloak shows Password confirmation doesn't match. Create an account remains unavailable.
""", "Password-confirmation validation; execution record."),

"VP-APP-HOSTED-REG-007": item("Reject registration with an existing email", "Hosted Registration is open. QA_ACTIVE_01 is available.", """
1. Enter the QA_ACTIVE_01 email.
2. Enter valid matching passwords, Given name(s) and Region. Family name(s) may be left empty.
3. Select Create an account once.
""", """
1. The form accepts the entered values.
2. The request is submitted once.
3. Keycloak rejects the duplicate registration, does not create another account or authenticated session, and leaves a recoverable registration or sign-in path.
""", "Completed form, duplicate-account response and recoverable state; execution record."),

"VP-APP-HOSTED-REG-008": item("Required registration fields", "Hosted Registration is open. Valid test values are available.", """
1. Complete all required fields, then clear Email.
2. Restore Email and clear Password.
3. Restore Password and clear Confirm password.
4. Restore Confirm password and clear Given name(s).
5. Restore Given name(s) and clear Region.
6. Restore Region, leave Family name(s) empty and do not create the account.
""", """
1. Keycloak shows Please specify this field. for each empty text field, and Create an account remains unavailable.
2. With Region empty, Create an account remains unavailable.
3. When Email, Password, Confirm password, Given name(s) and Region are valid, Create an account becomes available even when Family name(s) is empty.
""", "Required-field states and completed valid form; execution record."),

"VP-APP-HOSTED-REG-009": item("Create a new account", "Hosted Registration is open. Fresh email A and its inbox are available.", """
1. Enter Fresh email A, valid matching passwords, Given name(s) and Region. Family name(s) is optional.
2. Select Create an account once.
""", """
1. Create an account becomes available when all required values are valid.
2. The registration is submitted once and the email-verification state opens for Fresh email A without an unexpected error.
""", "Completed registration form and email-verification state; execution record."),

"VP-APP-HOSTED-REG-010": item("Email verification page content", "VP-APP-HOSTED-REG-009 has created Fresh email A and the verification page is open.", """
1. Inspect the verification page from top to bottom.
""", """
1. The page identifies Fresh email A, explains that verification is required and provides the available resend or recovery action.
""", "Email verification page; execution record."),

"VP-APP-HOSTED-REG-011": item("Receive the verification email", "Fresh email A has been registered and its inbox is available.", """
1. Open the newest verification email for Fresh email A.
2. Record the received time and stated link-validity period.
""", """
1. The verification email is addressed to Fresh email A, identifies the GlucoRx service and contains a verification link.
2. The email states the link-validity period.
""", "Verification email and recorded timing; execution record."),

"VP-APP-HOSTED-REG-012": item("Verify an account with a valid link", "The newest verification email for Fresh email A is open and its link is still valid.", """
1. Open the verification link.
2. Complete the confirmation action shown on the hosted page.
""", """
1. The link opens the verification flow for Fresh email A.
2. Verification completes and the account is no longer unverified.
""", "Verification confirmation and completed state; execution record."),

"VP-APP-HOSTED-REG-013": item("Reject an expired verification link", "Fresh email B is registered but unverified. Its verification email time and validity period are recorded.", """
1. Wait until the stated validity period has passed.
2. Open the expired verification link.
""", """
1. The execution record proves the link was opened after its stated validity period.
2. Verification does not complete, an expired-link message is shown and Fresh email B remains unverified.
""", "Email timing and expired-link response; execution record."),

"VP-APP-HOSTED-REG-014": item("Resend verification after expiry", "Fresh email B remains unverified and its earlier verification link has expired.", """
1. Select the resend-verification action.
2. Open the newest email for Fresh email B.
3. Open its link within the stated validity period and complete confirmation.
""", """
1. A new verification email is sent to Fresh email B.
2. The new email contains a new verification link.
3. The new link completes verification for Fresh email B.
""", "Resend result, new email and completed verification; execution record."),

"VP-APP-HOSTED-REG-015": item("Return to hosted sign in", "Hosted Registration is open and no field has been changed.", """
1. Select Back to sign in.
""", """
1. Hosted Sign In opens. No registration is submitted and the user remains signed out.
""", "Hosted Sign In page; execution record."),

"VP-APP-HOSTED-REG-016": item("Close hosted registration", "Hosted Registration is open and the user is signed out.", """
1. Close the hosted view using the app's top-left close control.
""", """
1. The hosted view closes without creating an account, and the native Create Account screen returns in a usable signed-out state.
""", "Native Create Account screen after closing; execution record."),

"VP-APP-HOSTED-REG-017": item("Hosted registration languages", "Hosted Registration is open.", """
1. In the hosted language selector, select English (UK), English (US), Cymraeg, العربية and Español one at a time.
2. For each language, inspect the heading, required-fields note, field labels, Region notice, Create an account and Back to sign in.
3. Trigger one required-field message in each language without creating an account.
""", """
1. Every listed language can be selected directly on the hosted page.
2. Registration labels, actions and the Region notice use the selected language and remain readable.
3. The required-field message uses the selected language. Changing language does not submit registration.
""", "Hosted form and one validation state for each language; execution record."),

"VP-APP-HOSTED-REG-018": item("Select and retain the registration region", "Hosted Registration is open. QA_REG_REGION_01 and its inbox are available.", """
1. Open Region and verify that United Kingdom and United States are available.
2. Select the region assigned to QA_REG_REGION_01 and read the notice below Region.
3. Complete the required fields, create the account, verify its email and sign in.
4. Open Settings > User Profile and inspect the account region.
""", """
1. Region provides United Kingdom and United States.
2. The notice says the selection determines where health data are stored and cannot be changed later.
3. Registration and verification retain the selected region.
4. User Profile shows the same region and provides no control that changes it.
""", "Region options and notice, selected value, verification and User Profile region; execution record."),

"VP-APP-HOSTED-REG-019": item("Apply glucose unit from the registration region", "Fresh UK-region and US-region emails are available. The expected unit for each region is recorded in Test Data.", """
1. Register and verify one account with United Kingdom selected, then sign in and open Profile Setup.
2. Record the Country and Glucose unit.
3. Repeat with a fresh account and United States selected.
4. Inspect whether either account can change its unit to conflict with its registered region.
""", """
1. The hosted registration form uses Region and does not show a separate glucose-unit field.
2. Each account's Profile Setup shows the Country and unit defined for its registered region in Test Data.
3. The user cannot create a Country/Glucose unit mismatch after registration.
""", "Both registration regions and both Profile Setup unit results; execution record."),

"VP-APP-HOSTED-REG-020": item("Registration language and region mismatch warning", "Test Data identifies a hosted language, an incompatible registration region and the expected correction and continue actions.", """
1. Select the Test Data language in the hosted language selector.
2. Select the incompatible Region and complete the other required fields.
3. Select Create an account and use the correction action on the mismatch warning.
4. Repeat the mismatch and use the continue action.
""", """
1. The form uses the selected language and region.
2. Before registration completes, a warning explains that signed-in content is unavailable in the selected language for that region.
3. The correction action returns to registration so the language or region can be changed.
4. The continue action allows registration to proceed. If no warning appears, record the case as failed.
""", "Mismatch warning, correction path and continue path; execution record."),

"VP-APP-HOSTED-REG-021": item("Confirm before discarding entered registration data", "Hosted Registration is open and all fields are empty.", """
1. Enter values in Email, Given name(s) and Family name(s).
2. Use the app's close or back control.
3. On the discard prompt, choose to stay.
4. Repeat the close or back action and confirm leaving.
5. Open Hosted Registration again.
""", """
1. The three fields retain the entered values before leaving.
2. A confirmation prompt appears before the values are discarded.
3. Staying returns to the form with all three values retained.
4. Confirming closes the hosted form without creating an account.
5. A newly opened registration form is empty.
""", "Recording of entered values, discard prompt, stay, leave and reopened empty form; execution record."),
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def apply_updates(rows, run_order=False):
    found = set()
    for row in rows:
        case_id = row.get("id")
        if case_id not in U:
            continue
        value = U[case_id]
        found.add(case_id)
        if run_order:
            row.update(title=value["title"], preconditions=value["pre"], procedure=value["procedure"],
                       expected=value["expected"], evidence=value["evidence"])
        else:
            row.update(t=value["title"], pre=value["pre"], proc=value["procedure"],
                       exp=value["expected"], ev=value["evidence"])
    return found


def main():
    cases_path = OUT / "PRT-0701-cases.json"
    run_path = OUT / "PRT-0701-run_order.json"
    html_path = OUT / "PRT-0701-Console-source.html"
    cases, run_order = load(cases_path), load(run_path)
    case_found = apply_updates(cases)
    run_found = apply_updates(run_order, run_order=True)
    expected_cases = set(U) - {"VP-APP-HOSTED-REG-021"}
    if case_found != expected_cases:
        raise RuntimeError(f"Unexpected cases coverage: {sorted(case_found ^ expected_cases)}")
    if run_found != set(U):
        raise RuntimeError(f"Unexpected run-order coverage: {sorted(run_found ^ set(U))}")
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
    print(f"Updated {len(case_found)} console cases and {len(run_found)} run-order cases")


if __name__ == "__main__":
    main()
