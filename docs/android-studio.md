# Android Studio và Flutter

1. Cài plugin **Flutter** trong Android Studio; plugin Dart sẽ được cài kèm.
2. Chọn Flutter SDK đã cài trên máy, không trỏ SDK vào repository.
3. Mở thư mục `mobile/` như một Flutter project.
4. Chạy `flutter doctor -v` và tự chấp nhận Android SDK licenses sau khi đọc điều khoản:

```bash
flutter doctor --android-licenses
```

Ứng dụng bắt buộc nhận API URL ở thời điểm build/run:

```bash
flutter run --dart-define=API_BASE_URL=http://<backend-host>:<api-port>
```

Với Android Emulator, `<backend-host>` là địa chỉ host mà emulator truy cập được;
với điện thoại thật, dùng IP LAN hoặc HTTPS endpoint. Giá trị này không được ghi
trực tiếp vào mã Dart. Có thể thêm `--dart-define` trong Run Configuration của
Android Studio.

Chạy kiểm tra trước khi commit:

```bash
flutter analyze
flutter test
```
