"""Cau hinh mac dinh da duoc khoa theo G0."""

from datetime import datetime, timedelta, timezone


START_TIME = datetime(2026, 11, 23, 0, 0, tzinfo=timezone(timedelta(hours=7)))
STEP_MINUTES = 1

SENSOR_DEFINITIONS = (
    {"sensor_id": "COLD-01", "location_id": "A", "sensor_type": "COLD_STORAGE"},
    {"sensor_id": "DRY-01", "location_id": "B", "sensor_type": "DRY_STORAGE"},
    {"sensor_id": "SERVER-01", "location_id": "C", "sensor_type": "SERVER_ROOM"},
)

SENSOR_PROFILES = {
    "COLD-01": {
        "initial_temperature": 5.0,
        "initial_humidity": 90.0,
        "temperature_step": 0.5,
        "humidity_step": 1.0,
        "incident_schedule": {3: "DISCONNECT", 4: "RECOVER", 7: "INVALID_DATA"},
    },
    "DRY-01": {
        "initial_temperature": 22.0,
        "initial_humidity": 50.0,
        "temperature_step": 0.8,
        "humidity_step": 1.5,
        "incident_schedule": {},
    },
    "SERVER-01": {
        "initial_temperature": 26.0,
        "initial_humidity": 50.0,
        "temperature_step": 1.0,
        "humidity_step": 1.0,
        "incident_schedule": {},
    },
}

THRESHOLDS = {
    "A": {
        "temperature": {
            "min": 2.0,
            "max": 8.0,
            "min_inclusive": True,
            "max_inclusive": True,
        },
        "humidity": {
            "min": 85.0,
            "max": 95.0,
            "min_inclusive": True,
            "max_inclusive": True,
        },
    },
    "B": {
        "temperature": {
            "min": 18.0,
            "max": 25.0,
            "min_inclusive": True,
            "max_inclusive": True,
        },
        "humidity": {
            "min": None,
            "max": 60.0,
            "min_inclusive": True,
            "max_inclusive": False,
        },
    },
    "C": {
        "temperature": {
            "min": None,
            "max": 30.0,
            "min_inclusive": True,
            "max_inclusive": False,
        },
        "humidity": {
            "min": 40.0,
            "max": 60.0,
            "min_inclusive": True,
            "max_inclusive": True,
        },
    },
}
