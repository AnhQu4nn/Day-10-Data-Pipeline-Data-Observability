from __future__ import annotations

import json


def main() -> None:
    """TODO(student): xay dung corruption -> evaluate -> repair -> compare flow.

    Pseudo-code:
    1. Load baseline metrics va clean dataset.
    2. Tao corrupted dataframe.
    3. Save corrupted artifacts.
    4. Rebuild index va evaluate.
    5. Run quality checks/freshness tren corrupted data.
    6. Repair lai tu raw records.
    7. Evaluate repaired dataset.
    8. Tao comparison report.
    """
    from datetime import UTC

    from core.config import load_settings
    from core.utils import now_utc, read_json, write_csv, write_json
    from ingestion import build_clean_dataframe, corrupt_clean_dataframe, load_raw_records
    from retrieval.index import LocalEmbeddingIndex
    from evaluation import build_test_set, evaluate_pipeline
    from observability import (
        run_data_quality_checks,
        build_freshness_report,
        generate_corruption_report,
    )

    settings = load_settings()
    run_date = now_utc()
    print("[Corruption] Settings loaded.")

    # 1. Load baseline metrics and clean dataset
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    print(f"[Corruption] Baseline metrics loaded (hit rate: {baseline_metrics.get('retrieval_hit_rate', 'N/A')})")

    records = load_raw_records(settings.paths.raw_records_json)
    df_clean = build_clean_dataframe(records, run_date)
    print(f"[Corruption] Clean dataframe: {len(df_clean)} rows.")

    # 2. Create corrupted dataframe
    print("[Corruption] Corrupting data...")
    df_corrupted = corrupt_clean_dataframe(df_clean, output_log_path=settings.paths.corruption_log)
    print(f"[Corruption] Corrupted dataframe: {len(df_corrupted)} rows.")

    # 3. Save corrupted artifacts
    write_csv(df_corrupted, settings.paths.corrupted_clean_csv)
    records_for_json = json.loads(df_corrupted.to_json(orient="records", force_ascii=False))
    write_json(settings.paths.corrupted_clean_json, records_for_json)
    print(f"[Corruption] Saved corrupted CSV → {settings.paths.corrupted_clean_csv}")

    # 4. Rebuild index and evaluate on corrupted data
    print("[Corruption] Building corrupted Chroma index...")
    corrupted_index = LocalEmbeddingIndex.build(
        df_corrupted, settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    print("[Corruption] Corrupted index built.")

    print("[Corruption] Evaluating corrupted pipeline...")
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    corrupted_metrics = corrupted_bundle.summary
    print(f"[Corruption] Corrupted hit rate: {corrupted_metrics.get('retrieval_hit_rate', 'N/A')}")

    # 5. Run quality checks/freshness on corrupted data
    print("[Corruption] Running quality checks on corrupted data...")
    corrupted_quality = run_data_quality_checks(df_corrupted, settings, report_name="corrupted")
    corrupted_freshness = build_freshness_report(
        df_corrupted, settings,
        report_path=settings.paths.quality_dir / "corrupted_freshness.json",
    )
    print(f"[Corruption] Corrupted quality: {corrupted_quality.get('passed', 0)}/{corrupted_quality.get('total_checks', 0)} passed")

    # 6. Repair from raw records (re-clean from scratch)
    print("[Corruption] Repairing data from raw records...")
    df_repaired = build_clean_dataframe(records, run_date)
    write_csv(df_repaired, settings.paths.repaired_clean_csv)
    records_for_json = json.loads(df_repaired.to_json(orient="records", force_ascii=False))
    write_json(settings.paths.repaired_clean_json, records_for_json)
    print(f"[Corruption] Repaired dataframe: {len(df_repaired)} rows.")

    # 7. Evaluate repaired dataset
    print("[Corruption] Building repaired Chroma index...")
    repaired_index = LocalEmbeddingIndex.build(
        df_repaired, settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    print("[Corruption] Evaluating repaired pipeline...")
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    repaired_metrics = repaired_bundle.summary
    print(f"[Corruption] Repaired hit rate: {repaired_metrics.get('retrieval_hit_rate', 'N/A')}")

    # Run quality/freshness on repaired data
    repaired_quality = run_data_quality_checks(df_repaired, settings, report_name="repaired")
    repaired_freshness = build_freshness_report(
        df_repaired, settings,
        report_path=settings.paths.quality_dir / "repaired_freshness.json",
    )

    # 8. Generate comparison report
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_metrics,
        repaired_metrics=repaired_metrics,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    print(f"[Corruption] Report saved → {settings.paths.comparison_report}")
    print("[Corruption] ✅ Corruption flow complete!")
