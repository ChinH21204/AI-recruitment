# HƯỚNG DẪN DEMO HỆ THỐNG AI RECRUITMENT + QLNS

## 🎯 Tổng Quan

Hệ thống quản lý nhân sự đã được tích hợp AI để tự động đánh giá CV ứng viên khi nộp hồ sơ.

## 🚀 Các Service Đang Chạy

### 1. Laravel Backend
- **URL**: http://127.0.0.1:8000
- **Port**: 8000
- **Status**: ✓ RUNNING

### 2. Vue.js Frontend  
- **URL**: http://localhost:5173
- **Port**: 5173
- **Status**: ✓ RUNNING

### 3. FastAPI AI Service
- **URL**: http://127.0.0.1:8001
- **Port**: 8001
- **Status**: Cần chạy thủ công (xem hướng dẫn bên dưới)

## 📋 DEMO TÍNH NĂNG AI

### Bước 1: Truy cập hệ thống
```
URL: http://localhost:5173
```

### Bước 2: Đăng nhập
- Username: admin
- Password: (theo database của bạn)

### Bước 3: Demo tích hợp AI

#### A. Tạo vị trí tuyển dụng
1. Vào menu **"Vị trí tuyển dụng"**
2. Click **"Thêm mới"**
3. Nhập:
   - Tiêu đề: "Senior PHP Developer"
   - Mô tả: "Tìm kiếm PHP Developer có kinh nghiệm Laravel, MySQL, API..."
   - Số lượng: 2
4. Lưu

#### B. Tạo ứng viên
1. Vào menu **"Ứng viên"**
2. Click **"Thêm mới"**
3. Nhập:
   - Họ tên: "Nguyễn Văn A"
   - Email: "nguyenvana@example.com"
   - Số điện thoại: "0123456789"
   - File CV: (upload file CV của ứng viên)
4. Lưu

#### C. Tạo hồ sơ ứng tuyển (AI sẽ tự động đánh giá)
1. Vào menu **"Hồ sơ ứng tuyển"**
2. Tạo hồ sơ mới:
   - Chọn ứng viên: "Nguyễn Văn A"
   - Chọn vị trí: "Senior PHP Developer"
   - Ngày ứng tuyển: hôm nay
3. Click **"Lưu"**

**✨ Hệ thống AI sẽ tự động:**
- Trích xuất nội dung từ CV (PDF/DOCX)
- So sánh với JD (Job Description)
- Tính điểm tương đồng (0-100%)
- Đưa ra quyết định:
  - 🟢 **Rất phù hợp** (≥75%)
  - 🟡 **Tương đối phù hợp** (55-74%)
  - 🔴 **Không phù hợp** (<55%)
- Giải thích lý do

#### D. Xem kết quả đánh giá AI
1. Trong danh sách **"Hồ sơ ứng tuyển"**
2. Cột **"Điểm AI"** hiển thị % tương đồng
3. Cột **"Đánh giá AI"** hiển thị badge màu
4. Click nút **"Xem AI"** để xem chi tiết:
   - Điểm tương đồng chi tiết
   - Quyết định của AI
   - Giải thích cụ thể
   - Thời gian đánh giá

#### E. Đánh giá lại CV
- Click nút **"Đánh giá lại"** để AI đánh giá lại CV
- Hữu ích khi:
  - JD thay đổi
  - CV được cập nhật
  - Muốn kiểm tra lại

## 🔧 Chạy FastAPI AI Service (Nếu chưa chạy)

Mở terminal mới và chạy:

```powershell
# Kích hoạt virtual environment
cd D:\ai-recruitment
.\venv\Scripts\Activate.ps1

# Cài đặt dependencies (nếu cần)
pip install fastapi uvicorn python-multipart

# Chạy service
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Kiểm tra:
```
http://127.0.0.1:8001/docs
```

## 📊 Kiến trúc tích hợp

```
┌─────────────────┐
│  Vue Frontend   │ :5173
│  (User Interface)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Laravel Backend │ :8000
│ (Business Logic)│
└────────┬────────┘
         │
         ├──────────────┐
         │              │
         ▼              ▼
┌──────────────┐  ┌─────────────┐
│   Database   │  │  FastAPI AI │ :8001
│   (SQLite)   │  │  (AI Service)│
└──────────────┘  └─────────────┘
```

## 🎬 Flow tự động đánh giá CV

```
1. HR tạo HoSoUngTuyen (hồ sơ ứng tuyển)
   ↓
