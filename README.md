# Chủ đề 36 — IoT Warehouse Monitoring System

Dự án Python OOP mô phỏng hệ thống giám sát nhiệt độ và độ ẩm tại nhiều khu vực trong nhà kho. MVP tuân theo **MASTER HANDOFF V1.0** và Integration Contract được khóa trong `docs/governance/G0_DECISION_LOG.md`.

## Yêu cầu môi trường

- Python 3.11 trở lên.
- Chỉ sử dụng Python Standard Library, không cần cài dependency bên ngoài.

## Kiến trúc

`main.py` đóng vai trò Application Orchestrator và điều phối luồng:

```text
SimulationEngine
       ↓
Sensor + MonitoringManager
       ↓
AlertSystem
       ↓
StatisticsTracker
       ↓
Console Display + CSV/JSON
```

- `sensors.py`: Sensor cơ sở và ba Sensor chuyên biệt.
- `monitoring_manager.py`: quản lý registry và tạo snapshot.
- `simulation.py`: Random Walk, seed theo MSSV và sự kiện sự cố.
- `alerts.py`: kiểm tra ngưỡng và phân loại WARNING/CRITICAL.
- `statistics.py`: chống ghi trùng, thống kê và export.
- `display.py`: hiển thị snapshot và tổng kết trên console.
- `main.py`: xử lý time-step và kết nối các module.
- `config.py`: cấu hình ngưỡng, profile và Sensor mặc định.

## Chạy chương trình

```powershell
python main.py --mssv 2312345 --steps 10 --output-dir output
```

Kết quả gồm snapshot và tổng kết trên console, `output/alert_logs.csv` và `output/report.json`. Timestamp bắt đầu tại `2026-11-23T00:00:00+07:00` và tăng một phút mỗi step.

## Chạy kiểm thử

```powershell
python -m unittest discover -s tests -v
```

Bằng chứng tích hợp gần nhất:

- **59/59 test PASS**.
- Unit, integration và end-to-end đều PASS.
- Demo console PASS.
- CSV và JSON được tạo và đọc lại thành công.

## Cấu trúc chính

```text
.
├── main.py
├── config.py
├── sensors.py
├── monitoring_manager.py
├── simulation.py
├── alerts.py
├── statistics.py
├── display.py
├── tests/
├── docs/
└── output/
```

## Quy trình branch và Pull Request

- `feature/tv1-Kien`
- `feature/tv2-Loi`
- `feature/tv3-Loc`
- `feature/tv4-Luong`
- `feature/tv5-Thuc`

Mỗi branch phải qua unit test, contract conformance và review chéo trước khi tạo Pull Request. Trưởng nhóm giữ quyền nghiệm thu và merge cuối cùng; workflow không tự merge vào `main`.

## Quy ước mã nguồn

- Comment, docstring, TODO và FIXME viết bằng tiếng Việt không dấu.
- Class, function, variable và API viết bằng tiếng Anh.
- README và báo cáo viết bằng tiếng Việt có dấu.

