from __future__ import annotations

import random
from datetime import timedelta
from pathlib import Path

import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """TODO(student): simulate nhieu dang data corruption.

    Pseudo-code:
    1. Drop mot so latest records.
    2. Blank summary o mot so dong.
    3. Inject noise vao text.
    4. Lam title bi truncate.
    5. Lam published date cu di.
    6. Add duplicate rows.
    7. Rebuild `text_for_embedding`.
    8. Ghi corruption log vao output_log_path.
    """
    output_log_path = Path(output_log_path)
    rng = random.Random(42)
    corrupted = df.copy()
    log: list[dict] = []

    n = len(corrupted)

    # 1. Drop some latest records (top 3 by published_dt)
    if "published_dt" in corrupted.columns and n > 5:
        sorted_idx = corrupted["published_dt"].sort_values(ascending=False).index[:3]
        drop_ids = corrupted.loc[sorted_idx, "paper_id"].tolist()
        corrupted = corrupted.drop(sorted_idx).reset_index(drop=True)
        log.append({
            "corruption": "drop_latest_records",
            "count": len(drop_ids),
            "paper_ids": drop_ids,
        })

    n = len(corrupted)

    # 2. Blank summary on some rows
    blank_count = max(1, n // 8)
    blank_indices = rng.sample(range(n), min(blank_count, n))
    for idx in blank_indices:
        log.append({
            "corruption": "blank_summary",
            "paper_id": corrupted.at[idx, "paper_id"],
            "original_length": len(corrupted.at[idx, "summary"]),
        })
        corrupted.at[idx, "summary"] = ""
        if "summary_chars" in corrupted.columns:
            corrupted.at[idx, "summary_chars"] = 0

    # 3. Inject noise into summary
    noise_count = max(1, n // 6)
    noise_indices = rng.sample(range(n), min(noise_count, n))
    noise_phrases = [
        " XXXNOISEXX ",
        " [CORRUPTED DATA] ",
        " $$random_garbage$$ ",
        " NULL_ENTRY ",
    ]
    for idx in noise_indices:
        original = corrupted.at[idx, "summary"]
        if original:
            noise = rng.choice(noise_phrases)
            insert_pos = rng.randint(0, max(1, len(original) // 2))
            corrupted.at[idx, "summary"] = original[:insert_pos] + noise + original[insert_pos:]
            log.append({
                "corruption": "inject_noise",
                "paper_id": corrupted.at[idx, "paper_id"],
                "noise": noise.strip(),
            })

    # 4. Truncate title
    trunc_count = max(1, n // 6)
    trunc_indices = rng.sample(range(n), min(trunc_count, n))
    for idx in trunc_indices:
        original_title = corrupted.at[idx, "title"]
        if len(original_title) > 10:
            cut = rng.randint(5, max(6, len(original_title) // 3))
            corrupted.at[idx, "title"] = original_title[:cut] + "..."
            log.append({
                "corruption": "truncate_title",
                "paper_id": corrupted.at[idx, "paper_id"],
                "original_title": original_title,
                "truncated_title": corrupted.at[idx, "title"],
            })

    # 5. Make published date stale (push back 2+ years)
    stale_count = max(1, n // 5)
    stale_indices = rng.sample(range(n), min(stale_count, n))
    for idx in stale_indices:
        if "published_dt" in corrupted.columns and pd.notna(corrupted.at[idx, "published_dt"]):
            original_dt = corrupted.at[idx, "published_dt"]
            days_back = rng.randint(730, 1460)  # 2-4 years back
            new_dt = original_dt - timedelta(days=days_back)
            corrupted.at[idx, "published_dt"] = new_dt
            corrupted.at[idx, "published"] = str(new_dt.date())
            if "age_days" in corrupted.columns:
                corrupted.at[idx, "age_days"] = corrupted.at[idx, "age_days"] + days_back
            log.append({
                "corruption": "stale_date",
                "paper_id": corrupted.at[idx, "paper_id"],
                "original_date": str(original_dt.date()),
                "new_date": str(new_dt.date()),
            })

    # 6. Add duplicate rows
    dup_count = max(1, n // 8)
    dup_indices = rng.sample(range(len(corrupted)), min(dup_count, len(corrupted)))
    dup_rows = corrupted.iloc[dup_indices].copy()
    log.append({
        "corruption": "duplicate_rows",
        "count": len(dup_rows),
        "paper_ids": dup_rows["paper_id"].tolist(),
    })
    corrupted = pd.concat([corrupted, dup_rows], ignore_index=True)

    # 7. Rebuild text_for_embedding
    corrupted["text_for_embedding"] = corrupted.apply(
        lambda row: f"{row['title']}. {row['summary']}", axis=1
    )
    if "summary_chars" in corrupted.columns:
        corrupted["summary_chars"] = corrupted["summary"].apply(len)

    # 8. Write corruption log
    write_json(output_log_path, log)

    return corrupted
