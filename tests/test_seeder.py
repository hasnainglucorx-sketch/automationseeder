import datetime as dt
import unittest
from src.seeder import generate, methods


class GenerationTests(unittest.TestCase):
    def test_repeatable_complete_scenario(self):
        end = dt.datetime(2026, 9, 29, 8, 0, tzinfo=dt.timezone.utc)
        data = generate(end)
        self.assertEqual(data, generate(end))
        rows = data['readings']
        self.assertEqual(len(rows), 20160 - 45)
        self.assertEqual(len({r['index'] for r in rows}), len(rows))
        times = [dt.datetime.fromisoformat(r['measure_time'].replace('Z', '+00:00')) for r in rows]
        self.assertEqual(times[-1], end)
        self.assertEqual(sum((b-a).total_seconds() == 2760 for a,b in zip(times,times[1:])), 1)
        self.assertEqual(sum(r['glucose_centi_mg_dl'] <= 5400 for r in rows), 60)

    def test_requires_timezone_and_bounded_duration(self):
        with self.assertRaises(ValueError):
            generate(dt.datetime(2026, 9, 29))
        with self.assertRaises(ValueError):
            generate(dt.datetime.now(dt.timezone.utc), days=0)

    def test_contract_inventory(self):
        inventory = methods()
        self.assertEqual(len(inventory), len(set(inventory)))
        for name in ['CreatePatient', 'CreateEvent', 'CreateAlarm', 'WriteReadings', 'CreateCalibration']:
            self.assertIn(name, inventory)


if __name__ == '__main__':
    unittest.main()
