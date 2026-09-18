# Thiết kế hệ thống học Tiếng Anh 7 dựa trên SGK và GraphRAG

**Ngày chốt thiết kế:** 2026-09-18  
**Thời gian triển khai dự kiến:** 7 tuần  
**Nhân sự:** 3 thành viên

## 1. Mục tiêu

Xây dựng ứng dụng mobile hỗ trợ học Tiếng Anh lớp 7 có chiều sâu về AI. Hệ thống số hóa nội dung SGK, tổ chức kiến thức thành Knowledge Graph, kết hợp graph retrieval với vector retrieval và dùng LLM để giải thích bài học, trả lời câu hỏi và sinh bài kiểm tra.

Ứng dụng mobile đóng vai trò giao diện minh họa cho toàn bộ pipeline. Giá trị kỹ thuật chính nằm ở xử lý tài liệu, truy xuất có căn cứ, Knowledge Graph, GraphRAG và kiểm soát câu trả lời của AI.

## 2. Phạm vi MVP

- Sách: **Tiếng Anh 7 – Global Success, Sách học sinh**.
- Phạm vi nội dung: **Unit 1 – Hobbies** và **Unit 2 – Healthy Living**.
- Nguồn chuẩn duy nhất: nội dung SGK và audio đi kèm do nhóm cung cấp.
- Không ánh xạ với chương trình đào tạo hoặc Learning Outcome của Bộ GD&ĐT.
- Không dùng kiến thức web hoặc kiến thức ngoài SGK để trả lời học sinh.
- Hỗ trợ ảnh chụp trang SGK hoặc bài tập in rõ; chưa hỗ trợ chữ viết tay.
- Hỗ trợ học bài, AI Tutor, audio, quiz, kiểm tra và theo dõi mức độ nắm vững kiến thức.

## 3. Nguyên tắc sản phẩm

### 3.1. Closed-world AI

AI chỉ được trả lời từ dữ liệu SGK đã được trích xuất và xác minh. Nếu không có bằng chứng đủ tin cậy, hệ thống phải từ chối trả lời thay vì suy đoán.

Mọi câu trả lời và câu hỏi do AI tạo phải truy vết được theo chuỗi:

```text
Answer / QuizQuestion
→ Concept / Activity
→ SourceFragment
→ Unit / Section
→ Page / Bounding Box
```

### 3.2. Dữ liệu đã duyệt mới được sử dụng

Kết quả YOLO và OCR ban đầu chỉ mang trạng thái nháp. Chỉ dữ liệu `VERIFIED` mới được index vào production Knowledge Graph và dùng làm context cho LLM.

### 3.3. Ảnh tải lên không phải nguồn tri thức

Ảnh học sinh tải lên chỉ là đầu vào truy vấn. Nội dung từ ảnh phải được đối chiếu với dữ liệu SGK chuẩn và không tự động được thêm vào knowledge base.

## 4. Kiến trúc tổng thể

Chọn kiến trúc **modular monolith** để cân bằng chiều sâu kỹ thuật với thời hạn 7 tuần.

```text
Flutter Mobile App
        ↓ REST API
FastAPI Modular Backend
        ├── SQL Server
        ├── Neo4j + Vector Index
        ├── MinIO
        ├── Background Worker
        ├── DocLayout-YOLO + OCR
        └── OpenRouter API
```

Các module backend chính:

- Authentication và authorization.
- Textbook content và media.
- Document ingestion và review.
- AI Tutor và image query.
- Quiz generation, validation và test attempts.
- Student progress, mastery và misconceptions.
- Admin review.

### 4.1. Nguyên tắc API-first

Toàn bộ client giao tiếp với hệ thống qua FastAPI. Flutter và trang quản trị không được kết nối trực tiếp tới SQL Server, Neo4j, MinIO hoặc OpenRouter.

- API được version theo prefix, bắt đầu bằng `/api/v1`.
- Thiết kế resource-oriented, dùng HTTP method và status code nhất quán.
- Request/response có schema rõ ràng bằng Pydantic.
- FastAPI sinh OpenAPI/Swagger để nhóm mobile tích hợp và kiểm thử contract.
- Response lỗi dùng một cấu trúc thống nhất gồm `code`, `message`, `details` và `trace_id`.
- Các endpoint danh sách hỗ trợ pagination, filter và sort khi cần.
- Upload/download media đi qua endpoint hoặc pre-signed URL do backend cấp.
- Tác vụ lâu như YOLO, OCR, embedding và sinh quiz chạy nền; API trả `job_id` để client theo dõi trạng thái.
- Authentication dùng access token; authorization được kiểm tra tại backend theo role.
- Không để lộ cấu trúc database, secret hoặc thông tin nội bộ của model qua response.

Các nhóm endpoint dự kiến:

