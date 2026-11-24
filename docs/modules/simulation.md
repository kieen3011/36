# Module SimulationEngine

## Trách nhiệm

`SimulationEngine` sinh sự kiện mô phỏng cho từng cảm biến theo mỗi bước thời gian. Module không thay đổi trực tiếp Sensor, không phân loại cảnh báo và không ghi thống kê.

## API

```python
SimulationEngine(mssv: str, sensor_profiles: dict)
generate_events(step_index: int, timestamp: str) -> list[dict]
```

Mỗi event có đúng năm trường:

```python
{
    "kind": "READING" | "DISCONNECT" | "RECOVER" | "INVALID_DATA",
    "sensor_id": "COLD-01",
    "timestamp": "2026-11-23T00:00:00+07:00",
    "temperature": 5.2,
    "humidity": 89.8,
}
```

## Khả năng tái lập

Seed được tạo bằng SHA-256 của MSSV, lấy 8 byte đầu theo thứ tự big-endian. Engine dùng một đối tượng `random.Random` riêng, vì vậy không làm thay đổi bộ sinh số ngẫu nhiên toàn cục. Với cùng MSSV, profile và thứ tự gọi, kết quả được tái lập.

Mỗi lần sinh READING, nhiệt độ và độ ẩm được cập nhật bằng Random Walk:

1. Sinh độ lệch đều trong khoảng âm/dương `temperature_step` hoặc `humidity_step`.
2. Cộng độ lệch vào trạng thái trước đó.
3. Làm tròn kết quả đến hai chữ số thập phân.
4. Không giới hạn giá trị để hệ thống có thể mô phỏng vượt ngưỡng.

## Xử lý sự cố

Lịch sự cố trong `incident_schedule` có ưu tiên cao hơn READING. Sự cố không tiêu thụ bước Random Walk và không cập nhật giá trị nội bộ.

- `DISCONNECT`, `RECOVER`: hai chỉ số bằng `None`.
- `INVALID_DATA`: nhiệt độ là chuỗi `"INVALID"`, độ ẩm bằng `None`.
- Sau `RECOVER`, phép đo mới có thể xuất hiện từ bước kế tiếp.

## Validation

- MSSV và sensor ID phải là chuỗi không rỗng.
- Các giá trị profile phải là số hữu hạn, không nhận `bool`.
- Bước Random Walk phải lớn hơn 0.
- Chỉ số bước phải là số nguyên không âm.
- Timestamp phải là ISO 8601 có timezone; hậu tố `Z` được chấp nhận.
- Sai kiểu gây `TypeError`; giá trị hoặc schema sai gây `ValueError`.

## Ví dụ tích hợp

```python
engine = SimulationEngine(mssv, sensor_profiles)
events = engine.generate_events(0, "2026-11-23T00:00:00+07:00")

for event in events:
    if event["kind"] == "READING":
        # Orchestrator chuyen du lieu hop le cho Sensor.
        pass
```