2. HoSoUngTuyenController::store()
   ↓
3. autoEvaluateCv() - tự động được gọi
   ↓
4. AIRecruitmentService::evaluateCv()
   ↓
5. HTTP POST → FastAPI (/evaluate_cv)
   ↓
6. AI xử lý:
   - Extract CV text
   - Encode CV & JD → vectors
   - Calculate cosine similarity
   - Generate decision & explanation
   ↓
7. Lưu vào bảng ai_cv_evaluations
   ↓
8. Frontend hiển thị kết quả
```

## 💾 Database Schema (AI mới thêm)

### Bảng: ai_cv_evaluations
```sql
- id
- id_ho_so_ung_tuyen (FK)
- similarity_score (0.0000 - 1.0000)
- decision (strong_match/medium_match/low_match)
- explanation (text)
- jd_text_used (text)
- cv_text_extracted (text)
- evaluated_at (timestamp)
```

## 🔍 API Endpoints mới

### 1. Đánh giá CV
```
POST /api/admin/ai/evaluate-cv
Headers: Authorization: Bearer {token}
Body: { "id_ho_so_ung_tuyen": 1 }
```

### 2. Xem kết quả đánh giá
```
GET /api/admin/ai/evaluation/{id}
Headers: Authorization: Bearer {token}
```

### 3. Tìm CV phù hợp từ kho
```
POST /api/admin/ai/search-candidates
Headers: Authorization: Bearer {token}
Body: { "id_vi_tri": 1, "top_k": 5 }
```

## 📝 File quan trọng

### Backend (Laravel)
- `app/Models/AiCvEvaluation.php` - Model
- `app/Services/AIRecruitmentService.php` - Service gọi AI
- `app/Http/Controllers/AICvEvaluationController.php` - Controller
- `app/Http/Controllers/HoSoUngTuyenController.php` - Tích hợp auto-eval
- `routes/api.php` - Routes

### Frontend (Vue)
- `src/components/Admin/HoSoUngTuyen/index.vue` - Hiển thị điểm AI

### AI Service (FastAPI)
- `app/main.py` - FastAPI endpoints
- `app/utils/embedding.py` - Sentence embeddings
- `app/utils/extract.py` - CV text extraction

## 🎨 UI Features

- Badge màu theo điểm:
  - 🟢 Xanh: ≥75% (Rất phù hợp)
  - 🟡 Vàng: 55-74% (Tương đối phù hợp)
  - 🔴 Đỏ: <55% (Không phù hợp)
- Modal chi tiết AI với giải thích
- Nút "Đánh giá lại" để re-evaluate

## 🐛 Troubleshooting

### Lỗi: AI service không kết nối
```
Kiểm tra:
1. FastAPI đã chạy chưa? → http://127.0.0.1:8001
2. Port 8001 có bị chiếm không?
3. File .env Laravel có AI_RECRUITMENT_API_URL đúng không?
```

### Lỗi: CV không được đánh giá
```
Kiểm tra:
1. File CV có tồn tại không? (storage/app/public/cvs/)
2. FastAPI có đang chạy không?
3. Xem log Laravel: storage/logs/laravel.log
```

### Lỗi: Điểm AI không hiển thị
```
Kiểm tra:
1. Relationship aiEvaluation trong Model HoSoUngTuyen
2. with(['ungVien', 'viTri', 'aiEvaluation']) trong Controller
3. Console browser có lỗi không?
```

## ✅ Checklist Demo

- [ ] Laravel đang chạy (port 8000)
- [ ] Vue đang chạy (port 5173)
- [ ] FastAPI đang chạy (port 8001)
- [ ] Database đã migrate
- [ ] Có data mẫu (vị trí, ứng viên)
- [ ] Có file CV mẫu trong storage/cvs
- [ ] Đã đăng nhập vào hệ thống
- [ ] Test tạo hồ sơ và xem AI đánh giá

## 📞 Support

Nếu gặp vấn đề, kiểm tra:
1. Laravel logs: `storage/logs/laravel.log`
2. Browser console: F12 → Console tab
3. FastAPI logs: terminal đang chạy uvicorn

---
**Lưu ý**: Đây là bản demo, trong production cần thêm authentication, validation, error handling tốt hơn.




