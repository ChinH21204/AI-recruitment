# 📚 HƯỚNG DẪN CHI TIẾT: TÍCH HỢP AI ĐÁNH GIÁ CV

## 🎯 Tổng Quan

Hệ thống đã được tích hợp **AI tự động đánh giá CV** ứng viên so với Job Description (JD). Khi HR tạo hồ sơ ứng tuyển, hệ thống sẽ tự động:
- Trích xuất nội dung từ CV (PDF/DOCX)
- So sánh với JD bằng AI (semantic similarity)
- Tính điểm tương đồng (0-100%)
- Đưa ra quyết định và giải thích
- Lưu kết quả vào database

---

## 🏗️ KIẾN TRÚC HỆ THỐNG

```
┌─────────────────────────────────────────────────────────────┐
│                    VUE FRONTEND (Port 5173)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Component: HoSoUngTuyen/index.vue                   │  │
│  │  - Hiển thị danh sách hồ sơ                          │  │
│  │  - Hiển thị điểm AI và đánh giá                      │  │
│  │  - Nút "Xem AI", "Đánh giá lại"                      │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                         │ HTTP Request
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              LARAVEL BACKEND API (Port 8000)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  HoSoUngTuyenController::store()                     │  │
│  │  └─> autoEvaluateCv()                                │  │
│  │      └─> AIRecruitmentService::evaluateCv()           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AICvEvaluationController                            │  │
│  │  - /admin/ai/evaluate-cv (POST)                     │  │
│  │  - /admin/ai/evaluation/{id} (GET)                  │  │
│  │  - /admin/ai/search-candidates (POST)                │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                         │ HTTP Request (File Upload)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            FASTAPI AI SERVICE (Port 8001)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  /evaluate_cv (POST)                                 │  │
│  │  - Nhận: file CV (PDF/DOCX) + JD text               │  │
│  │  - Extract text từ CV                               │  │
│  │  - Encode CV & JD → vectors (SentenceTransformer)   │  │
│  │  - Tính cosine similarity                           │  │
│  │  - Trả về: similarity, decision, explanation        │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  /search (GET)                                       │  │
│  │  - Tìm CV phù hợp từ kho dữ liệu (FAISS)             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE (SQLite)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ho_so_ung_tuyens                                    │  │
│  │  - id, id_ung_vien, id_vi_tri, ...                  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ai_cv_evaluations (BẢNG MỚI)                       │  │
│  │  - id                                                │  │
│  │  - id_ho_so_ung_tuyen (FK)                          │  │
│  │  - similarity_score (0.0000 - 1.0000)              │  │
│  │  - decision (strong_match/medium_match/low_match)  │  │
│  │  - explanation (text)                               │  │
│  │  - jd_text_used (text)                               │  │
│  │  - cv_text_extracted (text)                         │  │
│  │  - evaluated_at (timestamp)                         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 FLOW HOẠT ĐỘNG CHI TIẾT

### **Scenario 1: Tạo Hồ Sơ Ứng Tuyển (Auto-Evaluation)**

```
1. HR vào menu "Quản Lý Tuyển Dụng" → "Hồ Sơ Ứng Tuyển"
   ↓
2. Click "Thêm mới" hoặc tạo hồ sơ qua API
   ↓
3. Frontend gửi POST request:
   POST /api/admin/ho-so-ung-tuyen/create
   Body: {
     id_ung_vien: 1,
     id_vi_tri: 2,
     ngay_ung_tuyen: "2025-12-17"
   }
   ↓
4. HoSoUngTuyenController::store()
   - Validate data
   - Tạo record trong bảng ho_so_ung_tuyens
   - Gọi autoEvaluateCv($hoSo)
   ↓
