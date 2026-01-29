import os
import json
import numpy as np
import faiss
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from utils.extract import extract_text, extract_all_cvs
from utils.embedding import encode_text, encode_documents

# --- Khởi tạo ứng dụng FastAPI ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Tải dữ liệu và xây dựng Index khi khởi động ---
print("[*] Đang tải dữ liệu và xây dựng index... Vui lòng chờ.")

# Tải CVs và tạo embeddings
CV_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'data', 'cvs')
CV_FOLDER = os.path.normpath(CV_FOLDER)
cv_data = extract_all_cvs(CV_FOLDER)
cv_embeddings = encode_documents(cv_data)

# Tải JDs
JD_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'jd_xample.json')
JD_FILE = os.path.normpath(JD_FILE)
with open(JD_FILE, 'r', encoding='utf-8') as f:
    jd_data = json.load(f)
jd_embeddings = encode_documents({jd['id']: jd['description'] for jd in jd_data})

# Tạo FAISS index cho CVs
embedding_dim = list(cv_embeddings.values())[0].shape[0]
faiss_index = faiss.IndexFlatL2(embedding_dim)

# Thêm embeddings vào index
cv_ids = list(cv_embeddings.keys())
embeddings_matrix = np.array(list(cv_embeddings.values())).astype('float32')
faiss_index.add(embeddings_matrix)

print(f"[*] Hoàn tất! Đã tải {len(cv_data)} CVs và {len(jd_data)} JDs. Index đã sẵn sàng.")

# --- Định nghĩa các hàm tiện ích ---
def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1).reshape(1, -1)
    vec2 = np.array(vec2).reshape(1, -1)
    return (vec1 @ vec2.T) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# --- Định nghĩa các API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "AI Service is running (Full Mode)"}

@app.post("/search")
async def search(jd_id: str = Form(...)):
    if jd_id not in jd_embeddings:
        raise HTTPException(status_code=404, detail="Không tìm thấy JD ID")

    jd_embedding = np.array([jd_embeddings[jd_id]]).astype('float32')
    
    # Tìm kiếm 5 CVs tương thích nhất
    k = 5 
    distances, indices = faiss_index.search(jd_embedding, k)
    
    results = []
    for i in range(k):
        cv_id = cv_ids[indices[0][i]]
        similarity = (1 - distances[0][i] / 2) # Chuyển đổi L2 distance sang similarity
        results.append({"cv_id": cv_id, "score": similarity})
        
    return {"matches": results}

@app.post("/evaluate_cv")
async def evaluate_cv(cv_file: UploadFile = File(...), jd_id: str = Form(...)):
    if jd_id not in jd_embeddings:
        raise HTTPException(status_code=404, detail="Không tìm thấy JD ID")

    try:
        # Lưu tạm file CV
        temp_file_path = f"temp_{cv_file.filename}"
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await cv_file.read())
        
        # Trích xuất nội dung và tạo embedding
        cv_text = extract_text(temp_file_path)
        if not cv_text.strip():
            raise HTTPException(status_code=400, detail="Không thể đọc nội dung từ file CV.")

        cv_embedding = encode_text(cv_text)
        jd_embedding = jd_embeddings[jd_id]

        # Tính độ tương đồng
        similarity = cosine_similarity(cv_embedding, jd_embedding)
        score = float(similarity[0][0])

        # Xóa file tạm
        os.remove(temp_file_path)

        # Đánh giá
        if score >= 0.7:
            evaluation = "Rất phù hợp"
        elif score >= 0.5:
            evaluation = "Phù hợp"
        else:
            evaluation = "Chưa phù hợp"

        return {
            "similarity_score": score,
            "evaluation": evaluation,
            "explanation": f"CV có độ tương đồng {score:.2%} với mô tả công việc."
        }

    except Exception as e:
        # Xóa file tạm nếu có lỗi
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý CV: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
