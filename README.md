# English 7 GraphRAG

API-first learning application grounded exclusively in verified content from
*Tiếng Anh 7 – Global Success* Unit 1 and Unit 2.

## Thành phần

- FastAPI API/worker, SQL Server, Neo4j và MinIO qua Docker Compose.
- Hierarchical Graph-Vector Fusion: vector candidates, graph traversal và RRF.
- OpenRouter chỉ nhận context SGK đã xác minh và citation được backend kiểm tra.
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
cd mobile
flutter analyze
flutter test
```

## Tài liệu

- [Thiết lập Linux](docs/setup-linux.md)
- [Thiết lập Windows](docs/setup-windows.md)
- [Android Studio](docs/android-studio.md)
- [Thiết kế hệ thống](docs/plans/2026-09-18-english7-graphrag-design.md)