5. autoEvaluateCv() - Tự động đánh giá
   a. Lấy thông tin:
      - UngVien (ứng viên) → file_cv
      - ViTriTuyenDung (vị trí) → tieu_de + mo_ta
   
   b. Tìm file CV:
      - storage/app/public/cvs/{file_cv}
      - Hoặc: public/uploads/cvs/{file_cv}
   
   c. Tạo JD text:
      JD = "{tieu_de}\n\n{mo_ta}"
   
   d. Gọi AI Service:
      AIRecruitmentService::evaluateCv($cvPath, $jdText)
      ↓
      HTTP POST → http://127.0.0.1:8001/evaluate_cv
      - Attach file CV
      - Send JD text
   ↓
6. FastAPI AI Service xử lý:
   a. Extract text từ CV:
      - PDF: dùng pdfplumber
      - DOCX: dùng docx2txt
   
   b. Encode thành vectors:
      - CV text → SentenceTransformer('all-MiniLM-L6-v2')
      - JD text → SentenceTransformer
      → 2 vectors (384 dimensions)
   
   c. Tính cosine similarity:
      similarity = cos(θ) = (A · B) / (||A|| × ||B||)
      → Giá trị từ 0.0 đến 1.0
   
   d. Phân loại:
      - similarity ≥ 0.75 → "strong_match"
      - 0.55 ≤ similarity < 0.75 → "medium_match"
      - similarity < 0.55 → "low_match"
   
   e. Tạo explanation:
      - "CV rất phù hợp với JD, HR nên ưu tiên xem và liên hệ."
      - "CV tương đối phù hợp, HR nên xem xét thêm."
      - "CV khá xa yêu cầu JD, không phải ứng viên ưu tiên."
   
   f. Trả về JSON:
      {
        "similarity": 0.82,
        "decision": "strong_match",
        "explanation": "CV rất phù hợp...",
        "jd_used": "..."
      }
   ↓
7. Laravel lưu kết quả:
   AiCvEvaluation::updateOrCreate(
     ['id_ho_so_ung_tuyen' => $hoSo->id],
     [
       'similarity_score' => 0.82,
       'decision' => 'strong_match',
       'explanation' => '...',
       'jd_text_used' => '...',
       'evaluated_at' => now()
     ]
   )
   ↓
8. Response về Frontend:
   {
     "id": 1,
     "ung_vien": {...},
     "vi_tri": {...},
     "ai_evaluation": {
       "similarity_score": 0.82,
       "decision": "strong_match",
       "explanation": "..."
     }
   }
   ↓
9. Frontend hiển thị:
   - Cột "Điểm AI": 82.0% (badge màu xanh)
   - Cột "Đánh giá AI": "Rất phù hợp"
   - Nút "Xem AI" để xem chi tiết
```

### **Scenario 2: Đánh Giá Lại CV (Manual)**

```
1. HR vào danh sách "Hồ Sơ Ứng Tuyển"
   ↓
2. Click nút "Đánh giá lại" trên một hồ sơ
   ↓
3. Frontend gửi request:
   POST /api/admin/ai/evaluate-cv
   Body: { id_ho_so_ung_tuyen: 1 }
   ↓
4. AICvEvaluationController::evaluate()
   - Lấy thông tin hồ sơ, ứng viên, vị trí
   - Tìm file CV
   - Gọi AI Service (giống Scenario 1, bước 6)
   - Cập nhật hoặc tạo mới record trong ai_cv_evaluations
   ↓
5. Response về Frontend
   ↓
6. Frontend reload danh sách → hiển thị kết quả mới
```

### **Scenario 3: Xem Chi Tiết Đánh Giá AI**

```
1. HR click nút "Xem AI" trên một hồ sơ
   ↓
2. Frontend mở Modal "Chi tiết đánh giá AI"
   ↓
3. Hiển thị thông tin từ ai_evaluation:
   - Điểm tương đồng: 82.0%
   - Quyết định: "Rất phù hợp"
   - Giải thích: "CV rất phù hợp với JD..."
   - Thời gian đánh giá: "17/12/2025 10:30"
