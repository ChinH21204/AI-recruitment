import os
import json
from typing import List, Dict, Tuple

import numpy as np

from utils.extract import extract_all_cvs
from utils.embedding import encode_text, encode_documents


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = np.array(a)
    b = np.array(b)
    if a.ndim > 1:
        a = a.flatten()
    if b.ndim > 1:
        b = b.flatten()
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def load_jds(jd_path: str) -> List[Dict]:
    with open(jd_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_pseudo_labels(
    cv_folder: str,
    jd_path: str,
    output_path: str = "../data/pseudo_labels.jsonl",
    top_k_positive: int = 5,
    max_negative_per_jd: int = 20,
) -> None:
    """
    Sinh nhãn giả (pseudo-label) JD–CV dựa trên similarity từ model hiện tại.

    - Với mỗi JD:
      - Lấy top_k_positive CV có cosine similarity cao nhất làm "positive" (label = 1).
      - Lấy các CV ở cuối danh sách similarity làm "negative" (label = 0).
    - Ghi ra file JSONL: mỗi dòng là một cặp JD–CV và nhãn.
    """
    # 1. Load dữ liệu
    print(f"Đang load CV từ: {cv_folder}")
    cvs = extract_all_cvs(cv_folder)
    print(f"Tổng số CV: {len(cvs)}")

    print(f"Đang load JD từ: {jd_path}")
    jd_list = load_jds(jd_path)
    print(f"Tổng số JD: {len(jd_list)}")

    # 2. Tính embedding cho toàn bộ CV một lần
    print("Đang mã hoá toàn bộ CV...")
    cv_embeddings = encode_documents(cvs)

    # Chuyển sang mảng để tính toán nhanh hơn
    cv_keys: List[str] = list(cv_embeddings.keys())
    cv_vectors: np.ndarray = np.array([cv_embeddings[k] for k in cv_keys])

    # 3. Tạo pseudo-labels
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    num_pairs = 0

    with open(output_path, "w", encoding="utf-8") as out_f:
        for jd in jd_list:
            jd_id = jd.get("id")
            jd_text = f"{jd.get('title','')}. {jd.get('description','')}"

            print(f"Đang xử lý JD id={jd_id}...")

            # embedding JD
            jd_vec = encode_text(jd_text)

            # similarity với toàn bộ CV
            sims: List[float] = []
            for v in cv_vectors:
                sims.append(cosine_similarity(jd_vec, v))

            sims = np.array(sims)
            sorted_idx = np.argsort(-sims)  # giảm dần

            # Positive samples
            pos_idx = sorted_idx[: min(top_k_positive, len(sorted_idx))]

            # Negative samples: lấy từ cuối danh sách
            neg_idx = sorted_idx[::-1][: min(max_negative_per_jd, len(sorted_idx))]

            # Ghi positive
            for idx in pos_idx:
                record = {
                    "jd_id": jd_id,
                    "jd_text": jd_text,
                    "cv_file": cv_keys[int(idx)],
                    "label": 1,
                    "similarity": float(sims[int(idx)]),
                }
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                num_pairs += 1

            # Ghi negative
            for idx in neg_idx:
                record = {
                    "jd_id": jd_id,
                    "jd_text": jd_text,
                    "cv_file": cv_keys[int(idx)],
                    "label": 0,
                    "similarity": float(sims[int(idx)]),
                }
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                num_pairs += 1

    print(f"Đã sinh tổng cộng {num_pairs} cặp JD–CV (pseudo-label) vào: {output_path}")


if __name__ == "__main__":
    # Ví dụ chạy script:
    # python -m app.pseudo_labeling
    cv_folder = "../data/cvs"
    jd_path = "../data/jd_xample.json"
    output_path = "../data/pseudo_labels.jsonl"

    build_pseudo_labels(
        cv_folder=cv_folder,
        jd_path=jd_path,
        output_path=output_path,
        top_k_positive=5,
        max_negative_per_jd=20,
    )



