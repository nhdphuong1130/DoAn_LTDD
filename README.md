# English 7 Grounded Learning Platform

Nền tảng học tiếng Anh lớp 7 có gia sư AI sư phạm chuẩn mực, được tiếp đất (grounded) trực tiếp vào nội dung sách giáo khoa *Tiếng Anh 7 – Global Success* (Tập 1 và Tập 2).

Hệ thống này cho phép:

- Học bài học tương tác chuẩn SGK từ Unit 1 đến Unit 12 và các bài Review 1, 2, 3, 4.
- Nghe bài nghe audio bản ngữ chất lượng cao với trình phát âm thanh tích hợp.
- Làm các bài tập tương tác: bảng phát âm ngữ âm IPA (`/ə/`, `/ɜː/`), đọc hiểu True/False, nối từ vựng, trắc nghiệm.
- Hỏi đáp gia sư AI thông minh với cam kết 100% câu trả lời có trích dẫn xuất xứ sách giáo khoa (`[Unit X, Trang Y]`).
- Tải ảnh bài tập từ camera hoặc thư viện để gia sư AI nhận diện và hướng dẫn giải bài.
- Luyện tập bài thi trắc nghiệm tính giờ với giới hạn số lần nghe audio và chấm điểm tự động.
- Quản lý hồ sơ học sinh cá nhân (thông tin trường lớp, ngày sinh, đổi mật khẩu an toàn).

---

## Kiến trúc Hệ thống

Hệ thống gồm các thành phần chính:

- `sqlserver`: Microsoft SQL Server 2022 lưu trữ dữ liệu người dùng, hồ sơ, bài thi và cấu trúc bài học.
- `neo4j`: Cơ sở dữ liệu đồ thị Neo4j 5.26 lưu trữ Đồ thị Tri thức Sư phạm (Pedagogical Knowledge Graph) và chỉ mục vector kép (Dual Vector Indexing).
- `minio`: Lưu trữ đối tượng tương thích S3 cho các file âm thanh MP3 và hình ảnh bài học.
- `backend`: REST API xây dựng bằng Python 3.12 (FastAPI, SQLAlchemy, FastEmbed, Pytest).
- `worker`: Dịch vụ chạy nền xử lý tác vụ nạp tri thức và lập chỉ mục.
- `mobile`: Ứng dụng di động học sinh viết bằng Flutter / Dart 3.x (hỗ trợ Android & iOS).

Luồng truy xuất tri thức gia sư (GraphRAG):
1. Học sinh gửi câu hỏi hoặc ảnh chụp bài tập.
2. Backend trích xuất câu hỏi và sinh vector nhúng cục bộ qua `FastEmbed` (`BAAI/bge-small-en-v1.5`, 384 chiều).
3. Thực hiện truy vấn vector kép và duyệt đồ thị tri thức đa bước (multi-hop graph traversal).
4. Hợp nhất điểm số qua thuật toán Reciprocal Rank Fusion (RRF) để chọn đoạn trích SGK chuẩn nhất.
5. Mô hình ngôn ngữ tổng hợp lời giảng sư phạm kèm trích dẫn số trang và Unit gửi về cho học sinh.

---

## Công nghệ Chính

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, FastEmbed, PyJWT, Argon2-cffi.
- **Mobile:** Flutter 3.27+, Dart, HTTP Client, Flutter Secure Storage, Audioplayers.
- **Cơ sở dữ liệu:** Microsoft SQL Server 2022, Neo4j Community 5.26, MinIO S3 Storage.
- **Hạ tầng cục bộ:** Docker & Docker Compose, GNU Make.

---

## Cấu trúc Thư mục