```

---

## 📊 DATABASE SCHEMA

### **Bảng: ai_cv_evaluations**

```sql
CREATE TABLE ai_cv_evaluations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    id_ho_so_ung_tuyen BIGINT NOT NULL,
    similarity_score DECIMAL(5,4) DEFAULT 0,  -- 0.0000 to 1.0000
    decision VARCHAR(50) NULL,                -- strong_match, medium_match, low_match
    explanation TEXT NULL,
    jd_text_used TEXT NULL,                   -- JD text đã dùng để đánh giá
    cv_text_extracted TEXT NULL,              -- CV text đã extract
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    FOREIGN KEY (id_ho_so_ung_tuyen) 
        REFERENCES ho_so_ung_tuyens(id) 
        ON DELETE CASCADE,
    
    INDEX idx_ho_so (id_ho_so_ung_tuyen),
    INDEX idx_score (similarity_score)
);
```

### **Relationship**

```php
// HoSoUngTuyen Model
public function aiEvaluation()
{
    return $this->hasOne(AICvEvaluation::class, 'id_ho_so_ung_tuyen');
}

// AICvEvaluation Model
public function hoSoUngTuyen()
{
    return $this->belongsTo(HoSoUngTuyen::class, 'id_ho_so_ung_tuyen');
}
```

---

## 🔌 API ENDPOINTS

### **1. Đánh Giá CV (Manual)**

```http
POST /api/admin/ai/evaluate-cv
Authorization: Bearer {token}
Content-Type: application/json

{
  "id_ho_so_ung_tuyen": 1
}
```

**Response:**
```json
{
  "message": "Đánh giá thành công",
  "evaluation": {
    "id": 1,
    "id_ho_so_ung_tuyen": 1,
    "similarity_score": "0.8200",
    "decision": "strong_match",
    "explanation": "CV rất phù hợp với JD, HR nên ưu tiên xem và liên hệ.",
    "evaluated_at": "2025-12-17T10:30:00.000000Z"
  }
}
```

### **2. Xem Kết Quả Đánh Giá**

```http
GET /api/admin/ai/evaluation/{id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": 1,
  "id_ho_so_ung_tuyen": 1,
  "similarity_score": "0.8200",
  "decision": "strong_match",
  "explanation": "...",
  "jd_text_used": "Senior PHP Developer\n\nTìm kiếm...",
  "evaluated_at": "2025-12-17T10:30:00.000000Z"
}
```

### **3. Tìm CV Phù Hợp Từ Kho**

```http
POST /api/admin/ai/search-candidates
Authorization: Bearer {token}
Content-Type: application/json

{
  "id_vi_tri": 2,
  "top_k": 5
}
```

**Response:**
```json
{
  "vi_tri": "Senior PHP Developer",
  "results": [
    ["CV_accountant_1.pdf", 0.85],
    ["CV_developer_2.pdf", 0.78],
    ...
  ]
}
```

### **4. Tạo Hồ Sơ (Auto-Evaluation)**

```http
POST /api/admin/ho-so-ung-tuyen/create
Authorization: Bearer {token}
Content-Type: application/json

