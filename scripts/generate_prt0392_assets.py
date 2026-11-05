"""Generate shareable PRT-0392 QA artifacts without credentials."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "prt0392-qa"
REPORT = OUT / "provisioning-report.json"
sys.path.insert(0, str(ROOT / "tmp" / "prt0392-pydeps"))

import qrcode
from PIL import Image, ImageDraw


def gtin14(base13: str) -> str:
    if len(base13) != 13 or not base13.isdigit():
        raise ValueError("GTIN base must contain 13 digits")
    total = sum(int(char) * (3 if (len(base13) - index) % 2 else 1)
                for index, char in enumerate(base13))
    return base13 + str((-total) % 10)


def qr_png(value: str, path: Path, size: int = 900) -> None:
    code = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=4,
    )
    code.add_data(value)
    code.make(fit=True)
    matrix = code.get_matrix()
    modules = len(matrix)
    box = size // modules
    rendered = box * modules
    offset = (size - rendered) // 2
    image = Image.new("1", (size, size), 1)
    draw = ImageDraw.Draw(image)
    for row, values in enumerate(matrix):
        for column, filled in enumerate(values):
            if filled:
                x0 = offset + column * box
                y0 = offset + row * box
                draw.rectangle((x0, y0, x0 + box - 1, y0 + box - 1), fill=0)
    image.save(path, format="PNG", optimize=True)


def write_account_table(report: dict) -> None:
    path = OUT / "account-table.tsv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["Reference ID", "Email", "Region", "Unit", "State"])
        for row in report["accounts"]:
            state = row["state"]
            if row["reference_id"] == "QA-HISTORY-01":
                state += "; 90-day fixture read back"
            elif row["reference_id"] == "QA-NODATA-01":
                state += "; latest 24 hours empty; older 3-day data read back"
            writer.writerow([row["reference_id"], row["email"], row["region"],
                             row["unit"], state])


def write_form_data(report: dict) -> None:
    mail = {row["reference_id"]: row["email"] for row in report["mailbox_only"]}
    content = f"""PRT-0392 FORM DATA

Credentials
QA account password: [ Enter Password ]
QA-REG-PASSWORD: [ Enter Password ]
All real credentials are stored only in the controlled credential file.

REG-FORM-DATA
Valid-format email: {mail['QA-REG-EMAIL-A']}
Invalid-format email: qa.reg@
Password-policy test values: [ Enter Password ]
Given name: Test
Family name: User
Region: United Kingdom

PROFILE-DATA
Date of birth: 15 March 1990
Valid phone: 2025550123
Invalid phone: 12345

RESET-FORM-DATA
Account: use QA-RESET-01 from account-table.tsv
New password: [ Enter Password ]
Invalid-format email: qa.check@
Unregistered email: qa.nouser@example.com
Password-policy test values: [ Enter Password ]

SIGNIN-FORM-DATA
Invalid-format email: qa.check@
Unregistered email: qa.nouser@example.com
Dummy password: [ Enter Password ]
Wrong-password example: [ Enter Password ]

REG-MISMATCH
NEEDS MANUAL STEP: the current hosted registration form did not display a
language/region mismatch warning when Spanish and United Kingdom were selected.
Capture a combination and exact warning from the mobile build if the warning is
implemented there; do not invent the text.

REGISTRATION MAILBOXES
QA-REG-REGION-UK-01: {mail['QA-REG-REGION-UK-01']}
QA-REG-REGION-US-01: {mail['QA-REG-REGION-US-01']}
QA-REG-EMAIL-A: {mail['QA-REG-EMAIL-A']}
QA-REG-EMAIL-B: {mail['QA-REG-EMAIL-B']}
QA-REG-EMAIL-C: {mail['QA-REG-EMAIL-C']}

SENSOR-INVALID-01
SN-NOT-FOUND-PRT0392-01

Emergency contact test number
+44 7700 900001
"""
    (OUT / "form-data.txt").write_text(content, encoding="utf-8")


def write_transmitters() -> None:
    text = """PRT-0392 TRANSMITTER TEST DATA

Assigned Modus-D-Pocket-v3 for QA-MAIN-01
ID: [ Enter ID ]
GS1 or PIN: [ Enter value ]
State: NEEDS MANUAL STEP - record the physical simulator asset from PROCESS.

Unregistered transmitter
ID: [ Enter ID ]
GS1 or PIN: [ Enter value ]
State: NEEDS MANUAL STEP - requires a real first-registration transmitter.

TX-RECALLED-01
ID: [ Enter ID ]
GS1 or PIN: [ Enter value ]
State: NEEDS MANUAL STEP - GlobalService admin recall creation is unavailable.

TX-DELETE-B-01
ID: [ Enter ID ]
GS1 or PIN: [ Enter value ]
State: NEEDS MANUAL STEP - pair a physical transmitter to QA-DELETE-01.

Transmitter locked to Account A
ID: [ Enter ID ]
GS1 or PIN: [ Enter value ]
State: NEEDS MANUAL STEP - requires physical registration to QA-MAIN-01.
"""
    (OUT / "transmitters.txt").write_text(text, encoding="utf-8")


def write_checklist() -> None:
    text = """# PRT-0392 QA Preparation Checklist

