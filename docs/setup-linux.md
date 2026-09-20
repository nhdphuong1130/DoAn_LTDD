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

## Vận hành Knowledge Graph Phase 1

### 1. Import ontology đã review

Migrate database và import manifest. UUID của fragment/unit trong manifest phải
tồn tại trong SQL Server; mọi assertion `verified` phải trỏ tới evidence đã
review và publish.

```bash
docker compose --env-file .env run --rm \
  -v "$PWD/data:/work/data:ro" api \
  python -m english7.cli import-ontology \
  --manifest /work/data/manifests/knowledge-ontology.example.json
```

Importer là idempotent theo `manifest_id` và checksum. Không sửa nội dung của
một manifest đã import; hãy tạo version/manifest ID mới.

### 2. Preload và smoke test embedding model

API dùng volume `fastembed-cache`, nên model tải một lần được tái sử dụng giữa
các lần chạy container. Chạy smoke test trước maintenance window:

```bash
docker compose --env-file .env run --rm api python -c \
  "import os; from fastembed import TextEmbedding; m=TextEmbedding(model_name=os.environ['ENGLISH7_EMBEDDING_MODEL'], cache_dir=os.environ['ENGLISH7_EMBEDDING_CACHE_DIR']); print(len(next(m.embed(['sở thích và healthy habits']))))"
```

Kết quả phải bằng `ENGLISH7_EMBEDDING_DIMENSIONS` (mặc định `384`). Lỗi tải
model, sai số chiều hoặc vector không hữu hạn phải được xử lý trước khi build.

### 3. Benchmark model song ngữ

Chuẩn bị JSON gồm `cases` (`id`, `query`, `expected_candidate_ids`,
`expected_units`) và `candidates` (`id`, `text`, `unit_number`), sau đó chạy:

```bash
docker compose --env-file .env run --rm \
  -v "$PWD/data:/work/data:ro" api sh -ec \
  'python -m english7.cli benchmark-embeddings \
    --cases /work/data/benchmarks/embedding-cases.json \
    --model "$ENGLISH7_EMBEDDING_MODEL" \
    --model-version "$ENGLISH7_EMBEDDING_MODEL_VERSION" \
    --dimensions "$ENGLISH7_EMBEDDING_DIMENSIONS" --top-k 5'
```

Lưu report JSON cùng model/version. So sánh ít nhất `recall_at_k`,
`unit_accuracy`, `p95_latency_ms` và `peak_rss_mb`; không đổi model chỉ dựa trên
một chỉ số retrieval.

### 4. Build, validate và activate candidate

```bash
docker compose --env-file .env run --rm api \
  python -m english7.cli build-knowledge-graph \
  --ontology-version english7-v1
```

Lệnh dựng graph dưới `build_id` mới, tạo hai vector index riêng, đợi index
`ONLINE`, đối soát expected/actual counts, orphan, duplicate, provenance và số
chiều embedding. Chỉ report có `status: active` và không có validation failure
mới được cutover. JSON đầu ra ghi lại checksum, ontology/model identity, counts
và tên index để audit. Cùng checksum + ontology + embedding identity sẽ tái sử
dụng build active thay vì dựng lại.

### 5. Failure và rollback

Candidate thất bại được đánh dấu `failed`; transaction activation không chạy,
vì vậy build `active` trước đó vẫn nguyên vẹn. Sau một activation thành công,
build trước được giữ ở trạng thái `retired` cùng các node/index theo `build_id`
để phục hồi có kiểm soát. Phase 1 chưa cung cấp lệnh tự động re-activate một
build retired: không sửa trực tiếp trạng thái SQL. Nếu cần rollback sau cutover,
dừng rollout và dùng quy trình quản trị được review để khôi phục metadata active
trước khi Phase 2 cho runtime đọc graph này.

### 6. Gate tích hợp dùng hạ tầng disposable

```bash
./scripts/test-knowledge-integration.sh
```

Gate dùng fake embedder 384 chiều nên chạy offline và ổn định. Nó tạo database
rỗng, migrate đến head, kiểm tra dữ liệu tiếng Việt, loại draft khỏi projection,
xác minh provenance/index, rồi ép candidate thứ hai thất bại để chứng minh build
đang active không bị thay thế. Script chỉ xóa tài nguyên thuộc Compose project
`english7-knowledge-integration`.

### Giới hạn Phase 1

Phase 1 chỉ xây nền graph đáng tin cậy. Tutor và quiz hiện tại **chưa đọc build
mới**. Hybrid retrieval và quiz-to-concept mapping được triển khai ở Phase 2;
mastery diagnosis, xác định lỗ hổng và remediation có xác nhận của học sinh ở
Phase 3.

## Sao lưu

Không sao chép volume bằng tay khi container đang ghi dữ liệu. Dùng `sqlcmd` để
`BACKUP DATABASE`, Neo4j dump theo phiên bản image và MinIO `mc mirror`. Lưu bản
sao lưu ngoài thư mục Git và kiểm tra phục hồi định kỳ.
