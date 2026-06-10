from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils import write_text


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """TODO(student): viet markdown report cho baseline phase.

    Pseudo-code:
    1. Gom source summary.
    2. In metrics retrieval/evaluation.
    3. In data quality va freshness.
    4. Ghi markdown vao report_path.
    """
    report_path = Path(report_path)

    lines = [
        "# Phase 1 — Baseline Pipeline Report\n",
        "## 1. Source Summary\n",
        f"| Field | Value |",
        f"|-------|-------|",
    ]
    for key, value in source_summary.items():
        lines.append(f"| {key} | {value} |")

    lines.append("")
    lines.append("## 2. Evaluation Metrics\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    for key, value in metrics.items():
        if key == "ragas":
            continue
        display = f"{value:.4f}" if isinstance(value, float) else str(value)
        lines.append(f"| {key} | {display} |")

    if "ragas" in metrics:
        lines.append("")
        lines.append("### RAGAS Metrics\n")
        ragas = metrics["ragas"]
        if isinstance(ragas, dict):
            for key, value in ragas.items():
                display = f"{value:.4f}" if isinstance(value, float) else str(value)
                lines.append(f"- **{key}**: {display}")

    lines.append("")
    lines.append("## 3. Data Quality\n")
    lines.append(f"- **All passed**: {quality.get('all_passed', 'N/A')}")
    lines.append(f"- **Passed**: {quality.get('passed', 0)} / {quality.get('total_checks', 0)}")
    lines.append("")
    checks = quality.get("checks", [])
    if checks:
        lines.append("| Check | Passed | Detail |")
        lines.append("|-------|--------|--------|")
        for c in checks:
            status = "✅" if c["passed"] else "❌"
            lines.append(f"| {c['check']} | {status} | {c['detail']} |")

    lines.append("")
    lines.append("## 4. Freshness Report\n")
    lines.append(f"- **Latest published**: {freshness.get('latest_published', 'N/A')}")
    lines.append(f"- **Oldest published**: {freshness.get('oldest_published', 'N/A')}")
    lines.append(f"- **Total rows**: {freshness.get('total_rows', 0)}")
    lines.append(f"- **Stale rows**: {freshness.get('stale_rows', 0)}")
    lines.append(f"- **Is fresh**: {freshness.get('is_fresh', 'N/A')}")
    lines.append("")

    write_text(report_path, "\n".join(lines))


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """TODO(student): viet markdown report so sanh baseline/corrupted/repaired."""
    report_path = Path(report_path)

    lines = [
        "# Corruption & Repair Comparison Report\n",
        "## Evaluation Metrics Comparison\n",
        "| Metric | Baseline | Corrupted | Repaired |",
        "|--------|----------|-----------|----------|",
    ]

    all_keys = set()
    for d in [baseline_metrics, corrupted_metrics, repaired_metrics]:
        all_keys.update(k for k in d if k != "ragas")

    for key in sorted(all_keys):
        b = baseline_metrics.get(key, "N/A")
        c = corrupted_metrics.get(key, "N/A")
        r = repaired_metrics.get(key, "N/A")
        fmt = lambda v: f"{v:.4f}" if isinstance(v, float) else str(v)
        lines.append(f"| {key} | {fmt(b)} | {fmt(c)} | {fmt(r)} |")

    lines.append("")
    lines.append("## Data Quality Comparison\n")
    lines.append("| Phase | Passed | Failed | All Passed |")
    lines.append("|-------|--------|--------|------------|")
    for label, q in [("Corrupted", corrupted_quality), ("Repaired", repaired_quality)]:
        lines.append(
            f"| {label} | {q.get('passed', 0)} | {q.get('failed', 0)} | {q.get('all_passed', 'N/A')} |"
        )

    lines.append("")
    lines.append("## Freshness Comparison\n")
    lines.append("| Phase | Stale Rows | Total Rows | Is Fresh |")
    lines.append("|-------|------------|------------|----------|")
    for label, f in [("Corrupted", corrupted_freshness), ("Repaired", repaired_freshness)]:
        lines.append(
            f"| {label} | {f.get('stale_rows', 0)} | {f.get('total_rows', 0)} | {f.get('is_fresh', 'N/A')} |"
        )
    lines.append("")

    write_text(report_path, "\n".join(lines))
