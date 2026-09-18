# Tổng hợp Brainstorm – Ứng dụng học Tiếng Anh lớp 7 tích hợp số hóa SGK, Knowledge Graph, Full GraphRAG và AI

> Tài liệu này tổng hợp toàn bộ các ý tưởng đã brainstorm trong cuộc trao đổi, đồng thời phản ánh **phạm vi cuối cùng đã chốt**: tập trung vào **môn Tiếng Anh lớp 7**, bám theo **một chương trình giáo dục chính thức của Bộ GD&ĐT**, xử lý dữ liệu SGK từ PDF, xây dựng **Knowledge Graph + Full GraphRAG**, giữ **embedding/vector search**, và tích hợp AI để hỗ trợ học tập, giải thích kiến thức, sinh quiz và cá nhân hóa.

---

## 1. Ý tưởng ban đầu và quá trình thu hẹp phạm vi

Ý tưởng ban đầu xuất phát từ nhu cầu hỗ trợ học sinh khi **không có hoặc không đủ SGK**, nhưng vẫn muốn học theo đúng nội dung trên lớp. Ban đầu phạm vi được nghĩ tới từ lớp 6–12, sau đó mở rộng thành lớp 1–12. Tuy nhiên, để hệ thống có chiều sâu kỹ thuật, dữ liệu đủ tin cậy và phạm vi triển khai thực tế hơn, ý tưởng cuối cùng được thu hẹp lại thành:

**Ứng dụng học Tiếng Anh lớp 7, bám theo một chương trình giáo dục chính thức của Bộ GD&ĐT, có thể khai thác dữ liệu SGK dạng PDF, chuẩn hóa thành dữ liệu có cấu trúc, ánh xạ với chương trình, xây dựng Knowledge Graph và Full GraphRAG để hỗ trợ AI Tutor, quiz generation và adaptive learning.**

Phạm vi hiện tại:

- Môn học: **Tiếng Anh**.
- Lớp: **Lớp 7**.
- Chương trình: **một chương trình chính thức của Bộ GD&ĐT**.
- Dữ liệu SGK: bắt đầu từ các file PDF có sẵn.
- AI: dùng cho hỗ trợ học sinh, giải thích bài, sinh quiz, chẩn đoán điểm yếu.
- Kiến trúc tri thức: **Knowledge Graph + Full GraphRAG**.
- Embedding/vector search: **vẫn giữ**, không loại bỏ.

---

## 2. Vấn đề cốt lõi mà sản phẩm giải quyết

Ứng dụng hướng tới hai tình huống chính.

### 2.1. Học sinh không có SGK

Học sinh vẫn có thể học theo chương trình Tiếng Anh lớp 7 thông qua:

- chủ đề;
- kỹ năng;
- từ vựng;
- ngữ pháp;
- phát âm;
- nghe;
- nói;
- đọc;
- viết;
- bài tập;
- quiz;
- theo dõi tiến độ.

Luồng học có thể là:

```text
Học sinh
   ↓
Tiếng Anh lớp 7
   ↓
Học theo chương trình
   ↓
Topic / Skill / Learning Outcome
   ↓
Lesson
   ↓
Exercise / Quiz
   ↓
Progress
```

### 2.2. Học sinh có SGK

Học sinh không cần upload toàn bộ quyển sách mỗi lần sử dụng. Hệ thống có thể đã có dữ liệu SGK được xử lý và chuẩn hóa trước.

Luồng:

```text
Học sinh có SGK
   ↓
Chọn / nhận diện SGK
   ↓
Unit
   ↓
Lesson / Section
   ↓
Nội dung tương ứng
   ↓
Learning Content
   ↓
Exercise / Quiz
```

Trong tương lai việc nhận diện SGK có thể dựa vào:

- lựa chọn thủ công;
- ISBN / barcode;
- ảnh bìa;
- metadata của sách.

AI không nên tự quyết định chương trình chỉ bằng cách nhìn bìa sách. Việc xác định chương trình phải dựa trên dữ liệu đã kiểm chứng trong hệ thống.

---

## 3. Phân biệt “chương trình” và “SGK”

Một nguyên tắc thiết kế quan trọng đã được chốt:

> **Chương trình giáo dục là nguồn chuẩn về mục tiêu/yêu cầu cần đạt; SGK là một cách triển khai chương trình đó.**

Do đó hệ thống không nên lấy SGK làm “nguồn sự thật duy nhất”.

Kiến trúc khái niệm:

```text
Chương trình Bộ GD&ĐT
        ↓
Learning Outcomes
        ↓
   ┌────┴────┐
   │         │
Lesson     SGK
   │         │
   └────┬────┘
        ↓
   Learning App
```

