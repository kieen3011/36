# Hướng dẫn triển khai Vercel

## Cấu hình repository

- Frontend: Vite build ra `dist/` bằng `npm run build`.
- Backend: FastAPI entrypoint `app:app` khai báo trong `pyproject.toml`.
- Python: `.python-version` chọn Python 3.13.
- Function: `vercel.json` đặt thời gian tối đa 30 giây.
- Không cần database, secret hoặc biến môi trường.

## Các bước triển khai thủ công

1. Push branch `feature/web-demo` lên GitHub.
2. Trong Vercel, chọn **Add New → Project** và import repository `kieen3011/36`.
3. Chọn Production Branch hoặc branch preview là `feature/web-demo`.
4. Giữ Build Command `npm run build`; không đặt Output Directory thủ công vì FastAPI phục vụ `dist/`.
5. Deploy và chờ build hoàn tất.
6. Chỉ công bố thành công sau khi kiểm tra URL thật.

## Checklist sau deploy

```text
GET  https://<deployment>/api/health         → 200, status=ok
POST https://<deployment>/api/simulate       → 200 với request hợp lệ
POST https://<deployment>/api/simulate       → 422 với steps=0 hoặc MSSV rỗng
GET  https://<deployment>/                    → dashboard được tải
```

Trên dashboard, chạy cùng MSSV và số bước hai lần để xác nhận kết quả deterministic; sau đó tải CSV/JSON và so sánh với phiên đang hiển thị.

## Giới hạn serverless

- Mỗi request tự tạo phiên trong bộ nhớ; không kỳ vọng file hoặc state còn tồn tại sau request.
- `steps` giới hạn 200 để tránh request kéo dài quá mức.
- Cấu hình hiện tại chưa được gọi là **DEPLOYED** nếu chưa có deployment URL và chưa chạy checklist trên URL đó.

## Tài liệu nền tảng

- FastAPI on Vercel: <https://vercel.com/docs/frameworks/backend/fastapi>
- Python runtime: <https://vercel.com/docs/functions/runtimes/python>
- Vite on Vercel: <https://vercel.com/docs/frameworks/frontend/vite>
