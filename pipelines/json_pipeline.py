"""JSON Pipeline — reads from students_raw.json."""
from pathlib import Path
import json
import pandas as pd
from .base_pipeline import BasePipeline


class JSONPipeline(BasePipeline):
    SOURCE_NAME = "json"

    def __init__(self, output_dir: Path, input_file: Path):
        super().__init__(output_dir)
        self.input_file = Path(input_file)

    def extract(self) -> pd.DataFrame:
        if not self.input_file.exists():
            raise FileNotFoundError(f"Not found: {self.input_file}")
        with self.input_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON must be an array of objects")
        return pd.json_normalize(data)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = df.columns.str.lower().str.strip()
        if "student_id" in df.columns:
            df["student_id"] = (
                pd.to_numeric(df["student_id"], errors="coerce").round().astype("Int64")
            )
        if "age" in df.columns:
            df["age"] = (
                pd.to_numeric(df["age"], errors="coerce").round().astype("Int64")
            )
        if "gpa" in df.columns:
            df["gpa"] = pd.to_numeric(df["gpa"], errors="coerce")
        if "attendance" in df.columns:
            df["attendance"] = pd.to_numeric(df["attendance"], errors="coerce")
        if "age" in df.columns:
            df.loc[~df["age"].between(16, 80), "age"] = pd.NA
        if "gpa" in df.columns:
            df.loc[~df["gpa"].between(0, 4), "gpa"] = pd.NA
        if "attendance" in df.columns:
            df.loc[~df["attendance"].between(0, 100), "attendance"] = pd.NA
        if "student_id" in df.columns:
            df = df.drop_duplicates(subset=["student_id"])
        return self._standardize(df)

    def validate(self, df: pd.DataFrame) -> None:
        if df.empty:
            raise ValueError("Empty dataset")
        if df["student_id"].isna().any():
            raise ValueError("Null student_id")