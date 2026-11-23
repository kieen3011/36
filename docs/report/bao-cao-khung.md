# Báo cáo Chủ đề 36 — IoT Warehouse Monitoring System

## 1. Giới thiệu đề tài

Hệ thống mô phỏng việc giám sát nhiệt độ và độ ẩm tại kho lạnh, kho khô và phòng máy chủ. Chương trình phát hiện điều kiện môi trường không an toàn, phân loại cảnh báo và tổng hợp số lần vượt ngưỡng theo khu vực.

## 2. Phân tích yêu cầu

MVP đáp ứng sáu yêu cầu: sinh dữ liệu mô phỏng; quản lý nhiều Sensor; cấu hình ngưỡng theo vị trí; phát hiện vượt ngưỡng; phân loại WARNING/CRITICAL; thống kê số lần cảnh báo. Phạm vi không yêu cầu thiết bị IoT thật, cơ sở dữ liệu, website hoặc cloud.

## 3. Cơ sở lý thuyết Python OOP

Thiết kế sử dụng lớp `Sensor` làm concrete base class và ba lớp con mỏng. Dữ liệu nội bộ được đóng gói; module giao tiếp bằng dictionary theo schema đã khóa. Mỗi lớp và module có một trách nhiệm rõ ràng.

## 4. Thiết kế kiến trúc

`main.py` là Application Orchestrator. Luồng xử lý là SimulationEngine → Sensor/MonitoringManager → AlertSystem → StatisticsTracker → Display. Snapshot dùng để hiển thị, còn AlertSystem chỉ nhận reading mới được cập nhật thành công để tránh tính lặp cảnh báo từ dữ liệu cũ.

## 5. Mô tả từng module

- TV1: Sensor, các lớp Sensor con, MonitoringManager và Orchestrator.
- TV2: SimulationEngine, Random Walk và sự kiện DISCONNECT/RECOVER/INVALID_DATA.
- TV3: AlertSystem, validation ngưỡng và severity.
- TV4: StatisticsTracker, chống trùng và CSV/JSON.
- TV5: console Display và tài liệu dự án.

## 6. Thuật toán mô phỏng

MSSV được chuyển thành seed ổn định bằng SHA-256. Mỗi Sensor có trạng thái Random Walk riêng và được xử lý theo thứ tự ID ổn định. Incident theo lịch có ưu tiên cao hơn READING; sau RECOVER, Sensor tiếp tục đo từ step kế tiếp.

## 7. Thuật toán cảnh báo

AlertSystem kiểm tra nhiệt độ và độ ẩm theo location. Vi phạm nhẹ tạo WARNING. Độ lệch nhiệt độ từ 3°C hoặc độ ẩm từ 10 điểm phần trăm tạo CRITICAL. Một reading vi phạm cả hai metric vẫn chỉ tạo một Alert Record với severity cao nhất.

## 8. Thống kê và xử lý ngoại lệ

StatisticsTracker chống ghi trùng bằng khóa `(sensor_id, timestamp)`. Environmental Alert và Device/Data Error được lưu riêng. CSV chứa lịch sử cảnh báo; JSON chứa thông tin phiên, summary, alerts và errors. Sai kiểu gây `TypeError`; giá trị hoặc schema không hợp lệ gây `ValueError`.

## 9. Kiểm thử và kết quả

```powershell
python -m unittest discover -s tests -v
```

Kết quả tích hợp thực tế do Lead xác minh:

- **64 test đã chạy, 64 test PASS, 0 failure, 0 error**.
- Có 9 integration tests kiểm tra các luồng kết nối chính.
- Unit test của năm module PASS.
- Luồng end-to-end normal/environmental PASS.
- Luồng DISCONNECT → ERROR → RECOVER PASS.
- Không tạo lại cảnh báo từ reading cũ.
- Chống ghi trùng Alert Record PASS.
- Demo console PASS.
- Export và đọc lại CSV/JSON PASS.
- `py_compile` và `git diff --check` PASS.

## 10. Hướng dẫn cài đặt và chạy chương trình

Yêu cầu Python 3.11 trở lên, không cần thư viện ngoài.

```powershell
python main.py --mssv 2312345 --steps 10 --output-dir output
```

Sau khi chạy, kiểm tra console, `output/alert_logs.csv` và `output/report.json`.

## 11. Kết luận

MVP đã hoàn thành đầy đủ các module theo ownership và vượt mức tối thiểu 23 test với 64/64 test PASS. Kiến trúc giữ đúng nguyên tắc phân chia trách nhiệm, dữ liệu mô phỏng có thể tái lập và lỗi thiết bị được tách khỏi cảnh báo môi trường. Pull Request và quyết định merge cuối cùng thuộc quyền nghiệm thu của trưởng nhóm.