Điều này giúp hệ thống giải quyết được cả hai tình huống:

- không có SGK → học theo Curriculum Core;
- có SGK → học theo Unit/Lesson rồi ánh xạ về Curriculum Core.

---

## 4. Nguồn sự thật và độ tin cậy dữ liệu

Hệ thống không nên coi nội dung AI sinh ra hoặc nội dung OCR từ PDF là dữ liệu chính thức ngay lập tức.

Độ tin cậy nên dựa trên bốn thành phần:

```text
Official Curriculum Source
        +
Verified Textbook Data
        +
Curriculum Mapping
        +
Human / Academic Review
```

Mỗi nội dung nên có khả năng truy vết ngược:

```text
Lesson
  ↓
Learning Outcome
  ↓
Source Fragment
  ↓
Official Document / Textbook
  ↓
Page / Section
```

Đây là **traceability** và là một trong những nguyên tắc quan trọng nhất của hệ thống.

---

## 5. Dữ liệu chương trình giáo dục

Vì không có sẵn một API trả về chương trình giáo dục dưới dạng JSON, hướng tiếp cận được brainstorm là xây dựng một **Curriculum Dataset** từ nguồn chính thức.

Pipeline khái niệm:

```text
Official Curriculum Document
        ↓
Text / Structure Extraction
        ↓
Grade 7 Outcomes
        ↓
Normalization
        ↓
Human Verification
        ↓
Verified Curriculum Dataset
```

Các entity chính:

```text
Curriculum
LearningOutcome
Skill
Topic
SourceDocument
SourceFragment
```

Ví dụ một learning outcome:

```text
id: ENG7-READ-001
subject: English
grade: 7
skill: Reading
description: ...
source_document: ...
source_page: ...
verification_status: VERIFIED
```

Mọi lesson trong luồng học chính nên map được tới ít nhất một `LearningOutcome`.

---

## 6. PDF SGK là nguồn đầu vào, không phải dữ liệu cuối cùng

Khi có file PDF SGK, không nên đưa nguyên PDF vào app và biến app thành PDF reader.

Mục tiêu là:

```text
PDF SGK
  ↓
Knowledge Extraction
  ↓
Structured Textbook Dataset
  ↓
Mapping
  ↓
Learning Content
```

Một file PDF mẫu đã được xem xét trong quá trình brainstorm là một SGK Tiếng Anh có cấu trúc lặp lại theo Unit, gồm các phần như:

- Getting Started;
- A Closer Look 1;
- A Closer Look 2;
- Communication;
- Skills 1;
- Skills 2;
- Looking Back;
- Project;
- Review;
- Glossary.

File mẫu được dùng để điều chỉnh pipeline xử lý PDF cho ổn định hơn. Đây chỉ là tài liệu tham chiếu kỹ thuật trong brainstorm; phạm vi sản phẩm cuối cùng vẫn là **Tiếng Anh lớp 7**.

---

## 7. Pipeline PDF ban đầu và vấn đề

Pipeline đơn giản ban đầu:

```text
PDF
 ↓
OCR
 ↓
AI phân tích
 ↓
Database
```

được đánh giá là chưa đủ ổn định vì:

- PDF có thể là scan/image PDF;
- OCR toàn trang dễ sai thứ tự đọc;
- bố cục SGK có nhiều cột, hình, bảng, box;
- AI có thể suy luận sai section;
- không có cơ chế cross-check;
- khó trace ngược tới vị trí nguồn;
- khó xử lý version/edition của sách.

Do đó pipeline đã được nâng cấp thành **structure-first + layout detection + cross-validation**.

---

## 8. Pipeline xử lý PDF mới

Pipeline được đề xuất:

```text
PDF GỐC
   ↓
1. Source Registry
   ↓
2. PDF Preflight
   ↓
3. Structure Discovery
   ↓
4. Page Rendering
   ↓
5. YOLO Layout Detection
   ↓
6. OCR / Vision
   ↓
7. Semantic Extraction
   ↓
8. Normalization
   ↓
9. Cross Validation
   ↓
10. Human Review
   ↓
VERIFIED TEXTBOOK DATASET
```

### 8.1. Source Registry

Mỗi file PDF khi nhập vào phải được đăng ký:

```text
SourceDocument
- id
- original_filename
- file_hash
- page_count
- document_type
- subject
- grade
- title
- publisher
- isbn
- edition
- publication_year
- rights_status
- ingestion_version
```

`file_hash` giúp phát hiện file trùng ngay cả khi tên file khác nhau.

### 8.2. PDF Preflight

Phân loại:

```text
TEXT_PDF
SCANNED_PDF
IMAGE_PDF
```

Nếu PDF có text layer thì extraction dễ hơn; nếu là ảnh thì phải OCR/vision.