```text
/api/v1/auth
/api/v1/textbooks
/api/v1/lessons
/api/v1/media
/api/v1/tutor
/api/v1/uploads
/api/v1/quizzes
/api/v1/test-attempts
/api/v1/progress
/api/v1/admin
/api/v1/jobs
```

## 5. Công nghệ đã chốt

- Mobile: Flutter + Dart.
- Backend: Python + FastAPI.
- Cơ sở dữ liệu nghiệp vụ: SQL Server.
- Knowledge Graph và vector retrieval: Neo4j.
- Lưu ảnh/audio/object: MinIO.
- Layout detection: DocLayout-YOLO pretrained, cho phép fine-tune nhẹ nếu cần.
- OCR: chọn engine trong giai đoạn lập kế hoạch sau khi benchmark trên các trang SGK mẫu.
- LLM: OpenRouter API thông qua lớp `AIProvider` nội bộ.
- Môi trường: Docker Compose, hỗ trợ Linux và Windows.

### 5.1. Nguyên tắc không hardcode

Không hardcode các giá trị thay đổi theo môi trường hoặc nghiệp vụ trong source code, bao gồm:

- API key, mật khẩu, connection string và token.
- Host, port, base URL và đường dẫn file tuyệt đối.
- Tên/model ID của OpenRouter, embedding, YOLO và OCR.
- Confidence threshold, retrieval top-k, timeout, retry và token limit.
- Giới hạn dung lượng ảnh/audio và định dạng file cho phép.
- Thời lượng bài kiểm tra, số lượt nghe và cấu hình QuizBlueprint.
- Unit được kích hoạt, ngôn ngữ hỗ trợ và feature flags.

Phân lớp cấu hình:

- `.env` và Docker secrets cho secret cùng cấu hình theo môi trường.
- File cấu hình có kiểm soát phiên bản cho default không nhạy cảm.
- SQL Server cho chính sách nghiệp vụ cần quản trị hoặc thay đổi lúc runtime.
- Enum/constant trong code chỉ dành cho giá trị miền ổn định, không phải cấu hình triển khai.

Repository chỉ cung cấp `.env.example` không chứa giá trị bí mật. Backend phải validate cấu hình khi khởi động và dừng với thông báo rõ ràng nếu thiếu cấu hình bắt buộc.

## 6. Phân công dữ liệu giữa các hệ thống

### SQL Server

Lưu nguồn dữ liệu nghiệp vụ chính:

- User, role và cấu hình ngôn ngữ.
- Textbook, Unit, Section, Activity và SourceFragment.
- Metadata ảnh, audio và transcript.
- QuizBlueprint, QuizQuestion, TestAttempt và StudentAnswer.
- Tiến độ học, mastery score và lịch sử tương tác.
- Trạng thái review, model version và audit log.

### Neo4j

Lưu lớp tri thức được build lại từ dữ liệu đã xác minh:

- VocabularyConcept, GrammarConcept, PronunciationConcept và Skill.
- Unit, Section, Activity, SourceFragment và QuizQuestion.
- Quan hệ giữa kiến thức, bài học, bài tập, audio và lỗi thường gặp.
- Embedding/vector index phục vụ hybrid retrieval.

SQL Server là source of truth. Neo4j có thể được rebuild từ dữ liệu chuẩn.

### MinIO

Lưu file nhị phân:

- Ảnh render từ PDF.
- Crop theo bounding box.
- Ảnh do học sinh tải lên.
- Audio của sách.
- Các artifact phục vụ review.

## 7. Pipeline số hóa SGK

```text
SGK PDF
→ đăng ký SourceDocument và file hash
→ render từng trang thành ảnh
→ DocLayout-YOLO phát hiện vùng
→ crop vùng
→ OCR
→ sắp xếp thứ tự đọc
→ chuẩn hóa cấu trúc
→ quản trị viên kiểm tra
→ VERIFIED
→ graph builder + embeddings
```

YOLO dùng để phát hiện vị trí và loại vùng, không dùng để đọc chữ. Tập class MVP:

- `title`
- `section_header`
- `text`
- `list`
- `table`
- `picture`
- `caption`

Nếu pretrained model không đủ chính xác trên SGK, nhóm gán nhãn một tập nhỏ và fine-tune nhẹ. Không huấn luyện mô hình lớn từ đầu.

Mỗi `SourceFragment` cần có:

- Source document và phiên bản.
- PDF page và printed page.
- Bounding box.
- Region type.
- OCR text và normalized text.
- Detection confidence và OCR confidence.
- Detector/OCR model version.
- Review status và reviewer.

## 8. Audio

Nguồn audio gồm 89 file MP3 đánh số `001.mp3` đến `089.mp3`. MVP chỉ ingest các track thuộc Unit 1–2.

Audio được ánh xạ theo:

```text
Unit → Section → Activity → AudioAsset
```