```text
backend/                Mã nguồn Backend API (FastAPI, GraphRAG, 163 unit tests)
mobile/                 Mã nguồn Ứng dụng di động Flutter (33 widget & unit tests)
backups/                Thư mục sao lưu CSDL SQL Server (.bak, .sql)
db_scripts/             Kịch bản SQL khởi tạo lược đồ và seed CSDL
docs/                   Tài liệu thiết kế, hướng dẫn sử dụng và cài đặt
data/                   Dữ liệu siêu dữ liệu bài học và manifest SGK
evaluation/             Bộ dữ liệu đánh giá độ chuẩn xác truy xuất
scripts/                Các kịch bản tự động hóa, build knowledge graph, test queries
docker-compose.yml      Cấu hình cụm Docker Compose cục bộ
Makefile                Bộ lệnh Make điều khiển toàn bộ hệ thống
DESIGN.md               Tài liệu thiết kế kiến trúc và giao diện hệ thống
README.md               Tài liệu giới thiệu và hướng dẫn tổng quan dự án
```

---

## Yêu cầu Trước Khi Chạy

Cần cài sẵn trên máy:

- Docker & Docker Compose plugin (`docker compose`)
- GNU Make (`make`)
- Python 3.12 (khuyến nghị kèm công cụ quản lý gói `uv`)
- Flutter SDK (bản 3.27 trở lên)

Kiểm tra nhanh phiên bản:

```bash
docker --version
docker compose version
make --version
python3 --version
flutter --version
```

---

## Cách Chạy Hệ Thống Khi Mới Kéo Repo Về

### 1. Tạo file môi trường

Sao chép từ file mẫu:

```bash
cp .env.example .env
```

### 2. Khởi động cụm dịch vụ Docker

```bash
make up
```

Kiểm tra trạng thái các container:

```bash
make ps
```

Các cổng dịch vụ mặc định:
- **Backend API:** `http://localhost:8000` (Tài liệu Swagger: `http://localhost:8000/docs`)
- **SQL Server:** `localhost:1433`
- **Neo4j Browser:** `http://localhost:7474`
- **MinIO Console:** `http://localhost:9001`

### 3. Nạp dữ liệu bài học và Xây dựng Đồ thị Tri thức

```bash
make seed
```

Lệnh này sẽ tự động khởi tạo dữ liệu giáo trình 12 Unit vào SQL Server và xây dựng đồ thị vector sư phạm vào Neo4j.

### 4. Khởi chạy ứng dụng di động Flutter

```bash
cd mobile
flutter run
```

---

## Danh Sách Lệnh Makefile Thường Dùng

| Lệnh | Ý nghĩa |
|---|---|
| `make up` | Khởi động toàn bộ container dịch vụ ở chế độ chạy nền |
| `make down` | Dừng và dọn dẹp các container |
| `make ps` | Liệt kê trạng thái các container đang chạy |
| `make logs` | Xem live log từ tất cả các container |
| `make restart` | Khởi động lại toàn bộ dịch vụ |
| `make test` | Chạy toàn bộ kiểm thử backend (`pytest`) và mobile (`flutter test`) |
| `make test-backend` | Chạy 163 unit test backend |
| `make test-mobile` | Chạy 33 unit và widget test mobile |
| `make analyze` | Chạy phân tích cú pháp tĩnh Flutter (yêu cầu 0 lỗi, 0 cảnh báo) |
| `make seed` | Nạp dữ liệu SGK và lập chỉ mục đồ thị tri thức |
| `make backup-db` | Sao lưu CSDL SQL Server ra thư mục `backups/` |
| `make restore FILE=backups/<file>.bak` | Khôi phục CSDL từ bản sao lưu |
| `make clean` | Dọn dẹp các file cache `__pycache__`, `.pytest_cache`, `build` |

---

## Tài Khoản Mẫu Đăng Nhập Mặc Định

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Học sinh mẫu | `student@example.com` | `password` |
| Quản trị viên | `admin@example.com` | `password` |

---

## Tài Liệu Tham Khảo Thêm

- [Tài liệu Thiết kế Hệ thống](DESIGN.md)
- [Hướng dẫn Sử dụng Chi tiết](docs/HUONG_DAN_SU_DUNG.md)
- [Đặc tả Cấu trúc Dự án](docs/project-structure.md)
- [Danh mục Thư viện Phụ thuộc](docs/dependencies.md)
- [Hướng dẫn Cài đặt Linux](docs/setup-linux.md)
- [Hướng dẫn Cài đặt Windows](docs/setup-windows.md)
- [Hướng dẫn Android Studio](docs/android-studio.md)
