# Thiết kế flashcard và luyện nói

Ngày: 2026-09-25. Trạng thái: thống nhất phạm vi sản phẩm qua brainstorming;
chưa triển khai. Các lựa chọn kỹ thuật bên dưới là đề xuất cần kiểm chứng.

## Quyết định đã thống nhất

- Học từ và luyện nói theo Unit của Tiếng Anh 7 Global Success.
- Có bộ từ SGK được kiểm duyệt và bộ từ do học sinh tự tạo.
- Bộ cá nhân chỉ chủ tài khoản được xem; chưa chia sẻ bộ từ trong bản đầu.
- Nhận dạng giọng nói thành bản chép lời, trả nhận xét và đọc phản hồi bằng VieNeu-TTS.
- Ưu tiên tự chạy, không sử dụng dịch vụ bắt buộc trả phí theo lượt.
- Học sinh được chọn giọng gia sư, nghe thử và đổi lựa chọn.

## Flashcard

Bộ SGK chia theo Unit, có nguồn thật dạng `[Unit X, Page Y]`; tái sử dụng
ontology Vocabulary và PronunciationSound. Không tự tạo số trang để lấp dữ liệu thiếu.
Học sinh có thể lưu từ SGK vào bộ cá nhân và giữ liên kết nguồn.

Bộ cá nhân có tên, từ/cụm từ tiếng Anh và nghĩa tiếng Việt. Ví dụ, ghi chú và
hình ảnh là tùy chọn. Cho thêm/sửa/xóa từ, chuyển bộ và cảnh báo trùng từ trong bộ.
Từ trùng dữ liệu SGK được gợi ý dùng nội dung kiểm duyệt; không tự ghi đè nội dung
học sinh nhập. Phân biệt nội dung SGK, cá nhân và gợi ý AI.

Mặt trước gợi nhớ từ; mặt sau có nghĩa, loại từ, phát âm, ví dụ và nguồn nếu có.
Buổi học đề xuất: ôn thẻ đến hạn → học khoảng 5 từ mới → chọn nghĩa/điền từ → luyện nói.
Có đánh dấu từ khó và lựa chọn Chưa nhớ/Còn khó/Đã nhớ. Việc lật thẻ không chứng minh
đã thuộc: lịch ôn kết hợp kết quả truy hồi ở nhiều buổi. Thuật toán/lịch cụ thể sẽ
được xác định trong kế hoạch triển khai, với đồng hồ có thể thay thế trong test.

## Luyện nói và phản hồi

Bản đầu ưu tiên đọc từ/câu mẫu ngắn, đề xuất bản thu 5–15 giây; hội thoại tự do
không nằm trong phạm vi đầu. Học sinh nghe mẫu → thu âm → nghe lại hoặc thu lại →
gửi → xem bản chép lời và phản hồi → nghe hướng dẫn → luyện lại.

Đề xuất faster-whisper chạy cục bộ để chép lời. Đối chiếu với câu mẫu, hiển thị từ
khớp/khác/chưa nhận ra. Đây là **mức độ khớp câu mẫu**, không phải điểm phát âm
từng âm. Không dùng độ tin cậy nhận dạng làm điểm phát âm; nhận dạng cũng có thể sai.
Không khẳng định lỗi âm cụ thể khi không có bộ đánh giá âm học được kiểm chứng.

Phản hồi ngắn, tiếng Việt, chỉ gợi ý có căn cứ từ kết quả; bản đầu có thể dùng
mẫu nhận xét để không phụ thuộc API ngôn ngữ trả phí. Nếu bổ sung LLM, cần quyết
định model tự chạy và đo chất lượng trước. Phản hồi không được sửa sai nội dung SGK.

VieNeu-TTS đọc nhận xét/giải nghĩa tiếng Việt, dự kiến dùng bản mã nguồn mở v3 Turbo
và giọng dựng sẵn. Danh sách ban đầu 2–4 giọng nam/nữ phải được nghe kiểm duyệt;
tên/model/license được chốt khi thử nghiệm. Mỗi giọng có nút nghe thử cùng một câu;
lưu lựa chọn theo tài khoản. Audio tiếng Anh ưu tiên SGK hoặc nguồn đã kiểm duyệt,
không mặc định lấy giọng Việt làm chuẩn. Với từ cá nhân chưa có audio chuẩn, cần
chọn giải pháp tiếng Anh miễn phí và kiểm chứng trước khi mở bài đọc mẫu.

