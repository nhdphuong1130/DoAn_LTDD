# Thiết lập trên Windows

## Yêu cầu

- Windows 11, WSL2 và Docker Desktop ở chế độ Linux containers.
- Android Studio, Android SDK và Flutter stable.
- DBeaver hoặc SQL Server Management Studio đều có thể dùng để xem SQL Server.

## Khởi động

Mở PowerShell tại thư mục dự án:

```powershell
Copy-Item .env.example .env
docker compose --env-file .env config --quiet
docker compose --env-file .env up -d sqlserver neo4j minio minio-init
docker compose --env-file .env run --rm api alembic upgrade head
docker compose --env-file .env up -d api worker
```

Sửa `.env` trước khi chạy và không commit file này. Đồng đội Windows dùng cùng
schema/migration và image Docker như Linux, vì vậy không tạo database thủ công
khác với migration.

## Giới hạn tài nguyên và vận hành CPU trên Windows

- **Giới hạn CPU và RAM:** Trong môi trường WSL2 và Docker Desktop, việc chạy DocLayout-YOLO và PaddleOCR trên CPU tiêu tốn một lượng bộ nhớ và luồng xử lý đáng kể. Khuyến nghị thiết lập file `%USERPROFILE%\.wslconfig` với tối thiểu `memory=6GB` và `processors=4` để tránh hiện tượng worker bị hệ điều hành tắt do thiếu bộ nhớ (OOM).
- **Chế độ thiết bị:** Đặt `ENGLISH7_INGESTION_DEVICE=cpu` hoặc `auto` trong `.env` khi chạy trên máy Windows không hỗ trợ GPU passthrough.
- **Tải mô hình lần đầu:** Lần đầu chạy worker cần đường truyền Internet ổn định để container tải trọng số mô hình YOLO và PaddleOCR. Sau đó, mô hình sẽ được lưu trong container cache.
- **Thời hạn lưu trữ ảnh:** Ảnh học sinh tải lên được lưu tạm thời theo thời gian quy định tại `ENGLISH7_IMAGE_UPLOAD_RETENTION_MINUTES` và được bảo vệ theo phạm vi tài khoản của học sinh.

Nếu cổng bị chiếm, chỉ đổi các biến `*_HOST_PORT` trong `.env`. Không sửa URL hay
port trong Python/Dart. Nếu volume cũ không tương thích, sao lưu dữ liệu trước
khi tạo project Docker mới; không xóa volume khi chưa có bản sao lưu.
