"""Kiem thu StatisticsTracker theo contract G0."""

import csv
import json
import tempfile
import unittest
from pathlib import Path

from statistics import StatisticsTracker
from tests.fixtures import BASE_TIMESTAMP, STEP_ONE_TIMESTAMP, make_alert


class StatisticsTrackerTest(unittest.TestCase):
    """Kiem tra hanh vi quan sat duoc cua bo thong ke."""

    def setUp(self):
        self.tracker = StatisticsTracker()

    def test_record_alert_adds_valid_record_once(self):
        alert = make_alert()

        self.assertTrue(self.tracker.record_alert(alert))
        self.assertFalse(self.tracker.record_alert(dict(alert)))
        self.assertEqual(1, self.tracker.get_summary()["total_alerts"])

    def test_record_alert_counts_location_and_highest_severity(self):
        self.tracker.record_alert(make_alert())
        self.tracker.record_alert(
            make_alert(timestamp=STEP_ONE_TIMESTAMP, severity="CRITICAL")
        )

        self.assertEqual(
            {"A": {"WARNING": 1, "CRITICAL": 1, "total": 2}},
            self.tracker.get_summary()["by_location"],
        )

    def test_record_alert_rejects_wrong_schema_and_severity(self):
        wrong_schema = make_alert()
        wrong_schema["extra"] = True
        wrong_severity = make_alert(severity="NORMAL")

        with self.assertRaises(ValueError):
            self.tracker.record_alert(wrong_schema)
        with self.assertRaises(ValueError):
            self.tracker.record_alert(wrong_severity)

    def test_record_alert_rejects_bool_and_non_finite_measurement(self):
        with self.assertRaises(TypeError):
            self.tracker.record_alert(make_alert(temperature=True))
        with self.assertRaises(ValueError):
            self.tracker.record_alert(make_alert(humidity=float("nan")))

    def test_record_error_counts_each_error_without_deduplication(self):
        error = {
            "sensor_id": "COLD-01",
            "timestamp": BASE_TIMESTAMP,
            "error_type": "DISCONNECT",
            "message": "Mat ket noi cam bien",
            "details": {},
        }

        self.assertIsNone(self.tracker.record_error(error))
        self.assertIsNone(self.tracker.record_error(dict(error)))
        self.assertEqual(
            {
                "total_alerts": 0,
                "total_errors": 2,
                "by_location": {},
                "errors_by_type": {"DISCONNECT": 2},
            },
            self.tracker.get_summary(),
        )

    def test_record_error_rejects_invalid_contract(self):
        invalid = {
            "sensor_id": " ",
            "timestamp": BASE_TIMESTAMP,
            "error_type": "NETWORK",
            "message": " ",
            "details": [],
        }

        with self.assertRaises(ValueError):
            self.tracker.record_error(invalid)

    def test_get_summary_returns_independent_copy_with_sorted_locations(self):
        self.tracker.record_alert(
            make_alert(sensor_id="SERVER-01", location_id="C")
        )
        self.tracker.record_alert(
            make_alert(
                sensor_id="COLD-01",
                location_id="A",
                timestamp=STEP_ONE_TIMESTAMP,
            )
        )

        summary = self.tracker.get_summary()
        summary["by_location"]["A"]["WARNING"] = 99

        fresh = self.tracker.get_summary()
        self.assertEqual(["A", "C"], list(fresh["by_location"]))
        self.assertEqual(1, fresh["by_location"]["A"]["WARNING"])

    def test_export_csv_writes_contract_header_and_metric_list(self):
        self.tracker.record_alert(
            make_alert(
                severity="CRITICAL",
                violated_metrics=["temperature", "humidity"],
            )
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "nested" / "alerts.csv"
            self.tracker.export_csv(str(target))
            with target.open(encoding="utf-8", newline="") as file:
                rows = list(csv.DictReader(file))

        self.assertEqual(
            [
                "sensor_id",
                "location_id",
                "timestamp",
                "severity",
                "violated_metrics",
                "temperature",
                "humidity",
            ],
            list(rows[0]),
        )
        self.assertEqual("temperature;humidity", rows[0]["violated_metrics"])

    def test_export_json_writes_session_summary_alerts_and_errors(self):
        self.tracker.record_alert(make_alert(timestamp=STEP_ONE_TIMESTAMP))
        self.tracker.record_error(
            {
                "sensor_id": "COLD-01",
                "timestamp": BASE_TIMESTAMP,
                "error_type": "INVALID_DATA",
                "message": "Du lieu khong hop le",
                "details": {"temperature": "INVALID"},
            }
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "nested" / "report.json"
            self.tracker.export_json(str(target))
            with target.open(encoding="utf-8") as file:
                report = json.load(file)

        self.assertEqual(
            {"started_at": BASE_TIMESTAMP, "ended_at": STEP_ONE_TIMESTAMP},
            report["session"],
        )
        self.assertEqual(1, report["summary"]["total_alerts"])
        self.assertEqual(1, report["summary"]["total_errors"])
        self.assertEqual(1, len(report["alerts"]))
        self.assertEqual(1, len(report["errors"]))


if __name__ == "__main__":
    unittest.main()
