# Corruption & Repair Comparison Report

## Evaluation Metrics Comparison

| Metric | Baseline | Corrupted | Repaired |
|--------|----------|-----------|----------|
| judge_accuracy | 0.3333 | 0.2000 | 0.3333 |
| mean_judge_score | 2.3333 | 1.8000 | 2.3333 |
| mean_token_f1 | 0.4255 | 0.2872 | 0.4255 |
| retrieval_hit_rate | 1.0000 | 0.7000 | 1.0000 |
| samples | 30 | 30 | 30 |

## Data Quality Comparison

| Phase | Passed | Failed | All Passed |
|-------|--------|--------|------------|
| Corrupted | 3 | 3 | False |
| Repaired | 6 | 0 | True |

## Freshness Comparison

| Phase | Stale Rows | Total Rows | Is Fresh |
|-------|------------|------------|----------|
| Corrupted | 4 | 22 | False |
| Repaired | 0 | 23 | True |
