"""Compare outputs from all 4 pipelines."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
COMPARISON_DIR = ROOT / "data/comparison"
COMPARISON_DIR.mkdir(parents=True, exist_ok=True)

SOURCES = ["csv", "sqlite", "postgres", "mongodb"]


def main():
    rows = []
    for source in SOURCES:
        csv_file = ROOT / f"data/processed/{source}/{source}_clean.csv"
        if not csv_file.exists():
            rows.append({
                "source": source,
                "status": "MISSING",
                "rows": 0,
                "columns": 0,
                "column_names": "",
                "missing_values": 0,
                "unique_ids": 0,
            })
            continue

        df = pd.read_csv(csv_file)
        rows.append({
            "source": source,
            "status": "OK",
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": ",".join(df.columns),
            "missing_values": int(df.isna().sum().sum()),
            "unique_ids": int(df["student_id"].nunique()) if "student_id" in df.columns else 0,
        })

    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(COMPARISON_DIR / "comparison_data.csv", index=False)

    # Markdown report
    md = ["# Pipeline Comparison Report", ""]
    md.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}")
    md.append("")
    md.append("## Summary")
    md.append("")
    md.append(summary_df.to_markdown(index=False))
    md.append("")
    md.append("## Observations")
    md.append("")
    for _, row in summary_df.iterrows():
        if row["status"] == "MISSING":
            md.append(f"- **{row['source']}**: not available")
        else:
            md.append(
                f"- **{row['source']}**: {row['rows']} rows, "
                f"{row['columns']} cols, {row['missing_values']} missing"
            )

    (COMPARISON_DIR / "comparison_report.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Report saved: {COMPARISON_DIR / 'comparison_report.md'}")


if __name__ == "__main__":
    main()