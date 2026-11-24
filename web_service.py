"""Adapter in-memory cho FastAPI va dashboard web."""

import csv
from copy import deepcopy
from datetime import timedelta
from io import StringIO

from alerts import AlertSystem
from config import SENSOR_PROFILES, START_TIME, STEP_MINUTES, THRESHOLDS
from main import _build_manager, _handle_event, _make_error
from simulation import SimulationEngine
from statistics import CSV_FIELDS, StatisticsTracker, _spreadsheet_safe


def _collect_error(event, manager):
    """Sao chep Error Record ma orchestrator tao cho event he thong."""
    sensor = manager.get_sensor(event["sensor_id"])
    if sensor is None:
        return _make_error(event, "UNKNOWN_SENSOR", "Khong tim thay cam bien")
    if event["kind"] == "DISCONNECT":
        return _make_error(event, "DISCONNECT", "Mat ket noi cam bien")
    if event["kind"] == "INVALID_DATA":
        return _make_error(
            event,
            "INVALID_DATA",
            "Du lieu cam bien khong hop le",
            {"temperature": event["temperature"], "humidity": event["humidity"]},
        )
    if event["kind"] not in {"READING", "RECOVER"}:
        return _make_error(
            event,
            "PROCESSING_ERROR",
            "Loai event khong duoc ho tro",
            {"kind": event["kind"]},
        )
    return None


def _build_csv(alerts):
    """Tao noi dung CSV tu danh sach alert cua phien hien tai."""
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for alert in alerts:
        row = deepcopy(alert)
        row["violated_metrics"] = ";".join(row["violated_metrics"])
        writer.writerow(
            {key: _spreadsheet_safe(value) for key, value in row.items()}
        )
    return stream.getvalue()


def simulate_session(mssv, steps, sensor_profiles=None, thresholds=None):
    """Chay mo phong trong bo nho va tra payload day du cho web."""
    if isinstance(steps, bool) or not isinstance(steps, int):
        raise TypeError("steps must be an integer")
    if steps <= 0:
        raise ValueError("steps must be greater than zero")

    profiles = deepcopy(SENSOR_PROFILES if sensor_profiles is None else sensor_profiles)
    threshold_config = deepcopy(THRESHOLDS if thresholds is None else thresholds)
    engine = SimulationEngine(mssv, profiles)
    manager = _build_manager()
    alert_system = AlertSystem(threshold_config)
    tracker = StatisticsTracker()
    timeline = []
    alerts = []
    errors = []

    for step_index in range(steps):
        timestamp = (
            START_TIME + timedelta(minutes=STEP_MINUTES * step_index)
        ).isoformat()
        current_alerts = []
        current_errors = []
        for event in engine.generate_events(step_index, timestamp):
            error_record = _collect_error(event, manager)
            alert = _handle_event(event, manager, alert_system, tracker)
            if alert is not None:
                current_alerts.append(deepcopy(alert))
                alerts.append(deepcopy(alert))
            if error_record is not None:
                current_errors.append(deepcopy(error_record))
                errors.append(deepcopy(error_record))
        timeline.append(
            {
                "step_index": step_index,
                "timestamp": timestamp,
                "readings": manager.collect_readings(),
                "alerts": current_alerts,
                "errors": current_errors,
            }
        )

    sensors = manager.collect_readings()
    summary = tracker.get_summary()
    session = {
        "mssv": mssv,
        "steps": steps,
        "started_at": timeline[0]["timestamp"],
        "ended_at": timeline[-1]["timestamp"],
    }
    json_download = {
        "session": deepcopy(session),
        "sensors": deepcopy(sensors),
        "timeline": deepcopy(timeline),
        "alerts": deepcopy(alerts),
        "errors": deepcopy(errors),
        "summary": deepcopy(summary),
    }
    return {
        **json_download,
        "downloads": {
            "csv": _build_csv(alerts),
            "json": json_download,
        },
    }
