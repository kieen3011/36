import csv
from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest

from alerts import AlertSystem
from config import THRESHOLDS
from main import _build_manager, _handle_event, build_parser, run_simulation
from statistics import StatisticsTracker


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
                steps=4,
                output_dir=temporary_directory,
                sensor_profiles=make_profile(
                    initial_temperature=11.0,
                    incident_schedule={1: "DISCONNECT", 2: "RECOVER"},
                ),
                render=False,
            )

            self.assertEqual(result["summary"]["total_alerts"], 2)
            self.assertEqual(result["summary"]["total_errors"], 1)
            self.assertEqual(result["summary"]["errors_by_type"], {"DISCONNECT": 1})
            cold_reading = next(
                reading
                for reading in result["readings"]
                if reading["sensor_id"] == "COLD-01"
            )
            self.assertEqual(cold_reading["status"], "ACTIVE")
            self.assertEqual(cold_reading["timestamp"], "2026-11-23T00:03:00+07:00")
            self.assertEqual(result["summary"]["by_location"]["A"]["CRITICAL"], 2)

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

    def test_unknown_event_kind_is_recorded_as_processing_error(self):
        manager = _build_manager()
        tracker = StatisticsTracker()
        alert_system = AlertSystem(THRESHOLDS)
        event = {
            "kind": "UNSUPPORTED",
            "sensor_id": "COLD-01",
            "timestamp": "2026-11-23T00:00:00+07:00",
            "temperature": None,
            "humidity": None,
        }

        alert = _handle_event(event, manager, alert_system, tracker)

        self.assertIsNone(alert)
        self.assertEqual(tracker.get_summary()["errors_by_type"], {"PROCESSING_ERROR": 1})

    def test_malformed_reading_is_recorded_as_processing_error(self):
        manager = _build_manager()
        tracker = StatisticsTracker()
        alert_system = AlertSystem(THRESHOLDS)
        event = {
            "kind": "READING",
            "sensor_id": "COLD-01",
            "timestamp": "2026-11-23T00:00:00+07:00",
            "temperature": "INVALID",
            "humidity": 90.0,
        }

        alert = _handle_event(event, manager, alert_system, tracker)

        self.assertIsNone(alert)
        self.assertEqual(tracker.get_summary()["errors_by_type"], {"PROCESSING_ERROR": 1})
        cold_reading = manager.get_sensor("COLD-01").get_reading()
        self.assertIsNone(cold_reading["temperature"])

    def test_cli_parser_requires_non_blank_mssv(self):
        parser = build_parser()

        for arguments in ([], ["--mssv", "   "]):
            with self.subTest(arguments=arguments):
                with redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        parser.parse_args(arguments)

    def test_cli_parser_rejects_invalid_steps(self):
        parser = build_parser()

        for value in ("0", "abc"):
            with self.subTest(value=value):
                with redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        parser.parse_args(["--mssv", "2312345", "--steps", value])

    def test_cli_parser_applies_defaults_and_accepts_overrides(self):
        parser = build_parser()

        defaults = parser.parse_args(["--mssv", "2312345"])
        overrides = parser.parse_args(
            ["--mssv", "2312345", "--steps", "3", "--output-dir", "ket-qua"]
        )

        self.assertEqual(defaults.steps, 10)
        self.assertEqual(defaults.output_dir, "output")
        self.assertEqual(overrides.steps, 3)
        self.assertEqual(overrides.output_dir, "ket-qua")


if __name__ == "__main__":
    unittest.main()
