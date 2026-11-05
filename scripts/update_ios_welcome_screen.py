"""Update Welcome cases from the 1 Oct 2026 iOS Welcome reference screenshot."""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"

UPDATES = {
    "VP-APP-WELCOME-001": {
        "title": "Welcome screen content",
        "pre": "The Welcome screen is displayed and the user is signed out.",
        "procedure": (
            "1. Inspect the complete Welcome screen from top to bottom.\n"
            "2. Compare the product image, text, icons, privacy message and actions with the approved iOS Welcome reference."
        ),
        "expected": (
            "1. The screen shows the CGMx 1 product image and the heading See your glucose, clearly.\n"
            "2. The supporting text reads: Real-time readings, smart alerts, and sharing that helps you stay in range — every day.\n"
            "3. The three benefits read: Live readings every few minutes; Alerts you can act on — even on Silent; Share with the people who matter. Each benefit has its corresponding icon.\n"
            "4. The screen shows Your data is private and secure. with the Learn more link.\n"
            "5. Get started and Sign in are visible and available. No content is missing, duplicated, clipped, overlapping or corrupted."
        ),
        "evidence": "Full Welcome screenshot compared with IMG_6417.PNG; execution record.",
    },
    "VP-APP-WELCOME-002": {
        "title": "Welcome privacy information link",
        "pre": "The Welcome screen is displayed and the user is signed out.",
        "procedure": (
            "1. Select Learn more beside Your data is private and secure.\n"
            "2. Observe the destination.\n"
            "3. Return to the app using the available back or close action."
        ),
        "expected": (
            "1. Learn more responds once.\n"
            "2. The intended privacy or data-security information opens without a blank page, unrelated destination or error.\n"
            "3. Returning restores the Welcome screen without starting registration or authentication."
        ),
        "evidence": "Learn more destination and returned Welcome screen; execution record.",
    },
    "VP-APP-WELCOME-003": {
        "title": "Android Back from Welcome",
        "pre": "Android only. The Welcome screen is displayed and the user is signed out.",
        "procedure": (
            "1. Press the Android system Back control once.\n"
            "2. Open CGMx 1 again."
        ),
        "expected": (
            "1. CGMx 1 closes or moves to the background without opening an earlier app screen or starting an account action.\n"
            "2. CGMx 1 returns to a usable Welcome screen without a blank screen, crash or duplicate navigation."
        ),
        "evidence": "Android Back behavior and reopened Welcome screen; execution record.",
    },
    "VP-APP-WELCOME-004": {
        "title": "Get started navigation",
        "pre": "The Welcome screen is displayed and the user is signed out.",
        "procedure": "1. Select Get started once.",
        "expected": "1. The native Create Account screen opens once without an intermediate Sign In screen, blank state, crash or duplicate destination.",
        "evidence": "Welcome and native Create Account screens; execution record.",
    },
    "VP-APP-WELCOME-005": {
        "title": "Sign in navigation",
        "pre": "The Welcome screen is displayed and the user is signed out.",
        "procedure": "1. Select Sign in once.",
        "expected": "1. The native Sign In screen opens once without a blank state, crash, unrelated destination or duplicate navigation.",
        "evidence": "Welcome and native Sign In screens; execution record.",
    },
}

RUN_ONLY = {
    "VP-APP-WELCOME-NAV-004": {
        "title": "Welcome background, resume and Android Back",
        "pre": "The Welcome screen is displayed and the user is signed out.",
        "procedure": (
            "1. Send CGMx 1 to the background, wait 10 seconds and reopen it.\n"
            "2. Android only: press the system Back control once, then open CGMx 1 again."
        ),
        "expected": (
            "1. The Welcome screen returns in a usable state without starting registration or authentication.\n"
            "2. Android Back closes or backgrounds the app without opening an earlier screen; reopening returns to Welcome without a blank screen, crash or duplicate screen."
        ),
        "evidence": "Background/resume and Android Back recording; execution record.",
    },
    "VP-APP-WELCOME-NAV-003": {
        "title": "Repeated Get started tap prevention",
        "pre": "The Welcome screen is displayed and the user is signed out.",
        "procedure": (
            "1. Select Get started three times quickly.\n"
            "2. Use the native Create Account back action once."
        ),
        "expected": (
            "1. The native Create Account screen opens once without flicker or stacked screens.\n"
            "2. One back action returns to Welcome, proving that only one destination was opened."
        ),
        "evidence": "Rapid-tap navigation recording; execution record.",
    },
    "VP-APP-WELCOME-NAV-001": {
        "title": "Get started opens Create Account",
        "pre": "The Welcome screen is displayed and the user is signed out.",
        "procedure": "1. Select Get started once.",
        "expected": "1. The native Create Account screen opens directly without a Sign In screen, blank screen, crash or duplicate destination.",
        "evidence": "Welcome-to-Create-Account navigation; execution record.",
    },
    "VP-APP-WELCOME-NAV-002": {
        "title": "Sign in opens native Sign In",
        "pre": "The Welcome screen is displayed and the user is signed out.",
        "procedure": "1. Select Sign in once.",
        "expected": "1. The native Sign In screen opens directly without a blank screen, crash, unrelated destination or duplicate navigation.",
        "evidence": "Welcome-to-Sign-In navigation; execution record.",
    },
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def apply_case(row, value, run_order=False):
    if run_order:
        row.update(title=value["title"], preconditions=value["pre"], procedure=value["procedure"],
                   expected=value["expected"], evidence=value["evidence"])
    else:
        row.update(t=value["title"], pre=value["pre"], proc=value["procedure"],
                   exp=value["expected"], ev=value["evidence"])


def main():
    cases_path = OUT / "PRT-0701-cases.json"
    run_path = OUT / "PRT-0701-run_order.json"
    html_path = OUT / "PRT-0701-Console-source.html"
    cases, run_order = load(cases_path), load(run_path)

    found_cases = set()
    for row in cases:
        if row.get("id") in UPDATES:
            apply_case(row, UPDATES[row["id"]])
            found_cases.add(row["id"])
    if found_cases != set(UPDATES):
        raise RuntimeError(f"Missing Welcome cases: {sorted(set(UPDATES)-found_cases)}")

    run_updates = {**UPDATES, **RUN_ONLY}
    found_run = set()
    for row in run_order:
        if row.get("id") in run_updates:
            apply_case(row, run_updates[row["id"]], run_order=True)
            found_run.add(row["id"])
    expected_run = {"VP-APP-WELCOME-001", "VP-APP-WELCOME-002", *RUN_ONLY.keys()}
    if found_run != expected_run:
        raise RuntimeError(f"Unexpected Welcome run-order coverage: {sorted(found_run ^ expected_run)}")

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
    print("Updated current Welcome content, privacy link and navigation cases")


if __name__ == "__main__":
    main()
