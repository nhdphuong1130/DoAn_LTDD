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

## Vận hành CPU/GPU và mô hình AI

### Chế độ thiết bị suy luận (`auto / cpu / cuda`)

Biến môi trường `ENGLISH7_INGESTION_DEVICE` điều khiển thiết bị chạy DocLayout-YOLO:
- `auto`: Tự động phát hiện CUDA; nếu có GPU NVIDIA tương thích và Container Toolkit, worker dùng CUDA, ngược lại tự lùi về CPU.
- `cpu`: Buộc chạy bằng CPU (phù hợp máy không có GPU hoặc môi trường CI).
- `cuda`: Buộc chạy bằng CUDA trên GPU NVIDIA.

PaddleOCR chạy chế độ CPU ổn định cho việc nhận dạng ký tự đa ngôn ngữ (tiếng Anh và tiếng Việt).

### Tải mô hình và bộ nhớ đệm (Model Cache)

Ở lần khởi chạy đầu tiên, worker sẽ tải trọng số mô hình phát hiện bố cục (`ENGLISH7_LAYOUT_MODEL_ID`) và dữ liệu ngôn ngữ PaddleOCR (`ENGLISH7_OCR_LANGUAGES`). Các lần chạy tiếp theo sẽ tái sử dụng cache được lưu trữ nội bộ trong container.

### Thời hạn lưu trữ và dọn dẹp ảnh (`Retention Cleanup`)

Ảnh chụp bài tập của học sinh được lưu trong MinIO bucket `MINIO_UPLOAD_BUCKET` với tiền tố `ENGLISH7_IMAGE_UPLOAD_PREFIX`.
Biến `ENGLISH7_IMAGE_UPLOAD_RETENTION_MINUTES` quy định thời gian hiệu lực của ảnh (mặc định 60 phút). Các upload hết hạn sẽ bị từ chối truy vấn và được dọn dẹp khỏi hệ thống.

### Kiểm thử tích hợp và Smoke test mô hình

Để chạy bộ kiểm thử tích hợp đầy đủ với SQL Server, Neo4j và MinIO:

```bash
docker compose --env-file .env run --rm \
  -e MINIO_TEST_ENDPOINT=http://minio:9000 \
  -e MINIO_TEST_ACCESS_KEY=<MINIO_ROOT_USER> \
  -e MINIO_TEST_SECRET_KEY=<MINIO_ROOT_PASSWORD> \
  -e MINIO_TEST_BUCKET=<MINIO_UPLOAD_BUCKET> \
  -e NEO4J_TEST_URI=bolt://neo4j:7687 \
  -e NEO4J_TEST_USER=<NEO4J_USER> \
  -e NEO4J_TEST_PASSWORD=<NEO4J_PASSWORD> \
  api pytest -q
```

## Sao lưu

Không sao chép volume bằng tay khi container đang ghi dữ liệu. Dùng `sqlcmd` để
`BACKUP DATABASE`, Neo4j dump theo phiên bản image và MinIO `mc mirror`. Lưu bản
sao lưu ngoài thư mục Git và kiểm tra phục hồi định kỳ.
