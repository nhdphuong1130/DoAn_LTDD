# Thiết kế hồ sơ cá nhân và đăng xuất

## Mục tiêu

Bổ sung cho ứng dụng học sinh một khu vực **Cá nhân** dễ tìm, cho phép xem và
cập nhật hồ sơ, đổi mật khẩu và đăng xuất an toàn. Thay đổi phải tương thích với
tài khoản hiện có, không làm thay đổi hành vi của bài học, Tutor, quiz hoặc tiến
độ học tập.

## Phạm vi MVP

- Thêm tab thứ năm `Cá nhân` vào `StudentShell`.
- Hiển thị họ tên, email, ngày sinh, giới tính, trường, lớp và vai trò.
- Cho phép sửa mọi trường hồ sơ ngoại trừ email và vai trò.
- Cho phép đổi mật khẩu sau khi xác minh mật khẩu hiện tại.
- Cho phép đăng xuất bằng cách xóa access token trong secure storage và quay về
  màn hình đăng nhập.
- Khi khởi động, khôi phục phiên từ token đã lưu nếu token còn hợp lệ.

Không thuộc MVP: upload ảnh đại diện, sửa email, refresh token, danh sách thiết
bị, thu hồi JWT phía server và tích hợp thống kê học tập vào hồ sơ.

## Dữ liệu

Bảng `users` được mở rộng bằng một Alembic migration với các cột nullable:

```text
full_name        Unicode(255)
date_of_birth    Date
gender           String(30)
school_name      Unicode(255)
class_name       Unicode(100)
```

Các cột nullable bảo đảm tài khoản cũ tiếp tục hoạt động. `gender` chỉ nhận
`male`, `female`, `other` hoặc `prefer_not_to_say`. Chuỗi tùy chọn sau khi trim
mà rỗng được lưu thành `NULL`. Email tiếp tục là định danh đăng nhập, được hiển
thị chỉ đọc trong MVP.

Domain `AuthUser` mang theo các trường hồ sơ nhưng không bao giờ đưa
`password_hash` vào API response. Repository chịu trách nhiệm đọc/cập nhật đúng
user ID lấy từ token.

## API và quy tắc nghiệp vụ

### `GET /api/v1/auth/me`

Trả về `id`, `email`, `role`, `full_name`, `date_of_birth`, `gender`,
`school_name`, `class_name`. Endpoint yêu cầu bearer token hợp lệ.

### `PATCH /api/v1/auth/me`

Nhận các trường hồ sơ có thể chỉnh sửa. Request không nhận `user_id`, `email`,
`role`, `password_hash` hoặc trạng thái tài khoản. Backend trim chuỗi, chuẩn hóa
chuỗi rỗng thành `null`, giới hạn độ dài và từ chối giá trị giới tính ngoài enum.
Response trả hồ sơ sau cập nhật.

### `POST /api/v1/auth/change-password`

Nhận `current_password`, `new_password`, `confirm_password`. Backend phải:

1. xác minh mật khẩu hiện tại;
2. yêu cầu mật khẩu mới dài 8–128 ký tự;
3. yêu cầu xác nhận khớp;
4. không cho mật khẩu mới trùng mật khẩu hiện tại;
5. hash bằng `PasswordHasher` hiện có rồi cập nhật trong một transaction.

Endpoint trả `204 No Content`. Token hiện tại tiếp tục hợp lệ trong kiến trúc
JWT stateless hiện tại.

### Đăng xuất

MVP không cần endpoint server. Mobile xóa token khỏi `SecureTokenStore`, xóa
state hồ sơ và chuyển state gốc về unauthenticated. Điều này ngăn ứng dụng tiếp
tục gửi token, nhưng token không bị thu hồi server-side trước thời điểm hết hạn.

## Mobile UI và quản lý phiên

`StudentApi` bổ sung các thao tác `restoreSession`, `loadProfile`,
`updateProfile`, `changePassword` và `logout`. `ApiStudentApi` ánh xạ chúng vào
API và token store.

`English7App` dùng ba trạng thái khởi động: `checking`, `authenticated`,
`unauthenticated`. Trong `checking`, ứng dụng hiển thị progress indicator. Nó đọc
token và gọi `/auth/me`; token thiếu hoặc response `401` sẽ bị xóa. Lỗi mạng
không được giả làm token sai: ứng dụng hiển thị khả năng thử lại thay vì âm thầm
đăng xuất.

`ProfileScreen` có:

- header dùng avatar chữ cái từ họ tên hoặc email;
- thẻ thông tin hồ sơ và vai trò;
- form chỉnh sửa với date picker và dropdown giới tính;
- form đổi mật khẩu có ẩn/hiện nội dung;
- nút đăng xuất màu cảnh báo với dialog xác nhận.

Sau khi logout, `English7App` thay toàn bộ `StudentShell` bằng `LoginScreen`, nên
nút Back không thể quay lại nội dung đã đăng nhập. Form giữ dữ liệu khi API lỗi,
khóa nút khi request đang chạy và hiển thị lỗi bằng tiếng Việt.

## Luồng dữ liệu

```text
App start -> token store -> GET /auth/me
  -> 200: StudentShell/ProfileScreen
  -> no token or 401: clear token -> LoginScreen
  -> network/server error: retry state

Profile edit -> PATCH /auth/me -> validated SQL update -> refreshed profile
Change password -> verify current -> hash new -> SQL update -> success message
Logout confirm -> clear secure token -> clear profile state -> LoginScreen
```

## Xử lý lỗi và an toàn

- Toàn bộ profile/password endpoint lấy user từ JWT, không tin user ID của
  client.
- Sai mật khẩu hiện tại trả error code ổn định, không tiết lộ password hash.
- Validation trả lỗi theo field để mobile hiển thị rõ ràng.
- Chỉ response `401` làm mất phiên tự động; timeout/5xx cho phép thử lại.
- Mọi controller và async callback trên Flutter kiểm tra `mounted` trước khi cập
  nhật state.
- Logout phải đợi thao tác xóa secure storage hoàn tất trước khi đổi màn hình.

## Kiểm thử và tiêu chí chấp nhận

Backend:

- Migration tạo đúng cột nullable và hỗ trợ Unicode tiếng Việt.
- `/auth/me` trả đủ hồ sơ và không lộ password hash.
- PATCH chỉ cập nhật chính người dùng hiện tại, chuẩn hóa dữ liệu và từ chối
  gender/độ dài sai.
- Đổi mật khẩu kiểm tra mật khẩu cũ, xác nhận, hash mới và cho phép đăng nhập
  bằng mật khẩu mới.
- Tài khoản khác không bị thay đổi.

Mobile:

- Token hợp lệ khôi phục phiên; thiếu token hoặc `401` trở về login.
- Tab Cá nhân tải, hiển thị và cập nhật hồ sơ.
- Form giữ dữ liệu khi lưu lỗi.
- Đổi mật khẩu hiển thị trạng thái thành công/thất bại.
- Logout có xác nhận, xóa token và không thể Back vào Student Shell.

Hoàn thành khi unit/widget/API tests xanh, migration chạy trên database rỗng,
Flutter analyze không có lỗi và các chức năng hiện tại không hồi quy.
