"""Bo may sinh su kien mo phong cho he thong kho."""

from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import math
import random


_PROFILE_REQUIRED_FIELDS = {
    "initial_temperature",
    "initial_humidity",
    "temperature_step",
    "humidity_step",
}
_PROFILE_OPTIONAL_FIELDS = {"incident_schedule"}
_INCIDENT_KINDS = {"DISCONNECT", "RECOVER", "INVALID_DATA"}


def _validate_identifier(value, field_name):
    """Kiem tra dinh danh ma khong tu dong loai bo khoang trang."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def _validate_number(value, field_name, positive=False):
    """Kiem tra so huu han va loai bo bool."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a number")
    if not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite")
    if positive and value <= 0:
        raise ValueError(f"{field_name} must be greater than zero")


def _validate_timestamp(timestamp):
    """Kiem tra timestamp ISO 8601 co timezone."""
    if not isinstance(timestamp, str):
        raise TypeError("timestamp must be a string")
    if not timestamp.strip():
        raise ValueError("timestamp must not be blank")
    candidate = timestamp[:-1] + "+00:00" if timestamp.endswith("Z") else timestamp
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise ValueError("timestamp must be valid ISO 8601") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")


class SimulationEngine:
    """Sinh chuoi su kien cam bien co the tai lap."""

    def __init__(self, mssv: str, sensor_profiles: dict):
        _validate_identifier(mssv, "mssv")
        if not isinstance(sensor_profiles, dict):
            raise TypeError("sensor_profiles must be a dictionary")

        self._profiles = self._validate_profiles(sensor_profiles)
        digest = sha256(mssv.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:8], "big")
        self._random = random.Random(seed)
        self._states = {
            sensor_id: {
                "temperature": profile["initial_temperature"],
                "humidity": profile["initial_humidity"],
            }
            for sensor_id, profile in self._profiles.items()
        }

    @staticmethod
    def _validate_profiles(sensor_profiles):
        """Kiem tra va sao chep profile de bao ve du lieu dau vao."""
        validated = {}
        for sensor_id, source_profile in sensor_profiles.items():
            _validate_identifier(sensor_id, "sensor_id")
            if not isinstance(source_profile, dict):
                raise TypeError("each sensor profile must be a dictionary")

            fields = set(source_profile)
            missing = _PROFILE_REQUIRED_FIELDS - fields
            extra = fields - _PROFILE_REQUIRED_FIELDS - _PROFILE_OPTIONAL_FIELDS
            if missing or extra:
                raise ValueError("sensor profile has an invalid schema")

            profile = deepcopy(source_profile)
            for field_name in ("initial_temperature", "initial_humidity"):
                _validate_number(profile[field_name], field_name)
            for field_name in ("temperature_step", "humidity_step"):
                _validate_number(profile[field_name], field_name, positive=True)

            schedule = profile.get("incident_schedule", {})
            if not isinstance(schedule, dict):
                raise TypeError("incident_schedule must be a dictionary")
            for step_index, kind in schedule.items():
                if isinstance(step_index, bool) or not isinstance(step_index, int):
                    raise TypeError("incident step must be an integer")
                if step_index < 0:
                    raise ValueError("incident step must not be negative")
                if not isinstance(kind, str):
                    raise TypeError("incident kind must be a string")
                if kind not in _INCIDENT_KINDS:
                    raise ValueError("incident kind is not supported")
            profile["incident_schedule"] = schedule
            validated[sensor_id] = profile
        return validated

    def generate_events(self, step_index: int, timestamp: str) -> list[dict]:
        """Sinh toi da mot su kien cho moi cam bien trong mot buoc."""
        if isinstance(step_index, bool) or not isinstance(step_index, int):
            raise TypeError("step_index must be an integer")
        if step_index < 0:
            raise ValueError("step_index must not be negative")
        _validate_timestamp(timestamp)

        events = []
        for sensor_id in sorted(self._profiles):
            profile = self._profiles[sensor_id]
            kind = profile["incident_schedule"].get(step_index)
            if kind is not None:
                events.append(self._make_incident(kind, sensor_id, timestamp))
                continue
            events.append(self._make_reading(sensor_id, timestamp))
        return events

    @staticmethod
    def _make_incident(kind, sensor_id, timestamp):
        """Tao event su co theo schema chung."""
        temperature = "INVALID" if kind == "INVALID_DATA" else None
        return {
            "kind": kind,
            "sensor_id": sensor_id,
            "timestamp": timestamp,
            "temperature": temperature,
            "humidity": None,
        }

    def _make_reading(self, sensor_id, timestamp):
        """Cap nhat Random Walk va tao event reading."""
        profile = self._profiles[sensor_id]
        state = self._states[sensor_id]
        state["temperature"] = round(
            state["temperature"]
            + self._random.uniform(
                -profile["temperature_step"], profile["temperature_step"]
            ),
            2,
        )
        state["humidity"] = round(
            state["humidity"]
            + self._random.uniform(-profile["humidity_step"], profile["humidity_step"]),
            2,
        )
        return {
            "kind": "READING",
            "sensor_id": sensor_id,
            "timestamp": timestamp,
            "temperature": state["temperature"],
            "humidity": state["humidity"],
        }