### 8.3. Page numbering

Nên lưu hai loại số trang:

```text
pdf_page
printed_page
```

để vừa xử lý kỹ thuật chính xác vừa cho học sinh/reviewer tra đúng trang sách giấy.

---

## 9. Dùng cấu trúc sách để tăng độ ổn định

Không nên để AI tự dò toàn bộ tài liệu từ đầu.

Nếu sách có các trang như:

- Contents;
- Book Map;
- Unit opening;
- This Unit Includes;
- Looking Back;
- Now I Can;
- Glossary;

thì nên coi chúng là các “anchor” để kiểm tra dữ liệu.

Ví dụ:

```text
Contents
   ↓
Xác định Unit và page range

Book Map
   ↓
Xác định overview kỹ năng / grammar / vocabulary

Unit Opening
   ↓
Xác nhận metadata của Unit

Lesson Pages
   ↓
Lấy nội dung chi tiết

Looking Back / Now I Can
   ↓
Xác minh kiến thức/mục tiêu

Glossary
   ↓
Chuẩn hóa vocabulary
```

Cách này tạo ra **multi-source verification ngay trong chính cuốn sách**.

---

## 10. Tích hợp YOLO để nhận diện layout

YOLO được đề xuất như một lớp phát hiện **vùng bố cục**, không phải công cụ đọc nội dung.

Pipeline:

```text
PDF
 ↓
Render page → image
 ↓
YOLO
 ↓
Detect regions
 ↓
Crop từng region
 ↓
OCR / Vision
 ↓
Text + Structure
```

Các class YOLO gợi ý:

```text
unit_header
section_header
activity
instruction
vocabulary_block
grammar_block
pronunciation_block
reading_block
listening_block
image
table
audio_icon
remember_box
now_i_can
project_block
```

YOLO giúp:

- phát hiện vị trí section;
- tách bài tập khỏi hình ảnh;
- xác định vùng grammar/vocabulary;
- hỗ trợ thứ tự đọc;
- giảm lỗi OCR trên trang nhiều cột;
- tạo bbox để reviewer kiểm tra nhanh.

YOLO **không thay thế OCR**:

```text
YOLO → vùng nào là grammar_block
OCR/Vision → trong vùng đó ghi gì
Parser → nội dung đó có ý nghĩa gì
```

---

## 11. Lưu kết quả detection để trace và reprocess

Schema gợi ý:

```text
PageRegion
- id
- source_document_id
- pdf_page
- printed_page
- region_type
- x
- y
- width
- height
- detector_model
- detector_version
- detection_confidence
- ocr_text
- ocr_confidence
- normalized_text
- review_status
```

Phải lưu `detector_version` để sau này train YOLO mới và chạy lại dữ liệu mà vẫn so sánh được kết quả giữa các phiên bản model.

---

## 12. Active Learning cho YOLO

Thay vì annotate toàn bộ sách ngay từ đầu:

```text
50–100 pages manually labelled
       ↓
YOLO v1
       ↓
Inference on more pages
       ↓
Human correct predictions
       ↓
More labelled data
       ↓
YOLO v2
```

Đây là hướng active learning phù hợp nếu tiếp tục mở rộng số lượng trang SGK lớp 7.

---

## 13. Normalized Textbook Dataset

Dữ liệu cuối cùng không nên chỉ là text blob.

Cấu trúc đề xuất:

```text
Textbook
  ↓
TextbookEdition
  ↓
Volume
  ↓
ContentBlock
  ├── UNIT
  ├── REVIEW
  └── GLOSSARY
       ↓
Section
  ├── GETTING_STARTED
  ├── CLOSER_LOOK_1
  ├── CLOSER_LOOK_2
  ├── COMMUNICATION
  ├── SKILLS_1
  ├── SKILLS_2
  ├── LOOKING_BACK
  └── PROJECT
       ↓
Activity
```

Từ `Activity` có thể liên kết tới:

```text
VocabularyOccurrence
GrammarTopic
PronunciationTopic
Skill
ReadingPassage
Dialogue
Exercise
AudioReference
SourceFragment
```

---

## 14. Vocabulary nên có canonical entry

Không nên lưu cùng một từ lặp lại nhiều lần.

Tách:

```text
VocabularyEntry
- word
- IPA
- part_of_speech
- meaning
```

khỏi:

```text
VocabularyOccurrence
- vocabulary_id
- unit_id
- section_id
- activity_id
- source_page
```

Như vậy một từ chỉ có một canonical entry nhưng có thể xuất hiện nhiều lần trong SGK.

---

## 15. Exercise phải là dữ liệu có cấu trúc

Không nên chỉ lưu `exercise_text`.

Schema khái niệm:

