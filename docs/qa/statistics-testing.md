# StatisticsTracker — bàn giao và kiểm thử

## Phạm vi

Module `statistics.py` ghi nhận cảnh báo môi trường, ghi lỗi hệ thống, chống trùng cảnh báo và xuất CSV/JSON theo G0.

## API

```python
StatisticsTracker()
record_alert(alert: dict) -> bool
record_error(error: dict) -> None
get_summary() -> dict
export_csv(file_path: str) -> None
export_json(file_path: str) -> None
```

`record_alert()` dùng khóa `(sensor_id, timestamp)`. Bản ghi đầu tiên trả `True`; bản ghi trùng trả `False` và không thay đổi trạng thái. Lỗi hệ thống không dùng khóa chống trùng.

## Validation

- Dictionary phải có đúng field của contract.
- ID và message không được rỗng hoặc chỉ có khoảng trắng.
- Timestamp phải là ISO 8601 có timezone.
- Severity chỉ nhận `WARNING` hoặc `CRITICAL`.
- Nhiệt độ và độ ẩm phải là số hữu hạn, không nhận `bool`.
- `violated_metrics` phải là danh sách không rỗng, không trùng và theo thứ tự `temperature`, `humidity`.
- Sai kiểu gây `TypeError`; sai giá trị hoặc schema gây `ValueError`.

## Định dạng xuất

- CSV sử dụng UTF-8, đúng bảy cột Alert Record; nhiều metric được nối bằng dấu `;`.
- JSON chứa `session`, `summary`, `alerts`, `errors`; sử dụng UTF-8 và `ensure_ascii=False`.
- Module tự tạo thư mục cha nếu chưa tồn tại và không nuốt lỗi hệ thống file.

## Kiểm thử

Lệnh kiểm thử module:

```powershell
python -m unittest tests.test_statistics -v
```

Bộ test kiểm tra ghi mới, chống trùng, đếm theo location/severity, validation, lỗi không chống trùng, deep copy summary, thứ tự location và round-trip CSV/JSON.
