# Thư mục sao lưu CSDL (Database Backups)

Thư mục này chứa các bản backup định dạng `.bak` hoặc `.sql` của Microsoft SQL Server tạo ra từ lệnh `make backup-db`.

Các file backup lớn không được commit lên Git nhằm bảo mật dữ liệu và tối ưu dung lượng repository.

## Lệnh sao lưu và khôi phục

- **Sao lưu:**
  ```bash
  make backup-db
  ```
- **Khôi phục:**
  ```bash
  make restore FILE=backups/<ten_file>.bak
  ```
