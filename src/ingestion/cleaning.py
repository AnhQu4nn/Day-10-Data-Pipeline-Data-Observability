from __future__ import annotations

from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """TODO(student): clean raw records thanh dataframe san sang de embed.

    Pseudo-code:
    1. Normalize title, summary, authors, categories.
    2. Parse published/updated date.
    3. Tinh age_days.
    4. Tao cot helper:
       - authors_joined
       - categories_joined
       - summary_chars
       - text_for_embedding
    5. Drop duplicates va filter row xau.
    6. Sort dataframe va return.
    """
    import re
    from dataclasses import asdict

    def normalize_text(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', str(text))
        text = " ".join(text.split())
        return text.strip()

    def parse_date(date_str: str) -> pd.Timestamp | None:
        if not date_str:
            return None
        try:
            return pd.Timestamp(date_str)
        except Exception:
            return None

    # Convert records to dicts and build DataFrame
    rows = [asdict(r) for r in records]
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # 1. Normalize title, summary, authors, categories
    df["title"] = df["title"].apply(normalize_text)
    df["summary"] = df["summary"].apply(normalize_text)
    df["authors"] = df["authors"].apply(
        lambda lst: [normalize_text(a) for a in lst] if isinstance(lst, list) else []
    )
    df["categories"] = df["categories"].apply(
        lambda lst: [normalize_text(c) for c in lst] if isinstance(lst, list) else []
    )
    df["primary_category"] = df["primary_category"].apply(normalize_text)

    # 2. Parse published/updated date
    df["published_dt"] = df["published"].apply(parse_date)
    df["updated_dt"] = df["updated"].apply(parse_date)

    # 3. Compute age_days
    df["published_dt"] = pd.to_datetime(df["published_dt"], errors="coerce", utc=True)
    run_ts = pd.to_datetime(run_date, utc=True)

    df["age_days"] = (run_ts - df["published_dt"]).dt.days

    # 4. Create helper columns
    df["authors_joined"] = df["authors"].apply(lambda lst: ", ".join(lst))
    df["categories_joined"] = df["categories"].apply(lambda lst: ", ".join(lst))
    df["summary_chars"] = df["summary"].apply(len)
    df["text_for_embedding"] = df.apply(
        lambda row: f"{row['title']}. {row['summary']}", axis=1
    )

    # 5. Drop duplicates and filter bad rows
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df[df["title"].str.len() > 0]
    df = df[df["summary"].str.len() > 0]

    # 6. Sort and return
    df = df.sort_values("published_dt", ascending=False).reset_index(drop=True)

    return df
