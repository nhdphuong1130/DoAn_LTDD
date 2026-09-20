# Hướng Dẫn Sử Dụng Nền Tảng Học Tiếng Anh 7 Grounded Learning

Tài liệu này hướng dẫn chi tiết cách cài đặt, vận hành và sử dụng ứng dụng học tập tiếng Anh 7 có gia sư AI cho học sinh và lập trình viên.

---

## 1. Khởi động Nhanh Hệ thống

### 1.1. Chuẩn bị môi trường
- Cài đặt Docker & Docker Compose.
- Cài đặt Python 3.12 (kèm `uv`).
- Cài đặt Flutter SDK (bản 3.27 trở lên).
- Cài đặt Make (`sudo apt install make` trên Linux).

### 1.2. Khởi chạy cụm dịch vụ
Từ thư mục gốc của dự án:
```bash
# Tạo file môi trường từ mẫu
cp .env.example .env

# Khởi động SQL Server, Neo4j, MinIO, API và Worker
make up

# Kiểm tra trạng thái các container
make ps
```

### 1.3. Nạp dữ liệu sách giáo khoa & Đồ thị tri thức
```bash
make seed
```
Lệnh trên sẽ tự động:
1. Nạp toàn bộ cây nội dung Unit 1 đến Unit 12 vào SQL Server.
2. Xây dựng ontology sư phạm (chủ đề, ngữ pháp, từ vựng, ngữ âm) và sinh vector embedding vào Neo4j.

---

## 2. Hướng dẫn Dành cho Học sinh trên Ứng dụng Di động

### 2.1. Đăng nhập & Đăng ký
- Mở ứng dụng trên điện thoại hoặc máy ảo Android.
- Tài khoản mẫu mặc định:
  - **Email:** `student@example.com`
  - **Mật khẩu:** `password`
- Ứng dụng tự động ghi nhớ phiên đăng nhập an toàn qua Secure Storage, không cần đăng nhập lại mỗi khi mở app.

### 2.2. Học bài theo SGK (Tab Bài học)
- Danh sách bài học hiển thị đầy đủ 12 Unit học kỳ 1 và học kỳ 2:
  - **Học kỳ 1:** Unit 1 (Hobbies) đến Unit 6 + Review 1, 2.
  - **Học kỳ 2:** Unit 7 (Traffic) đến Unit 12 + Review 3, 4.
- Mỗi bài học chia thành các phần chuẩn SGK: *Getting Started, A Closer Look 1, A Closer Look 2, Communication, Skills 1, Skills 2, Looking Back & Project*.
- **Bài nghe Audio:** Nhấn nút Play/Pause tại các hoạt động có biểu tượng đĩa nghe để nghe giọng đọc bản xứ từ file audio chuẩn của NXB Giáo dục.
- **Bài tập tương tác:**
  - *Bảng phát âm:* Hiển thị từ và âm IPA (`/ə/` và `/ɜː/`) kèm hộp mẹo hướng dẫn phát âm chuẩn.
  - *True / False:* Chọn đúng/sai cho các câu hỏi đọc hiểu và nhận phản hồi giải thích ngay lập tức.
  - *Nối từ vựng / Điền từ:* Luyện tập phản xạ từ vựng trực quan.

### 2.3. Hỏi đáp Gia sư AI (Tab Gia sư)
- Nhập câu hỏi thắc mắc về bài học (ví dụ: *"Khi nào dùng thì hiện tại đơn?", "Cách phát âm đuôi -ed?"*).
- Học sinh có thể chụp ảnh hoặc chọn ảnh bài tập trong sách để gia sư phân tích câu hỏi.
- **Cam kết chống ảo giác:** Gia sư AI chỉ trả lời khi tìm thấy bằng chứng trong sách giáo khoa tiếng Anh 7 và luôn trích dẫn kèm số trang, số Unit cụ thể (`[Unit X, Trang Y]`).

### 2.4. Luyện tập Trắc nghiệm (Tab Kiểm tra)
- Chọn mức độ khó (Dễ / Trung bình / Khó) và thời gian làm bài (15, 45 hoặc 60 phút).
- Làm bài trắc nghiệm với đồng hồ đếm ngược và số lượt nghe bị giới hạn theo quy định bài thi.
- Nộp bài để nhận điểm số ngay lập tức cùng nhận xét đánh giá mức độ hoàn thành.

### 2.5. Hồ sơ Cá nhân (Tab Hồ sơ)
- Xem thông tin tài khoản học sinh.
- Chỉnh sửa họ tên, ngày sinh, trường học, khối lớp và phần giới thiệu bản thân.
- Đổi mật khẩu tài khoản trực tiếp trong ứng dụng.
- Đăng xuất an toàn khi muốn chuyển tài khoản.

---

## 3. Lệnh Quản trị & Sao lưu CSDL Dành cho Kỹ thuật viên

| Tác vụ | Lệnh thực hiện |
|---|---|
| Xem log hệ thống | `make logs` |
| Chạy unit test backend | `make test-backend` |
| Chạy unit test mobile | `make test-mobile` |
| Chạy toàn bộ test | `make test` |
| Kiểm tra tĩnh Flutter | `make analyze` |
| Sao lưu CSDL ra file | `make backup-db` (Lưu vào thư mục `backups/`) |
| Phục hồi CSDL | `make restore FILE=backups/<ten_file>.bak` |
