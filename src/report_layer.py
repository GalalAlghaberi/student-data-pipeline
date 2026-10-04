"""Report Layer — Data quality analysis (read-only)."""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

QUALITY_TIERS: tuple[tuple[float, str], ...] = (
    (0, "Excellent"),
    (5, "Good"),
    (20, "Acceptable"),
    (50, "Poor"),
    (100, "Critical"),
)


def _quality_tier(missing_pct: float) -> str:
    for threshold, label in QUALITY_TIERS:
        if missing_pct <= threshold:
            return label
    return "Critical"


def generate_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    """Vectorized quality report — one row per column."""
    report = pd.DataFrame(
        {
            "column": df.columns,
            "data_type": df.dtypes.astype(str).values,
            "missing_count": df.isnull().sum().values,
            "unique_count": df.nunique().values,
        }
    )

    if len(df) > 0:
        report["missing_percentage"] = (
            report["missing_count"] / len(df) * 100
        ).round(2)
    else:
        report["missing_percentage"] = 0.0
        logger.warning("Empty DataFrame: missing percentages set to 0.")

    report["completeness"] = (100 - report["missing_percentage"]).round(2)
    report["quality_tier"] = report["missing_percentage"].apply(_quality_tier)

    logger.info(
        "Quality report generated: %d columns, %d total missing.",
        len(report), int(report["missing_count"].sum()),
    )
    return report
