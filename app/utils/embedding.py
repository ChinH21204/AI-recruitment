import os
import re
import numpy as np

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:
    # Nếu không import được (thiếu torch, lỗi native lib, v.v.) thì dùng fallback thuần Python
    SentenceTransformer = None  # type: ignore


def _load_model():
    """
    Ưu tiên load model SentenceTransformer (nếu môi trường hỗ trợ),
    nếu không thì trả về None để dùng embedding fallback thuần Python.
    """
    if SentenceTransformer is None:
        print("[-] SentenceTransformer library not found. Using fallback hashing embedding.")
        return None

    # Đường dẫn tương đối từ thư mục app/utils tới thư mục models/
    finetuned_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "..",
        "models",
        "all-MiniLM-L6-v2-finetuned-jd-cv",
    )
    finetuned_path = os.path.normpath(finetuned_path)

    try:
        if os.path.isdir(finetuned_path):
            print(f"[*] Found fine-tuned model. Loading from: {finetuned_path}")
            return SentenceTransformer(finetuned_path)
        # Model gốc (mặc định tải từ HuggingFace)
        print("[*] Fine-tuned model not found. Loading base model 'all-MiniLM-L6-v2' from HuggingFace.")
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        # Nếu vẫn lỗi (ví dụ thiếu torch DLL), fallback về None
        print(f"[!] Error loading SentenceTransformer model: {e}")
        print("[!] Fallback to hashing embedding.")
        return None


model = _load_model()  # có thể là None nếu không dùng được SentenceTransformer


def _hashing_embed(text: str, dim: int = 1024) -> np.ndarray:
    """
    Fallback embedding thuần Python:
    - Tách từ đơn giản
    - Hash mỗi token vào một trong dim ô vector
    - Chuẩn hoá L2 để dùng với cosine similarity
    """
    vec = np.zeros(dim, dtype=np.float32)
    if not text:
        return vec

    tokens = re.findall(r"\w+", text.lower())
    for tok in tokens:
        idx = hash(tok) % dim
        vec[idx] += 1.0

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


def encode_text(text):
    # Nếu model load thành công, dùng SentenceTransformer
    if model is not None:
        return model.encode([text])[0]
    # Nếu không, dùng hashing embedding
    return _hashing_embed(text)


def encode_documents(doc_dict):
    embeddings = {}
    for key, text in doc_dict.items():
        embeddings[key] = encode_text(text)
    return embeddings
