# G0 — Decision Log cho Integration Contract MVP

**Trạng thái:** PROPOSED — chờ trưởng nhóm phê duyệt  
**Baseline:** MASTER HANDOFF V1.0  
**Phạm vi:** Chỉ khóa các chi tiết liên module còn thiếu; không thay đổi API đã được Master phê duyệt.

## 1. Nguyên tắc chung

1. Python mục tiêu là Python 3.11 trở lên và chỉ sử dụng thư viện chuẩn.
2. Comment và docstring viết bằng tiếng Việt không dấu. Identifier và API viết bằng tiếng Anh.
3. Dictionary đi qua ranh giới module phải có đúng các field đã khóa. Module nhận không tự sửa dictionary đầu vào.
4. ID là chuỗi không rỗng và không chỉ chứa khoảng trắng. ID được lưu nguyên văn; không tự động `strip()` khi lưu hoặc lookup.
5. Số hợp lệ là `int` hoặc `float`, không phải `bool`, và phải hữu hạn theo `math.isfinite()`.
6. Timestamp là chuỗi ISO 8601 có timezone. Hậu tố `Z` được chấp nhận như UTC. `None` chỉ hợp lệ trong Sensor trước khi có số đo.
7. Sai kiểu dữ liệu gây `TypeError`; đúng kiểu nhưng giá trị hoặc schema không hợp lệ gây `ValueError`; trùng ID gây `ValueError`.

## 2. Sensor contract bổ sung

### 2.1. TYPE_NAME

| Class | TYPE_NAME |
|---|---|
| `Sensor` | `GENERIC` |
| `ColdStorageSensor` | `COLD_STORAGE` |
| `DryStorageSensor` | `DRY_STORAGE` |
| `ServerRoomSensor` | `SERVER_ROOM` |

### 2.2. Validation

- `sensor_id` và `location_id`: áp dụng quy tắc ID chung.
- `status`: phải là chuỗi và thuộc `ACTIVE`, `INACTIVE`, `ERROR`.
- `set_status()` trả `None` khi thành công.
- `update_measurement()` kiểm tra trạng thái trước. Nếu Sensor không `ACTIVE`, hàm trả `False`, không validate payload và không đổi dữ liệu cũ.
- Với Sensor `ACTIVE`, payload sai kiểu gây `TypeError`; giá trị không hữu hạn hoặc timestamp sai gây `ValueError`.
- Timestamp hợp lệ được giữ đúng chuỗi đầu vào, không chuẩn hóa lại.
- `get_reading()` trả dictionary mới đúng 7 field theo thứ tự của Master.

## 3. MonitoringManager contract bổ sung

- Registry giữ thứ tự đăng ký bằng `dict` chuẩn của Python.
- `register_sensor()` trả `None`.
- `get_sensor()`, `remove_sensor()` áp dụng cùng validation ID; không strip ID.
- `get_all_sensors()` và `collect_readings()` trả list mới.
- `collect_readings()` không bắt exception từ Sensor.

## 4. Simulation contract bổ sung

### 4.1. `sensor_profiles` schema

```python
{
    "COLD-01": {
        "initial_temperature": 5.0,
        "initial_humidity": 90.0,
        "temperature_step": 0.5,
        "humidity_step": 1.0,
        "incident_schedule": {
            3: "DISCONNECT",
            4: "RECOVER",
            7: "INVALID_DATA",
        },
    }
}
```

- Khóa ngoài là `sensor_id` hợp lệ.
- Bốn giá trị số là bắt buộc, hữu hạn; hai giá trị `*_step` phải lớn hơn 0.
- `incident_schedule` là tùy chọn, mặc định `{}`; key là `int >= 0`; value thuộc `DISCONNECT`, `RECOVER`, `INVALID_DATA`.
- Không cho hai incident ở cùng sensor và step vì dictionary chỉ có một value.

### 4.2. Seed và Random Walk