```text
Activity
- id
- section_id
- activity_number
- activity_type
- instruction
- skill
- language_focus
- requires_audio
- requires_image
- answer_mode
- source_page
- source_bbox
- status
```

Một số `activity_type`:

```text
MULTIPLE_CHOICE
TRUE_FALSE
FILL_BLANK
MATCHING
LISTEN_AND_REPEAT
LISTEN_AND_CHOOSE
READ_AND_ANSWER
PAIR_WORK
GROUP_WORK
SPEAKING
WRITING
PROJECT
```

---

## 16. Audio và media

Nếu PDF chỉ có biểu tượng nghe mà không chứa file audio, hệ thống không được giả định rằng audio tồn tại.

Nên lưu:

```text
requires_audio = true
audio_asset_status = MISSING
```

Khi có nguồn audio hợp lệ mới chuyển thành:

```text
audio_asset_status = AVAILABLE
```

---

## 17. Versioning của SGK

Không overwrite dữ liệu khi có bản in mới.

```text
TextbookEdition
- textbook_id
- edition_id
- publication_year
- isbn
- source_hash
- valid_from
- valid_to
- status
```

Stable ID không nên phụ thuộc vào số trang.

Ví dụ:

```text
ENG-G07-BOOK01-U01-ACL1-A01
```

Số trang chỉ là metadata của nguồn.

---

## 18. Quy trình xác minh dữ liệu

Không publish dữ liệu extraction ngay.

Workflow:

```text
DRAFT
  ↓
STRUCTURED
  ↓
NORMALIZED
  ↓
SOURCE_CHECKED
  ↓
ACADEMIC_REVIEWED
  ↓
VERIFIED
  ↓
PUBLISHED
```

Chỉ dữ liệu `VERIFIED` mới được dùng trong hệ thống AI cho học sinh.

---

# PHẦN II – KNOWLEDGE GRAPH VÀ FULL GRAPHRAG

## 19. Tại sao dùng Knowledge Graph

Dữ liệu dạng bảng chỉ cho biết một nội dung tồn tại ở đâu.

Knowledge Graph giúp biểu diễn:

- nội dung này dạy khái niệm gì;
- khái niệm này liên quan tới khái niệm nào;
- prerequisite là gì;
- bài tập nào luyện kiến thức này;
- quiz nào đánh giá kiến thức này;
- learning outcome nào được cover;
- lỗi thường gặp của học sinh là gì;
- nguồn của kiến thức đến từ đâu.

Ví dụ:

```text
Unit 3
  ├── HAS_SECTION → A Closer Look 2
  ├── HAS_TOPIC → ...
  └── TEACHES → GrammarConcept
                    ├── PREREQUISITE → Concept A
                    ├── CONTRASTS_WITH → Concept B
                    ├── PRACTICED_BY → Exercise
                    └── ASSESSED_BY → QuizQuestion
```

---

## 20. Educational Ontology

Thay vì để GraphRAG mặc định tự extract các entity chung chung, hệ thống nên dùng ontology chuyên biệt cho giáo dục.

### Node types

```text
CurriculumOutcome
Unit
Section
Activity
Topic
GrammarConcept
VocabularyConcept
PronunciationConcept
ListeningSkill
SpeakingSkill
ReadingSkill
WritingSkill
Exercise
QuizQuestion
Example
ReadingPassage
Dialogue
CommonMistake
SourceDocument
SourceFragment
Student
```

### Relationship types

```text
HAS_SECTION
HAS_ACTIVITY
TEACHES
INTRODUCES
PRACTICES
COVERS
ASSESSES
PREREQUISITE_OF
RELATED_TO
CONTRASTS_WITH
HAS_EXAMPLE
HAS_COMMON_MISTAKE
EVIDENCE_FOR
DERIVED_FROM
```

---

## 21. Graph hai tầng tin cậy

Đề xuất chia graph thành:

```text
VERIFIED / EXPLICIT GRAPH
        │
        └── facts được xác nhận từ dữ liệu chuẩn

INFERRED GRAPH
        │
        └── quan hệ do AI suy luận
```

Mọi relation AI suy luận phải có:

```text
source
confidence
extraction_model
model_version
evidence
verification_status
```

Ví dụ:

```text
Present Continuous
  CONTRASTS_WITH
Present Simple
```

có thể là một relation inferred nếu tài liệu không nói trực tiếp.

Không được biến relation inferred thành fact verified một cách âm thầm.

---

## 22. Full GraphRAG

Hệ thống cuối cùng không chỉ dùng graph traversal cơ bản mà hướng tới Full GraphRAG.

Pipeline:

