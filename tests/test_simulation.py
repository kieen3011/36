"""Kiem thu SimulationEngine theo contract G0."""

import copy
import math
import unittest

from simulation import SimulationEngine
from tests.fixtures import BASE_TIMESTAMP, STEP_ONE_TIMESTAMP, copy_sensor_profiles


class SimulationEngineTests(unittest.TestCase):
    def test_sha256_seed_matches_approved_golden_vector(self):
        engine = SimulationEngine("2312345", copy_sensor_profiles())

        first_event = engine.generate_events(0, BASE_TIMESTAMP)[0]

        self.assertEqual(
            first_event,
            {
                "kind": "READING",
                "sensor_id": "COLD-01",
                "timestamp": "2026-11-23T00:00:00+07:00",
                "temperature": 4.87,
                "humidity": 90.17,
            },
        )

    def test_different_mssv_produce_different_sequences(self):
        first = SimulationEngine("2312345", copy_sensor_profiles())
        second = SimulationEngine("2312346", copy_sensor_profiles())

        first_events = first.generate_events(0, BASE_TIMESTAMP)
        second_events = second.generate_events(0, BASE_TIMESTAMP)

        self.assertNotEqual(first_events, second_events)

    def test_same_mssv_and_profiles_produce_same_events(self):
        profiles = copy_sensor_profiles()
        first = SimulationEngine("2312345", profiles)
        second = SimulationEngine("2312345", profiles)

        first_events = [
            first.generate_events(step, f"2026-11-23T00:0{step}:00+07:00")
            for step in range(3)
        ]
        second_events = [
            second.generate_events(step, f"2026-11-23T00:0{step}:00+07:00")
            for step in range(3)
        ]

        self.assertEqual(first_events, second_events)

    def test_events_are_sorted_and_have_exact_schema(self):
        engine = SimulationEngine("2312345", copy_sensor_profiles())

        events = engine.generate_events(0, BASE_TIMESTAMP)

        self.assertEqual(
            [event["sensor_id"] for event in events],
            ["COLD-01", "DRY-01", "SERVER-01"],
        )
        self.assertTrue(all(event["kind"] == "READING" for event in events))
        self.assertTrue(
            all(
                list(event) == [
                    "kind",
                    "sensor_id",
                    "timestamp",
                    "temperature",
                    "humidity",
                ]
                for event in events
            )
        )

    def test_scheduled_incidents_take_priority_over_readings(self):
        engine = SimulationEngine("2312345", copy_sensor_profiles())

        disconnect = engine.generate_events(3, "2026-11-23T00:03:00+07:00")[0]
        recover = engine.generate_events(4, "2026-11-23T00:04:00+07:00")[0]
        invalid = engine.generate_events(7, "2026-11-23T00:07:00+07:00")[0]

        self.assertEqual(
            disconnect,
            {
                "kind": "DISCONNECT",
                "sensor_id": "COLD-01",
                "timestamp": "2026-11-23T00:03:00+07:00",
                "temperature": None,
                "humidity": None,
            },
        )
        self.assertEqual(recover["kind"], "RECOVER")
        self.assertIsNone(recover["temperature"])
        self.assertIsNone(recover["humidity"])
        self.assertEqual(invalid["kind"], "INVALID_DATA")
        self.assertEqual(invalid["temperature"], "INVALID")
        self.assertIsNone(invalid["humidity"])

    def test_incident_does_not_advance_random_walk(self):
        incident_profiles = {
            "S-1": {
                "initial_temperature": 10.0,
                "initial_humidity": 20.0,
                "temperature_step": 1.0,
                "humidity_step": 2.0,
                "incident_schedule": {1: "DISCONNECT"},
            }
        }
        plain_profiles = copy.deepcopy(incident_profiles)
        plain_profiles["S-1"]["incident_schedule"] = {}
        incident_engine = SimulationEngine("99", incident_profiles)
        plain_engine = SimulationEngine("99", plain_profiles)

        incident_engine.generate_events(0, BASE_TIMESTAMP)
        incident_engine.generate_events(1, STEP_ONE_TIMESTAMP)
        after_incident = incident_engine.generate_events(
            2, "2026-11-23T00:02:00+07:00"
        )[0]
        plain_engine.generate_events(0, BASE_TIMESTAMP)
        corresponding = plain_engine.generate_events(
            2, "2026-11-23T00:02:00+07:00"
        )[0]

        self.assertEqual(after_incident["temperature"], corresponding["temperature"])
        self.assertEqual(after_incident["humidity"], corresponding["humidity"])

    def test_constructor_does_not_mutate_profiles(self):
        profiles = copy_sensor_profiles()
        original = copy.deepcopy(profiles)

        engine = SimulationEngine("2312345", profiles)
        engine.generate_events(0, BASE_TIMESTAMP)

        self.assertEqual(profiles, original)

    def test_rejects_invalid_mssv_and_profile_fields(self):
        profiles = copy_sensor_profiles()
        with self.assertRaises(TypeError):
            SimulationEngine(123, profiles)
        with self.assertRaises(ValueError):
            SimulationEngine("   ", profiles)

        missing = copy_sensor_profiles()
        del missing["COLD-01"]["temperature_step"]
        with self.assertRaises(ValueError):
            SimulationEngine("2312345", missing)

        wrong_type = copy_sensor_profiles()
        wrong_type["COLD-01"]["humidity_step"] = True
        with self.assertRaises(TypeError):
            SimulationEngine("2312345", wrong_type)

        non_finite = copy_sensor_profiles()
        non_finite["COLD-01"]["initial_temperature"] = math.inf
        with self.assertRaises(ValueError):
            SimulationEngine("2312345", non_finite)

    def test_rejects_invalid_schedule_step_and_kind(self):
        invalid_step = copy_sensor_profiles()
        invalid_step["COLD-01"]["incident_schedule"] = {True: "DISCONNECT"}
        with self.assertRaises(TypeError):
            SimulationEngine("2312345", invalid_step)

        invalid_kind = copy_sensor_profiles()
        invalid_kind["COLD-01"]["incident_schedule"] = {1: "READING"}
        with self.assertRaises(ValueError):
            SimulationEngine("2312345", invalid_kind)

    def test_generate_events_validates_step_and_timestamp(self):
        engine = SimulationEngine("2312345", copy_sensor_profiles())

        with self.assertRaises(TypeError):
            engine.generate_events(True, BASE_TIMESTAMP)
        with self.assertRaises(ValueError):
            engine.generate_events(-1, BASE_TIMESTAMP)
        with self.assertRaises(TypeError):
            engine.generate_events(0, None)
        with self.assertRaises(ValueError):
            engine.generate_events(0, "2026-11-23T00:00:00")


if __name__ == "__main__":
    unittest.main()
