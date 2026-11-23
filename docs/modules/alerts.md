# Module AlertSystem

## Trách nhiệm

`AlertSystem` kiểm tra một số đo mới đã được Sensor chấp nhận, đối chiếu với ngưỡng của vị trí và trả về tối đa một bản ghi cảnh báo môi trường. Module không thay đổi Sensor, không ghi thống kê và không xử lý lỗi thiết bị.

## API

```python
AlertSystem(thresholds: dict)
evaluate(reading: dict) -> dict | None
```

`thresholds` và `reading` phải tuân thủ schema trong `G0_DECISION_LOG.md`. Cấu hình được sao chép khi khởi tạo để thay đổi bên ngoài không làm thay đổi hành vi của hệ thống.

## Kết quả

- Trả về `None` khi nhiệt độ và độ ẩm đều an toàn.
- Trả về một Alert Record đúng 7 trường khi có ít nhất một metric vi phạm.
- `violated_metrics` luôn theo thứ tự `temperature`, sau đó `humidity`.
- Severity tổng là `CRITICAL` nếu có ít nhất một metric đạt ngưỡng critical; nếu không là `WARNING`.

## Quy tắc biên

- Biên inclusive nhận giá trị bằng ngưỡng là an toàn.
- Biên exclusive nhận giá trị bằng ngưỡng là `WARNING` dù độ lệch số học bằng 0.
- Nhiệt độ đạt `CRITICAL` khi lệch khỏi biên ít nhất 3°C.
- Độ ẩm đạt `CRITICAL` khi lệch khỏi biên ít nhất 10 điểm phần trăm.

## Ngoại lệ

- `TypeError`: sai kiểu dictionary, chuỗi, số hoặc cờ inclusive.
- `ValueError`: sai schema, giá trị không hữu hạn, Sensor không `ACTIVE`, timestamp thiếu timezone hoặc cấu hình ngưỡng không hợp lệ.
- `KeyError(location_id)`: reading dùng vị trí chưa được cấu hình.

Module không bắt và che giấu các ngoại lệ này; Orchestrator chịu trách nhiệm xử lý tại ranh giới tích hợp.

## Kiểm thử

`tests/test_alerts.py` kiểm tra reading bình thường, toàn bộ biên kho lạnh, biên exclusive, WARNING, CRITICAL, hai metric cùng vi phạm, tính bất biến của input và các trường hợp validation quan trọng.

Chạy riêng module:

```text
python -m unittest tests.test_alerts -v
```