- DONE - Twelve requested account identities were registered in the QA realm.
- DONE - Every account and unused registration address has a readable mailbox; access was rechecked after provisioning.
- DONE - Verified accounts pass QA sign-in and dev-backend identity checks.
- DONE - QA-UNVERIFIED-01 remains intentionally unverified.
- DONE - QA-FRESH-01 is verified and has no backend patient or onboarding state.
- DONE - QA-HISTORY-01 is PK/Asia-Karachi with 90 days of five-minute data, the exact 1 October 2026 07:22 PKT 125.45 mg/dL reading, all four bands, a recent full-hour gap, at least 19 manual events, and exactly 14 calibrations; remote read-back passed.
- DONE - QA-NODATA-01 has no readings in the latest 24 hours and has data inside the three-day window; remote read-back passed.
- DONE - QA-LOGIN-US-01 is a verified United States mg/dL account.
- DONE - QA-RESET-01 and both QA-EMAIL-CHANGE-01 inboxes are accessible.
- DONE - Fresh unused inboxes exist for both per-run regional registrations and QA-REG-EMAIL-A/B/C.
- DONE - High-contrast 900 x 900 PNG QR files were generated for SENSOR-VALID-01, SENSOR-EXPIRED-01 and BARCODE-WRONGTYPE-01.
- DONE - Shareable account table, form data, transmitter list, seed state, and refresh scripts were generated with no passwords.

- NEEDS MANUAL STEP - QA-MAIN-01 needs the physical Modus-D-Pocket-v3, its asset ID, notifications/critical-alert permissions, transmitter ownership, and a real live CGM session.
- NEEDS MANUAL STEP - Meal subtype labels (Breakfast, Lunch, Dinner, Snack) must be confirmed/entered through the app; the available backend event contract stores carbohydrate values but has no meal-subtype field.
- NEEDS MANUAL STEP - Sharing pending/active relationships, invitations, OTP generation, invalid OTP and expired OTP require the app or a sharing admin interface; they are not exposed by the available patient API contract.
- NEEDS MANUAL STEP - SENSOR-RECALLED-01 and TX-RECALLED-01 need active QA recall records created by an authorized GlobalService administrator.
- NEEDS MANUAL STEP - SENSOR-INVALID-01 must be confirmed absent from the QA sensor registry before execution.
- NEEDS MANUAL STEP - BARCODE-WRONGTYPE-01 is a syntactically valid transmitter-type GS1 QR; confirm the product GTIN/identifier against the approved physical QA asset before use.
- NEEDS MANUAL STEP - All transmitter IDs, GS1 values/PINs, device ownership/locking, and TX-DELETE-B-01 require physical test hardware.
- NEEDS MANUAL STEP - CLINIC-CODE-VALID-01 and its expected clinic name require an authorized QA clinic setup; no clinic code was invented.
- NEEDS MANUAL STEP - Verification-link and reset-link lifespans require Keycloak realm-admin access to Realm Settings > Tokens. They were not guessed.
- NEEDS MANUAL STEP - REG-MISMATCH warning needs capture from the mobile build; the hosted registration form did not show the warning for Spanish with United Kingdom.
- NEEDS MANUAL STEP - A second physical phone, SIM, push-notification certificate, OS permission prompts, and simulator SW1/SW2/SW3 actions remain manual.
"""
    (OUT / "checklist.md").write_text(text, encoding="utf-8")


def write_readme(wrong_gtin: str) -> None:
    text = f"""# PRT-0392 QA Test Data Package

Generated for the non-production QA realm and dev backend only.

## Files

- account-table.tsv - section 9.3 account mapping, emails only
- form-data.txt - dummy form values and placeholders, no credentials
- SENSOR-VALID-01.png - QR payload 01095060001343521730123121SN0001234
- SENSOR-EXPIRED-01.png - QR payload 01095060001343521722123121SN0009999
- BARCODE-WRONGTYPE-01.png - transmitter-type GS1 QR payload 01{wrong_gtin}21TXQAWRONG01
- SENSOR-INVALID-01.txt - controlled nonexistent identifier candidate
- transmitters.txt - required transmitter list and manual placeholders
- seed-state.json - remote seed/read-back status, no credentials
- provisioning-report.json - QA account/mailbox state, no credentials
- checklist.md - DONE and NEEDS MANUAL STEP status

## Refresh rolling seed data

From the workspace root in PowerShell:

    .\\scripts\\refresh-prt0392-seed.ps1

The script refreshes the rolling history/no-data fixtures and then verifies all
mailboxes, account logins, bindings, and remote fixture invariants. Credentials
remain only in .secrets/prt0392-qa.json.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    wrong_gtin = gtin14("0950600013436")
    qr_png("01095060001343521730123121SN0001234", OUT / "SENSOR-VALID-01.png")
    qr_png("01095060001343521722123121SN0009999", OUT / "SENSOR-EXPIRED-01.png")
    qr_png(f"01{wrong_gtin}21TXQAWRONG01", OUT / "BARCODE-WRONGTYPE-01.png")
    (OUT / "SENSOR-INVALID-01.txt").write_text(
        "SN-NOT-FOUND-PRT0392-01\n", encoding="utf-8"
    )
    write_account_table(report)
    write_form_data(report)
    write_transmitters()
    write_checklist()
    write_readme(wrong_gtin)
    print(f"Generated shareable PRT-0392 assets in {OUT}")


if __name__ == "__main__":
    main()