```text
VERIFIED DATASET
      ↓
GraphRAG Indexing
      ↓
Entities
Relationships
Claims
      ↓
Knowledge Graph
      ↓
Community Detection
      ↓
Hierarchical Communities
      ↓
Community Reports
      ↓
GraphRAG Index
```

Các chế độ retrieval/reasoning:

```text
Local Search
Global Search
DRIFT Search
```

### Local Search

Dùng khi câu hỏi xoay quanh một entity cụ thể.

Ví dụ:

> Adverbs of frequency đứng ở đâu trong câu?

GraphRAG có thể lấy:

- concept;
- rule;
- examples;
- related concepts;
- source fragments;
- exercises;
- learning outcomes.

### Global Search

Dùng khi cần overview ở mức rộng.

Ví dụ:

> Unit này cần nắm những kiến thức chính nào?

Global Search có thể dùng community reports để tổng hợp toàn Unit.

### DRIFT Search

Dùng cho reasoning/tutoring sâu hơn.

Ví dụ:

> Em vẫn không hiểu tại sao câu này dùng Present Continuous.

Hệ thống có thể đi qua:

```text
Present Continuous
  ↓
Time expression
  ↓
Contrast with Present Simple
  ↓
Prerequisite: Verb To Be
  ↓
Examples
  ↓
Source evidence
```

---

## 23. Community Detection và Community Reports

Knowledge Graph có thể được phân cụm để tìm các nhóm tri thức liên quan.

Ví dụ một community có thể gồm:

```text
Present Simple
Adverbs of Frequency
Daily Activities
School Routines
Related Vocabulary
```

Community report có thể tổng hợp:

- concept chính;
- các quan hệ quan trọng;
- learning outcomes liên quan;
- sections liên quan;
- examples;
- common mistakes;
- source evidence.

Điều này giúp AI Tutor hiểu “bức tranh lớn” thay vì chỉ truy xuất vài đoạn text rời rạc.

---

## 24. Embedding và Vector Search vẫn giữ

Full GraphRAG **không loại bỏ embedding/vector**.

Vai trò được phân biệt:

```text
Knowledge Graph
= hiểu quan hệ

Embedding / Vector
= hiểu độ gần ngữ nghĩa
```

Các loại embedding nên giữ:

### 24.1. Text Embedding

Cho:

```text
SourceFragment
ReadingPassage
Example
Exercise
Explanation
```

### 24.2. Entity Embedding

Cho:

```text
GrammarConcept
VocabularyConcept
Topic
Skill
LearningOutcome
```

### 24.3. Community/Report Embedding

Cho các community reports và summary.

Query flow:

```text
Student Query
   │
   ├── Query Embedding
   ├── Entity Linking
   ├── Vector Candidate Retrieval
   ├── Graph Traversal
   ├── Community Retrieval
   ├── Source Evidence Retrieval
   └── GraphRAG Reasoning
            ↓
        Re-ranking
            ↓
            LLM
```

---

## 25. Kiến trúc lưu trữ đề xuất

Một lựa chọn đã brainstorm:

```text
PostgreSQL + pgvector
        +
Neo4j
```

### PostgreSQL

Lưu:

- normalized textbook data;
- curriculum data;
- user;
- quiz attempts;
- progress;
- mastery;
- embeddings/vector index nếu dùng pgvector.

### Neo4j

Lưu:

- knowledge graph;
- node;
- relationship;
- graph traversal;
- knowledge communities;
- graph-oriented queries.

Nguyên tắc:

> **Normalized Database là Source of Truth. Knowledge Graph được build/rebuild từ dữ liệu chuẩn.**

Không nên để graph là nơi duy nhất chứa dữ liệu gốc.

---

# PHẦN III – AI TUTOR, QUIZ VÀ ADAPTIVE LEARNING

## 26. AI Tutor

AI Tutor sử dụng cùng một GraphRAG knowledge base.

AI không chỉ tìm text gần nghĩa mà còn có thể:

- xác định concept;
- kiểm tra prerequisite;
- tìm concept liên quan;
- tìm contrast concept;
- tìm examples;
- tìm exercises;
- tìm common mistakes;
- truy vết tới source evidence.

Ví dụ:

```text
Student:
"Em chưa hiểu bài này."

System context:
Unit 4 → A Closer Look 2 → Comparative Adjectives

GraphRAG:
Comparative Adjectives
   ├── prerequisite → Adjective
   ├── examples
   ├── related vocabulary
   ├── common mistakes
   └── exercises
```

AI Tutor có thể giải thích theo trình tự:

1. nhắc kiến thức prerequisite;
2. giải thích concept chính;
3. cho example;
4. cho một câu luyện nhanh;
5. nếu sai → giải thích lại theo lỗi cụ thể.

---

## 27. Quiz Generation

