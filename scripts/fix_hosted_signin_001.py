"""Correct VP-APP-HOSTED-SIGNIN-001 and keep all console sources synchronized."""

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"
CASE_ID = "VP-APP-HOSTED-SIGNIN-001"

TITLE = "Hosted Sign In page content"
REQUIREMENT_COMPACT = "DO-806 / DI-786; DO-672 / DI-284"
PRECONDITION = (
    "The user is signed out, internet is available, and the native Sign In screen is displayed."
)
PROCEDURE = (
    "1. Select Sign in on the native Sign In screen and wait for the hosted page to open.\n"
    "2. Inspect the hosted page branding, heading, instructions and credential fields without entering data.\n"
    "3. Inspect the actions and footer shown below the credential fields.\n"
    "4. Open the language selector, inspect all available languages, then close it without changing the language."
)
EXPECTED = (
    "1. The hosted GlucoRx Sign In page opens once without a blank page, error or unrelated destination.\n"
    "2. The page shows GlucoRx branding, the Sign in heading and Welcome back. Use your GlucoRx account to continue. "
    "Email and Password are marked required; Email shows you@example.com; Password has a visibility control; and "
    "Forgot password? is available.\n"
    "3. Sign in, New to GlucoRx? Create an account, © 2026 GlucoRx Ltd and the language control are visible and "
    "readable, with no missing, duplicated, clipped or corrupted content.\n"
    "4. The language selector offers English (UK), English (US), Cymraeg, العربية and Español. Closing it without a "
    "selection leaves the page language unchanged."
)
EVIDENCE = "Native Sign In screen, complete Hosted Sign In page and expanded language list; execution record."


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main():
    cases_path = OUT / "PRT-0701-cases.json"
    run_path = OUT / "PRT-0701-run_order.json"
    html_path = OUT / "PRT-0701-Console-source.html"

    cases = load(cases_path)
    run_order = load(run_path)

    compact = next((row for row in cases if row.get("id") == CASE_ID), None)
    full = next((row for row in run_order if row.get("id") == CASE_ID), None)
    if compact is None or full is None:
        raise RuntimeError(f"Missing {CASE_ID}")

    compact.update(
        t=TITLE,
        req=REQUIREMENT_COMPACT,
        pre=PRECONDITION,
        proc=PROCEDURE,
        exp=EXPECTED,
        ev=EVIDENCE,
    )
    full.update(
        title=TITLE,
        preconditions=PRECONDITION,
        procedure=PROCEDURE,
        expected=EXPECTED,
        evidence=EVIDENCE,
    )

    save(cases_path, cases)
    save(run_path, run_order)

    html = html_path.read_text(encoding="utf-8")
    embedded = json.dumps(cases, ensure_ascii=False, separators=(",", ":")).replace(
        "<", "\\u003c"
    )
    pattern = re.compile(
        r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)", re.DOTALL
    )
    html, count = pattern.subn(
        lambda match: match.group(1) + embedded + match.group(2), html, count=1
    )
    if count != 1:
        raise RuntimeError("Embedded console case list was not found")

    html_path.write_text(html, encoding="utf-8")
    shutil.copy2(html_path, ROOT / "PRT-0701-Console-source.updated.html")
    print(f"Updated {CASE_ID}")


if __name__ == "__main__":
    main()
