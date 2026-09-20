# Unit 6 & Review 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Seed and verify Unit 6 ("A Visit to a School") and Review 2 ("Units 4-5-6") into the English 7 Global Success curriculum, uploading all audio tracks (38–46) and textbook illustrations to MinIO, and verifying interactive exercises on the Android emulator with 100% textbook authenticity.

**Architecture:** 
1. Crop textbook visuals from the original 150 DPI PDF pages (pages 60–71).
2. Upload MP3 audio tracks (038.mp3–046.mp3) and cropped images to MinIO (`english7-media`).
3. Seed Unit 6 and Review 2 into SQL Server (`units`, `sections`, `activities`, `source_fragments`, `audio_tracks`, `media_assets`) strictly matching SGK Global Success text and exercises without synthetic hints.
4. Verify end-to-end on Android Pixel 10 Pro emulator and execute full backend/mobile test suites.

**Tech Stack:** Python 3.12, PyMuPDF (fitz), Pillow, MinIO S3 SDK, SQLAlchemy / FreeTDS / SQL Server, Flutter 3.x / Dart, Android Emulator (Pixel 10 Pro).

**Spec:** SGK Tiếng Anh 7 – Global Success (Sách học sinh, NXB Giáo dục Việt Nam), Pages 60–71, Audio Tracks 38–46.

## Global Constraints
- Strictly 100% authentic to SGK Tiếng Anh 7: DO NOT add sample sentences, hints, or boilerplate text if the textbook does not have them.
- Preserve existing units: Unit 1, 2, 3, Review 1, 4, 5 must remain intact and functional.
- Unit titles must not repeat "Unit X: " prefix in the database `units.title` column because Flutter dynamically formats `"Unit ${number}: ${title}"`.
- Review 2 must follow the pattern established in Review 1 (`number = 61`, title = `"Review 2 (Units 4-5-6)"`).
- Audio files must stream cleanly from MinIO via `/api/v1/media/audio/{track_number}`.

---

### Task 1: Extract and Crop Visuals for Unit 6 & Review 2

**Files:**
- Create: `scratch/crop_unit6_review2.py`
- Output: `unit6_crops/*.png`, `review2_crops/*.png`

**Interfaces:**
- Consumes: `unit6_pages/page_{60..71}.png`
- Produces: Visual PNG files cropped cleanly around activities for MinIO upload

- [ ] **Step 1: Write python cropping script**

```python
# scratch/crop_unit6_review2.py
import os
from PIL import Image

os.makedirs("unit6_crops", exist_ok=True)
os.makedirs("review2_crops", exist_ok=True)

# Define crop boxes (left, upper, right, lower) scaled to 150 DPI page dimensions
# Page 61: Getting Started Act 3 school places
img_p61 = Image.open("unit6_pages/page_61.png")
w, h = img_p61.size
# Crop places pictures (Act 3)
places_crop = img_p61.crop((int(w * 0.05), int(h * 0.72), int(w * 0.52), int(h * 0.94)))
places_crop.save("unit6_crops/unit6_gettingstarted_act3_places.png")

# Page 64: A Closer Look 2 Act 4 pictures
img_p64 = Image.open("unit6_pages/page_64.png")
w, h = img_p64.size
act4_crop = img_p64.crop((int(w * 0.45), int(h * 0.08), int(w * 0.85), int(h * 0.36)))
act4_crop.save("unit6_crops/unit6_closerlook2_act4_pictures.png")

# Page 65: Communication School gate illustration
img_p65 = Image.open("unit6_pages/page_65.png")
w, h = img_p65.size
gate_crop = img_p65.crop((int(w * 0.05), int(h * 0.08), int(w * 0.50), int(h * 0.50)))
gate_crop.save("unit6_crops/unit6_communication_school.png")

# Page 66: Skills 1 Quoc Hoc Hue pictures
img_p66 = Image.open("unit6_pages/page_66.png")
w, h = img_p66.size
qh_crop = img_p66.crop((int(w * 0.05), int(h * 0.12), int(w * 0.50), int(h * 0.28)))
qh_crop.save("unit6_crops/unit6_skills1_act1_quochoc.png")

# Page 67: Skills 2 Activities pictures
img_p67 = Image.open("unit6_pages/page_67.png")
w, h = img_p67.size
act_crop = img_p67.crop((int(w * 0.05), int(h * 0.20), int(w * 0.50), int(h * 0.38)))
act_crop.save("unit6_crops/unit6_skills2_act1_activities.png")

# Page 68: Looking Back Van Mieu picture
img_p68 = Image.open("unit6_pages/page_68.png")
w, h = img_p68.size
vm_crop = img_p68.crop((int(w * 0.10), int(h * 0.74), int(w * 0.48), int(h * 0.94)))
vm_crop.save("unit6_crops/unit6_lookingback_vanmieu.png")

# Page 69: Project School photo
img_p69 = Image.open("unit6_pages/page_69.png")
w, h = img_p69.size
proj_crop = img_p69.crop((int(w * 0.08), int(h * 0.12), int(w * 0.92), int(h * 0.47)))
proj_crop.save("unit6_crops/unit6_project_school.png")

# Page 71: Review 2 Speaking School picture
img_p71 = Image.open("unit6_pages/page_71.png")
w, h = img_p71.size
r2_school = img_p71.crop((int(w * 0.10), int(h * 0.77), int(w * 0.46), int(h * 0.99)))
r2_school.save("review2_crops/review2_speaking_act2_school.png")

print("All crops generated successfully!")
```