Không nên dùng prompt kiểu:

```text
"Hãy tạo 10 câu quiz Tiếng Anh lớp 7"
```

Hướng đúng là tạo **Quiz Blueprint** trước.

Ví dụ:

```text
Quiz Request
- scope: Unit 3
- learning outcomes: ...
- concepts: ...
- skills: ...
- difficulty: medium
- question_count: 10
```

GraphRAG lấy:

```text
Relevant Concepts
Learning Outcomes
Prerequisites
Examples
Existing Activities
Source Fragments
Community Context
```

Sau đó mới tạo blueprint:

```text
3 Vocabulary
3 Grammar
2 Reading
2 Application
```

LLM chỉ sinh câu hỏi dựa trên blueprint.

---

## 28. Question Validator

Quiz do AI sinh phải đi qua validation.

```text
GraphRAG
  ↓
LLM generates candidate questions
  ↓
Question Validator
  ↓
Accepted / Rejected
```

Validator kiểm tra:

- có đúng kiến thức lớp 7 không;
- có nằm trong scope bài không;
- có đáp án rõ ràng không;
- có nhiều hơn một đáp án đúng không;
- distractor có hợp lý không;
- có trùng câu cũ không;
- có source support không;
- có map đúng concept không;
- có map đúng learning outcome không.

---

## 29. Embedding để kiểm tra quiz trùng

Embedding có thể dùng để phát hiện hai câu gần như giống nhau dù khác wording.

Ví dụ:

```text
Q1: She goes to school every day.
Q2: She goes to school every morning.
```

Nếu similarity quá cao thì Q2 có thể bị reject hoặc rewrite.

Embedding cũng có thể hỗ trợ kiểm tra:

```text
Question ↔ Concept
Question ↔ LearningOutcome
Question ↔ SourceFragment
```

Nếu question được gắn nhãn Present Continuous nhưng embedding gần Present Simple hơn, hệ thống có thể flag để review.

---

## 30. Question cũng là node trong graph

```text
QuizQuestion
   ├── ASSESSES → Concept
   ├── COVERS → LearningOutcome
   ├── REQUIRES → PrerequisiteConcept
   ├── HAS_DIFFICULTY → Difficulty
   └── EVIDENCE_FROM → SourceFragment
```

Nhờ vậy kết quả làm quiz có thể cập nhật trực tiếp vào Student Model.

---

## 31. Student Knowledge / Mastery Model

Không cần tạo một graph hoàn toàn riêng cho mỗi học sinh. Có thể giữ knowledge graph chung và tạo các relation từ Student tới concept.

```text
Student
   ├── MASTERED → Concept A
   ├── LEARNING → Concept B
   └── WEAK_AT → Concept C
```

Metadata:

```text
mastery_score
attempt_count
correct_count
last_practiced_at
last_updated_at
```

Ví dụ:

```text
Present Simple       0.91
Present Continuous   0.58
Vocabulary Unit 3    0.81
Reading Skill        0.45
```

---

## 32. Adaptive Quiz

Quiz tiếp theo không cần phân bố đều.

Ví dụ mastery:

```text
Vocabulary    90%
Grammar       45%
Reading       75%
Listening     60%
```

Quiz tiếp theo có thể ưu tiên Grammar nhưng vẫn giữ coverage.

Quan trọng hơn, graph có thể nhìn prerequisite.

Ví dụ:

```text
Student weak at:
Present Continuous
        ↓
Graph discovers prerequisite weakness:
Verb To Be
        ↓
Next Quiz:
2 prerequisite questions
5 Present Continuous
2 contrast questions
1 application question
```

Đây là adaptive learning dựa trên knowledge graph, không chỉ dựa trên điểm trung bình.

---

## 33. Misconception Graph

Một ý tưởng mở rộng quan trọng:

```text
GrammarConcept
   └── HAS_MISCONCEPTION → CommonMistake
```

Ví dụ:

```text
Present Simple
   ↓
ForgetThirdPersonS
```

Nếu học sinh chọn `go` thay vì `goes`, hệ thống không chỉ ghi “sai câu hỏi”, mà có thể cập nhật:

```text
Student
  └── HAS_MISCONCEPTION → ForgetThirdPersonS
```

AI Tutor từ đó giải thích đúng lỗi mà học sinh thường mắc.

---

## 34. AI Gateway

Cùng một GraphRAG backend có thể phục vụ nhiều tính năng:

```text
GraphRAG Engine
    ├── AI Tutor
    ├── Quiz Generator
    ├── Explanation Engine
    ├── Error Diagnosis
    └── Study Planner
```

Khác nhau chủ yếu ở:

- retrieval policy;
- prompt;
- output schema;
- validation rules.

