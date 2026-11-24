# Báo cáo kiểm thử Web Demo

Ngày kiểm thử: 24/11/2026

Branch: `feature/web-demo`
Baseline: `integration/mvp-full` tại `e480ace0a21ceb4d885a1ec8ac7324be3ca69805`

## Phạm vi

- Regression toàn bộ Python OOP Core.
- Contract và validation của FastAPI.
- Determinism, phân tách alert/error, CSV/JSON consistency.
- Trạng thái empty/loading/error/reset của React.
- API client, nội dung download và frontend production build.
- CLI, compile Python và kiểm tra whitespace Git.

## Lệnh tái kiểm tra

```powershell
python -m unittest discover -s tests -v
npm test
npm run build
python -m compileall -q .
git diff --check
python main.py --mssv 2312345 --steps 10 --output-dir output
```

## Kết quả

| Gate | Kết quả thực tế |
|---|---|
| Python unittest | 85/85 PASS: 76 test core đã remediation + 9 test adapter/API |
| Frontend Vitest | 8/8 PASS trên 3 test files |
| Vite production build | PASS, 18 modules transformed |
| FastAPI phục vụ production bundle | PASS qua TestClient |
| CLI 10 bước | PASS, tạo CSV/JSON và tổng kết 0 alert, 2 error |
| CSV/JSON parse | PASS; số record khớp summary của phiên CLI |
| `py_compile` | PASS |
| `git diff --check` | PASS |
| Dependency audit | `npm audit`: 0 vulnerability |
| Secret pattern scan | Không phát hiện token/private key theo các pattern đã kiểm tra |

Review độc lập đã kiểm tra kiến trúc/Vercel, security/performance, UI/testing/accessibility và remediation audit core. SEC-001, TEST-01, TEST-02 cùng các finding Medium về giới hạn MSSV, thống kê theo vị trí, reading cũ trên biểu đồ và reset race đã được bổ sung regression test rồi sửa. Còn một ghi chú Low: adapter hiện suy ra Error Record cho response và core đồng thời ghi error vào `StatisticsTracker`; hai kết quả đã được test đồng nhất nhưng có thể gom về một nguồn ở refactor contract-compatible sau này.

Không dùng báo cáo này để tuyên bố Vercel đã deploy; deployment production không thuộc phạm vi branch này và chưa có URL để kiểm tra.
