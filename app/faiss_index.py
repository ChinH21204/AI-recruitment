import numpy as np


def build_index(embeddings):
    """
    Xây dựng index đơn giản dùng numpy (không dùng faiss, tránh lỗi native lib).
    - Chuẩn hoá vector CV về độ dài 1 để dùng cosine.
    """
    keys = list(embeddings.keys())
    vectors = np.array([embeddings[k] for k in keys], dtype="float32")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    vectors = vectors / norms

    index = {
        "vectors": vectors,  # shape: (n_docs, dim)
        "keys": keys,
    }
    return index, keys


def search(index, keys, query_vector, top_k=5):
    """
    Tìm kiếm top_k CV gần nhất với query_vector bằng cosine similarity.
    """
    vectors = index["vectors"]
    q = np.array(query_vector, dtype="float32")
    q_norm = np.linalg.norm(q)
    if q_norm > 0:
        q = q / q_norm

    # Cosine similarities
    sims = vectors @ q  # shape: (n_docs,)
    if top_k > len(sims):
        top_k = len(sims)

    top_idx = np.argsort(-sims)[:top_k]
    results = [(keys[i], float(sims[i])) for i in top_idx]
    return results
