"""Align Hosted Sign In and password-reset cases with the current Keycloak UI."""
import json
import re
import shutil
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"


def c(value):
    return textwrap.dedent(value).strip()


def u(title, pre, procedure, expected, evidence):
    return {"title": title, "pre": c(pre), "procedure": c(procedure),
            "expected": c(expected), "evidence": evidence}


U = {
"VP-APP-HOSTED-SIGNIN-001": u("Hosted Sign In page content", "Hosted Sign In is open.", """
1. Inspect the page from top to bottom.
2. Open the language selector.
""", """
1. The page shows GlucoRx branding, Sign in, the welcome text, required Email and Password fields, Show password, Forgot password?, Sign in, Create an account and the language selector.
2. The language selector offers English (UK), English (US), Cymraeg, العربية and Español.
3. All content is readable and no control is missing, duplicated, clipped or corrupted.
""", "Full Hosted Sign In page and language list; execution record."),

"VP-APP-HOSTED-SIGNIN-002": u("Sign In email input handling", "Hosted Sign In is open. Use a non-sensitive password.", """
1. Enter a valid-format test email, then clear it.
2. Enter malformed email text and the non-sensitive password.
3. Select Sign in once.
""", """
1. Email accepts the valid-format value and clears normally.
2. The malformed value remains exactly as entered; the page does not show a separate email-format message.
3. Sign-in is rejected with Invalid username or password. and the user remains signed out.
""", "Valid, cleared and malformed Email states; generic rejection; execution record."),

"VP-APP-HOSTED-SIGNIN-003": u("Sign In password required handling", "Hosted Sign In is open. Use a non-sensitive test email.", """
1. Enter the test email and leave Password empty.
2. Select Sign in once.
3. Enter a non-sensitive password.
""", """
1. Email retains the entered value and Password remains empty.
2. Sign-in is rejected with Invalid username or password. and the user remains signed out.
3. Password accepts the value and masks it by default.
""", "Empty-password rejection and masked Password state; execution record."),

"VP-APP-HOSTED-SIGNIN-004": u("Password visibility control", "Hosted Sign In is open. Use a non-sensitive password.", """
1. Enter the password.
2. Select Show password.
3. Select the visibility control again.
""", """
1. Password is masked by default.
2. The existing value becomes visible without changing or submitting it.
3. The same value becomes masked again.
""", "Masked, visible and re-masked Password states; execution record."),

"VP-APP-HOSTED-SIGNIN-006": u("Reject an incorrect password", "Hosted Sign In is open. QA_ACTIVE_01 is available.", """
1. Enter the QA_ACTIVE_01 email and an incorrect password.
2. Select Sign in once.
3. Replace the password with the correct QA_ACTIVE_01 password and select Sign in once.
""", """
1. Email is retained and Password is masked.
2. Keycloak shows Invalid username or password. and the user remains signed out.
3. Corrected credentials authenticate successfully without restarting the app.
""", "Incorrect-password response and successful retry; execution record."),

"VP-APP-HOSTED-SIGNIN-011": u("Authentication failure does not reveal account existence", "Hosted Sign In is open. QA_ACTIVE_01 and an unregistered test email are available.", """
1. Submit the QA_ACTIVE_01 email with an incorrect password and capture the response.
2. Submit the unregistered email with the same incorrect password and capture the response.
3. Compare both responses.
""", """
1. The registered-email attempt fails with Invalid username or password.
2. The unregistered-email attempt fails with the same Invalid username or password. response.
3. Neither response reveals whether the email is registered.
""", "Both generic authentication responses; execution record."),

"VP-APP-HOSTED-SIGNIN-013": u("Hosted Sign In languages", "Hosted Sign In is open.", """
1. Select English (UK), English (US), Cymraeg, العربية and Español one at a time.
2. In each language inspect the heading, Email, Password, password visibility action, Forgot password?, Sign in and Create an account.
3. Submit non-sensitive invalid credentials once in each language.
""", """
1. Every listed language can be selected.
2. The Sign In labels and actions use the selected language and remain readable.
3. The generic authentication rejection uses the selected language and the user remains signed out.
""", "Hosted Sign In and one rejection state for each language; execution record."),

"VP-APP-RESET-001": u("Open Forgot Password", "Hosted Sign In is open.", """
1. Select Forgot password?.
2. Inspect the page that opens.
""", """
1. Forgot your password? opens without authenticating the user.
2. The page shows required Email, Continue, the reset-link explanation, Back to sign in and the language selector.
""", "Forgot Password page; execution record."),

"VP-APP-RESET-002": u("Empty recovery email validation", "Forgot your password? is open and Email is empty.", """
1. Select Continue.
""", """
1. Keycloak shows Please specify username. The request does not proceed and the user remains signed out.
""", "Empty Email validation; execution record."),

"VP-APP-RESET-003": u("Malformed recovery email privacy response", "Forgot your password? is open.", """
1. Enter malformed email text.
2. Select Continue.
""", """
1. The malformed value is accepted as entered; no separate email-format message is shown.
2. Keycloak returns to Sign In and shows You should receive an email shortly with further instructions. The response does not reveal whether an account exists.
""", "Malformed input and generic recovery response; execution record."),

"VP-APP-RESET-004": u("Unknown recovery email privacy response", "Forgot your password? is open. An unregistered valid-format email is available.", """
1. Enter the unregistered email.
2. Select Continue.
3. Compare the response with VP-APP-RESET-005.
""", """
1. Email retains the entered value.
2. Keycloak returns to Sign In and shows You should receive an email shortly with further instructions.
3. The response matches the registered-email request and does not reveal whether the account exists.
""", "Unknown-email generic response and registered-path comparison; execution record."),

"VP-APP-RESET-005": u("Request a password reset and open its valid link", "Forgot your password? is open. QA_RESET_01 and its inbox are available.", """
1. Enter the QA_RESET_01 email and select Continue.
2. Open the newest password-reset email for QA_RESET_01.
3. Record the stated validity period and open the link before it expires.
""", """
1. Keycloak returns to Sign In and shows You should receive an email shortly with further instructions.
2. A password-reset email for QA_RESET_01 arrives and contains a reset link.
3. The valid link opens the Update password page for QA_RESET_01.
""", "Generic request response, reset email and Update password page; execution record."),

"VP-APP-RESET-006": u("Reset-link validity wording", "A reset has been requested for QA_RESET_01 and its newest reset email is available.", """
1. Record any validity wording in the request response.
2. Record the validity period in the reset email.
3. Compare the values when both locations state a period.
""", """
1. The request response is recorded without assuming that it states a validity period.
2. The email states its reset-link validity period.
3. Any period shown in both places is consistent.
""", "Request response and reset-email validity wording; execution record."),

"VP-APP-RESET-007": u("Reset password confirmation validation", "A valid reset link has opened Update password.", """
1. Enter different valid-format values in New password and Confirm password.
2. Attempt to submit the password update.
""", """
1. Both fields accept the values and remain masked by default.
2. The update does not complete and Keycloak shows Password confirmation doesn't match.
""", "Password-confirmation mismatch; execution record."),

"VP-APP-RESET-008": u("Sign out other devices during password reset", "Update password is open for QA_RESET_01, which has an active session on a second approved device.", """
1. Enter matching valid new-password values.
2. Select Sign out from other devices and submit the update.
3. On the second device, attempt an authenticated action.
""", """
1. Both password fields contain the same masked value.
2. The password update completes with other sessions selected for sign-out.
3. The second device requires authentication again.
""", "Successful update and second-device session result; execution record."),

"VP-APP-RESET-009": u("Reject an expired password-reset link", "QA_RESET_01 and its inbox are available.", """
1. Request a reset and record the email received time and stated validity period without opening the link.
2. After the period has expired, open the link.
3. Request another reset and confirm that a new email arrives.
""", """
1. The first reset email contains a link and its validity period is recorded.
2. The expired link cannot open a usable Update password action and shows an expired or invalid-link state.
3. A new request is accepted and a new reset email arrives.
""", "Reset-email timing, expired-link state and replacement email; execution record."),

"VP-APP-RESET-010": u("Reject reuse of a password-reset link", "An unused reset link for QA_RESET_01 is available.", """
1. Use the link to set a valid new password successfully.
2. Open the same link again.
""", """
1. The first use completes the password update.
2. The same link cannot be used again and shows an invalid, expired or already-used state.
""", "Successful first use and rejected second use; execution record."),

"VP-APP-RESET-011": u("Return from Forgot Password to Sign In", "Forgot your password? is open.", """
1. Select Back to sign in.
""", """
1. Hosted Sign In opens without requesting or changing a password, and the user remains signed out.
""", "Hosted Sign In after returning; execution record."),

"VP-APP-RESET-012": u("Reset password format validation", "A valid reset link has opened Update password.", """
1. Enter matching values shorter than 12 characters that otherwise contain a number, lowercase letter, uppercase letter and special character.
2. Repeat with at least 12 characters while omitting, one at a time, the number, lowercase letter, uppercase letter and special character.
3. Enter matching values of at least 12 characters containing every required character type. Do not submit the valid password in this case.
""", """
1. Keycloak shows Invalid password: minimum length 12.
2. Keycloak shows the corresponding numerical digit, lower case, upper case or special character message for each omitted type.
3. No password-format message is shown for the valid-format value.
""", "Each password-format message and valid-format state; execution record."),

"VP-APP-RESET-013": u("Verify credentials after password reset", "QA_RESET_01 has completed a reset. Its new and previous passwords are recorded in controlled Test Data.", """
1. Sign in with the new password.
2. Sign out and return to Hosted Sign In.
3. Attempt sign-in with the previous password.
""", """
1. The new password authenticates successfully.
2. Sign-out returns the user to a signed-out state.
3. The previous password is rejected with Invalid username or password.
""", "Successful new-password sign-in and rejected previous password; execution record."),
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update(rows, run_order=False):
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
    if update(cases) != set(U) or update(run_order, True) != set(U):
        raise RuntimeError("One or more targeted cases were not found")
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
    print(f"Updated {len(U)} Hosted Sign In / Forgot Password cases")


if __name__ == "__main__":
    main()
