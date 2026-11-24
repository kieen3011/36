"""Theo doi canh bao, loi he thong va xuat bao cao."""

from __future__ import annotations

import csv
import json
import math
import os
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import tempfile


ALERT_FIELDS = {
    "sensor_id",
    "location_id",
    "timestamp",
    "severity",
    "violated_metrics",
    "temperature",
    "humidity",
}
ERROR_FIELDS = {"sensor_id", "timestamp", "error_type", "message", "details"}
ERROR_TYPES = {
    "DISCONNECT",
    "INVALID_DATA",
    "PROCESSING_ERROR",
    "UNKNOWN_SENSOR",
}
SEVERITIES = {"WARNING", "CRITICAL"}
METRICS = ("temperature", "humidity")
CSV_FIELDS = [
    "sensor_id",
    "location_id",
    "timestamp",
    "severity",
    "violated_metrics",
    "temperature",
    "humidity",
]


def _validate_identifier(value, field_name):
    """Kiem tra mot dinh danh chuoi ma khong tu dong strip."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def _parse_timestamp(value):
    """Phan tich timestamp ISO 8601 co timezone."""
    if not isinstance(value, str):
        raise TypeError("timestamp must be a string")
    if not value.strip():
        raise ValueError("timestamp must not be blank")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError("timestamp must be valid ISO 8601") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include timezone")
    return parsed


def _validate_timestamp(value):
    """Kiem tra timestamp ISO 8601 co timezone."""
    _parse_timestamp(value)


def _validate_number(value, field_name):
    """Kiem tra gia tri so huu han va loai bo bool."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a number")
    if not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite")


def _validate_path(file_path):
    """Kiem tra duong dan xuat file."""
    if not isinstance(file_path, str):
        raise TypeError("file_path must be a string")
    if not file_path.strip():
        raise ValueError("file_path must not be blank")
    return Path(file_path)


def _validate_json_safe(value, path="details", ancestors=None):
    """Kiem tra cay du lieu chi chua gia tri JSON an toan va khong co chu ky."""
    if value is None or type(value) in (bool, str, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{path} must contain only finite numbers")
        return
    if type(value) not in (list, dict):
        raise TypeError(f"{path} must contain only JSON-safe values")

    active = set() if ancestors is None else ancestors
    identity = id(value)
    if identity in active:
        raise ValueError(f"{path} must not contain cyclic references")
    active.add(identity)
    try:
        if type(value) is list:
            for index, item in enumerate(value):
                _validate_json_safe(item, f"{path}[{index}]", active)
            return
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError(f"{path} keys must be strings")
            _validate_json_safe(item, f"{path}.{key}", active)
    finally:
        active.remove(identity)


def _spreadsheet_safe(value):
    """Vo hieu hoa prefix cong thuc khi mo CSV bang spreadsheet."""
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


class StatisticsTracker:
    """Luu lich su va tong hop canh bao cung loi he thong."""

    def __init__(self):
        self._alerts = []
        self._errors = []
        self._alert_keys = set()

    def record_alert(self, alert: dict) -> bool:
        """Them canh bao hop le neu khoa cam bien va timestamp chua ton tai."""
        self._validate_alert(alert)
        key = (alert["sensor_id"], alert["timestamp"])
        if key in self._alert_keys:
            return False
        self._alerts.append(deepcopy(alert))
        self._alert_keys.add(key)
        return True

    def record_error(self, error: dict) -> None:
        """Them mot loi he thong hop le ma khong chong ghi trung."""
        self._validate_error(error)
        self._errors.append(deepcopy(error))

    def get_summary(self) -> dict:
        """Tra ve ban sao tong hop theo location, severity va loai loi."""
        by_location = {}
        for alert in self._alerts:
            location = alert["location_id"]
            counts = by_location.setdefault(
                location, {"WARNING": 0, "CRITICAL": 0, "total": 0}
            )
            counts[alert["severity"]] += 1
            counts["total"] += 1
        errors_by_type = {}
        for error in self._errors:
            error_type = error["error_type"]
            errors_by_type[error_type] = errors_by_type.get(error_type, 0) + 1
        summary = {
            "total_alerts": len(self._alerts),
            "total_errors": len(self._errors),
            "by_location": {
                key: by_location[key] for key in sorted(by_location)
            },
            "errors_by_type": {
                key: errors_by_type[key] for key in sorted(errors_by_type)
            },
        }
        return deepcopy(summary)

    def export_csv(self, file_path: str) -> None:
        """Xuat lich su canh bao moi truong sang CSV UTF-8."""
        target = _validate_path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for alert in self._alerts:
                row = deepcopy(alert)
                row["violated_metrics"] = ";".join(row["violated_metrics"])
                writer.writerow(
                    {key: _spreadsheet_safe(value) for key, value in row.items()}
                )

    def export_json(self, file_path: str) -> None:
        """Xuat thong tin phien, tong hop, canh bao va loi sang JSON."""
        target = _validate_path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        timestamps = [item["timestamp"] for item in self._alerts]
        timestamps.extend(item["timestamp"] for item in self._errors)
        started_at = min(timestamps, key=_parse_timestamp) if timestamps else None
        ended_at = max(timestamps, key=_parse_timestamp) if timestamps else None
        report = {
            "session": {
                "started_at": started_at,
                "ended_at": ended_at,
            },
            "summary": self.get_summary(),
            "alerts": deepcopy(self._alerts),
            "errors": deepcopy(self._errors),
        }
        serialized = json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(serialized)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, target)
        except Exception:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise

    @staticmethod
    def _validate_alert(alert):
        """Kiem tra Alert Record dung schema G0."""
        if not isinstance(alert, dict):
            raise TypeError("alert must be a dictionary")
        if set(alert) != ALERT_FIELDS:
            raise ValueError("alert must contain exactly the contract fields")
        _validate_identifier(alert["sensor_id"], "sensor_id")
        _validate_identifier(alert["location_id"], "location_id")
        _validate_timestamp(alert["timestamp"])
        severity = alert["severity"]
        if not isinstance(severity, str):
            raise TypeError("severity must be a string")
        if severity not in SEVERITIES:
            raise ValueError("severity must be WARNING or CRITICAL")
        metrics = alert["violated_metrics"]
        if not isinstance(metrics, list):
            raise TypeError("violated_metrics must be a list")
        if not metrics or len(metrics) != len(set(metrics)):
            raise ValueError("violated_metrics must be non-empty and unique")
        if any(not isinstance(metric, str) for metric in metrics):
            raise TypeError("violated_metrics values must be strings")
        expected_order = [metric for metric in METRICS if metric in metrics]
        if metrics != expected_order:
            raise ValueError("violated_metrics must use contract values and order")
        _validate_number(alert["temperature"], "temperature")
        _validate_number(alert["humidity"], "humidity")

    @staticmethod
    def _validate_error(error):
        """Kiem tra Error Record dung schema G0."""
        if not isinstance(error, dict):
            raise TypeError("error must be a dictionary")
        if set(error) != ERROR_FIELDS:
            raise ValueError("error must contain exactly the contract fields")
        _validate_identifier(error["sensor_id"], "sensor_id")
        _validate_timestamp(error["timestamp"])
        error_type = error["error_type"]
        if not isinstance(error_type, str):
            raise TypeError("error_type must be a string")
        if error_type not in ERROR_TYPES:
            raise ValueError("error_type is not supported")
        message = error["message"]
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        if not message.strip():
            raise ValueError("message must not be blank")
        if not isinstance(error["details"], dict):
            raise TypeError("details must be a dictionary")
        _validate_json_safe(error["details"])
