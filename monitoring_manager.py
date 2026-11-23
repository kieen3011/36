"""Quan ly registry va snapshot cua cac cam bien."""

from sensors import Sensor


def _validate_sensor_id(sensor_id):
    """Kiem tra sensor ID ma khong chuan hoa chuoi."""
    if not isinstance(sensor_id, str):
        raise TypeError("sensor_id must be a string")
    if not sensor_id.strip():
        raise ValueError("sensor_id must not be blank")


class MonitoringManager:
    """Quan ly thu tu dang ky va thu thap snapshot cam bien."""

    def __init__(self):
        self._sensors = {}

    def register_sensor(self, sensor):
        """Dang ky mot Sensor chua ton tai trong registry."""
        if not isinstance(sensor, Sensor):
            raise TypeError("sensor must be a Sensor")
        sensor_id = sensor._sensor_id
        if sensor_id in self._sensors:
            raise ValueError(f"duplicate sensor_id: {sensor_id}")
        self._sensors[sensor_id] = sensor

    def remove_sensor(self, sensor_id):
        """Xoa Sensor theo ID va tra ve ket qua."""
        _validate_sensor_id(sensor_id)
        return self._sensors.pop(sensor_id, None) is not None

    def get_sensor(self, sensor_id):
        """Lay Sensor theo ID neu ton tai."""
        _validate_sensor_id(sensor_id)
        return self._sensors.get(sensor_id)

    def get_all_sensors(self):
        """Tra ve list moi theo thu tu dang ky."""
        return list(self._sensors.values())

    def collect_readings(self):
        """Thu thap snapshot cua tat ca Sensor theo thu tu dang ky."""
        return [sensor.get_reading() for sensor in self._sensors.values()]
