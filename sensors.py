"""Mo hinh cam bien cho he thong giam sat nha kho."""

from datetime import datetime
import math


VALID_STATUSES = frozenset({"ACTIVE", "INACTIVE", "ERROR"})


def _validate_identifier(value, field_name):
    """Kiem tra dinh danh va giu nguyen chuoi dau vao."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def _validate_status(status):
    """Kiem tra trang thai cam bien theo contract."""
    if not isinstance(status, str):
        raise TypeError("status must be a string")
    if status not in VALID_STATUSES:
        raise ValueError("status must be ACTIVE, INACTIVE, or ERROR")


def _validate_number(value, field_name):
    """Kiem tra gia tri so huu han va loai bool."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a number")
    if not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite")


def _validate_timestamp(timestamp):
    """Kiem tra timestamp ISO 8601 co timezone khi duoc cung cap."""
    if timestamp is None:
        return
    if not isinstance(timestamp, str):
        raise TypeError("timestamp must be a string or None")
    if not timestamp.strip():
        raise ValueError("timestamp must not be blank")
    normalized = timestamp[:-1] + "+00:00" if timestamp.endswith("Z") else timestamp
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError("timestamp must be valid ISO 8601") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include timezone")


class Sensor:
    """Cam bien co ban luu phep do gan nhat."""

    TYPE_NAME = "GENERIC"

    def __init__(self, sensor_id, location_id, status="ACTIVE"):
        _validate_identifier(sensor_id, "sensor_id")
        _validate_identifier(location_id, "location_id")
        _validate_status(status)
        self._sensor_id = sensor_id
        self._location_id = location_id
        self._status = status
        self._last_measurement = None

    def set_status(self, new_status):
        """Cap nhat trang thai cam bien."""
        _validate_status(new_status)
        self._status = new_status

    def update_measurement(self, temperature, humidity, timestamp=None):
        """Cap nhat phep do neu cam bien dang hoat dong."""
        if self._status != "ACTIVE":
            return False
        _validate_number(temperature, "temperature")
        _validate_number(humidity, "humidity")
        _validate_timestamp(timestamp)
        self._last_measurement = {
            "temperature": float(temperature),
            "humidity": float(humidity),
            "timestamp": timestamp,
        }
        return True

    def get_reading(self):
        """Tra ve snapshot moi cua cam bien."""
        measurement = self._last_measurement or {}
        return {
            "sensor_id": self._sensor_id,
            "sensor_type": self.TYPE_NAME,
            "location_id": self._location_id,
            "status": self._status,
            "temperature": measurement.get("temperature"),
            "humidity": measurement.get("humidity"),
            "timestamp": measurement.get("timestamp"),
        }


class ColdStorageSensor(Sensor):
    """Cam bien cho kho lanh."""

    TYPE_NAME = "COLD_STORAGE"


class DryStorageSensor(Sensor):
    """Cam bien cho kho kho."""

    TYPE_NAME = "DRY_STORAGE"


class ServerRoomSensor(Sensor):
    """Cam bien cho phong may chu."""

    TYPE_NAME = "SERVER_ROOM"
