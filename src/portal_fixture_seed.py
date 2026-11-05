"""Plan, seed and verify reusable Patient fixtures for PRT-0702.

Credentials stay in .secrets/portal-test-accounts.json. Public output contains
aliases, fixture timestamps and expected values, never emails or passwords.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import statistics
import uuid
from zoneinfo import ZoneInfo

from src.auth import access_token, login
from src.qa_run import matches_payload, paged, stamp
from src.seeder import rpc
from src.storage import write_json


ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = ROOT / ".secrets" / "portal-test-accounts.json"
RUN_DIR = ROOT / "output" / "portal-fixtures"
PUBLIC_MANIFEST = RUN_DIR / "fixture-manifest.json"
TIME_ZONE = ZoneInfo("Europe/London")

ALIASES = {
    "QA-PORTAL-HISTORY-01": "history",
    "QA-PORTAL-SPARSE-01": "sparse",
    "QA-PORTAL-MMOL-01": "mmol",
    "QA-PORTAL-SECONDARY-01": "secondary",
    "QA-PORTAL-TIMEZONE-01": "timezone",
}


def local_time(anchor: dt.datetime, days: int, hour: int = 0, minute: int = 0) -> dt.datetime:
    day = anchor.date() - dt.timedelta(days=days)
    return dt.datetime(day.year, day.month, day.day, hour, minute, tzinfo=TIME_ZONE)


def last_sunday(year: int, month: int) -> dt.date:
    if month == 12:
        first_next = dt.date(year + 1, 1, 1)
    else:
        first_next = dt.date(year, month + 1, 1)
    day = first_next - dt.timedelta(days=1)
    return day - dt.timedelta(days=(day.weekday() + 1) % 7)


def row(index: int, when: dt.datetime, value_mg_dl: int) -> dict:
    return {"index": index, "measure_time": stamp(when),
            "glucose_centi_mg_dl": value_mg_dl * 100}


def history_rows(anchor: dt.datetime) -> list[dict]:
    """Minute readings with deterministic per-hour distributions."""
    periods = [
        (range(1, 7), [50] * 3 + [63] * 6 + [156] * 42 + [240] * 9),
        (range(8, 15), [50] * 5 + [63] * 7 + [120] * 38 + [200] * 10),
        (range(16, 30), [50] * 2 + [63] * 5 + [110] * 46 + [200] * 7),
        (range(31, 90), [50] + [63] * 3 + [140] * 49 + [240] * 7),
    ]
    result, index = [], 1
    for days, values in periods:
        for age in reversed(list(days)):
            for hour in range(24):
                # A deliberate two-hour discontinuity used by portal chart and
                # history cases. D0-9 10:00 through 11:59 has no readings.
                if age == 9 and hour in (10, 11):
                    continue
                for minute, value in enumerate(values):
                    if age == 10 and hour == 3:
                        value = 300
                    elif age == 12 and hour == 15:
                        value = 45
                    result.append(row(index, local_time(anchor, age, hour, minute), value))
                    index += 1
    result.sort(key=lambda item: item["measure_time"])
    for index, item in enumerate(result, 1):
        item["index"] = index
    return result


def fixture(alias: str, anchor: dt.datetime) -> dict:
    kind = ALIASES[alias]
    if kind == "history":
        readings = history_rows(anchor)
    elif kind == "sparse":
        readings = [row(1, local_time(anchor, 3, 12), 154)]
    elif kind == "mmol":
        readings = []
        for minute in range(60):
            readings.append(row(len(readings) + 1, local_time(anchor, 1, 8, minute), 180))
        for minute in range(60):
            readings.append(row(len(readings) + 1, local_time(anchor, 1, 9, minute), 70))
    elif kind == "secondary":
        readings = [row(i + 1, local_time(anchor, 1, 8, i), 200) for i in range(60)]
    else:
        year = anchor.year
        # Fixed UTC instants on both sides of the Europe/London daylight-saving
        # rules. These are kept outside the rolling report account.
        spring = last_sunday(year, 3)
        autumn_year = year if last_sunday(year, 10) < anchor.date() else year - 1
        autumn = last_sunday(autumn_year, 10)
        instants = [
            dt.datetime(year, 1, 15, 23, 30, tzinfo=dt.timezone.utc),
            dt.datetime(year, 7, 15, 23, 30, tzinfo=dt.timezone.utc),
            dt.datetime.combine(spring, dt.time(0, 30), dt.timezone.utc),
            dt.datetime.combine(spring, dt.time(0, 59), dt.timezone.utc),
            dt.datetime.combine(spring, dt.time(1, 0), dt.timezone.utc),
            dt.datetime.combine(spring, dt.time(1, 30), dt.timezone.utc),
            dt.datetime.combine(autumn, dt.time(0, 30), dt.timezone.utc),
            dt.datetime.combine(autumn, dt.time(0, 59), dt.timezone.utc),
            dt.datetime.combine(autumn, dt.time(1, 0), dt.timezone.utc),
            dt.datetime.combine(autumn, dt.time(1, 30), dt.timezone.utc),
        ]
        instants.sort()
        readings = [row(i + 1, when, 100 + i) for i, when in enumerate(instants)]
    return {"alias": alias, "kind": kind, "anchor": anchor.date().isoformat(),
            "time_zone": "Europe/London", "readings": readings}


def percentile(values: list[int], percent: int) -> float:
    """Return a linearly interpolated percentile for an already known fixture."""
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile requires at least one value")
    position = (len(ordered) - 1) * percent / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def hourly_ogp(data: dict, days: int) -> list[dict]:
    anchor = dt.date.fromisoformat(data["anchor"])
    buckets: dict[int, list[int]] = {hour: [] for hour in range(24)}
    for item in data["readings"]:
        when = dt.datetime.fromisoformat(
            item["measure_time"].replace("Z", "+00:00")
        ).astimezone(TIME_ZONE)
        age = (anchor - when.date()).days
        if 0 <= age < days:
            buckets[when.hour].append(item["glucose_centi_mg_dl"] // 100)
    return [
        {
            "hour_local": f"{hour:02d}:00",
            "reading_count": len(values),
            "p10_mg_dl": round(percentile(values, 10), 1),
            "p25_mg_dl": round(percentile(values, 25), 1),
            "median_mg_dl": round(percentile(values, 50), 1),
            "p75_mg_dl": round(percentile(values, 75), 1),
            "p90_mg_dl": round(percentile(values, 90), 1),
        }
        for hour, values in buckets.items()
        if values
    ]


def summary(data: dict) -> dict:
    values = [r["glucose_centi_mg_dl"] // 100 for r in data["readings"]]
    result = {"alias": data["alias"], "kind": data["kind"], "anchor": data["anchor"],
              "time_zone": data["time_zone"], "reading_count": len(values)}
    if values:
        result.update(first_reading=data["readings"][0]["measure_time"],
                      last_reading=data["readings"][-1]["measure_time"],
                      minimum_mg_dl=min(values), maximum_mg_dl=max(values),
                      average_mg_dl=round(statistics.fmean(values), 3),
                      below_70=sum(v < 70 for v in values),
                      in_70_180=sum(70 <= v <= 180 for v in values),
                      above_180=sum(v > 180 for v in values))
    if data["kind"] == "history":
        anchor = dt.date.fromisoformat(data["anchor"])
        result["ranges"] = {}
        for days in (7, 15, 30, 90):
            selected = []
            for item in data["readings"]:
                when = dt.datetime.fromisoformat(item["measure_time"].replace("Z", "+00:00")).astimezone(TIME_ZONE)
                age = (anchor - when.date()).days
                if 0 <= age < days:
                    selected.append(item["glucose_centi_mg_dl"] // 100)
            below = sum(v < 70 for v in selected)
            inside = sum(70 <= v <= 180 for v in selected)
            above = sum(v > 180 for v in selected)
            severe_low = sum(v < 54 for v in selected)
            low = sum(54 <= v < 70 for v in selected)
            high = sum(180 < v < 250 for v in selected)
            urgent_high = sum(v >= 250 for v in selected)
            count = len(selected)
            mean = statistics.fmean(selected)
            population_sd = statistics.pstdev(selected)
            result["ranges"][f"{days}_days"] = {
                "reading_count": count, "minimum_mg_dl": min(selected),
                "maximum_mg_dl": max(selected), "latest_mg_dl": selected[-1],
                "average_mg_dl": round(mean, 3),
                "below_70_count": below, "in_70_180_count": inside, "above_180_count": above,
                "below_70_percent": round(below * 100 / count, 3),
                "in_70_180_percent": round(inside * 100 / count, 3),
                "above_180_percent": round(above * 100 / count, 3),
                "severe_low_percent": round(severe_low * 100 / count, 3),
                "low_percent": round(low * 100 / count, 3),
                "high_percent": round(high * 100 / count, 3),
                "urgent_high_percent": round(urgent_high * 100 / count, 3),
                "device_usage_percent": round(count * 100 / (days * 1440), 3),
                "sd_population_mg_dl": round(population_sd, 3),
                "sd_sample_mg_dl": round(statistics.stdev(selected), 3),
                "cv_population_percent": round(population_sd * 100 / mean, 3),
                "mean_absolute_deviation_mg_dl": round(
                    statistics.fmean(abs(value - mean) for value in selected), 3),
                "gmi_percent": round(3.31 + 0.02392 * mean, 3),
                "adag_estimated_a1c_percent": round((mean + 46.7) / 28.7, 3),
            }
        result["ogp_hourly"] = {
            "method": "Local-hour buckets; linear percentiles P10/P25/P50/P75/P90",
            "7_days": hourly_ogp(data, 7),
            "90_days": hourly_ogp(data, 90),
        }
        result["daily_history_7_days"] = [
            {
                "days_before_anchor": age,
                "first_local": "00:00",
                "last_local": "23:59",
                "minimum_mg_dl": 50,
                "maximum_mg_dl": 240,
            }
            for age in range(6, 0, -1)
        ]
        result["controlled_states"] = {
            "empty_days_before_anchor": [0, 7, 15, 30, 90],
            "gap": {"days_before_anchor": 9, "start_local": "10:00", "end_local": "11:59"},
            "high_marker": {"days_before_anchor": 10, "start_local": "03:00", "minutes": 60, "mg_dl": 300},
            "low_marker": {"days_before_anchor": 12, "start_local": "15:00", "minutes": 60, "mg_dl": 45},
            "calibration": {"days_before_anchor": 3, "local_time": "09:30", "mg_dl": 156},
            "events": [
                {"days_before_anchor": 3, "local_time": "07:00", "type": "sickness"},
                {"days_before_anchor": 2, "local_time": "18:00", "type": "activity"},
                {"days_before_anchor": 1, "local_time": "08:00", "type": "carbohydrate"},
                {"days_before_anchor": 1, "local_time": "08:05", "type": "insulin"},
            ],
        }
    result["patient_profile"] = {
        "display_name": {
            "history": "QA Portal History",
            "sparse": "QA Portal Sparse",
            "mmol": "QA Portal mmol",
            "secondary": "QA Portal Secondary",
            "timezone": "QA Portal Timezone",
        }[data["kind"]],
        "given_names": "QA Portal",
        "family_name": data["kind"].title(),
        "date_of_birth": "1985-04-12",
        "country": "GB",
        "time_zone": "Europe/London",
        "diabetes_type": "TYPE_2",
    }
    if data["kind"] == "sparse":
        result["controlled_readings"] = [
            {"days_before_anchor": 3, "local_time": "12:00", "mg_dl": 154}
        ]
    elif data["kind"] == "mmol":
        result["controlled_readings"] = [
            {"days_before_anchor": 1, "local_period": "08:00-08:59", "mg_dl": 180},
            {"days_before_anchor": 1, "local_period": "09:00-09:59", "mg_dl": 70},
        ]
    elif data["kind"] == "secondary":
        result["controlled_readings"] = [
            {"days_before_anchor": 1, "local_period": "08:00-08:59", "mg_dl": 200}
        ]
    elif data["kind"] == "timezone":
        result["controlled_readings"] = [
            {
                "utc": item["measure_time"],
                "europe_london": dt.datetime.fromisoformat(
                    item["measure_time"].replace("Z", "+00:00")
                ).astimezone(TIME_ZONE).isoformat(),
                "mg_dl": item["glucose_centi_mg_dl"] // 100,
            }
            for item in data["readings"]
        ]
    return result


def load_account(alias: str) -> dict:
    if not ACCOUNTS.exists():
        raise RuntimeError(f"Create {ACCOUNTS} with the account alias, email and password")
    matches = [a for a in json.loads(ACCOUNTS.read_text(encoding="utf-8"))
               if a.get("alias") == alias]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one secret account for {alias}")
    if not matches[0].get("email") or not matches[0].get("password"):
        raise RuntimeError(f"Secret account for {alias} is incomplete")
    return matches[0]


def run_path(alias: str) -> Path:
    return RUN_DIR / (alias.lower() + ".json")


def plan(aliases: list[str]) -> None:
    anchor = dt.datetime.now(TIME_ZONE).replace(hour=0, minute=0, second=0, microsecond=0)
    manifest = {"generated_at": stamp(dt.datetime.now(dt.timezone.utc)),
                "fixture_anchor": anchor.date().isoformat(),
                "fixtures": [summary(fixture(alias, anchor)) for alias in aliases]}
    write_json(PUBLIC_MANIFEST, manifest)
    print(json.dumps(manifest, indent=2))


def refresh_manifest(aliases: list[str]) -> None:
    fixtures = []
    for alias in aliases:
        state_path = run_path(alias)
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            anchor = dt.datetime.combine(
                dt.date.fromisoformat(state["anchor"]), dt.time(), TIME_ZONE
            )
        else:
            anchor = dt.datetime.now(TIME_ZONE).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        fixtures.append(summary(fixture(alias, anchor)))
    history = next((item for item in fixtures if item["alias"] == "QA-PORTAL-HISTORY-01"), None)
    manifest = {
        "generated_at": stamp(dt.datetime.now(dt.timezone.utc)),
        "fixture_anchor": history["anchor"] if history else fixtures[0]["anchor"],
        "fixtures": fixtures,
    }
    write_json(PUBLIC_MANIFEST, manifest)
    print(f"Refreshed {PUBLIC_MANIFEST} with {len(fixtures)} fixtures")


def partition_sessions(readings: list[dict]) -> list[list[dict]]:
    """Keep every generated session inside a 15-calendar-day span."""
    groups: list[list[dict]] = []
    for item in readings:
        when = dt.datetime.fromisoformat(item["measure_time"].replace("Z", "+00:00"))
        if not groups:
            groups.append([])
        first = (dt.datetime.fromisoformat(groups[-1][0]["measure_time"].replace("Z", "+00:00"))
                 if groups[-1] else when)
        if when - first >= dt.timedelta(days=15):
            groups.append([])
        groups[-1].append(item)
    return groups


def authenticated_patient(account: dict, create_missing: bool = False) -> tuple[str, str]:
    login(account["email"], account["password"])
    user = rpc("GetUser", {"name": "users/me"}, access_token())
    patient = user.get("selfPatient")
    if not patient and create_missing:
        patient_id = str(uuid.uuid5(uuid.NAMESPACE_URL, user["name"] + ":portal-fixture"))
        created = rpc("CreatePatient", {
            "patient_id": patient_id,
            "patient": {
                "display_name": "QA Portal Patient",
                "time_zone": "Europe/London",
                "country": "GB",
                "date_of_birth": {"year": 1985, "month": 4, "day": 12},
                "diabetes_type": "TYPE_2",
            },
        }, access_token())
        patient = created.get("name")
    if not patient:
        raise RuntimeError("The account has no self Patient")
    if account.get("user") and account["user"] != user.get("name"):
        raise RuntimeError("The secret account is bound to a different API user")
    if account.get("self_patient") and account["self_patient"] != patient:
        raise RuntimeError("The secret account is bound to a different Patient")
    return user["name"], patient


def prepare(alias: str) -> None:
    account = load_account(alias)
    user, patient = authenticated_patient(account, create_missing=True)
    existing = paged("ListSessions", {"parent": patient}, "sessions")
    if existing:
        raise RuntimeError("Patient already has sessions; use a fresh account for an exact portal fixture")
    anchor = dt.datetime.now(TIME_ZONE).replace(hour=0, minute=0, second=0, microsecond=0)
    data = fixture(alias, anchor)
    run_id = uuid.uuid4()
    sessions = []
    for number, readings in enumerate(partition_sessions(data["readings"]), 1):
        session_id = str(uuid.uuid5(run_id, f"session-{number}"))
        # Reading indexes are scoped to their session.
        session_rows = [dict(item, index=i) for i, item in enumerate(readings, 1)]
        sessions.append({"number": number, "id": session_id, "rows": session_rows,
                         "transmitter": "transmitters/QAWEB" + run_id.hex[:7].upper() + f"{number:02d}",
                         "status": "pending", "batches": []})
    state = {"version": 1, "alias": alias, "user": user, "patient": patient,
             "anchor": data["anchor"], "time_zone": data["time_zone"],
             "run_id": str(run_id), "sessions": sessions, "profile": "pending",
             "events": {}, "calibration": "pending"}
    write_json(run_path(alias), state)
    print(f"Prepared {alias}: {len(data['readings'])} readings in {len(sessions)} sessions")


def load_bound(alias: str) -> tuple[dict, dict]:
    account = load_account(alias)
    user, patient = authenticated_patient(account)
    state = json.loads(run_path(alias).read_text(encoding="utf-8"))
    if state["user"] != user or state["patient"] != patient:
        raise RuntimeError("The checkpoint belongs to a different account")
    return state, account


def execute(alias: str) -> None:
    state, _ = load_bound(alias)
    token = access_token()
    if state["profile"] != "done":
        display = {"history": "QA Portal History", "sparse": "QA Portal Sparse",
                   "mmol": "QA Portal mmol", "secondary": "QA Portal Secondary",
                   "timezone": "QA Portal Timezone"}[ALIASES[alias]]
        rpc("UpdatePatient", {"patient": {"name": state["patient"], "display_name": display,
            "time_zone": state["time_zone"], "country": "GB",
            "date_of_birth": {"year": 1985, "month": 4, "day": 12},
            "diabetes_type": "TYPE_2"},
            "update_mask": "displayName,timeZone,country,dateOfBirth,diabetesType"}, token)
        rpc("UpdatePatientSettings", {"patient_settings": {
            "name": state["patient"] + "/settings", "urgent_low_centi_mg_dl": 5400,
            "low_centi_mg_dl": 7000, "high_centi_mg_dl": 18000,
            "urgent_high_centi_mg_dl": 25000}}, token)
        state["profile"] = "done"
        write_json(run_path(alias), state)
    for session in state["sessions"]:
        if session["status"] == "pending":
            created = rpc("CreateSession", {"parent": state["patient"], "session_id": session["id"],
                "session": {"transmitter": session["transmitter"], "session_index": str(session["number"]),
                    "start_time": session["rows"][0]["measure_time"],
                    "firmware_version": {"major": 3, "minor": 1, "patch": 0,
                        "image_sha256": hashlib.sha256(b"QA portal fixture v1").hexdigest()},
                    "app_build": {"platform": "IOS", "version": "1.0.4"}}}, access_token())
            session["name"] = created["name"]
            session["status"] = "created"
            write_json(run_path(alias), state)
        for offset in range(0, len(session["rows"]), 200):
            key = f"{offset}:{min(200, len(session['rows']) - offset)}"
            if key in session["batches"]:
                continue
            response = rpc("WriteReadings", {"parent": session["name"], "partial_success": False,
                "readings": session["rows"][offset:offset + 200]}, access_token())
            if response.get("failedReadings") or response.get("failed_readings"):
                raise RuntimeError("Backend rejected a reading batch")
            session["batches"].append(key)
            write_json(run_path(alias), state)
            print(f"{alias} session {session['number']}: {min(offset + 200, len(session['rows']))}/{len(session['rows'])}", flush=True)
        if session["status"] != "done":
            current = rpc("GetSession", {"name": session["name"]}, access_token())
            if current.get("state") == "ACTIVE":
                rpc("StopSession", {"name": session["name"]}, access_token())
            session["status"] = "done"
            write_json(run_path(alias), state)
    if alias == "QA-PORTAL-HISTORY-01":
        event_specs = {
            "sickness": (3, 7, {"note": {"text": "QA sickness event", "category": "SICKNESS"}}),
            "activity": (2, 18, {"activity": {"activity_type": "QA walking", "duration_minutes": 30,
                                                   "intensity": "MODERATE"}}),
            "carbohydrate": (1, 8, {"carbohydrate": {"grams": 40}}),
            "insulin": (1, 8, {"insulin": {"units": 2.0, "kind": "BOLUS",
                                                "product": "QA synthetic fixture"}}),
        }
        anchor = dt.datetime.combine(dt.date.fromisoformat(state["anchor"]), dt.time(), TIME_ZONE)
        for name, (age, hour, detail) in event_specs.items():
            if name in state["events"]:
                continue
            minute = 5 if name == "insulin" else 0
            result = rpc("CreateEvent", {"parent": state["patient"],
                "request_id": str(uuid.uuid5(uuid.UUID(state["run_id"]), "event-" + name)),
                "event": {"event_time": stamp(local_time(anchor, age, hour, minute)), **detail}}, access_token())
            state["events"][name] = result.get("name", "created")
            write_json(run_path(alias), state)
        if state["calibration"] == "pending":
            target = local_time(anchor, 3, 9, 30)
            target_utc = target.astimezone(dt.timezone.utc)
            chosen = None
            for session in state["sessions"]:
                start = dt.datetime.fromisoformat(session["rows"][0]["measure_time"].replace("Z", "+00:00"))
                end = dt.datetime.fromisoformat(session["rows"][-1]["measure_time"].replace("Z", "+00:00"))
                if start <= target_utc <= end:
                    chosen = session
                    break
            if not chosen:
                raise RuntimeError("No fixture session contains the calibration time")
            result = rpc("CreateCalibration", {"parent": chosen["name"],
                "calibration_id": str(uuid.uuid5(uuid.UUID(state["run_id"]), "calibration")),
                "calibration": {"reference_glucose_centi_mg_dl": 15600,
                                "measure_time": stamp(target)}}, access_token())
            state["calibration"] = result.get("name", "created")
            write_json(run_path(alias), state)
    verify(alias)


def verify(alias: str) -> None:
    state, _ = load_bound(alias)
    expected = actual = 0
    missing = []
    for session in state["sessions"]:
        rows = paged("QueryReadings", {"parent": session["name"]}, "readings")
        expected += len(session["rows"])
        actual += len(rows)
        found = {item["index"]: item for item in rows}
        missing.extend(f"{session['number']}:{item['index']}" for item in session["rows"]
                       if not matches_payload(item, found.get(item["index"])))
    report = {"alias": alias, "anchor": state["anchor"], "expected_readings": expected,
              "actual_readings": actual, "mismatches": missing, "passed": expected == actual and not missing}
    write_json(RUN_DIR / (alias.lower() + "-verification.json"), report)
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise RuntimeError("Portal fixture verification failed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "manifest", "prepare", "run", "verify"))
    parser.add_argument("--alias", choices=tuple(ALIASES))
    args = parser.parse_args()
    aliases = [args.alias] if args.alias else list(ALIASES)
    if args.command == "plan":
        plan(aliases)
        return
    if args.command == "manifest":
        refresh_manifest(aliases)
        return
    if not args.alias:
        parser.error("--alias is required for API operations")
    if args.command == "prepare":
        prepare(args.alias)
    elif args.command == "run":
        execute(args.alias)
    else:
        verify(args.alias)


if __name__ == "__main__":
    main()