- Seed: `int.from_bytes(sha256(mssv.encode("utf-8")).digest()[:8], "big")`.
- Engine sở hữu một instance `random.Random(seed)`.
- Mỗi step xử lý sensor ID theo thứ tự `sorted()`.
- Reading mới bằng giá trị trước cộng `uniform(-step, step)`, làm tròn 2 chữ số thập phân.
- Không clamp giá trị; việc vượt ngưỡng là hành vi hợp lệ của mô phỏng.
- Incident theo lịch có ưu tiên cao hơn READING.
- `DISCONNECT` và `RECOVER`: temperature/humidity bằng `None`.
- `INVALID_DATA`: temperature là chuỗi `"INVALID"`, humidity là `None`.
- Incident không cập nhật trạng thái Random Walk nội bộ.
- Sau `RECOVER`, READING sớm nhất là step kế tiếp.

### 4.3. Validation và exception

- `mssv`: chuỗi không rỗng; sai kiểu `TypeError`, rỗng `ValueError`.
- Profile sai schema gây `ValueError`; field sai kiểu gây `TypeError`.
- `step_index`: `int >= 0`, không chấp nhận bool.
- `timestamp`: ISO 8601 có timezone.

## 5. Threshold schema và Alert contract

### 5.1. Threshold schema

```python
{
    "A": {
        "temperature": {
            "min": 2.0,
            "max": 8.0,
            "min_inclusive": True,
            "max_inclusive": True,
        },
        "humidity": {
            "min": 85.0,
            "max": 95.0,
            "min_inclusive": True,
            "max_inclusive": True,
        },
    },
    "B": {
        "temperature": {
            "min": 18.0,
            "max": 25.0,
            "min_inclusive": True,
            "max_inclusive": True,
        },
        "humidity": {
            "min": None,
            "max": 60.0,
            "min_inclusive": True,
            "max_inclusive": False,
        },
    },
    "C": {
        "temperature": {
            "min": None,
            "max": 30.0,
            "min_inclusive": True,
            "max_inclusive": False,
        },
        "humidity": {
            "min": 40.0,
            "max": 60.0,
            "min_inclusive": True,
            "max_inclusive": True,
        },
    },
}
```

- Mỗi location phải có đúng `temperature` và `humidity`.
- Mỗi metric có đúng bốn field trên.
- `None` biểu diễn biên không tồn tại; flag inclusive của biên `None` không ảnh hưởng tính toán.
- `min <= max` khi cả hai tồn tại.

### 5.2. `evaluate()`

- Reading phải có đúng 7 field của Sensor Reading.
- Chỉ chấp nhận `status == "ACTIVE"`, temperature/humidity hữu hạn và timestamp khác `None`.
- Location thiếu threshold gây `KeyError(location_id)`.
- Schema/giá trị reading sai gây `TypeError` hoặc `ValueError` theo quy tắc chung.
- `violated_metrics` có thứ tự cố định: `temperature`, rồi `humidity`.
- Độ lệch critical được đo tới biên bị vi phạm gần nhất.
- Với biên exclusive, giá trị bằng biên là WARNING dù độ lệch số học bằng 0.
- Temperature critical khi độ lệch `>= 3.0`; humidity critical khi độ lệch `>= 10.0`.
- Hàm không sửa reading đầu vào.

## 6. Statistics contract bổ sung

### 6.1. Error Record schema

```python
{
    "sensor_id": "COLD-01",
    "timestamp": "2026-11-23T00:03:00+07:00",
    "error_type": "DISCONNECT",
    "message": "Mat ket noi cam bien",
    "details": {},
}
```

- Có đúng 5 field.
- `error_type` thuộc `DISCONNECT`, `INVALID_DATA`, `PROCESSING_ERROR`, `UNKNOWN_SENSOR`.
- `message` là chuỗi không rỗng; `details` là dictionary.
- Error không dùng khóa chống trùng của environmental alert.

