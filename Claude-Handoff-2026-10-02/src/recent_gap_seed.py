"""Seed and verify a recent 24-hour glucose fixture with a 45-minute gap."""
import argparse
import datetime as dt
import json
import math
from pathlib import Path

from src.auth import access_token
from src.qa_run import identity, paged
from src.seeder import rpc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "output" / "qa-run.json"
DEFAULT_REPORT = ROOT / "output" / "recent-gap-verification.json"


def iso(value):
    return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def build_fixture(end, gap_minutes=45):
    end = end.astimezone(dt.timezone.utc).replace(second=0, microsecond=0)
    start = end - dt.timedelta(hours=23, minutes=59)
    gap_start = end - dt.timedelta(hours=6)
    gap_end = gap_start + dt.timedelta(minutes=gap_minutes - 1)
    rows = []
    when = start
    minute_offset = 0
    while when <= end:
        if not gap_start <= when <= gap_end:
            minute_of_day = when.hour * 60 + when.minute
            glucose = round((115 + 18 * math.sin(minute_of_day / 1440 * 2 * math.pi)) * 100)
            rows.append({
                # The service contract accepts session indexes only through 21600.
                # The original 14-day fixture occupies 1..20160, leaving exactly
                # 1440 indexes for this recent 24-hour fixture.
                "index": 20_161 + minute_offset,
                "measure_time": iso(when),
                "glucose_centi_mg_dl": glucose,
            })
        when += dt.timedelta(minutes=1)
        minute_offset += 1
    return rows, gap_start, gap_end


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--run-file", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    state = json.loads(args.run_file.read_text(encoding="utf-8"))
    if state.get("email", "").casefold() != args.email.casefold():
        raise RuntimeError("Run file is bound to a different email")
    user = identity(args.email)
    if user.get("selfPatient") != state.get("patient"):
        raise RuntimeError("Authenticated account does not match the run patient")

    end = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=10)
    rows, gap_start, gap_end = build_fixture(end)
    current = paged("QueryReadings", {"parent": state["session"]}, "readings")
    existing = {row.get("index"): row for row in current}
    collisions = [row["index"] for row in rows if row["index"] in existing and (
        existing[row["index"]].get("measureTime") != row["measure_time"] or
        existing[row["index"]].get("glucoseCentiMgDl") != row["glucose_centi_mg_dl"]
    )]
    if collisions:
        raise RuntimeError(f"Fixture indexes already contain different readings: {collisions[:10]}")
    pending = [row for row in rows if row["index"] not in existing]
    for offset in range(0, len(pending), 200):
        batch = pending[offset:offset + 200]
        result = rpc("WriteReadings", {
            "parent": state["session"],
            "partial_success": False,
            "readings": batch,
        }, access_token())
        if result.get("failedReadings") or result.get("failed_readings"):
            raise RuntimeError("Backend rejected one or more readings")
        print(f"Accepted {min(offset + len(batch), len(pending))}/{len(pending)} new readings", flush=True)

    verified = paged("QueryReadings", {"parent": state["session"]}, "readings")
    by_index = {row.get("index"): row for row in verified}
    missing = [row["index"] for row in rows if row["index"] not in by_index]
    in_gap = [row for row in verified if row.get("measureTime") and
              gap_start <= dt.datetime.fromisoformat(row["measureTime"].replace("Z", "+00:00")) <= gap_end]
    before_time = gap_start - dt.timedelta(minutes=1)
    after_time = gap_end + dt.timedelta(minutes=1)
    before = next((row for row in rows if row["measure_time"] == iso(before_time)), None)
    after = next((row for row in rows if row["measure_time"] == iso(after_time)), None)
    report = {
        "account": args.email,
        "patient": state["patient"],
        "session": state["session"],
        "report_view": "Day",
        "report_filter": "24 Hours",
        "fixture_start_utc": iso(rows[0] and dt.datetime.fromisoformat(rows[0]["measure_time"].replace("Z", "+00:00"))),
        "fixture_end_utc": iso(end.replace(second=0, microsecond=0)),
        "gap_start_utc": iso(gap_start.replace(second=0, microsecond=0)),
        "gap_end_utc": iso(gap_end.replace(second=0, microsecond=0)),
        "gap_minutes_without_readings": 45,
        "reading_before_gap": before,
        "reading_after_gap": after,
        "expected_readings": len(rows),
        "new_readings_written": len(pending),
        "missing_expected_indices": missing,
        "readings_found_inside_gap": len(in_gap),
        "verified": not missing and not in_gap and before is not None and after is not None,
        "classification": "Synthetic controlled test data; Quality/Test Engineering approval required by VP-APP-REPORT-DAY-004.",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["verified"]:
        raise RuntimeError("Recent gap verification failed")


if __name__ == "__main__":
    main()
