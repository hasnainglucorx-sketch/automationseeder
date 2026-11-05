"""
Update Batch 19 (SCAN-001..008) and Batch 20 (SENSOR-ID-001, SENSOR-ID-005)
based on observed screenshots of Step 14/22 scan and manual-entry flow.

Changes per case:
  SCAN-001  – Fix 3-proc/1-exp violation; use verified UI labels (STEP 14/22,
               Scan QR code, Type manually).
  SCAN-002  – Fix 2-proc/1-exp violation; add verified scanner title
               "Scan the sensor QR code".
  SCAN-003  – Fix 2-proc/1-exp violation; confirm button label and scanner title.
  SCAN-004  – Fix 3-proc/1-exp violation; embed exact verified iOS permission
               title and rationale.
  SCAN-005  – Fix 3-proc/1-exp violation; add verified scanner title.
  SCAN-008  – Fix 3-proc/1-exp violation; add verified "Sensor registered" /
               "Sensor details saved" destination (Step 15/22).
  SENSOR-ID-001 – Fix 3-proc/1-exp violation; confirm inline expansion, exact
                  placeholder, helper texts and control labels.
  SENSOR-ID-005 – Fix 5-proc/1-exp violation; embed verified "Confirm Sensor ID"
                  modal body, "Edit Sensor ID" and "Continue" actions.
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/console-update"


def numbered(items):
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))


UPDATES = {
    "VP-APP-SCAN-001": {
        "t": "Scan your sensor screen content and identification actions",
        "pre": (
            "Step 14 of 22 - Scan your sensor is displayed in the normal "
            "sensor-setup/onboarding flow on an approved real device."
        ),
        "proc": numbered([
            "Inspect the complete Scan your sensor screen: step indicator, "
            "sensor-box image, heading, instruction text, identification "
            "actions and navigation controls.",
        ]),
        "exp": numbered([
            "STEP 14 / 22 is displayed. The sensor-box image, Scan your sensor "
            "heading and the instruction Tap the sensor box above to scan the QR "
            "code printed on it. Prefer to type it in? Tap “Type manually”. are "
            "visible. Scan QR code (primary action) and Type manually (secondary "
            "action) are both accessible. Back, voice control and Skip are "
            "available and no content is missing or truncated.",
        ]),
        "ev": "Screenshot of the complete Step 14 / 22 - Scan your sensor screen.",
    },

    "VP-APP-SCAN-002": {
        "t": "Sensor-box image opens the sensor QR scanner",
        "pre": (
            "Step 14 of 22 - Scan your sensor is displayed and camera access "
            "is available or can be requested."
        ),
        "proc": numbered([
            "Tap the sensor-box image shown above the instruction text.",
            "Observe the resulting screen or operating-system camera permission "
            "request.",
        ]),
        "exp": numbered([
            "Tapping the sensor-box image initiates the sensor QR scanning flow "
            "without crash or unrelated navigation.",
            "The Scan the sensor QR code camera scanner is presented with a live "
            "camera feed, a white rounded viewfinder and an X close control, or "
            "the system camera permission dialog is shown if camera access has "
            "not yet been granted.",
        ]),
        "ev": (
            "Step 14 / 22 screenshot and scanner or camera permission screenshot; "
            "execution record."
        ),
    },

    "VP-APP-SCAN-003": {
        "t": "Scan QR code action opens the sensor QR scanner",
        "pre": "Step 14 of 22 - Scan your sensor is displayed.",
        "proc": numbered([
            "Select Scan QR code.",
            "Observe the resulting screen or operating-system camera permission "
            "request.",
        ]),
        "exp": numbered([
            "Selecting Scan QR code initiates the sensor scanning flow without "
            "crash, blank state or unrelated navigation.",
            "The Scan the sensor QR code camera scanner is presented with a live "
            "camera feed, a white rounded viewfinder and an X close control, or "
            "the system camera permission dialog is shown if camera access has "
            "not yet been granted.",
        ]),
        "ev": (
            "Scan your sensor screenshot followed by the scanner or camera "
            "permission screenshot; execution record."
        ),
    },

    "VP-APP-SCAN-004": {
        "t": "Camera permission dialog states the correct purpose for sensor scanning",
        "pre": "Camera permission has not previously been granted or denied for the app.",
        "proc": numbered([
            "Initiate sensor QR scanning for the first time.",
            "Observe the operating-system camera permission dialog that is presented.",
            "Read and record the displayed title and rationale text.",
        ]),
        "exp": numbered([
            "The system camera permission dialog is presented in response to the "
            "scanner initiation without crash or blank state.",
            "The dialog title reads: “CGMx 1” would like to access the Camera.",
            "The rationale reads: CGMx1 uses the camera to scan the QR code on "
            "your sensor when pairing a new transmitter.",
        ]),
        "ev": "Screenshot of the first camera permission dialog; execution record.",
    },

    "VP-APP-SCAN-005": {
        "t": "Granting camera permission immediately opens the sensor QR scanner",
        "pre": (
            "Camera permission has not previously been granted or denied and "
            "the first permission dialog can be triggered."
        ),
        "proc": numbered([
            "Initiate sensor QR scanning.",
            "Select Allow on the operating-system camera permission dialog.",
            "Observe the app immediately after permission is granted.",
        ]),
        "exp": numbered([
            "The operating-system camera permission dialog is presented.",
            "Camera permission is accepted and the app proceeds without an error "
            "or a repeated permission request.",
            "The Scan the sensor QR code camera scanner is displayed with a live "
            "camera feed, white rounded viewfinder and an X close control, without "
            "a Settings recovery prompt.",
        ]),
        "ev": (
            "Camera permission dialog screenshot and working Scan the sensor QR "
            "code scanner screenshot; execution record."
        ),
    },

    "VP-APP-SCAN-008": {
        "t": "Valid sensor QR/GS1 barcode is accepted and advances to Sensor registered",
        "pre": (
            "Approved QA sensor barcode/test packaging known to represent a "
            "valid in-date sensor is available."
        ),
        "proc": numbered([
            "Open the Scan the sensor QR code camera scanner.",
            "Present the approved valid sensor GS1/QR barcode within the viewfinder.",
            "Observe the identification response and the subsequent step.",
        ]),
        "exp": numbered([
            "The scanner reads the barcode without crash or unrelated navigation.",
            "The valid sensor barcode is recognized as the correct product type "
            "and is accepted for the sensor setup flow.",
            "Step 15 of 22 – Sensor registered is displayed showing a green "
            "Sensor details saved confirmation row and a Continue action.",
        ]),
        "ev": (
            "Approved QA barcode asset identifier; scanner and Sensor registered "
            "screenshots; execution record."
        ),
    },

    "VP-APP-SENSOR-ID-001": {
        "t": "Type manually expands inline Sensor ID entry on Scan your sensor",
        "pre": "Step 14 of 22 - Scan your sensor is displayed in the normal new-sensor setup flow.",
        "proc": numbered([
            "Select Type manually and observe the inline expansion.",
            "Inspect the Sensor ID field, helper text and expiry warning displayed "
            "below the field.",
            "Verify the Continue and Hide manual entry controls are both accessible.",
        ]),
        "exp": numbered([
            "The Sensor ID field (placeholder: Enter the sensor ID) expands inline "
            "on the same Scan your sensor screen without navigating to a new page; "
            "the Scan your sensor heading and sensor-box image remain visible above.",
            "Find the sensor ID on the sensor box label. and Before applying the "
            "sensor, check the expiry date on the packaging and make sure the "
            "sensor has not expired. are both displayed below the field.",
            "Continue (primary) and Hide manual entry (secondary) are both "
            "accessible without crash or blank state.",
        ]),
        "ev": (
            "Screenshot of the expanded inline Sensor ID entry area showing the "
            "field, helper texts and controls; execution record."
        ),
    },

    "VP-APP-SENSOR-ID-005": {
        "t": "Confirm Sensor ID modal allows review and correction before installation",
        "pre": (
            "An approved Sensor Test ID from the physical/test packaging is "
            "recorded in Test Data and manual Sensor ID entry is available."
        ),
        "proc": numbered([
            "Enter the approved Sensor Test ID in the Sensor ID field and "
            "select Continue.",
            "Read the Confirm Sensor ID modal without selecting either action.",
            "Compare the displayed Sensor ID value with the approved packaging "
            "reference.",
            "Select Edit Sensor ID and observe the return state.",
            "Re-enter the approved ID, select Continue, then select Continue on "
            "the Confirm Sensor ID modal to confirm.",
        ]),
        "exp": numbered([
            "The Confirm Sensor ID modal appears showing the entered ID, the "
            "message Please check that this ID exactly matches the Sensor ID "
            "printed on your sensor packaging. An accurate Sensor ID is required "
            "for correct sensor identification and recall handling., and the "
            "Edit Sensor ID and Continue actions.",
            "The modal presents the entered ID and the accuracy and "
            "recall-handling requirement without missing or truncated content.",
            "The displayed ID matches the packaging reference; any discrepancy "
            "is recorded as a finding.",
            "Edit Sensor ID dismisses the modal and returns to the Sensor ID "
            "field with the previously entered value retained.",
            "After confirming the ID, the flow advances past the Confirm Sensor "
            "ID modal without crash or unintended navigation.",
        ]),
        "ev": (
            "Entered ID screenshot, Confirm Sensor ID modal screenshot, "
            "packaging/reference comparison, Edit Sensor ID return-state "
            "screenshot and post-confirmation destination screenshot; "
            "execution record."
        ),
    },
}

FULL_MAPPING = {
    "t": "title",
    "req": "requirement",
    "pre": "preconditions",
    "proc": "procedure",
    "exp": "expected",
    "ev": "evidence",
}

TARGET_IDS = set(UPDATES)


def main():
    compact_path = OUT / "PRT-0701-cases.json"
    full_path = OUT / "PRT-0701-run_order.json"
    html_path = OUT / "PRT-0701-Console-source.html"

    compact = json.loads(compact_path.read_text(encoding="utf-8-sig"))
    full = json.loads(full_path.read_text(encoding="utf-8-sig"))

    before_compact_ids = [row["id"] for row in compact]
    before_full_ids = [row["id"] for row in full]

    # Verify all target IDs exist exactly once in both files
    for cid in TARGET_IDS:
        c_count = sum(1 for row in compact if row["id"] == cid)
        f_count = sum(1 for row in full if row["id"] == cid)
        assert c_count == 1, f"Compact: expected 1 of {cid}, found {c_count}"
        assert f_count == 1, f"Run-order: expected 1 of {cid}, found {f_count}"

    # Apply updates
    for cid, fields in UPDATES.items():
        c = next(row for row in compact if row["id"] == cid)
        f = next(row for row in full if row["id"] == cid)
        c.update(fields)
        f.update({FULL_MAPPING[k]: v for k, v in fields.items()})

    # Counts and ID order must be unchanged
    assert [row["id"] for row in compact] == before_compact_ids
    assert [row["id"] for row in full] == before_full_ids
    assert len(compact) == len(before_compact_ids)
    assert len(full) == len(before_full_ids)

    # Re-embed compact array into HTML
    html = html_path.read_text(encoding="utf-8-sig")
    embedded = (
        json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
    )
    html, count = re.subn(
        r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)",
        lambda m: m[1] + embedded + m[2],
        html,
        count=1,
        flags=re.S,
    )
    assert count == 1, "EMBEDDED_CASES replacement failed"

    compact_path.write_text(
        json.dumps(compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    full_path.write_text(
        json.dumps(full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    html_path.write_text(html, encoding="utf-8")
    shutil.copy2(html_path, ROOT / "PRT-0701-Console-source.updated.html")

    print("Updated:", ", ".join(sorted(TARGET_IDS)))
    print("Compact count:", len(compact))
    print("Run-order count:", len(full))


if __name__ == "__main__":
    main()
