# Module Display

## Trách nhiệm

Module `display.py` hiển thị snapshot cảm biến của từng bước và bảng tổng kết cuối phiên. Module chỉ đọc dữ liệu do các module khác cung cấp, không sửa registry, không đánh giá lại ngưỡng và không thay đổi severity.

## API

```python
render_snapshot(readings: list[dict], alerts: list[dict], step_index: int) -> None
render_summary(summary: dict) -> None
```

`render_snapshot()` ghép cảnh báo của bước hiện tại với reading bằng `sensor_id`. Sensor `ACTIVE` không có cảnh báo được hiển thị là `NORMAL`. Sensor `INACTIVE` hoặc `ERROR` được hiển thị mức `N/A`; nếu còn phép đo gần nhất, giá trị có nhãn `(gia tri cu)`.

`render_summary()` hiển thị tổng số cảnh báo, tổng số lỗi, thống kê theo khu vực và số lỗi theo loại từ schema Summary đã khóa trong G0.

## Giới hạn

Giao diện sử dụng `print()` của thư viện chuẩn. Module không phụ thuộc `rich`, `matplotlib` hoặc thư viện bên ngoài.
