"""Kiem thu adapter web dung truc tiep Python core."""

import csv
import io
import unittest

from web_service import _build_csv, simulate_session


class WebServiceTests(unittest.TestCase):
    def test_csv_download_neutralizes_spreadsheet_formula_prefixes(self):
        alert = {
            "sensor_id": "=2+3",
            "location_id": "+A",
            "timestamp": "2026-11-23T00:00:00+07:00",
            "severity": "WARNING",
            "violated_metrics": ["temperature"],
            "temperature": 8.1,
            "humidity": 90.0,
        }

        row = next(csv.DictReader(io.StringIO(_build_csv([alert]))))

        self.assertEqual("'=2+3", row["sensor_id"])
        self.assertEqual("'+A", row["location_id"])

    def test_session_is_deterministic_and_has_complete_schema(self):
        first = simulate_session("2312345", 3)
        second = simulate_session("2312345", 3)

        self.assertEqual(first, second)
        self.assertEqual(
            {
                "session",
                "sensors",
                "timeline",
                "alerts",
                "errors",
                "summary",
                "downloads",
            },
            set(first),
        )
        self.assertEqual(3, len(first["timeline"]))
        self.assertEqual(3, len(first["sensors"]))

    def test_device_errors_are_separate_from_environmental_alerts(self):
        result = simulate_session("2312345", 8)

        self.assertEqual(0, result["summary"]["total_alerts"])
        self.assertEqual(2, result["summary"]["total_errors"])
        self.assertEqual(
            {"DISCONNECT", "INVALID_DATA"},
            {error["error_type"] for error in result["errors"]},
        )

    def test_custom_profile_produces_real_alert_and_matching_csv(self):
        profiles = {
            "COLD-01": {
                "initial_temperature": 11.0,
                "initial_humidity": 90.0,
                "temperature_step": 0.0001,
                "humidity_step": 0.0001,
                "incident_schedule": {},
            }
        }

        result = simulate_session("2312345", 1, sensor_profiles=profiles)
        rows = list(csv.DictReader(io.StringIO(result["downloads"]["csv"])))

        self.assertEqual(1, result["summary"]["total_alerts"])
        self.assertEqual("CRITICAL", result["alerts"][0]["severity"])
        self.assertEqual(result["alerts"][0]["sensor_id"], rows[0]["sensor_id"])
        self.assertEqual(result["summary"], result["downloads"]["json"]["summary"])

    def test_downloads_match_every_record_in_the_displayed_session(self):
        profiles = {
            "COLD-01": {
                "initial_temperature": 11.0,
                "initial_humidity": 90.0,
                "temperature_step": 0.0001,
                "humidity_step": 0.0001,
                "incident_schedule": {},
            }
        }

        result = simulate_session("2312345", 2, sensor_profiles=profiles)
        rows = list(csv.DictReader(io.StringIO(result["downloads"]["csv"])))
        downloaded_json = result["downloads"]["json"]

        self.assertEqual(len(result["alerts"]), len(rows))
        self.assertEqual(result["alerts"], downloaded_json["alerts"])
        self.assertEqual(result["timeline"], downloaded_json["timeline"])
        self.assertEqual(result["errors"], downloaded_json["errors"])
        self.assertEqual(result["session"], downloaded_json["session"])


if __name__ == "__main__":
    unittest.main()
