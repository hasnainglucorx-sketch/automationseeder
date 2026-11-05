"""Verify that all QA fixtures coexist on the bound main account."""
import datetime as dt
import json
from pathlib import Path

from src.qa_run import identity, matches_payload, paged


ROOT = Path(__file__).resolve().parents[1]


def parse(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def main():
    run = json.loads((ROOT / "output" / "qa-run.json").read_text(encoding="utf-8"))
    gap = json.loads((ROOT / "output" / "recent-gap-verification.json").read_text(encoding="utf-8"))
    boundary = json.loads((ROOT / "output" / "boundary-90-days.json").read_text(encoding="utf-8"))
    user = identity(run["email"])
    if user.get("selfPatient") != run["patient"]:
        raise RuntimeError("Authenticated account does not match fixture patient")

    primary = paged("QueryReadings", {"parent": run["session"]}, "readings")
    primary_by_index = {row["index"]: row for row in primary}
    original_missing = [row["index"] for row in run["data"]["readings"]
                        if not matches_payload(row, primary_by_index.get(row["index"]))]
    gap_start, gap_end = parse(gap["gap_start_utc"]), parse(gap["gap_end_utc"])
    readings_in_gap = [row for row in primary if gap_start <= parse(row["measureTime"]) <= gap_end]
    recent_start, recent_end = parse(gap["fixture_start_utc"]), parse(gap["fixture_end_utc"])
    recent = [row for row in primary if recent_start <= parse(row["measureTime"]) <= recent_end]

    events = paged("ListEvents", {"parent": run["patient"]}, "events")
    calibrations = paged("ListCalibrations", {"parent": run["session"]}, "calibrations")
    sessions = paged("ListSessions", {"parent": run["patient"]}, "sessions")
    boundary_rows = paged("QueryReadings", {"parent": boundary["session"]}, "readings")
    boundary_by_index = {row["index"]: row for row in boundary_rows}
    boundary_missing = [row["index"] for row in boundary["readings"]
                        if not matches_payload(row, boundary_by_index.get(row["index"]))]
    boundary_session = next((s for s in sessions if s.get("name") == boundary["session"]), None)

    checks = {
        "account_matches": True,
        "original_14_day_readings_preserved": not original_missing,
        "original_expected_count": len(run["data"]["readings"]),
        "primary_session_total_readings": len(primary),
        "recent_fixture_readings": len(recent),
        "recent_fixture_expected": gap["expected_readings"],
        "recent_gap_is_empty": not readings_in_gap,
        "events_preserved": len(events) >= 84,
        "events_count": len(events),
        "calibrations_preserved": len(calibrations) >= 14,
        "calibrations_count": len(calibrations),
        "boundary_readings_match": len(boundary_rows) == 3 and not boundary_missing,
        "boundary_session_ended": boundary_session is not None and boundary_session.get("state") == "ENDED",
        "sessions_count": len(sessions),
    }
    checks["passed"] = all([
        checks["original_14_day_readings_preserved"],
        checks["recent_fixture_readings"] == checks["recent_fixture_expected"],
        checks["recent_gap_is_empty"], checks["events_preserved"],
        checks["calibrations_preserved"], checks["boundary_readings_match"],
        checks["boundary_session_ended"],
    ])
    output = ROOT / "output" / "account-coverage-verification.json"
    output.write_text(json.dumps(checks, indent=2), encoding="utf-8")
    print(json.dumps(checks, indent=2))
    if not checks["passed"]:
        raise RuntimeError("Account coverage verification failed")


if __name__ == "__main__":
    main()
