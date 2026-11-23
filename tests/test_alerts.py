"""Kiem thu hop dong cua AlertSystem."""

import importlib.util
import unittest
from copy import deepcopy

import alerts
from tests.fixtures import BASE_TIMESTAMP, copy_thresholds, make_reading


class AlertModuleTests(unittest.TestCase):
    def test_alert_module_is_available(self):
        """Bat loi khi module Alert chua duoc ban giao."""
        self.assertIsNotNone(importlib.util.find_spec("alerts"))

    def test_alert_system_class_is_available(self):
        """Bat loi khi class AlertSystem chua duoc ban giao."""
        self.assertTrue(hasattr(alerts, "AlertSystem"))

    def test_constructor_accepts_valid_thresholds(self):
        """Bat loi khi constructor khong nhan threshold hop le."""
        try:
            instance = alerts.AlertSystem(copy_thresholds())
        except TypeError:
            instance = None
        self.assertIsInstance(instance, alerts.AlertSystem)


class AlertSystemTests(unittest.TestCase):
    def setUp(self):
        self.alert_system = alerts.AlertSystem(copy_thresholds())

    def test_normal_reading_returns_none(self):
        """Bat loi neu reading an toan tao canh bao."""
        self.assertIsNone(self.alert_system.evaluate(make_reading()))

    def test_inclusive_boundaries_are_normal(self):
        """Bat loi neu bien bao gom cua kho lanh bi xem la vi pham."""
        lower = make_reading(temperature=2.0, humidity=85.0)
        upper = make_reading(temperature=8.0, humidity=95.0)

        self.assertIsNone(self.alert_system.evaluate(lower))
        self.assertIsNone(self.alert_system.evaluate(upper))

    def test_small_temperature_violation_is_warning(self):
        """Bat loi neu sai lech nhiet do nho bi nang thanh critical."""
        reading = make_reading(
            sensor_id="DRY-01",
            sensor_type="DRY_STORAGE",
            location_id="B",
            temperature=25.1,
            humidity=59.0,
        )

        alert = self.alert_system.evaluate(reading)

        self.assertEqual("WARNING", alert["severity"])
        self.assertEqual(["temperature"], alert["violated_metrics"])

    def test_exclusive_boundary_is_warning(self):
        """Bat loi neu gia tri bang bien exclusive bi xem la normal."""
        reading = make_reading(
            sensor_id="DRY-01",
            sensor_type="DRY_STORAGE",
            location_id="B",
            temperature=22.0,
            humidity=60.0,
        )

        alert = self.alert_system.evaluate(reading)

        self.assertEqual("WARNING", alert["severity"])
        self.assertEqual(["humidity"], alert["violated_metrics"])

    def test_temperature_deviation_of_three_is_critical(self):
        """Bat loi neu moc critical nhiet do ba do bi xu ly sai."""
        reading = make_reading(
            sensor_id="DRY-01",
            sensor_type="DRY_STORAGE",
            location_id="B",
            temperature=28.0,
            humidity=50.0,
        )

        alert = self.alert_system.evaluate(reading)

        self.assertEqual("CRITICAL", alert["severity"])

    def test_exclusive_server_temperature_boundary_is_warning(self):
        """Bat loi neu 30 do tai phong may chu khong tao warning."""
        reading = make_reading(
            sensor_id="SERVER-01",
            sensor_type="SERVER_ROOM",
            location_id="C",
            temperature=30.0,
            humidity=50.0,
        )

        alert = self.alert_system.evaluate(reading)

        self.assertEqual("WARNING", alert["severity"])

    def test_dual_violation_returns_one_critical_record(self):
        """Bat loi neu hai metric tao sai record hoac sai thu tu."""
        reading = make_reading(temperature=11.0, humidity=105.0)
        original = deepcopy(reading)

        alert = self.alert_system.evaluate(reading)

        self.assertEqual(
            {
                "sensor_id": "COLD-01",
                "location_id": "A",
                "timestamp": BASE_TIMESTAMP,
                "severity": "CRITICAL",
                "violated_metrics": ["temperature", "humidity"],
                "temperature": 11.0,
                "humidity": 105.0,
            },
            alert,
        )
        self.assertEqual(original, reading)

    def test_inactive_reading_is_rejected(self):
        """Bat loi neu AlertSystem danh gia reading khong active."""
        with self.assertRaises(ValueError):
            self.alert_system.evaluate(make_reading(status="ERROR"))

    def test_boolean_measurement_is_rejected(self):
        """Bat loi neu bool duoc chap nhan nhu mot gia tri so."""
        with self.assertRaises(TypeError):
            self.alert_system.evaluate(make_reading(temperature=True))

    def test_naive_timestamp_is_rejected(self):
        """Bat loi neu timestamp khong timezone duoc chap nhan."""
        with self.assertRaises(ValueError):
            self.alert_system.evaluate(
                make_reading(timestamp="2026-11-23T00:00:00")
            )

    def test_reading_requires_exact_schema(self):
        """Bat loi neu reading thieu hoac thua field di qua contract."""
        missing = make_reading()
        missing.pop("humidity")
        extra = make_reading()
        extra["unexpected"] = "value"

        with self.assertRaises(ValueError):
            self.alert_system.evaluate(missing)
        with self.assertRaises(ValueError):
            self.alert_system.evaluate(extra)

    def test_missing_location_configuration_raises_key_error(self):
        """Bat loi neu location khong cau hinh bi bo qua im lang."""
        reading = make_reading(location_id="UNKNOWN")

        with self.assertRaises(KeyError) as context:
            self.alert_system.evaluate(reading)

        self.assertEqual(("UNKNOWN",), context.exception.args)

    def test_threshold_schema_is_validated_at_construction(self):
        """Bat loi neu threshold sai schema duoc chap nhan."""
        invalid = copy_thresholds()
        invalid["A"]["temperature"].pop("max_inclusive")

        with self.assertRaises(ValueError):
            alerts.AlertSystem(invalid)

    def test_threshold_field_type_is_validated_at_construction(self):
        """Bat loi neu threshold dung bool lam bien so."""
        invalid = copy_thresholds()
        invalid["A"]["temperature"]["max"] = True

        with self.assertRaises(TypeError):
            alerts.AlertSystem(invalid)


if __name__ == "__main__":
    unittest.main()