### 6.2. Summary schema

```python
{
    "total_alerts": 2,
    "total_errors": 1,
    "by_location": {
        "A": {"WARNING": 1, "CRITICAL": 1, "total": 2},
    },
    "errors_by_type": {"DISCONNECT": 1},
}
```

- Chỉ location đã có alert xuất hiện trong `by_location`.
- Dictionary location được sắp xếp theo ID khi tạo snapshot/export.
- `get_summary()` trả deep copy đủ để caller không sửa trạng thái tracker.

### 6.3. CSV và JSON

- CSV encoding `utf-8`, `newline=""`.
- CSV header cố định: `sensor_id,location_id,timestamp,severity,violated_metrics,temperature,humidity`.
- `violated_metrics` trong CSV nối bằng dấu `;`.
- JSON encoding UTF-8, `ensure_ascii=False`, indent 2.
- JSON schema:

```python
{
    "session": {
        "started_at": "timestamp nho nhat hoac null",
        "ended_at": "timestamp lon nhat hoac null",
    },
    "summary": {},
    "alerts": [],
    "errors": [],
}
```

- Export tạo thư mục cha nếu chưa tồn tại; lỗi hệ thống file không bị nuốt.
- Alert sai schema/severity gây `TypeError` hoặc `ValueError`.
- Duplicate `(sensor_id, timestamp)` trả `False` và không thay đổi state.

## 7. Display contract bổ sung

- Alert hiện tại được ghép với reading bằng `sensor_id`; danh sách alerts chỉ thuộc step hiện tại.
- Alert level là severity nếu có alert; nếu không là `NORMAL` cho ACTIVE, `N/A` cho INACTIVE/ERROR.
- Giá trị thiếu hiển thị `N/A`.
- Sensor không ACTIVE nhưng có last measurement hiển thị thêm nhãn `(gia tri cu)`.
- `render_snapshot()` và `render_summary()` trả `None`, ghi ra stdout và không sửa input.
- Không dùng `rich`, `matplotlib` hoặc dependency ngoài.

## 8. Orchestrator và cấu hình phiên

- CLI: `python main.py --mssv <MSSV> [--steps 10] [--output-dir output]`.
- `--mssv` bắt buộc, chuỗi không rỗng.
- `--steps` mặc định 10, phải là số nguyên dương.
- Thời điểm bắt đầu cố định: `2026-11-23T00:00:00+07:00`.
- Khoảng cách step: 1 phút.
- Timestamp step `n` bằng start time cộng `n` phút.
- Sensor mặc định:
  - `COLD-01`, location `A`, class `ColdStorageSensor`.
  - `DRY-01`, location `B`, class `DryStorageSensor`.
  - `SERVER-01`, location `C`, class `ServerRoomSensor`.
- Unknown sensor event được ghi `UNKNOWN_SENSOR`, không làm dừng toàn phiên.
- `INVALID_DATA` được ghi error và không gọi `update_measurement()`.
- Exception dự kiến từ validation được chuyển thành `PROCESSING_ERROR`; lỗi lập trình ngoài contract không bị bắt bằng `except Exception: pass`.
- Output cuối phiên: `<output-dir>/alert_logs.csv` và `<output-dir>/report.json`.

## 9. Shared fixtures bắt buộc

### 9.1. Timestamp

- Step 0: `2026-11-23T00:00:00+07:00`.
- Step 1: `2026-11-23T00:01:00+07:00`.
- Step 3: `2026-11-23T00:03:00+07:00`.

### 9.2. Reading fixtures

- Normal A: `5.0°C`, `90.0%`.
- Boundary A: `2.0°C`, `85.0%` và `8.0°C`, `95.0%` đều NORMAL.
- Warning B: `25.1°C`, `59.0%`.
- Exclusive warning B: humidity `60.0%`.
- Critical B: temperature `28.0°C`.
- Warning C: temperature `30.0°C`.
- Dual critical A: temperature `11.0°C`, humidity `105.0%`; một record, severity CRITICAL.

