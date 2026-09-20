# English 7 GraphRAG

API-first learning application grounded exclusively in verified content from
*Tiếng Anh 7 – Global Success* Unit 1 and Unit 2.

## Thành phần

- FastAPI API/worker, SQL Server, Neo4j và MinIO qua Docker Compose.
- Hierarchical Graph-Vector Fusion: vector candidates, graph traversal và RRF.
- OpenRouter chỉ nhận context SGK đã xác minh và citation được backend kiểm tra.
- Image Tutor Runtime: học sinh tải ảnh bài tập (JPEG/PNG/WebP); worker chạy DocLayout-YOLO và PaddleOCR trích xuất câu hỏi đóng vai trò query signal và chỉ trả lời khi có bằng chứng SGK Unit 1–2.
- Worker hỗ trợ suy luận linh hoạt (`auto / cpu / cuda`), vận hành CPU trên Windows và GPU NVIDIA trên Linux.
- Flutter/Dart cho Android, cấu hình API qua `--dart-define`.

Phạm vi tri thức là Unit 1–2. PDF/MP3 gốc không được commit; Git chỉ chứa manifest
metadata, hash và object key.

## Docker configuration

Copy `.env.example` to `.env`, replace every local example credential, then run:

```bash
docker compose config --quiet
docker compose up --build
```

Do not commit `.env`. All ports, image tags, credentials, bucket names, and
service-facing settings are supplied through environment variables.

## Kiểm thử

```bash
docker compose --env-file .env.example run --rm api pytest -q
./scripts/test-knowledge-integration.sh
cd mobile
flutter analyze
flutter test
```

Script `test-knowledge-integration.sh` tạo SQL Server và Neo4j dùng một lần,
kiểm tra migrate/import/build/validate/activate và rollback an toàn khi candidate
lỗi, rồi tự xóa container, network và volume thuộc project kiểm thử.

## Knowledge graph Phase 1

Phase 1 đã cung cấp nguồn tri thức có review trong SQL Server, ontology có
provenance, embedding song ngữ có version và các Neo4j build cô lập theo
`build_id`. Candidate chỉ được active sau khi counts, quan hệ, kích thước vector
và vector index đều hợp lệ; candidate lỗi không thay thế build active trước đó.

Phase này **chưa chuyển tutor hoặc quiz runtime sang graph mới**. Hybrid
retrieval/tutor và quiz mapping thuộc Phase 2; chẩn đoán mastery và remediation
thuộc Phase 3. Xem quy trình import, benchmark, build và phục hồi trong
[Thiết lập Linux](docs/setup-linux.md#vận-hành-knowledge-graph-phase-1).

## Hồ sơ cá nhân và Phiên đăng nhập

- Quản lý hồ sơ học sinh: Xem và cập nhật thông tin cá nhân (Họ tên, Ngày sinh, Giới tính, Trường học, Lớp) qua `GET /api/v1/auth/me` và `PATCH /api/v1/auth/me`.
- Đổi mật khẩu an toàn qua `POST /api/v1/auth/password`.
- Quản lý phiên đăng nhập & Đăng xuất: Ứng dụng tự động khôi phục phiên từ secure storage khi mở app; chức năng Đăng xuất xóa token đã lưu trên thiết bị. Do sử dụng JWT không lưu trạng thái (stateless), việc đăng xuất phía client không yêu cầu bảng thu hồi token phía máy chủ.
- Yêu cầu di trú cơ sở dữ liệu: Chạy `alembic upgrade head` trước khi khởi động dịch vụ để thêm các cột hồ sơ Unicode cho bảng người dùng.

## Tài liệu

- [Thiết lập Linux](docs/setup-linux.md)
- [Thiết lập Windows](docs/setup-windows.md)
- [Android Studio](docs/android-studio.md)
- [Thiết kế hệ thống](docs/plans/2026-09-18-english7-graphrag-design.md)
