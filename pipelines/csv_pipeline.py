"""CSV Pipeline — reads from students_raw.csv."""
from pathlib import Path
import pandas as pd
from .base_pipeline import BasePipeline


class CSVPipeline(BasePipeline):
    SOURCE_NAME = "csv"

    def __init__(self, output_dir: Path, input_file: Path):
        super().__init__(output_dir)
        self.input_file = Path(input_file)

    def extract(self) -> pd.DataFrame:
        if not self.input_file.exists():
            raise FileNotFoundError(f"Not found: {self.input_file}")
        return pd.read_csv(self.input_file)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = df.columns.str.lower().str.strip()

        # Type conversions
        if "student_id" in df.columns:
            df["student_id"] = pd.to_numeric(df["student_id"], errors="coerce").astype("Int64")
        if "age" in df.columns:
            df["age"] = pd.to_numeric(df["age"], errors="coerce").astype("Int64")
        if "gpa" in df.columns:
            df["gpa"] = pd.to_numeric(df["gpa"], errors="coerce")
        if "attendance" in df.columns:
            df["attendance"] = pd.to_numeric(df["attendance"], errors="coerce")

        # Handle outliers
        if "age" in df.columns:
            df.loc[~df["age"].between(16, 80), "age"] = pd.NA
        if "gpa" in df.columns:
            df.loc[~df["gpa"].between(0, 4), "gpa"] = pd.NA
        if "attendance" in df.columns:
            df.loc[~df["attendance"].between(0, 100), "attendance"] = pd.NA

        # Fill missing
        if "age" in df.columns and df["age"].isna().any():
            df["age"] = df["age"].fillna(df["age"].median())
        if "gpa" in df.columns and df["gpa"].isna().any():
            df["gpa"] = df["gpa"].fillna(df["gpa"].median())
        if "attendance" in df.columns and df["attendance"].isna().any():
            df["attendance"] = df["attendance"].fillna(df["attendance"].median())

        # Deduplicate by student_id
        df = df.drop_duplicates(subset=["student_id"])

        return self._standardize(df)

    def validate(self, df: pd.DataFrame) -> None:
        if df.empty:
            raise ValueError("Empty dataset")
        if df["student_id"].isna().any():
            raise ValueError("Null student_id")
        if not df["student_id"].is_unique:
            raise ValueError("Duplicate student_id")