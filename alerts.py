"""Phan loai canh bao moi truong cho tung vi tri."""

from copy import deepcopy
from datetime import datetime
from math import isfinite


READING_FIELDS = {
    "sensor_id",
    "sensor_type",
    "location_id",
    "status",
    "temperature",
    "humidity",
    "timestamp",
}
LOCATION_FIELDS = {"temperature", "humidity"}
METRIC_FIELDS = {"min", "max", "min_inclusive", "max_inclusive"}
CRITICAL_DEVIATIONS = {"temperature": 3.0, "humidity": 10.0}


class AlertSystem:
    """Danh gia reading theo threshold cua tung vi tri."""

    def __init__(self, thresholds: dict):
        self._thresholds = self._validate_thresholds(thresholds)

    def evaluate(self, reading: dict) -> dict | None:
        """Tra ve mot alert cao nhat hoac None neu reading an toan."""
        self._validate_reading(reading)
        location_id = reading["location_id"]
        if location_id not in self._thresholds:
            raise KeyError(location_id)

        violations = []
        severity = "WARNING"
        location_thresholds = self._thresholds[location_id]
        for metric in ("temperature", "humidity"):
            deviation = self._violation_deviation(
                reading[metric], location_thresholds[metric]
            )
            if deviation is None:
                continue
            violations.append(metric)
            if deviation >= CRITICAL_DEVIATIONS[metric]:
                severity = "CRITICAL"

        if not violations:
            return None
        return {
            "sensor_id": reading["sensor_id"],
            "location_id": location_id,
            "timestamp": reading["timestamp"],
            "severity": severity,
            "violated_metrics": violations,
            "temperature": reading["temperature"],
            "humidity": reading["humidity"],
        }

    @classmethod
    def _validate_thresholds(cls, thresholds: dict) -> dict:
        if not isinstance(thresholds, dict):
            raise TypeError("thresholds phai la dict")
        if not thresholds:
            raise ValueError("thresholds khong duoc rong")

        validated = {}
        for location_id, location_config in thresholds.items():
            cls._validate_text(location_id, "location_id")
            if not isinstance(location_config, dict):
                raise TypeError("cau hinh location phai la dict")
            if set(location_config) != LOCATION_FIELDS:
                raise ValueError("location phai co dung temperature va humidity")
            validated[location_id] = {}
            for metric in ("temperature", "humidity"):
                metric_config = location_config[metric]
                cls._validate_metric_threshold(metric_config)
                validated[location_id][metric] = deepcopy(metric_config)
        return validated

    @classmethod
    def _validate_metric_threshold(cls, metric_config: dict) -> None:
        if not isinstance(metric_config, dict):
            raise TypeError("cau hinh metric phai la dict")
        if set(metric_config) != METRIC_FIELDS:
            raise ValueError("cau hinh metric sai schema")

        for field in ("min_inclusive", "max_inclusive"):
            if not isinstance(metric_config[field], bool):
                raise TypeError("inclusive flag phai la bool")
        for field in ("min", "max"):
            value = metric_config[field]
            if value is not None:
                cls._validate_number(value, field)

        minimum = metric_config["min"]
        maximum = metric_config["max"]
        if minimum is None and maximum is None:
            raise ValueError("metric phai co it nhat mot bien")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError("min khong duoc lon hon max")

    @classmethod
    def _validate_reading(cls, reading: dict) -> None:
        if not isinstance(reading, dict):
            raise TypeError("reading phai la dict")
        if set(reading) != READING_FIELDS:
            raise ValueError("reading sai schema 7 field")

        for field in ("sensor_id", "sensor_type", "location_id"):
            cls._validate_text(reading[field], field)
        if not isinstance(reading["status"], str):
            raise TypeError("status phai la str")
        if reading["status"] != "ACTIVE":
            raise ValueError("chi danh gia reading cua Sensor ACTIVE")
        cls._validate_number(reading["temperature"], "temperature")
        cls._validate_number(reading["humidity"], "humidity")
        cls._validate_timestamp(reading["timestamp"])

    @staticmethod
    def _validate_text(value: object, field: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{field} phai la str")
        if not value.strip():
            raise ValueError(f"{field} khong duoc rong")

    @staticmethod
    def _validate_number(value: object, field: str) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{field} phai la so")
        if not isfinite(value):
            raise ValueError(f"{field} phai la so huu han")

    @staticmethod
    def _validate_timestamp(value: object) -> None:
        if not isinstance(value, str):
            raise TypeError("timestamp phai la str")
        if not value.strip():
            raise ValueError("timestamp khong duoc rong")
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as error:
            raise ValueError("timestamp phai dung ISO 8601") from error
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("timestamp phai co timezone")

    @staticmethod
    def _violation_deviation(value: float, threshold: dict) -> float | None:
        minimum = threshold["min"]
        maximum = threshold["max"]
        if minimum is not None:
            below = value < minimum
            equal_exclusive = value == minimum and not threshold["min_inclusive"]
            if below or equal_exclusive:
                return minimum - value
        if maximum is not None:
            above = value > maximum
            equal_exclusive = value == maximum and not threshold["max_inclusive"]
            if above or equal_exclusive:
                return value - maximum
        return None
