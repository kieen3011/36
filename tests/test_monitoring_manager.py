import unittest

from monitoring_manager import MonitoringManager
from sensors import Sensor


class BrokenSensor(Sensor):
    def get_reading(self):
        raise RuntimeError("reading failed")


class MonitoringManagerTests(unittest.TestCase):
    def test_register_get_and_list_keep_registration_order(self):
        manager = MonitoringManager()
        first = Sensor("S-01", "A")
        second = Sensor("S-02", "B")

        self.assertIsNone(manager.register_sensor(first))
        manager.register_sensor(second)

        self.assertIs(manager.get_sensor("S-01"), first)
        sensors = manager.get_all_sensors()
        self.assertEqual(sensors, [first, second])
        self.assertIsNot(sensors, manager.get_all_sensors())

    def test_register_rejects_non_sensor_and_duplicate_id(self):
        manager = MonitoringManager()
        manager.register_sensor(Sensor("S-01", "A"))

        with self.assertRaises(TypeError):
            manager.register_sensor(object())
        with self.assertRaises(ValueError):
            manager.register_sensor(Sensor("S-01", "B"))

    def test_lookup_and_remove_validate_id_without_stripping(self):
        manager = MonitoringManager()
        sensor = Sensor(" S-01 ", "A")
        manager.register_sensor(sensor)

        self.assertIs(manager.get_sensor(" S-01 "), sensor)
        self.assertIsNone(manager.get_sensor("S-01"))
        for method in (manager.get_sensor, manager.remove_sensor):
            with self.subTest(method=method.__name__):
                with self.assertRaises(TypeError):
                    method(1)
                with self.assertRaises(ValueError):
                    method("   ")

    def test_remove_returns_boolean_for_found_and_missing_sensor(self):
        manager = MonitoringManager()
        manager.register_sensor(Sensor("S-01", "A"))

        self.assertTrue(manager.remove_sensor("S-01"))
        self.assertFalse(manager.remove_sensor("S-01"))

    def test_collect_readings_includes_every_sensor_and_returns_new_snapshots(self):
        manager = MonitoringManager()
        active = Sensor("S-01", "A")
        inactive = Sensor("S-02", "B", "INACTIVE")
        error = Sensor("S-03", "C", "ERROR")
        for sensor in (active, inactive, error):
            manager.register_sensor(sensor)

        first_snapshot = manager.collect_readings()
        second_snapshot = manager.collect_readings()

        self.assertEqual(
            [reading["status"] for reading in first_snapshot],
            ["ACTIVE", "INACTIVE", "ERROR"],
        )
        self.assertIsNot(first_snapshot, second_snapshot)
        self.assertIsNot(first_snapshot[0], second_snapshot[0])

    def test_collect_readings_propagates_sensor_exception(self):
        manager = MonitoringManager()
        manager.register_sensor(BrokenSensor("S-01", "A"))

        with self.assertRaisesRegex(RuntimeError, "reading failed"):
            manager.collect_readings()


if __name__ == "__main__":
    unittest.main()
