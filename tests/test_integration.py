import csv
import json
from pathlib import Path
import tempfile
import unittest

from main import run_simulation


def make_profile(initial_temperature=5.0, incident_schedule=None):
    return {
        "COLD-01": {
            "initial_temperature": initial_temperature,
            "initial_humidity": 90.0,
            "temperature_step": 0.0001,
            "humidity_step": 0.0001,
            "incident_schedule": incident_schedule or {},
        }
    }


class IntegrationTests(unittest.TestCase):
    def test_environmental_reading_flows_to_alert_exports(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = run_simulation(
                mssv="2312345",
                steps=1,
                output_dir=temporary_directory,
                sensor_profiles=make_profile(initial_temperature=11.0),
                render=False,
            )

            self.assertEqual(result["summary"]["total_alerts"], 1)
            self.assertEqual(result["summary"]["total_errors"], 0)
            self.assertEqual(result["summary"]["by_location"]["A"]["CRITICAL"], 1)

            csv_path = Path(temporary_directory, "alert_logs.csv")
            json_path = Path(temporary_directory, "report.json")
            with csv_path.open(encoding="utf-8", newline="") as file:
                rows = list(csv.DictReader(file))
            with json_path.open(encoding="utf-8") as file:
                report = json.load(file)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["sensor_id"], "COLD-01")
            self.assertEqual(report["summary"], result["summary"])

    def test_disconnect_and_recover_do_not_realert_stale_reading(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = run_simulation(
                mssv="2312345",
                steps=3,
                output_dir=temporary_directory,
                sensor_profiles=make_profile(
                    initial_temperature=11.0,
                    incident_schedule={1: "DISCONNECT", 2: "RECOVER"},
                ),
                render=False,
            )

            self.assertEqual(result["summary"]["total_alerts"], 1)
            self.assertEqual(result["summary"]["total_errors"], 1)
            self.assertEqual(result["summary"]["errors_by_type"], {"DISCONNECT": 1})
            cold_reading = next(
                reading
                for reading in result["readings"]
                if reading["sensor_id"] == "COLD-01"
            )
            self.assertEqual(cold_reading["status"], "ACTIVE")
            self.assertEqual(cold_reading["timestamp"], "2026-11-23T00:00:00+07:00")

    def test_invalid_data_is_recorded_without_updating_sensor(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = run_simulation(
                mssv="2312345",
                steps=1,
                output_dir=temporary_directory,
                sensor_profiles=make_profile(incident_schedule={0: "INVALID_DATA"}),
                render=False,
            )

            self.assertEqual(result["summary"]["total_alerts"], 0)
            self.assertEqual(result["summary"]["errors_by_type"], {"INVALID_DATA": 1})
            cold_reading = next(
                reading
                for reading in result["readings"]
                if reading["sensor_id"] == "COLD-01"
            )
            self.assertIsNone(cold_reading["temperature"])
            self.assertIsNone(cold_reading["timestamp"])

    def test_unknown_sensor_event_becomes_separate_error(self):
        profiles = {
            "MISSING-01": {
                "initial_temperature": 5.0,
                "initial_humidity": 90.0,
                "temperature_step": 0.1,
                "humidity_step": 0.1,
                "incident_schedule": {},
            }
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = run_simulation(
                mssv="2312345",
                steps=1,
                output_dir=temporary_directory,
                sensor_profiles=profiles,
                render=False,
            )

            self.assertEqual(result["summary"]["total_alerts"], 0)
            self.assertEqual(result["summary"]["errors_by_type"], {"UNKNOWN_SENSOR": 1})


if __name__ == "__main__":
    unittest.main()
