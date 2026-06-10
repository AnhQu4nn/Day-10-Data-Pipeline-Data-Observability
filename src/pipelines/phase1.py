from __future__ import annotations

import json


def main() -> None:
    """TODO(student): xay dung baseline pipeline end-to-end.

    Pseudo-code:
    1. Load settings.
    2. Load hoac fetch raw records.
    3. Clean data.
    4. Save clean CSV/JSON.
    5. Build Chroma index.
    6. Tao hoac load evaluation set.
    7. Evaluate.
    8. Run quality checks va freshness report.
    9. Tao markdown report.
    10. Co the demo agent tren vai sample question.
    """
    from datetime import datetime, UTC

    from core.config import load_settings
    from core.utils import now_utc, write_csv, write_json
    from ingestion import fetch_source_records, load_raw_records, build_clean_dataframe
    from retrieval.index import LocalEmbeddingIndex
    from evaluation import build_test_set, evaluate_pipeline
    from observability import (
        run_data_quality_checks,
        build_freshness_report,
        generate_phase1_report,
    )

    # 1. Load settings
    settings = load_settings()
    run_date = now_utc()
    print("[Phase 1] Settings loaded.")

    # 2. Load or fetch raw records
    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        print("[Phase 1] Fetching records from Crossref API...")
        records = fetch_source_records(settings)
    else:
        print("[Phase 1] Loading cached raw records...")
        records = load_raw_records(settings.paths.raw_records_json)
    print(f"[Phase 1] {len(records)} raw records ready.")

    # 3. Clean data
    df = build_clean_dataframe(records, run_date)
    print(f"[Phase 1] Cleaned dataframe: {len(df)} rows.")

    # 4. Save clean CSV/JSON
    write_csv(df, settings.paths.clean_csv)
    records_for_json = json.loads(df.to_json(orient="records", force_ascii=False))
    write_json(settings.paths.clean_json, records_for_json)
    print(f"[Phase 1] Saved clean CSV → {settings.paths.clean_csv}")
    print(f"[Phase 1] Saved clean JSON → {settings.paths.clean_json}")

    # 5. Build Chroma index
    print("[Phase 1] Building Chroma index...")
    index = LocalEmbeddingIndex.build(df, settings)
    print("[Phase 1] Chroma index built.")

    # 6. Create or load evaluation test set
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        print("[Phase 1] Building evaluation test set...")
        # Adapt column names for testset builder
        df_for_testset = df.copy()
        df_for_testset["id"] = df_for_testset["paper_id"]
        df_for_testset["abstract"] = df_for_testset["summary"]
        df_for_testset["published_date"] = df_for_testset["published"]
        build_test_set(df_for_testset, settings.paths.eval_testset)
    print(f"[Phase 1] Test set ready at {settings.paths.eval_testset}")

    # 7. Evaluate
    print("[Phase 1] Running evaluation...")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    metrics = bundle.summary
    print(f"[Phase 1] Evaluation complete — retrieval hit rate: {metrics.get('retrieval_hit_rate', 'N/A')}")

    # 8. Run quality checks and freshness report
    print("[Phase 1] Running quality checks...")
    quality = run_data_quality_checks(df, settings, report_name="baseline")
    freshness = build_freshness_report(df, settings, report_path=settings.paths.freshness_report)
    print("[Phase 1] Quality checks and freshness report done.")

    # 9. Generate markdown report
    source_summary = {
        "api": settings.source_api,
        "query": settings.source_query,
        "filter": settings.source_filter,
        "raw_records": len(records),
        "clean_rows": len(df),
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=metrics,
        quality=quality,
        freshness=freshness,
    )
    print(f"[Phase 1] Report saved → {settings.paths.baseline_report}")
    print("[Phase 1] ✅ Pipeline complete!")

