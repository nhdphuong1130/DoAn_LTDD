# Thiết lập trên Linux

## Yêu cầu

- Docker Engine và Docker Compose v2.
- Android Studio với Android SDK.
- Flutter stable. Có thể cài theo hướng dẫn chính thức rồi thêm `flutter/bin`
  vào `PATH`.

## Backend

```bash
cp .env.example .env
```

Thay toàn bộ giá trị `ChangeThis`/`replace-with` trong `.env`, đặc biệt là mật
khẩu SQL Server, Neo4j, MinIO, JWT và OpenRouter. Sau đó:

```bash
docker compose --env-file .env config --quiet
docker compose --env-file .env up -d sqlserver neo4j minio minio-init
docker compose --env-file .env run --rm api alembic upgrade head
docker compose --env-file .env up -d api worker
```

API Swagger nằm tại `http://localhost:<API_HOST_PORT>/docs`. DBeaver kết nối
SQL Server qua `localhost:<SQLSERVER_HOST_PORT>` bằng thông tin trong `.env`.

## GPU NVIDIA tùy chọn

Máy RTX 2050 cần NVIDIA driver và NVIDIA Container Toolkit. Dừng worker CPU rồi
chạy profile GPU:

```bash
docker compose --env-file .env stop worker
docker compose --env-file .env --profile gpu up -d worker-gpu
```

Các máy không có NVIDIA tiếp tục dùng `worker`; cấu hình mặc định không yêu cầu GPU.

## Sao lưu

Không sao chép volume bằng tay khi container đang ghi dữ liệu. Dùng `sqlcmd` để
`BACKUP DATABASE`, Neo4j dump theo phiên bản image và MinIO `mc mirror`. Lưu bản
sao lưu ngoài thư mục Git và kiểm tra phục hồi định kỳ.
