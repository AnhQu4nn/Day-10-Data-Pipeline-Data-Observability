from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """TODO(student): tao bo data quality checks.

    Pseudo-code:
    1. Check row count.
    2. Check `paper_id` not null va unique.
    3. Check `title` not null.
    4. Check do dai `summary`.
    5. Check freshness bang `age_days`.
        6. Ghi ket qua vao `data/quality/`.
    """
    checks: list[dict[str, Any]] = []

    # 1. Check row count
    row_count = len(df)
    checks.append({
        "check": "row_count",
        "passed": row_count > 0,
        "detail": f"{row_count} rows",
    })

    # 2. Check paper_id not null and unique
    paper_id_null = int(df["paper_id"].isna().sum())
    paper_id_unique = int(df["paper_id"].nunique())
    checks.append({
        "check": "paper_id_not_null",
        "passed": paper_id_null == 0,
        "detail": f"{paper_id_null} null paper_ids",
    })
    checks.append({
        "check": "paper_id_unique",
        "passed": paper_id_unique == row_count,
        "detail": f"{paper_id_unique} unique out of {row_count}",
    })

    # 3. Check title not null
    title_null = int(df["title"].isna().sum()) + int((df["title"].str.len() == 0).sum())
    checks.append({
        "check": "title_not_null",
        "passed": title_null == 0,
        "detail": f"{title_null} null/empty titles",
    })

    # 4. Check summary length
    if "summary_chars" in df.columns:
        short_summaries = int((df["summary_chars"] < 50).sum())
    else:
        short_summaries = int((df["summary"].str.len() < 50).sum())
    checks.append({
        "check": "summary_min_length",
        "passed": short_summaries == 0,
        "detail": f"{short_summaries} summaries shorter than 50 chars",
    })

    # 5. Check freshness via age_days
    if "age_days" in df.columns:
        stale = int((df["age_days"] > settings.freshness_threshold_days).sum())
    else:
        stale = 0
    checks.append({
        "check": "freshness",
        "passed": stale == 0,
        "detail": f"{stale} rows older than {settings.freshness_threshold_days} days",
    })

    all_passed = all(c["passed"] for c in checks)
    report = {
        "report_name": report_name,
        "total_checks": len(checks),
        "passed": sum(1 for c in checks if c["passed"]),
        "failed": sum(1 for c in checks if not c["passed"]),
        "all_passed": all_passed,
        "checks": checks,
    }

    # 6. Write results to data/quality/
    output_path = settings.paths.quality_dir / f"{report_name}_quality.json"
    write_json(output_path, report)

    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """TODO(student): tong hop freshness report.

    Pseudo-code:
    1. Tim latest va oldest published date.
    2. Dem so dong stale.
    3. Tao payload:
       - latest_published
       - oldest_published
       - stale_rows
       - total_rows
       - is_fresh
    4. Ghi JSON report.
    """
    report_path = Path(report_path)

    # 1. Find latest and oldest published date
    if "published_dt" in df.columns:
        valid_dates = df["published_dt"].dropna()
        if len(valid_dates) > 0:
            latest = str(valid_dates.max())
            oldest = str(valid_dates.min())
        else:
            latest = "N/A"
            oldest = "N/A"
    else:
        latest = "N/A"
        oldest = "N/A"

    # 2. Count stale rows
    if "age_days" in df.columns:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    else:
        stale_rows = 0

    total_rows = len(df)

    # 3. Build payload
    payload = {
        "latest_published": latest,
        "oldest_published": oldest,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": stale_rows == 0,
        "freshness_threshold_days": settings.freshness_threshold_days,
    }

    # 4. Write JSON report
    write_json(report_path, payload)

    return payload
