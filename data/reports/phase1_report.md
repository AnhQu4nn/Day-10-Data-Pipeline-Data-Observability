# Phase 1 — Baseline Pipeline Report

## 1. Source Summary

| Field | Value |
|-------|-------|
| api | Crossref REST API |
| query | agentic retrieval augmented generation large language model |
| filter | from-pub-date:2025-12-12,has-abstract:true |
| raw_records | 24 |
| clean_rows | 23 |

## 2. Evaluation Metrics

| Metric | Value |
|--------|-------|
| samples | 30 |
| retrieval_hit_rate | 1.0000 |
| mean_token_f1 | 0.4255 |
| judge_accuracy | 0.3333 |
| mean_judge_score | 2.3333 |

### RAGAS Metrics

- **context_precision**: [0.9999999999, 0.0, 0.0, 0.9999999999, 0.0, 0.0, 0.9999999999, 0.0, 0.0, 0.9999999999, 0.0, 0.0, 0.9999999999, 0.0, 0.0, 0.9999999999, 0.0, 0.0, 0.9999999999, 0.0, 0.0, 0.9999999999, 0.0, 0.0, 0.9999999999, 0.0, 0.0, 0.9999999999, 0.0, 0.0]
- **context_recall**: [1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, nan, 0.0, 0.0, 1.0, 0.0, 0.0]
- **faithfulness**: [nan, 1.0, 0.0, 1.0, 1.0, 0.0, nan, 1.0, 0.0, nan, nan, 0.0, 1.0, 1.0, 0.0, nan, nan, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0, nan, nan, 0.0, 1.0, 1.0, 0.0]

## 3. Data Quality

- **All passed**: True
- **Passed**: 6 / 6

| Check | Passed | Detail |
|-------|--------|--------|
| row_count | ✅ | 23 rows |
| paper_id_not_null | ✅ | 0 null paper_ids |
| paper_id_unique | ✅ | 23 unique out of 23 |
| title_not_null | ✅ | 0 null/empty titles |
| summary_min_length | ✅ | 0 summaries shorter than 50 chars |
| freshness | ✅ | 0 rows older than 180 days |

## 4. Freshness Report

- **Latest published**: 2026-06-02 00:00:00+00:00
- **Oldest published**: 2025-12-19 00:00:00+00:00
- **Total rows**: 23
- **Stale rows**: 0
- **Is fresh**: True