### 9.3. Event fixtures

- `DISCONNECT`: cả hai metric `None`.
- `RECOVER`: cả hai metric `None`.
- `INVALID_DATA`: temperature `"INVALID"`, humidity `None`.

### 9.4. Duplicate fixture

- Hai Alert Record giống `sensor_id="COLD-01"` và cùng timestamp; record thứ hai phải trả `False`.

## 10. Ownership khóa sau G0

| TV | Owned files |
|---|---|
| TV1 Kiên | `main.py`, `config.py`, `sensors.py`, `monitoring_manager.py`, `tests/test_sensors.py`, `tests/test_monitoring_manager.py`, `tests/test_integration.py` |
| TV2 Lợi | `simulation.py`, `tests/test_simulation.py`, tài liệu Simulation |
| TV3 Lộc | `alerts.py`, `tests/test_alerts.py`, tài liệu Alert |
| TV4 Lương | `statistics.py`, `tests/test_statistics.py`, báo cáo QA/export |
| TV5 Thục | `display.py`, `tests/test_display.py`, `docs/report/` |
| Lead | `tests/fixtures.py`, tài liệu governance, review report; không sửa implementation của worker trừ vòng sửa lỗi được giao rõ ràng |

Không worker nào sửa file của owner khác. Thay đổi contract phải dừng phần bị ảnh hưởng và quay lại phê duyệt.

## 11. Contract Conformance Gate

Mỗi module chỉ được bàn giao khi:

1. Chữ ký API khớp Master và G0.
2. Schema, validation và exception khớp Decision Log.
3. Unit test của module PASS với bằng chứng lệnh chạy.
4. Không có dependency ngoài thư viện chuẩn.
5. Comment/docstring và identifier tuân thủ quy định ngôn ngữ.
6. Không sửa file ngoài ownership.
7. Review chéo không còn finding Critical/High; finding Medium phải được sửa hoặc có quyết định chấp nhận rõ ràng.

## 12. Test acceptance tối thiểu

- Sensor: ít nhất 6 test.
- MonitoringManager: ít nhất 5 test.
- Simulation: ít nhất 3 test.
- Alert: ít nhất 4 test.
- Statistics/Export: ít nhất 3 test.
- End-to-end: ít nhất 2 test.
- Display có test riêng ngoài mức tối thiểu 23 nếu triển khai kiểm tra stdout.
- Lệnh chuẩn: `python -m unittest discover -s tests -v` để không cần dependency ngoài.

## 13. Quyết định cần phê duyệt trong G0

Phê duyệt G0 đồng nghĩa chấp nhận toàn bộ các mục 1–12 như phần bổ sung cho MASTER HANDOFF V1.0. Nếu có mục bị từ chối, ghi rõ số mục và giá trị thay thế; không cần duyệt lại các mục không đổi.

## 14. Cơ chế kích hoạt sau phê duyệt

1. Lead commit riêng Decision Log đã phê duyệt lên `main` để năm branch có cùng contract gốc. Commit này chỉ chứa tài liệu governance, không chứa production code.
2. Lead tạo năm branch từ đúng commit G0 trên `main`: `feature/tv1-Kien`, `feature/tv2-Loi`, `feature/tv3-Loc`, `feature/tv4-Luong`, `feature/tv5-Thuc`.
3. Mỗi branch có worktree riêng dưới `.worktrees/`; thư mục này đã được ignore.
4. Shared fixtures do Lead chuẩn bị từ G0 trước khi worker viết production code và được phân phối nguyên trạng cho các worktree.
5. Tối đa ba worker hoạt động đồng thời vì Lead chiếm một trong bốn slot.
6. Không merge feature branch vào `main`; PR chỉ được tạo để trưởng nhóm nghiệm thu.

