# Semester 2 (Units 7–12 & Reviews 3–4) Curriculum Completion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement, crop, seed, and verify all remaining units of Tiếng Anh 7 – Global Success (Units 7, 8, 9, 10, 11, 12 and Reviews 3, 4) with authentic textbook illustrations, accurate audio tracks (Tracks 47 to 89), and 100% textbook-faithful interactive exercises.

**Architecture:**
1. High-resolution page extraction from `SGK – Tiếng Anh 7 – Chương trình mới.pdf` (pages 72 to 135) using `pdftoppm`.
2. Crop visual assets for key activities (matching, road signs, film posters, festivals, energy sources, future transports, country maps) and upload to MinIO `images/`.
3. Upload all audio tracks (047.mp3 to 089.mp3) from `/home/nguyenphuong/Music/MP3_Tieng anh 7_Global Success` to MinIO `audio/`.
4. Create seed scripts adhering to DB schema (`units`, `sections`, `activities`, `activity_source_fragments`, `media_assets`, `audio_tracks`) with correct numbering and ordering.
5. Live verification on Android Pixel 10 Pro emulator (`emulator-5554`) and execution of Pytest and Flutter test suites.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, SQL Server, MinIO (S3-compatible), Flutter 3.38+ / Dart, Poppler `pdftoppm`, Pillow.

**Spec:** Textbook *Tiếng Anh 7 – Global Success (Tập 2)*, Nhà xuất bản Giáo dục Việt Nam.

## Global Constraints
- Strictly 100% authentic SGK content: no synthetic sample sentences, hints, or fabricated questions where the textbook does not provide them.
- Preserve all existing Semester 1 units (Units 1–6, Reviews 1–2).
- Section types: `getting_started`, `closer_look_1`, `closer_look_2`, `communication`, `skills_1`, `skills_2`, `looking_back_project` (or `language`, `skills` for Reviews).
- Review units numbering: Review 3 -> `91`, Review 4 -> `121` so ordering naturally succeeds Unit 9 and Unit 12.
- Media routing: audio under `/api/v1/media/audio/{track_num}` and images under `/api/v1/media/images/{filename}`.

---

### Task 1: Page Extraction & Media Ingestion Scaffolding
**Files:**
- Create: `scratch/extract_tap2_pages.py`
- Create: `scratch/upload_all_audio.py`
- Test: MinIO upload verification script

- [ ] **Step 1: Extract all pages 72 to 135 into `tap2_pages/` using `pdftoppm`**
- [ ] **Step 2: Upload all remaining audio tracks (Track 47 to 89) into MinIO `english7-media/audio/`**
- [ ] **Step 3: Verify HTTP 200 on all uploaded audio tracks via API gateway**

---

### Task 2: Implement Unit 7 (Traffic) & Unit 8 (Films)
**Files:**
- Create: `scratch/crop_unit7_unit8.py`
- Create: `seed_unit7.py`
- Create: `seed_unit8.py`

- [ ] **Step 1: Crop illustrations for Unit 7 (road signs, means of transport) and Unit 8 (film posters, types of films)**
- [ ] **Step 2: Upload Unit 7 & 8 crops to MinIO `images/`**
- [ ] **Step 3: Write and execute `seed_unit7.py` (Tracks 47–53, 7 sections, 35 activities)**
- [ ] **Step 4: Write and execute `seed_unit8.py` (Tracks 54–60, 7 sections, 35 activities)**
- [ ] **Step 5: Verify API returns Unit 7 & 8 with correct sections and activities**

---

### Task 3: Implement Unit 9 (Festivals around the World) & Review 3 (Units 7-8-9)
**Files:**
- Create: `scratch/crop_unit9_review3.py`
- Create: `seed_unit9.py`
- Create: `seed_review3.py`

- [ ] **Step 1: Crop illustrations for Unit 9 (festivals, costumes) and Review 3 (road signs, activities)**
- [ ] **Step 2: Upload Unit 9 & Review 3 crops to MinIO `images/`**
- [ ] **Step 3: Write and execute `seed_unit9.py` (Tracks 61–66, 7 sections, 35 activities)**
- [ ] **Step 4: Write and execute `seed_review3.py` (Tracks 67–68, 2 sections, 10 activities, unit number 91)**
- [ ] **Step 5: Verify API returns Unit 9 & Review 3**

---

### Task 4: Implement Unit 10 (Energy Sources) & Unit 11 (Travelling in the Future)
**Files:**
- Create: `scratch/crop_unit10_unit11.py`
- Create: `seed_unit10.py`
- Create: `seed_unit11.py`

- [ ] **Step 1: Crop illustrations for Unit 10 (energy types) and Unit 11 (flying cars, future vehicles)**
- [ ] **Step 2: Upload Unit 10 & 11 crops to MinIO `images/`**
- [ ] **Step 3: Write and execute `seed_unit10.py` (Tracks 69–74, 7 sections, 35 activities)**
- [ ] **Step 4: Write and execute `seed_unit11.py` (Tracks 75–81, 7 sections, 35 activities)**
- [ ] **Step 5: Verify API returns Unit 10 & 11**

---

### Task 5: Implement Unit 12 (English Speaking Countries) & Review 4 (Units 10-11-12)
**Files:**
- Create: `scratch/crop_unit12_review4.py`
- Create: `seed_unit12.py`
- Create: `seed_review4.py`

- [ ] **Step 1: Crop illustrations for Unit 12 (country attractions, maps) and Review 4 (future trains, icons)**
- [ ] **Step 2: Upload Unit 12 & Review 4 crops to MinIO `images/`**
- [ ] **Step 3: Write and execute `seed_unit12.py` (Tracks 82–87, 7 sections, 35 activities)**
- [ ] **Step 4: Write and execute `seed_review4.py` (Tracks 88–89, 2 sections, 10 activities, unit number 121)**
- [ ] **Step 5: Verify API returns Unit 12 & Review 4**

---

### Task 6: Full Verification & Live Demonstration
**Files:**
- Mobile and backend verification

- [ ] **Step 1: Hot restart Flutter mobile app and inspect home list (all 16 units present: Units 1–12 + Reviews 1–4)**
- [ ] **Step 2: Live test audio playback and visual rendering on emulator for Semester 2 units**
- [ ] **Step 3: Run backend pytest suite (`pytest tests`)**
- [ ] **Step 4: Run Flutter test suite (`flutter test`)**
- [ ] **Step 5: Document and present completion evidence**
