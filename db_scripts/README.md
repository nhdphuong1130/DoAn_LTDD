# Thư mục Database Scripts

Thư mục này chứa các kịch bản SQL khởi tạo, di trú lược đồ (migrations) và dữ liệu mẫu (seed data) cho Microsoft SQL Server.

## Danh mục scripts

- `init_schema.sql`: Kịch bản kiểm tra và tạo cơ sở dữ liệu `english7` nếu chưa tồn tại.
- Để áp dụng migrations mới nhất qua Alembic:
  ```bash
  cd backend && uv run alembic upgrade head
  ```
- Để nạp dữ liệu mẫu SGK:
  ```bash
  make seed
  ```
