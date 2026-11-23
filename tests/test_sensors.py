import math
import unittest

from sensors import (
    ColdStorageSensor,
    DryStorageSensor,
    Sensor,
    ServerRoomSensor,
)


class SensorTests(unittest.TestCase):
    def test_new_sensor_returns_empty_reading_with_exact_schema(self):
        sensor = Sensor("GEN-01", "A")

        self.assertEqual(
            sensor.get_reading(),
            {
                "sensor_id": "GEN-01",
                "sensor_type": "GENERIC",
                "location_id": "A",
                "status": "ACTIVE",
                "temperature": None,
                "humidity": None,
                "timestamp": None,
            },
        )

    def test_subclasses_expose_approved_sensor_types(self):
        cases = (
            (ColdStorageSensor, "COLD_STORAGE"),
            (DryStorageSensor, "DRY_STORAGE"),
            (ServerRoomSensor, "SERVER_ROOM"),
        )

        for sensor_class, expected_type in cases:
            with self.subTest(sensor_class=sensor_class.__name__):
                reading = sensor_class("S-01", "A").get_reading()
                self.assertEqual(reading["sensor_type"], expected_type)

    def test_active_sensor_accepts_measurement_and_preserves_timestamp_text(self):
        sensor = Sensor("GEN-01", "A")
        timestamp = "2026-11-23T00:00:00Z"

        accepted = sensor.update_measurement(5, 90.5, timestamp)

        self.assertTrue(accepted)
        self.assertEqual(sensor.get_reading()["temperature"], 5.0)
        self.assertEqual(sensor.get_reading()["humidity"], 90.5)
        self.assertEqual(sensor.get_reading()["timestamp"], timestamp)

    def test_non_active_sensor_ignores_payload_and_keeps_previous_measurement(self):
        sensor = Sensor("GEN-01", "A")
        sensor.update_measurement(5.0, 90.0, "2026-11-23T00:00:00+07:00")
        previous = sensor.get_reading()
        sensor.set_status("ERROR")

        accepted = sensor.update_measurement(True, math.nan, "not-a-timestamp")

        self.assertFalse(accepted)
        current = sensor.get_reading()
        self.assertEqual(current["temperature"], previous["temperature"])
        self.assertEqual(current["humidity"], previous["humidity"])
        self.assertEqual(current["timestamp"], previous["timestamp"])
        self.assertEqual(current["status"], "ERROR")

    def test_active_sensor_rejects_invalid_numeric_values(self):
        sensor = Sensor("GEN-01", "A")
        invalid_cases = (
            (True, 90.0, TypeError),
            (5.0, False, TypeError),
            (math.nan, 90.0, ValueError),
            (5.0, math.inf, ValueError),
        )

        for temperature, humidity, error_type in invalid_cases:
            with self.subTest(temperature=temperature, humidity=humidity):
                with self.assertRaises(error_type):
                    sensor.update_measurement(
                        temperature,
                        humidity,
                        "2026-11-23T00:00:00+07:00",
                    )

    def test_sensor_validates_identifiers_status_and_timestamp(self):
        with self.assertRaises(TypeError):
            Sensor(1, "A")
        with self.assertRaises(ValueError):
            Sensor("   ", "A")
        with self.assertRaises(ValueError):
            Sensor("S-01", "A", "BROKEN")

        sensor = Sensor("S-01", "A")
        with self.assertRaises(TypeError):
            sensor.set_status(1)
        with self.assertRaises(ValueError):
            sensor.set_status("BROKEN")
        with self.assertRaises(TypeError):
            sensor.update_measurement(5.0, 90.0, 123)
        with self.assertRaises(ValueError):
            sensor.update_measurement(5.0, 90.0, "2026-11-23T00:00:00")
        with self.assertRaises(ValueError):
            sensor.update_measurement(5.0, 90.0, "invalid")


if __name__ == "__main__":
    unittest.main()