{
  "id_ung_vien": 1,
  "id_vi_tri": 2,
  "ngay_ung_tuyen": "2025-12-17"
}
```

**Response:**
```json
{
  "id": 1,
  "id_ung_vien": 1,
  "id_vi_tri": 2,
  "ung_vien": {...},
  "vi_tri": {...},
  "ai_evaluation": {
    "similarity_score": "0.8200",
    "decision": "strong_match",
    "explanation": "..."
  }
}
```

---

## 💻 CÁCH SỬ DỤNG TRONG UI

### **Bước 1: Chuẩn Bị Dữ Liệu**

1. **Tạo Vị Trí Tuyển Dụng:**
   - Menu: "Quản Lý Tuyển Dụng" → "Vị Trí Tuyển Dụng"
   - Click "Thêm mới"
   - Nhập:
     - Tiêu đề: "Senior PHP Developer"
     - Mô tả: "Tìm kiếm PHP Developer có kinh nghiệm Laravel, MySQL, API development..."
     - Số lượng: 2
   - Lưu

2. **Tạo Ứng Viên:**
   - Menu: "Quản Lý Tuyển Dụng" → "Ứng Viên"
   - Click "Thêm mới"
   - Nhập:
     - Họ tên: "Nguyễn Văn A"
     - Email: "nguyenvana@example.com"
     - Số điện thoại: "0123456789"
     - **File CV:** Upload file PDF hoặc DOCX
   - Lưu

### **Bước 2: Tạo Hồ Sơ Ứng Tuyển (AI Tự Động Đánh Giá)**

1. **Vào trang Hồ Sơ Ứng Tuyển:**
   - Menu: "Quản Lý Tuyển Dụng" → "Hồ Sơ Ứng Tuyển (AI)"

2. **Tạo hồ sơ mới:**
   - Click "Thêm mới" (nếu có) hoặc tạo qua form
   - Chọn:
     - **Ứng viên:** Nguyễn Văn A
     - **Vị trí:** Senior PHP Developer
     - **Ngày ứng tuyển:** Hôm nay
   - Click "Lưu"

3. **Hệ thống tự động:**
   - ✅ Trích xuất text từ CV
   - ✅ So sánh với JD bằng AI
   - ✅ Tính điểm similarity
   - ✅ Lưu kết quả vào database
   - ✅ Hiển thị trong danh sách

### **Bước 3: Xem Kết Quả Đánh Giá**

**Trong danh sách hồ sơ:**

| Ứng viên | Vị trí | Điểm AI | Đánh giá AI | Action |
|----------|--------|---------|-------------|--------|
| Nguyễn Văn A | Senior PHP Developer | **82.0%** 🟢 | **Rất phù hợp** | Xem AI |

**Giải thích màu sắc:**
- 🟢 **Xanh lá:** ≥75% (Rất phù hợp - Ưu tiên xem xét)
- 🟡 **Vàng:** 55-74% (Tương đối phù hợp - Cần xem xét thêm)
- 🔴 **Đỏ:** <55% (Không phù hợp - Không phải ưu tiên)

**Click "Xem AI" để xem chi tiết:**
- Điểm tương đồng chi tiết
- Quyết định của AI
- Giải thích cụ thể
- Thời gian đánh giá

### **Bước 4: Đánh Giá Lại (Nếu Cần)**

1. Click nút **"Đánh giá lại"** trên hồ sơ
2. Xác nhận
3. Hệ thống sẽ:
   - Gọi lại AI API
   - Cập nhật kết quả mới
   - Hiển thị trong danh sách

**Khi nào nên đánh giá lại:**
- JD thay đổi
- CV được cập nhật
- Muốn kiểm tra lại độ chính xác

---

## 🧠 CƠ CHẾ AI HOẠT ĐỘNG

### **1. Sentence Embeddings**

Sử dụng model **SentenceTransformer ('all-MiniLM-L6-v2')**:
- **Input:** Text (CV hoặc JD)
- **Output:** Vector 384 dimensions
- **Cách hoạt động:**
  - Tokenize text
  - Encode qua transformer layers
  - Pooling → fixed-size vector
  - Normalize

### **2. Cosine Similarity**

```python
similarity = cosine_similarity(cv_vector, jd_vector)

# Công thức:
# cos(θ) = (A · B) / (||A|| × ||B||)
# 
# A · B = dot product
# ||A|| = norm của vector A
# ||B|| = norm của vector B
```

**Ý nghĩa:**
- **1.0:** Hoàn toàn giống nhau
- **0.8-0.9:** Rất giống
- **0.6-0.7:** Tương đối giống
- **0.4-0.5:** Ít giống
- **0.0:** Không giống

### **3. Phân Loại Quyết Định**

```python
if similarity >= 0.75:
    decision = "strong_match"
    explanation = "CV rất phù hợp với JD, HR nên ưu tiên xem và liên hệ."