- [ ] **Step 2: Run cropping script and inspect crops**

Run: `python3 scratch/crop_unit6_review2.py`
Expected: Success message and valid PNG files generated.

---

### Task 2: Upload Media Assets (Audio Tracks 38–46 & Images) to MinIO

**Files:**
- Create: `scratch/upload_unit6_review2_media.py`

**Interfaces:**
- Consumes: MP3 tracks `038.mp3` through `046.mp3`, cropped PNG images
- Produces: MinIO objects in `english7-media` bucket:
  - `audio/unit-6-track-38.mp3` through `audio/unit-6-track-43.mp3`
  - `audio/review-2-track-44.mp3` through `audio/review-2-track-46.mp3`
  - `images/unit6_*.png`
  - `images/review2_*.png`

- [ ] **Step 1: Write and run media upload script**

```python
# scratch/upload_unit6_review2_media.py
from minio import Minio
import glob, os

client = Minio("localhost:9000", access_key="minioadmin", secret_key="minioadmin123", secure=False)
bucket = "english7-media"

# Upload audio
audio_source = "/home/nguyenphuong/Music/MP3_Tieng anh 7_Global Success"
tracks = {
    38: "038.mp3", 39: "039.mp3", 40: "040.mp3",
    41: "041.mp3", 42: "042.mp3", 43: "043.mp3",
    44: "044.mp3", 45: "045.mp3", 46: "046.mp3"
}

for track_num, filename in tracks.items():
    prefix = "unit-6" if track_num <= 43 else "review-2"
    key = f"audio/{prefix}-track-{track_num:02d}.mp3"
    path = os.path.join(audio_source, filename)
    client.fput_object(bucket, key, path, content_type="audio/mpeg")
    print(f"Uploaded audio: {key}")

# Upload images
for img_path in glob.glob("unit6_crops/*.png") + glob.glob("review2_crops/*.png"):
    filename = os.path.basename(img_path)
    key = f"images/{filename}"
    client.fput_object(bucket, key, img_path, content_type="image/png")
    print(f"Uploaded image: {key}")
```

- [ ] **Step 2: Verify audio endpoints return HTTP 200**

Run: `for t in $(seq 38 46); do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/media/audio/$t; done`
Expected: Nine `200` responses.

---

### Task 3: Seed Unit 6 Database Content

**Files:**
- Create: `seed_unit6.py`

**Interfaces:**
- Consumes: FreeTDS database connection to SQL Server (`mssql+pyodbc://sa:YourStrong@Passw0rd@localhost:1433/english7_db`)
- Produces: 
  - 1 Unit record (`number = 6, title = "A Visit to a School"`)
  - 7 Sections (`GETTING STARTED`, `A CLOSER LOOK 1`, `A CLOSER LOOK 2`, `COMMUNICATION`, `SKILLS 1`, `SKILLS 2`, `LOOKING BACK & PROJECT`)
  - Activities, Source Fragments, Audio Tracks (38–43), and Media Assets

- [ ] **Step 1: Write and run `seed_unit6.py`**
- [ ] **Step 2: Verify Unit 6 structure via API endpoint `/api/v1/lessons/{unit6_id}/structure`**

---

### Task 4: Seed Review 2 Database Content

**Files:**
- Create: `seed_review2.py`

**Interfaces:**
- Consumes: FreeTDS database connection
- Produces:
  - 1 Unit record (`number = 61, title = "Review 2 (Units 4-5-6)"`)
  - 2 Sections (`LANGUAGE`, `SKILLS`)
  - 9 Activities with authentic SGK questions, Audio Tracks (44–46), Source Fragments, and Media Assets

- [ ] **Step 1: Write and run `seed_review2.py`**
- [ ] **Step 2: Verify Review 2 structure via API endpoint `/api/v1/lessons/{review2_id}/structure`**

---

### Task 5: Live Android Emulator Verification

**Files:**
- Modify/Run: ADB commands on `emulator-5554`

**Interfaces:**
- Consumes: Running Flutter app on `emulator-5554`
- Produces: Visual verification screenshots showing:
  - Complete home list with Unit 1 through Unit 6 and Review 1 & 2
  - Unit 6 section navigation and exercise completion
  - Audio playback for Track 38 & Track 44
  - Review 2 section navigation and interactive exercises

- [ ] **Step 1: Hot reload / restart Flutter app on emulator**
- [ ] **Step 2: Capture Home screen showing all units including Unit 6 & Review 2**
- [ ] **Step 3: Navigate into Unit 6, play audio Track 38, interact with an exercise, verify green checkmark**
- [ ] **Step 4: Navigate into Review 2, verify Language and Skills sections, test audio Track 44**

---

### Task 6: Full Regression Verification

**Files:**
- Backend: `backend/tests`
- Mobile: `mobile/test`

**Interfaces:**
- Consumes: Pytest & Flutter Test CLI
- Produces: Exit code 0 across both test suites

- [ ] **Step 1: Run Pytest: `docker exec english7-api-1 pytest tests`** (Expected: 106+ pass)
- [ ] **Step 2: Run Flutter test: `flutter test` in `mobile/`** (Expected: 17+ pass)
- [ ] **Step 3: Check git status and summarize completed work**
