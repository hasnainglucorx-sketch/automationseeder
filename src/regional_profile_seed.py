"""Complete and verify the backend profile for the regional QA account."""
import argparse
import json
from pathlib import Path

from src.auth import access_token, login
from src.seeder import rpc


ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = ROOT / ".secrets" / "test-accounts.json"
REPORT = ROOT / "output" / "regional-profile-verification.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", default="regional-configuration")
    args = parser.parse_args()
    accounts = json.loads(ACCOUNTS.read_text(encoding="utf-8"))
    matches = [item for item in accounts if item.get("role") == args.role]
    if len(matches) != 1:
        raise RuntimeError("Expected exactly one saved regional account")
    account = matches[0]
    login(account["email"], account["password"])
    token = access_token()
    user = rpc("GetUser", {"name": "users/me"}, token)
    # This issuer currently omits the optional email/display fields from GetUser.
    # Bind to the immutable API user and self-patient captured at registration.
    if user.get("name") != account.get("user"):
        raise RuntimeError("Authenticated API user does not match saved regional account")
    patient = user.get("selfPatient")
    if not patient or patient != account.get("self_patient"):
        raise RuntimeError("Authenticated account does not match the saved patient")

    desired_patient = {
        "name": patient,
        "display_name": "QA Regional US Patient",
        "time_zone": "America/New_York",
        "date_of_birth": {"year": 1985, "month": 6, "day": 15},
        "diabetes_type": "TYPE_2",
        "country": "US",
    }
    rpc("UpdatePatient", {
        "patient": desired_patient,
        "update_mask": "displayName,timeZone,dateOfBirth,diabetesType,country",
    }, token)
    rpc("UpdatePatientSettings", {
        "patient_settings": {
            "name": patient + "/settings",
            "urgent_low_centi_mg_dl": 5400,
            "low_centi_mg_dl": 7000,
            "high_centi_mg_dl": 18000,
            "urgent_high_centi_mg_dl": 25000,
        },
    }, token)
    actual_patient = rpc("GetPatient", {"name": patient}, access_token())
    actual_settings = rpc("GetPatientSettings", {"name": patient + "/settings"}, access_token())
    patient_ok = all(actual_patient.get(key) == value for key, value in {
        "displayName": desired_patient["display_name"],
        "timeZone": desired_patient["time_zone"],
        "dateOfBirth": desired_patient["date_of_birth"],
        "diabetesType": desired_patient["diabetes_type"],
        "country": desired_patient["country"],
    }.items())
    settings_ok = all(actual_settings.get(key) == value for key, value in {
        "urgentLowCentiMgDl": 5400,
        "lowCentiMgDl": 7000,
        "highCentiMgDl": 18000,
        "urgentHighCentiMgDl": 25000,
    }.items())
    report = {
        "account": account["email"],
        "role": args.role,
        "registered_region": "US",
        "patient_country": actual_patient.get("country"),
        "patient_time_zone": actual_patient.get("timeZone"),
        "expected_glucose_unit": "mg/dL",
        "unit_basis": "US registration region; portal previously observed in mg/dL",
        "expected_language_or_fallback": "English",
        "language_check": "Device-only: verify Settings > Language after sign-in",
        "thresholds_centi_mg_dl": {
            "urgent_low": actual_settings.get("urgentLowCentiMgDl"),
            "low": actual_settings.get("lowCentiMgDl"),
            "high": actual_settings.get("highCentiMgDl"),
            "urgent_high": actual_settings.get("urgentHighCentiMgDl"),
        },
        "backend_profile_verified": patient_ok and settings_ok,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["backend_profile_verified"]:
        raise RuntimeError("Regional backend profile verification failed")


if __name__ == "__main__":
    main()
