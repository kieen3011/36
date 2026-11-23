"""Application Orchestrator cho he thong giam sat nha kho."""

import argparse
from copy import deepcopy
from datetime import timedelta
from pathlib import Path

from alerts import AlertSystem
from config import (
    SENSOR_DEFINITIONS,
    SENSOR_PROFILES,
    START_TIME,
    STEP_MINUTES,
    THRESHOLDS,
)
from display import render_snapshot, render_summary
from monitoring_manager import MonitoringManager
from sensors import ColdStorageSensor, DryStorageSensor, ServerRoomSensor
from simulation import SimulationEngine
from statistics import StatisticsTracker


SENSOR_CLASSES = {
    "COLD_STORAGE": ColdStorageSensor,
    "DRY_STORAGE": DryStorageSensor,
    "SERVER_ROOM": ServerRoomSensor,
}


def _build_manager():
    """Khoi tao registry cam bien mac dinh theo G0."""
    manager = MonitoringManager()
    for definition in SENSOR_DEFINITIONS:
        sensor_class = SENSOR_CLASSES[definition["sensor_type"]]
        manager.register_sensor(
            sensor_class(definition["sensor_id"], definition["location_id"])
        )
    return manager


def _make_error(event, error_type, message, details=None):
    """Tao Error Record dung schema G0."""
    return {
        "sensor_id": event["sensor_id"],
        "timestamp": event["timestamp"],
        "error_type": error_type,
        "message": message,
        "details": dict(details or {}),
    }


def _handle_event(event, manager, alert_system, tracker):
    """Ap dung mot event va tra ve alert moi cua event do."""
    sensor = manager.get_sensor(event["sensor_id"])
    if sensor is None:
        tracker.record_error(
            _make_error(event, "UNKNOWN_SENSOR", "Khong tim thay cam bien")
        )
        return None

    kind = event["kind"]
    if kind == "DISCONNECT":
        sensor.set_status("ERROR")
        tracker.record_error(_make_error(event, "DISCONNECT", "Mat ket noi cam bien"))
        return None
    if kind == "RECOVER":
        if sensor.get_reading()["status"] == "ERROR":
            sensor.set_status("ACTIVE")
        return None
    if kind == "INVALID_DATA":
        tracker.record_error(
            _make_error(
                event,
                "INVALID_DATA",
                "Du lieu cam bien khong hop le",
                {"temperature": event["temperature"], "humidity": event["humidity"]},
            )
        )
        return None
    if kind != "READING":
        tracker.record_error(
            _make_error(
                event,
                "PROCESSING_ERROR",
                "Loai event khong duoc ho tro",
                {"kind": kind},
            )
        )
        return None

    try:
        accepted = sensor.update_measurement(
            event["temperature"], event["humidity"], event["timestamp"]
        )
        if not accepted:
            return None
        reading = sensor.get_reading()
        alert = alert_system.evaluate(reading)
        if alert is not None:
            tracker.record_alert(alert)
        return alert
    except (TypeError, ValueError, KeyError) as error:
        tracker.record_error(
            _make_error(
                event,
                "PROCESSING_ERROR",
                "Khong the xu ly phep do",
                {"exception": type(error).__name__, "reason": str(error)},
            )
        )
        return None


def run_simulation(
    mssv,
    steps=10,
    output_dir="output",
    sensor_profiles=None,
    thresholds=None,
    render=True,
):
    """Chay mot phien mo phong xac dinh va tra ve ket qua cuoi."""
    if isinstance(steps, bool) or not isinstance(steps, int):
        raise TypeError("steps must be an integer")
    if steps <= 0:
        raise ValueError("steps must be greater than zero")
    if not isinstance(render, bool):
        raise TypeError("render must be a boolean")

    profiles = deepcopy(SENSOR_PROFILES if sensor_profiles is None else sensor_profiles)
    alert_thresholds = deepcopy(THRESHOLDS if thresholds is None else thresholds)
    engine = SimulationEngine(mssv, profiles)
    manager = _build_manager()
    alert_system = AlertSystem(alert_thresholds)
    tracker = StatisticsTracker()

    for step_index in range(steps):
        timestamp = (
            START_TIME + timedelta(minutes=STEP_MINUTES * step_index)
        ).isoformat()
        current_alerts = []
        for event in engine.generate_events(step_index, timestamp):
            alert = _handle_event(event, manager, alert_system, tracker)
            if alert is not None:
                current_alerts.append(alert)
        readings = manager.collect_readings()
        if render:
            render_snapshot(readings, current_alerts, step_index)

    output_path = Path(output_dir)
    tracker.export_csv(str(output_path / "alert_logs.csv"))
    tracker.export_json(str(output_path / "report.json"))
    summary = tracker.get_summary()
    if render:
        render_summary(summary)
    return {"summary": summary, "readings": manager.collect_readings()}


def _positive_integer(value):
    """Chuyen doi tham so CLI thanh so nguyen duong."""
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("steps phai la so nguyen") from error
    if parsed <= 0:
        raise argparse.ArgumentTypeError("steps phai lon hon 0")
    return parsed


def _non_blank_text(value):
    """Tu choi chuoi CLI rong hoac chi co khoang trang."""
    if not value.strip():
        raise argparse.ArgumentTypeError("gia tri khong duoc rong")
    return value


def build_parser():
    """Tao parser CLI theo contract G0."""
    parser = argparse.ArgumentParser(description="IoT Warehouse Monitoring System")
    parser.add_argument("--mssv", required=True, type=_non_blank_text)
    parser.add_argument("--steps", type=_positive_integer, default=10)
    parser.add_argument("--output-dir", type=_non_blank_text, default="output")
    return parser


def main(argv=None):
    """Entry point cua ung dung console."""
    arguments = build_parser().parse_args(argv)
    run_simulation(arguments.mssv, arguments.steps, arguments.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
