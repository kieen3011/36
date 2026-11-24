"""Kiem thu StatisticsTracker theo contract G0."""

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_record_error_validates_each_contract_field_independently(self):
        valid = {
            "sensor_id": "COLD-01",
            "timestamp": BASE_TIMESTAMP,
            "error_type": "DISCONNECT",
            "message": "Mat ket noi cam bien",
            "details": {},
        }
        cases = (
            ("schema", {**valid, "extra": True}, ValueError),
            ("sensor_type", {**valid, "sensor_id": 1}, TypeError),
            ("sensor_blank", {**valid, "sensor_id": " "}, ValueError),
            ("timestamp_type", {**valid, "timestamp": 1}, TypeError),
            ("timestamp_value", {**valid, "timestamp": "not-iso"}, ValueError),
            ("error_type_type", {**valid, "error_type": 1}, TypeError),
            ("error_type_value", {**valid, "error_type": "NETWORK"}, ValueError),
            ("message_type", {**valid, "message": 1}, TypeError),
            ("message_blank", {**valid, "message": " "}, ValueError),
            ("details_type", {**valid, "details": []}, TypeError),
        )

        for name, record, exception_type in cases:
            with self.subTest(name=name):
                with self.assertRaises(exception_type):
                    self.tracker.record_error(record)

    def test_record_error_accepts_nested_json_safe_details(self):
        error = {
            "sensor_id": "COLD-01",
            "timestamp": BASE_TIMESTAMP,
            "error_type": "PROCESSING_ERROR",
            "message": "Loi xu ly",
            "details": {
                "context": [None, True, "text", 3, 1.5, {"nested": "ok"}]
            },
        }

        self.assertIsNone(self.tracker.record_error(error))
        self.assertEqual(1, self.tracker.get_summary()["total_errors"])

    def test_record_error_rejects_non_json_safe_nested_details(self):
        class CustomDict(dict):
            pass

        class CustomList(list):
            pass

        class CustomString(str):
            pass

        invalid_values = (
            object(),
            float("nan"),
            float("inf"),
            float("-inf"),
            ("tuple",),
            {"set"},
            {1: "non-string-key"},
            {"nested": [object()]},
            {"nested": {"value": float("nan")}},
            CustomDict({"value": "text"}),
            {"value": CustomList(["text"])},
            {"value": CustomString("text")},
            {CustomString("key"): "text"},
        )

        for value in invalid_values:
            with self.subTest(value=repr(value)):
                error = {
                    "sensor_id": "COLD-01",
                    "timestamp": BASE_TIMESTAMP,
                    "error_type": "PROCESSING_ERROR",
                    "message": "Loi xu ly",
                    "details": value if isinstance(value, dict) else {"value": value},
                }
                with self.assertRaises((TypeError, ValueError)):
                    self.tracker.record_error(error)

    def test_record_error_rejects_cyclic_details(self):
        details = {}
        details["self"] = details
        error = {
            "sensor_id": "COLD-01",
            "timestamp": BASE_TIMESTAMP,
            "error_type": "PROCESSING_ERROR",
            "message": "Loi xu ly",
            "details": details,
        }

        with self.assertRaises(ValueError):
            self.tracker.record_error(error)

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

    def test_export_csv_neutralizes_spreadsheet_formula_prefixes(self):
        self.tracker.record_alert(
            make_alert(sensor_id="=2+3", location_id="+A")
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "alerts.csv"
            self.tracker.export_csv(str(target))
            with target.open(encoding="utf-8", newline="") as file:
                row = next(csv.DictReader(file))

        self.assertEqual("'=2+3", row["sensor_id"])
        self.assertEqual("'+A", row["location_id"])

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

    def test_export_json_orders_session_by_instant_across_timezone_offsets(self):
        earlier = "2026-11-23T01:00:00+07:00"
        later = "2026-11-22T20:00:00+00:00"
        for timestamp in (later, earlier):
            self.tracker.record_error(
                {
                    "sensor_id": "COLD-01",
                    "timestamp": timestamp,
                    "error_type": "PROCESSING_ERROR",
                    "message": "Loi xu ly",
                    "details": {},
                }
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "report.json"
            self.tracker.export_json(str(target))
            with target.open(encoding="utf-8") as file:
                report = json.load(file)

        self.assertEqual(
            {"started_at": earlier, "ended_at": later}, report["session"]
        )

    def test_export_json_preserves_existing_target_on_fsync_failure(self):
        self.tracker.record_error(
            {
                "sensor_id": "COLD-01",
                "timestamp": BASE_TIMESTAMP,
                "error_type": "DISCONNECT",
                "message": "Mat ket noi cam bien",
                "details": {},
            }
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "report.json"
            target.write_text('{"stable": true}', encoding="utf-8")
            with patch("os.fsync", side_effect=OSError("disk failure")):
                with self.assertRaisesRegex(OSError, "disk failure"):
                    self.tracker.export_json(str(target))

            self.assertEqual('{"stable": true}', target.read_text(encoding="utf-8"))
            self.assertEqual([target], list(Path(temp_dir).iterdir()))

    def test_export_json_preserves_existing_target_on_serialization_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "report.json"
            target.write_text('{"stable": true}', encoding="utf-8")
            with patch(
                "statistics.json.dumps",
                side_effect=TypeError("serialization failure"),
            ):
                with self.assertRaisesRegex(TypeError, "serialization failure"):
                    self.tracker.export_json(str(target))

            self.assertEqual('{"stable": true}', target.read_text(encoding="utf-8"))
            self.assertEqual([target], list(Path(temp_dir).iterdir()))

    def test_export_json_preserves_existing_target_on_replace_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "report.json"
            target.write_text('{"stable": true}', encoding="utf-8")
            with patch("statistics.os.replace", side_effect=OSError("replace failure")):
                with self.assertRaisesRegex(OSError, "replace failure"):
                    self.tracker.export_json(str(target))

            self.assertEqual('{"stable": true}', target.read_text(encoding="utf-8"))
            self.assertEqual([target], list(Path(temp_dir).iterdir()))


if __name__ == "__main__":
    unittest.main()
