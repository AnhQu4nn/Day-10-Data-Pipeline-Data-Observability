from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _safe_str(value: Any) -> str:
    """Convert value to clean string."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return str(value).strip()
    if pd.isna(value):
        return ""
    return str(value).strip()


def _safe_list(value: Any) -> list[str]:
    """
    Convert authors/categories field to list[str].
    Hỗ trợ trường hợp value là list hoặc string ngăn cách bởi dấu phẩy.
    """
    if value is None:
        return []

    if isinstance(value, (list, tuple)):
        return [str(x).strip() for x in value if str(x).strip()]

    if pd.isna(value):
        return []

    if isinstance(value, str):
        # Nếu data lưu kiểu "A, B, C"
        return [x.strip() for x in value.split(",") if x.strip()]

    return [str(value).strip()]


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Tạo evaluation set từ cleaned dataframe.

    Mỗi item có schema:
    - id
    - question_type
    - question
    - ground_truth
    - ground_truth_doc_ids
    """

    if df is None or df.empty:
        raise ValueError("DataFrame is empty. Need at least some documents to build test set.")

    min_docs = 3
    if len(df) < min_docs:
        raise ValueError(f"Need at least {min_docs} documents, got {len(df)}.")

    required_columns = ["id", "title"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Chọn một số paper đại diện
    # Nếu dataset lớn thì lấy tối đa 10 paper để test set không quá to
    sample_size = min(10, len(df))
    sampled_df = df.sample(n=sample_size, random_state=42)

    test_set: list[dict[str, Any]] = []
    question_id = 1

    for _, row in sampled_df.iterrows():
        doc_id = _safe_str(row.get("id"))
        title = _safe_str(row.get("title"))

        if not doc_id or not title:
            continue

        abstract = _safe_str(row.get("abstract"))
        authors = _safe_list(row.get("authors"))
        published_date = _safe_str(row.get("published_date"))
        year = _safe_str(row.get("year"))
        categories = _safe_list(row.get("categories"))

        # 1. Summary question
        if abstract:
            test_set.append({
                "id": f"q{question_id:04d}",
                "question_type": "summary",
                "question": f"What is the paper '{title}' about?",
                "ground_truth": abstract,
                "ground_truth_doc_ids": [doc_id],
            })
            question_id += 1

        # 2. Authors question
        if authors:
            test_set.append({
                "id": f"q{question_id:04d}",
                "question_type": "authors",
                "question": f"Who are the authors of the paper '{title}'?",
                "ground_truth": authors,
                "ground_truth_doc_ids": [doc_id],
            })
            question_id += 1

        # 3. Date question
        if published_date or year:
            answer = published_date if published_date else year

            test_set.append({
                "id": f"q{question_id:04d}",
                "question_type": "date",
                "question": f"When was the paper '{title}' published?",
                "ground_truth": answer,
                "ground_truth_doc_ids": [doc_id],
            })
            question_id += 1

        # 4. Categories question
        if categories:
            test_set.append({
                "id": f"q{question_id:04d}",
                "question_type": "categories",
                "question": f"What categories does the paper '{title}' belong to?",
                "ground_truth": categories,
                "ground_truth_doc_ids": [doc_id],
            })
            question_id += 1

    if not test_set:
        raise ValueError("No valid test questions were generated. Check your dataframe columns/content.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(test_set, f, ensure_ascii=False, indent=2)

    return test_set