## Tiến độ

- Từ vựng: thẻ đến hạn, kết quả nhớ qua các lần kiểm tra và từ cần ôn thêm.
- Luyện nói: số bài hoàn thành, lịch sử bản chép lời và mức độ khớp câu mẫu.
- Tách hoàn thành hoạt động khỏi thành thạo. Không gộp điểm nói/flashcard thành
  điểm quiz hiện có hoặc tuyên bố thành thạo chỉ từ số lần học.
- Lưu theo tài khoản, cập nhật sau khi lưu hoạt động thành công và khi mở Tiến độ.

## Kiến trúc và dữ liệu đề xuất

Flutter: các feature flashcards và speaking dùng StudentApi; màn hình không gọi
trực tiếp model. Backend router xác thực vai trò student và quyền sở hữu; service
chứa lịch ôn, đối chiếu và điều phối; repository quản lý SQL. Cấu trúc tuân thủ
Clean Architecture hiện có.

Các nhóm dữ liệu cần thiết: bộ/thẻ, tham chiếu nguồn SGK, trạng thái ôn và sự kiện
trả lời, bài nói/lần luyện/bản chép lời/nhận xét, lựa chọn giọng. Model/version và
phiên bản nội dung cần gắn với kết quả để kết quả cũ không bị diễn giải theo mẫu mới.
Thử lại yêu cầu sau mất mạng không tạo trùng sự kiện học hoặc lần luyện.

Nhận dạng và TTS chạy thành dịch vụ riêng, tránh phụ thuộc worker OCR. Model lưu
cache bền vững, tải trong bước setup riêng, không tải lại mỗi lần make run. Chỉ
chốt CPU/model/cấu hình sau khi đo trên máy thực tế; chưa cam kết độ trễ thời gian thực.
Khi triển khai cập nhật Makefile và docs/dependencies.md cùng các license liên quan.

## Lỗi và quyền riêng tư

- Từ chối microphone: hướng dẫn bật quyền, không khóa phần flashcard.
- Không có tiếng nói/bản thu quá nhỏ: yêu cầu thu lại, không cho điểm thấp giả.
- Nhận dạng/TTS lỗi: cho thử lại; TTS lỗi vẫn hiển thị nhận xét chữ đã có.
- Không có audio mẫu đã kiểm duyệt: thông báo rõ thay vì tự giả lập audio chuẩn.
- Bản thu chỉ giữ thời gian cần xử lý theo chính sách retention được triển khai;
  không lưu lâu dài mặc định. Không nhân bản giọng học sinh.
- Kiểm tra quyền sở hữu ở server cho bộ từ, bản thu, kết quả và giọng đã chọn.

## Kiểm chứng trước khi phát hành

1. Tạo/sửa/xóa/ôn bộ cá nhân, chống truy cập chéo tài khoản và giữ nguồn thẻ SGK.
2. Lịch ôn ổn định qua đăng nhập lại; thử lại không cộng trùng; lật thẻ không tăng thành thạo.
3. Thu âm → bản chép lời → đối chiếu → phản hồi chữ/âm thanh → lưu Tiến độ.
4. Từ khác, thiếu, thừa; âm thanh im lặng/nhiễu; lỗi mạng; lỗi model; quyền microphone.
5. Chọn giọng, nghe thử, lưu lựa chọn; audio tiếng Anh/Việt được đánh giá riêng.
6. Đo tốc độ, RAM và dung lượng tải trên máy mục tiêu; kiểm tra khởi động lại dùng cache.
7. Chạy make test và make analyze khi triển khai; báo giới hạn đánh giá phát âm rõ ràng.

## Nguồn tham khảo đã xem

- VieNeu-TTS: https://github.com/pnnbao97/VieNeu-TTS
- Faster-whisper: https://github.com/SYSTRAN/faster-whisper

Các khả năng/version được tham khảo ở thời điểm thiết kế; cần pin phiên bản và
xác nhận license của cả code, model và giọng trước khi tích hợp.
