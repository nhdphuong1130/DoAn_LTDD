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

Nếu cổng bị chiếm, chỉ đổi các biến `*_HOST_PORT` trong `.env`. Không sửa URL hay
port trong Python/Dart. Nếu volume cũ không tương thích, sao lưu dữ liệu trước
khi tạo project Docker mới; không xóa volume khi chưa có bản sao lưu.
