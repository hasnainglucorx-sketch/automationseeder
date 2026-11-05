import datetime as dt
import unittest
from zoneinfo import ZoneInfo

from src.portal_fixture_seed import fixture, partition_sessions, summary


class PortalFixtureTests(unittest.TestCase):
    def setUp(self):
        self.anchor = dt.datetime(2026, 10, 7, tzinfo=ZoneInfo("Europe/London"))

    def test_history_fixture_has_controlled_boundaries_and_gap(self):
        data = fixture("QA-PORTAL-HISTORY-01", self.anchor)
        rows = data["readings"]
        self.assertEqual(123720, len(rows))
        self.assertEqual(list(range(1, len(rows) + 1)), [r["index"] for r in rows])
        local = [dt.datetime.fromisoformat(r["measure_time"].replace("Z", "+00:00")).astimezone(
            ZoneInfo("Europe/London")) for r in rows]
        ages = {(self.anchor.date() - value.date()).days for value in local}
        self.assertTrue({7, 15, 30, 90, 0}.isdisjoint(ages))
        self.assertFalse(any((self.anchor.date() - value.date()).days == 9 and value.hour in (10, 11)
                             for value in local))
        markers = {(value.date(), value.hour): row["glucose_centi_mg_dl"]
                   for value, row in zip(local, rows) if value.minute == 0}
        self.assertEqual(30000, markers[(self.anchor.date() - dt.timedelta(days=10), 3)])
        self.assertEqual(4500, markers[(self.anchor.date() - dt.timedelta(days=12), 15)])

    def test_sessions_do_not_span_fifteen_days(self):
        groups = partition_sessions(fixture("QA-PORTAL-HISTORY-01", self.anchor)["readings"])
        self.assertGreater(len(groups), 1)
        for group in groups:
            first = dt.datetime.fromisoformat(group[0]["measure_time"].replace("Z", "+00:00"))
            last = dt.datetime.fromisoformat(group[-1]["measure_time"].replace("Z", "+00:00"))
            self.assertLess(last - first, dt.timedelta(days=15))

    def test_small_fixture_counts(self):
        self.assertEqual(1, len(fixture("QA-PORTAL-SPARSE-01", self.anchor)["readings"]))
        self.assertEqual(120, len(fixture("QA-PORTAL-MMOL-01", self.anchor)["readings"]))
        self.assertEqual(60, len(fixture("QA-PORTAL-SECONDARY-01", self.anchor)["readings"]))
        self.assertEqual(10, len(fixture("QA-PORTAL-TIMEZONE-01", self.anchor)["readings"]))

    def test_manifest_contains_executable_ogp_and_history_values(self):
        result = summary(fixture("QA-PORTAL-HISTORY-01", self.anchor))
        self.assertEqual(24, len(result["ogp_hourly"]["7_days"]))
        midnight = result["ogp_hourly"]["7_days"][0]
        self.assertEqual("00:00", midnight["hour_local"])
        self.assertEqual(156.0, midnight["median_mg_dl"])
        self.assertEqual(6, len(result["daily_history_7_days"]))
        self.assertEqual("1985-04-12", result["patient_profile"]["date_of_birth"])


if __name__ == "__main__":
    unittest.main()
