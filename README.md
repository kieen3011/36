# Chủ đề 36 — IoT Warehouse Monitoring System

Dự án Python OOP mô phỏng hệ thống giám sát nhiệt độ và độ ẩm tại nhiều khu vực trong nhà kho. MVP tuân theo **MASTER HANDOFF V1.0** và Integration Contract được khóa trong `docs/governance/G0_DECISION_LOG.md`.

## Yêu cầu môi trường

- Python 3.12–3.14 (khuyến nghị Python 3.13 cho web demo).
- Node.js 20 trở lên và npm.
- CLI core chỉ dùng Python Standard Library; web API dùng FastAPI.

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

Web demo bổ sung một lớp adapter, không viết lại thuật toán mô phỏng:

```text
React/Vite → POST /api/simulate → FastAPI → web_service.py → Python OOP Core
```

- `app.py`: endpoint FastAPI, validation và phục vụ bundle frontend.
- `web_service.py`: chạy core hoàn toàn trong bộ nhớ, tạo payload và nội dung tải xuống của đúng phiên.
- `src/`: dashboard React, biểu đồ SVG, trạng thái loading/error/empty và tải CSV/JSON.
- `vercel.json`, `pyproject.toml`: cấu hình build và Python entrypoint cho Vercel.

## Chạy chương trình

```powershell
python main.py --mssv 2312345 --steps 10 --output-dir output
```

Kết quả gồm snapshot và tổng kết trên console, `output/alert_logs.csv` và `output/report.json`. Timestamp bắt đầu tại `2026-11-23T00:00:00+07:00` và tăng một phút mỗi step.

`--steps` phải nằm trong khoảng 1–200 để giới hạn tài nguyên. JSON được ghi qua file tạm cùng thư mục rồi thay thế atomic; nếu validation, serialization hoặc ghi file thất bại thì báo cáo cũ được giữ nguyên. CSV giữ nguyên schema G0 và prefix dấu nháy đơn cho chuỗi có thể bị spreadsheet hiểu là công thức.

## Chạy kiểm thử

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
npm install
npm test
npm run build
```

Xem bằng chứng mới nhất tại `docs/web/WEB_TEST_REPORT.md`.

## Chạy web demo cục bộ

Mở hai terminal tại thư mục dự án:

```powershell
# Terminal 1
python -m uvicorn app:app --reload --port 8000

# Terminal 2
npm run dev
```

Truy cập `http://localhost:5173`. Vite chuyển tiếp `/api` sang FastAPI. Health check nằm tại `http://localhost:8000/api/health`.

Để thử bản gần với production, chạy `npm run build`, sau đó khởi động Uvicorn và truy cập `http://localhost:8000`; FastAPI sẽ phục vụ thư mục `dist`.

## API web

- `GET /api/health`: trạng thái sẵn sàng của API.
- `POST /api/simulate`: nhận JSON `{ "mssv": "2312345", "steps": 10 }`.
- `steps` phải là số nguyên từ 1 đến 200; `mssv` không được rỗng.
- Kết quả gồm metadata phiên, snapshot cảm biến, timeline, alerts, errors, summary và dữ liệu CSV/JSON để tải xuống.

## Triển khai Vercel

Import repository vào Vercel, chọn branch `feature/web-demo` và giữ Build Command là `npm run build`. Vercel sử dụng `app:app` trong `pyproject.toml`; không cần biến môi trường hoặc persistent storage. Chi tiết và checklist xác minh nằm tại `docs/web/VERCEL_DEPLOYMENT.md`.

Giới hạn của demo:

- Không có database hoặc authentication.
- Không lưu session trên server; mọi kết quả được tạo trong bộ nhớ theo từng request.
- Dữ liệu là mô phỏng deterministic phục vụ học tập, không phải dữ liệu IoT thật.
- Chưa thể coi là đã deploy cho đến khi có URL Vercel và health/API/UI được kiểm tra trên URL đó.

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
├── app.py
├── web_service.py
├── src/
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