File audio nằm trong MinIO; SQL Server chỉ lưu metadata và object key. Transcript được tạo và xác minh để phục vụ retrieval, nhưng không hiển thị trong lúc học sinh đang làm bài kiểm tra.

## 9. Knowledge Graph

Node types MVP:

- `Unit`
- `Section`
- `Activity`
- `SourceFragment`
- `VocabularyConcept`
- `GrammarConcept`
- `PronunciationConcept`
- `Skill`
- `AudioTrack`
- `QuizQuestion`
- `CommonMistake`
- `Student`

Relationship types MVP:

- `HAS_SECTION`
- `HAS_ACTIVITY`
- `TEACHES`
- `PRACTICES`
- `HAS_SOURCE`
- `HAS_AUDIO`
- `ASSESSES`
- `RELATED_TO`
- `PREREQUISITE_OF`
- `HAS_COMMON_MISTAKE`
- `MASTERED`
- `WEAK_AT`

Quan hệ do AI đề xuất phải có evidence, confidence, model version và review status. Không tự động biến quan hệ suy luận thành fact đã xác minh.

## 10. Hybrid GraphRAG

Luồng truy xuất:

```text
Student query / OCR text
→ xác định Unit và Section nếu có
→ query embedding
→ vector candidate retrieval
→ entity linking
→ graph traversal
→ source fragment retrieval
→ reranking
→ context assembly
→ OpenRouter
→ source validation
→ response
```

Backend chỉ gọi LLM khi có context đạt ngưỡng tin cậy. LLM nhận context đóng và yêu cầu trả về output có cấu trúc gồm câu trả lời cùng source IDs. Backend xác minh source IDs trước khi trả kết quả.

Nếu không có bằng chứng, hệ thống trả thông báo rằng nội dung không tồn tại trong phạm vi SGK đã xử lý.

## 11. AI Tutor

AI Tutor hỗ trợ hai ngữ cảnh:

1. Học sinh hỏi khi đang xem Unit/Section/Activity cụ thể.
2. Học sinh tải ảnh trang SGK hoặc bài tập để hệ thống nhận diện và tìm nội dung tương ứng.

Hai chế độ ngôn ngữ:

- Tiếng Việt: giải thích bằng tiếng Việt, giữ thuật ngữ và ví dụ tiếng Anh.
- Tiếng Anh: giải thích hoàn toàn bằng tiếng Anh ở mức phù hợp lớp 7.

AI ưu tiên đưa gợi ý trước khi đưa đáp án hoàn chỉnh. Với ảnh mờ, ảnh ngoài Unit 1–2 hoặc ảnh không đối chiếu được với dữ liệu chuẩn, hệ thống yêu cầu chụp lại hoặc thông báo ngoài phạm vi.

## 12. Quiz và bài kiểm tra

Học sinh lựa chọn:

- Phạm vi: Unit 1, Unit 2 hoặc cả hai.
- Độ khó: dễ, trung bình, khó hoặc thích nghi.
- Thời lượng: 15 phút, 45 phút, 60 phút hoặc tùy chỉnh.

Hệ thống tạo `QuizBlueprint` trước, quy định số câu, loại câu, concept, kỹ năng và thời lượng dự kiến. Sau đó mới gọi LLM sinh câu hỏi dựa trên SourceFragment đã chọn.

Question validator kiểm tra:

- Câu hỏi có nằm trong Unit đã chọn không.
- Có source support hợp lệ không.
- Có đúng concept và độ khó không.
- Đáp án có rõ ràng và duy nhất không.
- Distractor có hợp lý không.
- Có trùng hoặc quá giống câu đã tồn tại không.
- Dữ liệu có vượt ra ngoài SGK không.

Dạng câu MVP:

- Multiple choice.
- True/false.
- Fill in the blank.
- Matching.
- Reading comprehension.
- Listening multiple choice.

Đề được khóa sau khi tạo. Timer do backend quản lý và tự nộp khi hết giờ.

## 13. Chính sách nghe

### Chế độ học/luyện tập

- Nghe lại không giới hạn.
- Cho phép tạm dừng và tua.

### Chế độ kiểm tra

- Mỗi audio được phát tối đa hai lần.
- Không cho tua.
- Số lượt nghe lưu ở backend theo `test_attempt_id`.
- Thoát rồi vào lại không reset lượt nghe.
- Lỗi tải trước khi bắt đầu phát không trừ lượt.
- Transcript không được hiển thị trước khi nộp bài.

## 14. Student model và adaptive learning

SQL Server lưu kết quả chi tiết từng câu. Neo4j thể hiện quan hệ giữa học sinh và concept:

```text
Student -[:MASTERED]-> Concept
Student -[:WEAK_AT]-> Concept
Student -[:HAS_MISCONCEPTION]-> CommonMistake
```

