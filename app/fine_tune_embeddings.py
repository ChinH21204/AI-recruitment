import json
from typing import List

from sentence_transformers import SentenceTransformer, InputExample, losses
from sentence_transformers.evaluation import BinaryClassificationEvaluator
from torch.utils.data import DataLoader


def load_pseudo_labels(path: str) -> List[dict]:
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data.append(json.loads(line))
    return data


def create_examples(pairs: List[dict], cv_folder: str) -> List[InputExample]:
    """
    Chuyển các cặp JD–CV đã pseudo-label thành InputExample
    để fine-tune SentenceTransformer.
    """
    from utils.extract import extract_text  # import lazy để tránh vòng lặp
    import os

    examples: List[InputExample] = []
    for item in pairs:
        jd_text = item["jd_text"]
        cv_path = os.path.join(cv_folder, item["cv_file"])
        label = float(item["label"])

        # Trích xuất text từ CV
        cv_text = extract_text(cv_path)

        ex = InputExample(texts=[jd_text, cv_text], label=label)
        examples.append(ex)

    return examples


def main():
    """
    Ví dụ pipeline fine-tune đơn giản:
    - Đọc pseudo_labels.jsonl
    - Tạo InputExample
    - Fine-tune model SentenceTransformer với CosineSimilarityLoss

    Lưu ý: đây là ví dụ cơ bản, dùng cho nghiên cứu/demo.
    Để sản xuất cần thêm:
    - chia train/validation
    - checkpointing, logging, early stopping, v.v.
    """
    pseudo_label_path = "../data/pseudo_labels.jsonl"
    cv_folder = "../data/cvs"

    print(f"Đang load pseudo-labels từ: {pseudo_label_path}")
    pairs = load_pseudo_labels(pseudo_label_path)
    print(f"Tổng số cặp pseudo-label: {len(pairs)}")

    # (Tuỳ chọn) chia đơn giản train / dev
    split = int(0.8 * len(pairs)) if len(pairs) > 10 else len(pairs)
    train_pairs = pairs[:split]
    dev_pairs = pairs[split:] if split < len(pairs) else []

    print("Đang xây InputExample cho train...")
    train_examples = create_examples(train_pairs, cv_folder)

    if dev_pairs:
        print("Đang xây InputExample cho dev...")
        dev_examples = create_examples(dev_pairs, cv_folder)
    else:
        dev_examples = []

    # Load model gốc (cùng model đang dùng trong hệ thống)
    model_name = "all-MiniLM-L6-v2"
    print(f"Đang load model SentenceTransformer: {model_name}")
    model = SentenceTransformer(model_name)

    # DataLoader
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=8)

    # Loss: CosineSimilarityLoss phù hợp cho bài toán similarity nhị phân/continuous
    train_loss = losses.CosineSimilarityLoss(model=model)

    evaluator = None
    if dev_examples:
        # Dùng evaluator nhị phân đơn giản
        evaluator = BinaryClassificationEvaluator.from_input_examples(dev_examples)

    # Fine-tune
    output_path = "../models/all-MiniLM-L6-v2-finetuned-jd-cv"
    print(f"Bắt đầu fine-tune, model sẽ được lưu tại: {output_path}")

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=1,
        warmup_steps=int(0.1 * len(train_dataloader)),
        evaluator=evaluator,
        evaluation_steps=100 if dev_examples else 0,
        output_path=output_path,
        show_progress_bar=True,
    )

    print("Hoàn tất fine-tune.")


if __name__ == "__main__":
    # Ví dụ chạy:
    #   python -m app.fine_tune_embeddings
    main()