Không cần xây một knowledge base riêng cho từng tính năng.

---

# PHẦN IV – KIẾN TRÚC TỔNG THỂ CUỐI CÙNG

## 35. Kiến trúc end-to-end

```text
                      SGK PDF LỚP 7
                           │
                    PDF PREPROCESS
                           │
                    PAGE IMAGES
                           │
                  YOLO LAYOUT DETECTOR
                           │
                     OCR / VISION
                           │
                      NORMALIZER
                           │
                       VALIDATOR
                           │
                     HUMAN REVIEW
                           │
                    VERIFIED DATA
                           │
             ┌─────────────┴─────────────┐
             │                           │
        PostgreSQL                 Graph Builder
             │                           │
             │                     Knowledge Graph
             │                           │
             │                  Full GraphRAG Indexing
             │                           │
             │          Entities / Relations / Claims
             │                           │
             │                   Community Detection
             │                           │
             │                  Community Reports
             │                           │
             │              Graph + Vector Embeddings
             │                           │
             └──────────────┬────────────┘
                            │
                       AI Gateway
                            │
          ┌─────────────────┼──────────────────┐
          │                 │                  │
      AI Tutor        Quiz Generator     Study Planner
          │                 │                  │
          └─────────────────┼──────────────────┘
                            │
                      Student Model
                            │
                     Adaptive Learning
```

---

## 36. Data Flow

### Ingestion flow

```text
PDF
→ SourceDocument
→ Page
→ PageRegion
→ OCR Text
→ Normalized Entity
→ Review
→ Verified Data
```

### Graph flow

```text
Verified Data
→ Graph Builder
→ Verified Graph Seed
→ AI Relationship Enrichment
→ Community Detection
→ Community Reports
→ Embeddings
→ GraphRAG Index
```

### Learning flow

```text
Student
→ Lesson / Question
→ GraphRAG Retrieval
→ AI Tutor / Quiz
→ Student Answer
→ Mastery Update
→ Adaptive Recommendation
```

---

## 37. Nguyên tắc kỹ thuật quan trọng

### 37.1. Không để AI là nguồn sự thật

AI dùng để:

- extraction;
- classification;
- enrichment;
- reasoning;
- explanation;
- quiz generation.

Nhưng nguồn sự thật phải là:

- tài liệu chương trình;
- dữ liệu SGK được kiểm chứng;
- source fragment;
- mapping;
- review status.

### 37.2. Verified data mới vào production graph

```text
YOLO/OCR output
   ↓
DRAFT
```

không được dùng trực tiếp để trả lời học sinh.

Chỉ:

```text
VERIFIED
```

mới được đưa vào production retrieval.

### 37.3. AI inferred relation phải được gắn nhãn

Mọi relation AI suy luận cần có confidence/evidence/status.

### 37.4. Embedding/vector là thành phần bắt buộc

Full GraphRAG vẫn cần semantic embeddings để:

- query matching;
- entity search;
- community search;
- deduplication;
- quiz similarity;
- reranking.

### 37.5. Source traceability phải tồn tại ở mọi tầng

Một câu trả lời hoặc quiz nên truy ngược được:

```text
Question / Answer
→ Concept
→ SourceFragment
→ SourceDocument
→ Page / Region
```

---

# PHẦN V – PHẠM VI CUỐI CÙNG ĐÃ CHỐT

## 38. Phạm vi hiện tại

```text
Subject: English
Grade: 7
Curriculum: 1 official Ministry of Education curriculum
Textbook: initially one or more Grade-7 textbooks belonging to this curriculum
Input: PDF
Document AI: YOLO + OCR/Vision
Data architecture: Normalized relational data
Knowledge layer: Knowledge Graph
RAG architecture: Full GraphRAG
Semantic layer: Embeddings + Vector Search
AI features: Tutor + Quiz + Explanation + Diagnosis + Adaptive Learning
```

Điểm quan trọng:

- **không còn scope lớp 1–12**;
- **không còn nhiều chương trình giáo dục**;
- tập trung sâu vào một lớp và một curriculum;
- ưu tiên chất lượng dữ liệu và reasoning hơn breadth.

---

## 39. Tên đề tài gợi ý

Một số tên đã brainstorm:

### Hướng sản phẩm

**Xây dựng ứng dụng hỗ trợ học Tiếng Anh lớp 7 dựa trên chương trình giáo dục và nội dung sách giáo khoa.**

### Hướng AI

**Xây dựng ứng dụng học Tiếng Anh lớp 7 tích hợp nhận diện và trích xuất nội dung sách giáo khoa bằng AI.**

### Hướng kỹ thuật đầy đủ hơn

