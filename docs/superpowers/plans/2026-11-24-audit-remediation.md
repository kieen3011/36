# Audit Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Khắc phục toàn bộ finding blocking của FINAL_MVP_AUDIT_REPORT và xác minh lại core cùng web demo mà không đổi public API/schema G0.

**Architecture:** Giữ nguyên module boundaries. `StatisticsTracker` validate `details` theo JSON-safe tree và xuất JSON qua temporary file cùng thư mục rồi atomic replace; test khóa threshold/alert contract và low-risk hardening nằm trong module hiện hữu. Core commit được cherry-pick an toàn sang web branch sau khi core gate xanh.

**Tech Stack:** Python 3.13 Standard Library, unittest, React/Vite/Vitest, FastAPI.

**Spec:** `docs/audit/FINAL_MVP_AUDIT_REPORT.md` (audit evidence được bảo toàn ở integration worktree) và yêu cầu AUTONOMOUS AUDIT REMEDIATION trong phiên làm việc.

## Global Constraints

- Không đổi public API hoặc schema đã khóa.
- Comment/docstring tiếng Việt không dấu; identifiers tiếng Anh.
- Không sửa main, không force-push, không deploy.
- Test-first cho mọi thay đổi hành vi.
- Core phải PASS trước khi tích hợp web.

## Review Focus

- Nested JSON value không hữu hạn/object/cycle phải bị từ chối trước khi đổi state.
- Mọi lỗi serialization/write phải giữ nguyên target cũ và dọn temp.
- CSV formula prefix phải an toàn nhưng header/schema không đổi.
- Boundary A/B/C và humidity critical phải khớp G0 fixture/config.
- Core cherry-pick không được làm hỏng API, downloads hoặc dashboard.

---

### Task 1: SEC-001 JSON validation và atomic export

**Files:** `statistics.py`, `tests/test_statistics.py`

- [ ] Viết regression tests cho object, NaN/Infinity nested, tuple/set, key không phải chuỗi, cycle, nested hợp lệ.
- [ ] Chạy test để xác nhận RED.
- [ ] Implement recursive validator và `json.dumps(..., allow_nan=False)`.
- [ ] Viết test giữ target cũ khi `os.replace`/write failure và cleanup temp; xác nhận RED.
- [ ] Implement temp file cùng thư mục, flush, fsync, replace và cleanup.
- [ ] Chạy statistics suite và full suite.

### Task 2: TEST-01/02 và Error Record field coverage

**Files:** `tests/test_alerts.py`, `tests/test_statistics.py`, `tests/fixtures.py`

- [ ] Thêm humidity-only 9.9 WARNING, 10.0 CRITICAL và temperature-normal/humidity-critical.
- [ ] Thêm full boundary matrix cho B/C và equality `config.THRESHOLDS == G0 fixture`.
- [ ] Tách invalid Error Record theo từng field/schema/type/value.
- [ ] Chạy targeted và full suite.

### Task 3: Low-risk hardening và governance hygiene

**Files:** `statistics.py`, `main.py`, tests tương ứng, `README.md`, governance/docs/EOF files.

- [ ] Viết RED tests cho CSV formula neutralization và CLI steps 201.
- [ ] Implement spreadsheet-safe prefix và CLI max 200; cập nhật tài liệu.
- [ ] Giữ MonitoringManager private-field finding deferred vì accessor mới đổi public contract.
- [ ] Cập nhật G0 thành APPROVED/LOCKED dựa trên phê duyệt người dùng đã có; không thêm danh tính approver.
- [ ] Dọn blank EOF được audit nêu và chạy branch-wide diff check.

### Task 4: Core release gate và commit

- [ ] Chạy full unittest, py_compile, CLI 10 steps, CSV/JSON/security probes và diff check.
- [ ] Review độc lập security, architecture và tests; sửa finding trong scope.
- [ ] Commit/push `fix/audit-remediation` nếu mọi gate PASS.

### Task 5: Web integration và release gate

**Files:** core files được cherry-pick vào `feature/web-demo`; web adapter/tests chỉ sửa nếu regression chứng minh cần.

- [ ] Cherry-pick core remediation commit vào web branch sau core PASS.
- [ ] Chạy Python/API/frontend/build/CLI/CSV/JSON/npm audit/diff checks.
- [ ] Review độc lập kết quả tích hợp.
- [ ] Commit bổ sung chỉ khi cần, push `feature/web-demo`; không merge/deploy.
