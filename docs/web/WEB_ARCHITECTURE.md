# Kiến trúc Web Demo — Chủ đề 36

## Mục tiêu

Web demo trình bày trực quan hệ thống giám sát kho nhưng giữ nguyên Python OOP Core và Integration Contract G0. React chỉ hiển thị dữ liệu do FastAPI trả về; không mô phỏng lại thuật toán trong JavaScript.

## Luồng dữ liệu

```text
React Dashboard
  └─ POST /api/simulate {mssv, steps}
       └─ FastAPI validation
            └─ web_service.simulate_session()
                 ├─ SimulationEngine
                 ├─ Sensor + MonitoringManager
                 ├─ AlertSystem
                 └─ StatisticsTracker
                      └─ JSON response + CSV/JSON in-memory downloads
```

`GET /api/health` không chạy mô phỏng và chỉ xác nhận function đã sẵn sàng.

## Hợp đồng API

### Request

```json
{
  "mssv": "2312345",
  "steps": 10
}
```

- `mssv`: chuỗi không rỗng sau khi loại khoảng trắng hai đầu, tối đa 64 ký tự.
- `steps`: số nguyên nghiêm ngặt, từ 1 đến 200.

### Response

- `session`: MSSV, số bước, thời điểm đầu/cuối.
- `sensors`: snapshot cuối phiên theo Sensor Reading G0.
- `timeline`: reading, alert và error theo từng time-step.
- `alerts`: chỉ cảnh báo môi trường WARNING/CRITICAL.
- `errors`: lỗi thiết bị/dữ liệu như DISCONNECT và INVALID_DATA.
- `summary`: tổng hợp bởi `StatisticsTracker`.
- `downloads`: CSV cảnh báo và JSON của chính phiên đang hiển thị.

## Tính chất vận hành

- Deterministic theo MSSV và số bước.
- Stateless: không database, không authentication, không ghi session xuống local disk.
- CSV được tạo bằng `csv.DictWriter`; JSON dùng object response cùng phiên nên không lệch dữ liệu hiển thị.
- FastAPI phục vụ `dist/` khi bundle tồn tại. Khi phát triển, Vite proxy `/api` sang Uvicorn.

## Frontend

Dashboard có KPI, snapshot cảm biến, thống kê cảnh báo theo vị trí, biểu đồ nhiệt độ/độ ẩm bằng SVG, danh sách cảnh báo môi trường, lỗi thiết bị và tải báo cáo. Biểu đồ bỏ reading cũ khi mất kết nối và ngắt đường tại khoảng dữ liệu thiếu. Form, button và vùng lỗi dùng semantic HTML; layout chuyển sang một cột trên màn hình nhỏ.

## Biên giới kiến trúc

`web_service.py` tái sử dụng orchestrator hiện hành và không thay đổi API của các module core. CLI tiếp tục chạy trực tiếp qua `main.py`; web adapter không can thiệp output CLI.