**Xây dựng hệ thống số hóa và hỗ trợ học Tiếng Anh lớp 7 sử dụng YOLO, OCR, Knowledge Graph và GraphRAG.**

### Hướng nhấn mạnh cá nhân hóa

**Xây dựng hệ thống học Tiếng Anh lớp 7 ứng dụng Knowledge Graph, Full GraphRAG và AI nhằm hỗ trợ học tập và sinh bài kiểm tra thích nghi.**

---

# PHẦN VI – NHỮNG ĐIỂM CÒN CẦN CHỐT

## 40. Các quyết định chưa hoàn toàn đóng

### 40.1. SGK cụ thể

Cần xác định chính xác:

- bộ sách;
- phiên bản;
- năm xuất bản;
- tập/quyển;
- nguồn PDF;
- quyền sử dụng nội dung.

### 40.2. Curriculum source

Cần có tài liệu chính thức tương ứng với chương trình Tiếng Anh lớp 7 để xây `LearningOutcome` dataset.

### 40.3. Closed-world vs open-world AI

Chưa chốt hoàn toàn AI Tutor:

- chỉ được trả lời từ dữ liệu verified của chương trình/SGK;
- hay được dùng thêm kiến thức ngoài nhưng phải tách rõ nguồn.

Một hướng an toàn cho đồ án là:

```text
Core answers → verified knowledge only
Optional enrichment → clearly marked external knowledge
```

### 40.4. Graph ontology chi tiết

Cần chốt:

- node types chính thức;
- relationship types chính thức;
- relation nào explicit;
- relation nào AI được quyền infer;
- confidence threshold;
- review workflow.

### 40.5. Quiz policy

Cần chốt:

- số lượng câu;
- difficulty model;
- question types;
- adaptive weighting;
- mastery update algorithm;
- deduplication threshold;
- review policy cho câu do AI tạo.

---

# PHẦN VII – THỨ TỰ TRIỂN KHAI ĐƯỢC ĐỀ XUẤT

## 41. Roadmap đề xuất

### Phase 1 – Data Foundation

- xác định curriculum source;
- xác định SGK lớp 7;
- xây Source Registry;
- xây PDF preflight;
- render page images;
- thiết kế YOLO classes;
- annotate dataset;
- train YOLO v1;
- OCR/Vision pipeline;
- normalized textbook schema;
- human review workflow.

### Phase 2 – Curriculum Mapping

- extract Learning Outcomes;
- verify outcomes;
- map textbook content ↔ learning outcomes;
- xây source traceability.

### Phase 3 – Knowledge Graph

- chốt ontology;
- build verified graph seed;
- add inferred relations;
- add evidence/confidence;
- graph validation.

### Phase 4 – Full GraphRAG

- entity/relationship/claim indexing;
- community detection;
- hierarchical communities;
- community reports;
- text/entity/community embeddings;
- Local Search;
- Global Search;
- DRIFT Search.

### Phase 5 – AI Tutor

- question understanding;
- entity linking;
- graph retrieval;
- evidence retrieval;
- grounded explanation;
- misconception diagnosis.

### Phase 6 – Quiz Engine

- quiz blueprint;
- GraphRAG retrieval;
- candidate generation;
- validation;
- deduplication;
- difficulty estimation;
- source traceability.

### Phase 7 – Student Model & Adaptive Learning

- mastery score;
- misconception tracking;
- weak concept detection;
- prerequisite analysis;
- adaptive quiz;
- study recommendations.

---

# 42. Kết luận ý tưởng

Ý tưởng cuối cùng không còn là một app “đọc SGK” hay một app quiz đơn giản.

Nó trở thành một hệ thống gồm ba lớp chính:

```text
1. DATA LAYER
PDF / Curriculum
→ YOLO / OCR
→ Normalization
→ Verification

2. KNOWLEDGE LAYER
Verified Data
→ Knowledge Graph
→ Full GraphRAG
→ Embeddings / Vector

3. LEARNING LAYER
AI Tutor
Quiz Generation
Student Mastery
Adaptive Learning
```

Giá trị cốt lõi của hệ thống là:

> **Biến nội dung Tiếng Anh lớp 7 từ SGK và chương trình giáo dục thành một kho tri thức có cấu trúc, có nguồn gốc rõ ràng, có quan hệ ngữ nghĩa, rồi sử dụng Full GraphRAG và AI để hỗ trợ học sinh hiểu bài, luyện tập đúng trọng tâm và nhận quiz phù hợp với mức độ hiện tại của mình.**

Đây là hướng phù hợp cho một đồ án có chiều sâu về:

- Computer Vision;
- OCR;
- Data Engineering;
- Knowledge Graph;
- GraphRAG;
- Vector Embedding;
- LLM;
- Educational AI;
- Adaptive Learning.