Ban đầu học sinh tự chọn độ khó. Khi có đủ lịch sử, chế độ thích nghi ưu tiên concept yếu và prerequisite liên quan nhưng vẫn giữ độ phủ của Unit.

## 15. Quản trị và review

Trang quản trị tối giản hỗ trợ:

- Xem trang SGK và bounding box YOLO.
- Sửa nội dung OCR.
- Duyệt hoặc từ chối SourceFragment.
- Ánh xạ audio với Activity.
- Xem quan hệ graph được AI đề xuất.
- Xem câu hỏi bị validator từ chối.
- Re-index dữ liệu đã duyệt.

Mobile tập trung cho học sinh. Chưa xây module giáo viên riêng trong MVP.

## 16. Triển khai đa nền tảng

Docker Compose gồm:

- `api`
- `worker`
- `sqlserver`
- `neo4j`
- `minio`
- migration/seed job

Chế độ CPU mặc định chạy được trên Linux và Windows. GPU là Docker profile tùy chọn trên máy có NVIDIA RTX 2050 để tăng tốc YOLO/OCR trong pipeline ingestion.

Pipeline xử lý SGK chạy offline một lần. Dữ liệu chuẩn hóa được đóng gói thành seed/export để các thành viên không có GPU vẫn chạy được toàn bộ ứng dụng.

OpenRouter key chỉ tồn tại ở backend qua environment variable. Flutter không chứa API key. `AIProvider` hỗ trợ timeout, retry, token usage log, model configuration và mock khi test.

## 17. Xử lý lỗi

- Ảnh mờ/nghiêng: trả hướng dẫn chụp lại.
- Ảnh ngoài phạm vi: từ chối có giải thích.
- Nhiều vùng phù hợp: yêu cầu chọn vùng cần hỏi.
- Retrieval confidence thấp: không gọi LLM.
- OpenRouter timeout: cho thử lại, không giả lập câu trả lời.
- Output không có source hợp lệ: loại bỏ và ghi audit log.
- Audio load lỗi trước khi phát: không trừ lượt.
- Database hoặc graph tạm thời lỗi: trả trạng thái dịch vụ, không làm mất attempt.

## 18. Kiểm thử và đánh giá

### Unit test

- Source validator.
- Quiz policy và blueprint.
- Timer và auto-submit.
- Giới hạn hai lượt nghe.
- Mastery update.

### Integration test

- FastAPI với SQL Server, Neo4j và MinIO.
- Migration và seed.
- Worker ingestion.
- OpenRouter mock và failure paths.

### Retrieval evaluation

Xây một bộ câu hỏi chuẩn cho Unit 1–2 và đo:

- Page/fragment retrieval accuracy.
- Citation correctness.
- Answer groundedness.
- Tỉ lệ từ chối đúng với câu ngoài phạm vi.

### End-to-end test

- Đăng nhập.
- Xem bài học.
- Nghe audio.
- Tải ảnh và hỏi AI.
- Làm quiz/test.
- Tự nộp khi hết giờ.
- Xem kết quả và tiến độ.

## 19. Tiêu chí demo thành công

- Dự án khởi chạy bằng Docker Compose trên Linux và Windows.
- Unit 1–2 có dữ liệu được duyệt và truy vết tới trang SGK.
- Ảnh trang/bài tập SGK được nhận diện và đối chiếu đúng.
- AI Tutor trả lời song ngữ theo lựa chọn và có nguồn.
- AI từ chối câu hỏi không có trong knowledge base.
- Quiz sinh đúng phạm vi, thời lượng và độ khó.
- Audio trong bài kiểm tra chỉ nghe tối đa hai lần.
- Kết quả bài làm cập nhật mastery theo concept.

## 20. Nội dung không thuộc MVP

- Toàn bộ 12 Unit.
- Ánh xạ chương trình đào tạo của Bộ GD&ĐT.
- Nhận dạng chữ viết tay.
- Huấn luyện YOLO quy mô lớn từ đầu.
- Tính năng riêng đầy đủ cho giáo viên.
- Kiến thức web hoặc external RAG.
- Hệ thống production đa tenant hoặc scale lớn.

## 21. Rủi ro chính và biện pháp giảm thiểu

- **OCR sai do bố cục SGK:** dùng YOLO tách vùng và human review.
- **YOLO pretrained không phù hợp:** fine-tune nhẹ trên tập nhỏ.
- **LLM bịa nội dung:** closed context, confidence gate và source validator.
- **GraphRAG quá rộng:** giới hạn ontology và dữ liệu ở Unit 1–2.
- **Máy khác không có GPU:** ingestion offline và cung cấp seed đã xử lý.
- **Chi phí OpenRouter:** giới hạn model/token, cache và mock khi test.
- **Chậm tiến độ:** hoàn thiện vertical slice Unit 1 trước, sau đó mở rộng Unit 2.
