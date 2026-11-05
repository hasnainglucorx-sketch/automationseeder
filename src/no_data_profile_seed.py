"""Seed a populated 3-day window while keeping the latest 24 hours empty."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import uuid

from src.auth import access_token, login
from src.qa_run import matches_payload, paged, stamp
from src.seeder import rpc
from src.storage import write_json


ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = ROOT / ".secrets" / "test-accounts.json"
FILE = ROOT / "output" / "no-data-profile.json"


def save(state):
    write_json(FILE, state)


def main():
    account = next(item for item in json.loads(ACCOUNTS.read_text(encoding="utf-8"))
                   if item.get("role") == "server-restoration")
    login(account["email"], account["password"])
    token = access_token()
    user = rpc("GetUser", {"name": "users/me"}, token)
    if user.get("name") != account.get("user") or user.get("selfPatient") != account.get("self_patient"):
        raise RuntimeError("Authenticated account does not match saved no-data account")
    patient = user["selfPatient"]
    rpc("UpdatePatient", {"patient": {
        "name": patient, "display_name": "QA No Data Window Patient",
        "time_zone": "Europe/London", "country": "GB",
        "date_of_birth": {"year": 1985, "month": 6, "day": 15}, "diabetes_type": "TYPE_2",
    }, "update_mask": "displayName,timeZone,country,dateOfBirth,diabetesType"}, token)
    rpc("UpdatePatientSettings", {"patient_settings": {
        "name": patient + "/settings", "urgent_low_centi_mg_dl": 5400,
        "low_centi_mg_dl": 7000, "high_centi_mg_dl": 18000,
        "urgent_high_centi_mg_dl": 25000,
    }}, token)

    if FILE.exists():
        state = json.loads(FILE.read_text(encoding="utf-8"))
        if state.get("patient") != patient:
            raise RuntimeError("No-data checkpoint belongs to another patient")
    else:
        now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
        start, end = now - dt.timedelta(hours=48), now - dt.timedelta(hours=30)
        rows = []
        when, index = start, 1
        values = [5200, 8500, 12000, 19500, 23000, 14500]
        while when <= end:
            rows.append({"index": index, "measure_time": stamp(when),
                         "glucose_centi_mg_dl": values[(index - 1) % len(values)]})
            when += dt.timedelta(minutes=5)
            index += 1
        run_id = uuid.uuid4()
        state = {
            "account": account["email"], "patient": patient,
            "created_at": stamp(now), "fixture_start": stamp(start), "fixture_end": stamp(end),
            "readings": rows, "session_id": str(run_id),
            "transmitter": "transmitters/QANODATA" + run_id.hex[:8].upper(),
        }
        save(state)

    if not state.get("session"):
        sessions = paged("ListSessions", {"parent": patient}, "sessions")
        found = [s for s in sessions if s.get("transmitter") == state["transmitter"]]
        if len(found) > 1:
            raise RuntimeError("Ambiguous no-data fixture session")
        session = found[0] if found else rpc("CreateSession", {
            "parent": patient, "session_id": state["session_id"], "session": {
                "transmitter": state["transmitter"], "session_index": "1",
                "start_time": state["fixture_start"],
                "firmware_version": {"major": 3, "minor": 1, "patch": 0,
                    "image_sha256": hashlib.sha256(b"QA no-data fixture").hexdigest()},
                "app_build": {"platform": "IOS", "version": "1.0.4"},
            }}, access_token())
        state["session"] = session["name"]
        save(state)
    existing = paged("QueryReadings", {"parent": state["session"]}, "readings")
    by_index = {row["index"]: row for row in existing}
    pending = [row for row in state["readings"] if row["index"] not in by_index]
    for offset in range(0, len(pending), 200):
        response = rpc("WriteReadings", {"parent": state["session"], "partial_success": False,
            "readings": pending[offset:offset + 200]}, access_token())
        if response.get("failedReadings") or response.get("failed_readings"):
            raise RuntimeError("No-data fixture reading batch was rejected")
    session = rpc("GetSession", {"name": state["session"]}, access_token())
    if session.get("state") == "ACTIVE":
        session = rpc("StopSession", {"name": state["session"]}, access_token())
    actual = paged("QueryReadings", {"parent": state["session"]}, "readings")
    actual_by_index = {row["index"]: row for row in actual}
    missing = [row["index"] for row in state["readings"]
               if not matches_payload(row, actual_by_index.get(row["index"]))]
    now = dt.datetime.now(dt.timezone.utc)
    latest = max(dt.datetime.fromisoformat(row["measureTime"].replace("Z", "+00:00")) for row in actual)
    state["verification"] = {
        "passed": not missing and latest < now - dt.timedelta(hours=24) and session.get("state") == "ENDED",
        "reading_count": len(actual), "missing_indices": missing,
        "latest_reading": stamp(latest), "latest_24_hours_empty": latest < now - dt.timedelta(hours=24),
        "three_day_window_populated": latest >= now - dt.timedelta(days=3),
        "low_readings": sum(row["glucoseCentiMgDl"] < 7000 for row in actual),
        "high_readings": sum(row["glucoseCentiMgDl"] > 18000 for row in actual),
        "session_state": session.get("state"),
    }
    save(state)
    print(json.dumps({"account": state["account"], **state["verification"]}, indent=2))
    if not state["verification"]["passed"] or not state["verification"]["three_day_window_populated"]:
        raise RuntimeError("No-data profile verification failed")


if __name__ == "__main__":
    main()