elif similarity >= 0.55:
    decision = "medium_match"
    explanation = "CV tương đối phù hợp, HR nên xem xét thêm."
else:
    decision = "low_match"
    explanation = "CV khá xa yêu cầu JD, không phải ứng viên ưu tiên."
```

### **4. Text Extraction**

**PDF:**
```python
import pdfplumber
with pdfplumber.open(file_path) as pdf:
    text = ""
    for page in pdf.pages:
        text += page.extract_text() or ""
```

**DOCX:**
```python
import docx2txt
text = docx2txt.process(file_path)
```

---

## ⚙️ CẤU HÌNH

### **Backend (.env)**

```env
AI_RECRUITMENT_API_URL=http://127.0.0.1:8001
```

### **File CV Storage**

CV files nên được lưu tại:
- `storage/app/public/cvs/` (Laravel storage)
- Hoặc: `public/uploads/cvs/` (Public folder)

**Lưu ý:** Đảm bảo folder có quyền write.

### **FastAPI Service**

Chạy trên port **8001**:
```bash
cd D:\ai-recruitment
.\venv\Scripts\Activate.ps1
cd app
python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

---

## 🐛 TROUBLESHOOTING

### **Lỗi: AI không đánh giá được**

**Nguyên nhân:**
1. FastAPI service chưa chạy
2. File CV không tồn tại
3. Đường dẫn file sai

**Giải pháp:**
```bash
# Kiểm tra FastAPI
curl http://127.0.0.1:8001/docs

# Kiểm tra file CV
ls storage/app/public/cvs/

# Xem log Laravel
tail -f storage/logs/laravel.log
```

### **Lỗi: Điểm AI không hiển thị**

**Nguyên nhân:**
1. Relationship chưa load
2. Frontend chưa map đúng field

**Giải pháp:**
```php
// Controller: Đảm bảo load relationship
HoSoUngTuyen::with(['ungVien', 'viTri', 'aiEvaluation'])->get()
```

```vue
// Frontend: Đảm bảo map đúng
v.ai_evaluation?.similarity_score
```

### **Lỗi: Timeout khi gọi AI**

**Nguyên nhân:**
- CV file quá lớn
- AI service chậm

**Giải pháp:**
```php
// Tăng timeout trong AIRecruitmentService
Http::timeout(60)  // Thay vì 30
```

---

## 📈 CẢI TIẾN TƯƠNG LAI

1. **Fine-tune model:** Train trên dataset CV-JD của công ty
2. **Multi-language:** Hỗ trợ CV tiếng Việt
3. **Extract skills:** Tự động trích xuất kỹ năng từ CV
4. **JD matching:** Gợi ý JD phù hợp với CV
5. **Batch evaluation:** Đánh giá nhiều CV cùng lúc
6. **Analytics:** Thống kê tỷ lệ match, xu hướng

---

## ✅ CHECKLIST SỬ DỤNG

- [ ] FastAPI AI service đang chạy (port 8001)
- [ ] Laravel backend đang chạy (port 8000)
- [ ] Vue frontend đang chạy (port 5173)
- [ ] Database đã migrate (bảng ai_cv_evaluations)
- [ ] File CV được lưu đúng thư mục
- [ ] Đã tạo vị trí tuyển dụng với mô tả JD
- [ ] Đã tạo ứng viên với file CV
- [ ] Test tạo hồ sơ và xem AI đánh giá

---

**Tài liệu này giải thích đầy đủ cơ chế hoạt động và cách sử dụng tính năng AI đánh giá CV. Nếu có thắc mắc, vui lòng xem code hoặc log để debug.**

