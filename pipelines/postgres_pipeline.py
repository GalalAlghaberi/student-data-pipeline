"""PostgreSQL Pipeline — reads from university_training DB."""
from pathlib import Path
import os
import pandas as pd
from .base_pipeline import BasePipeline


class PostgresPipeline(BasePipeline):
    SOURCE_NAME = "postgres"

    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.db_config = {
            "host": os.getenv("PG_HOST", "localhost"),
            "port": int(os.getenv("PG_PORT", "5432")),
            "dbname": os.getenv("PG_DB", "university_training"),
            "user": os.getenv("PG_USER", "postgres"),
            "password": os.getenv("PG_PASSWORD", "postgres"),
        }

    def extract(self) -> pd.DataFrame:
        try:
            import psycopg2
        except ImportError:
            raise ImportError("Install: pip install psycopg2-binary")

        conn = psycopg2.connect(**self.db_config)
        try:
            df = pd.read_sql_query("SELECT * FROM students", conn)
            return df
        finally:
            conn.close()

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = df.columns.str.lower().str.strip()

        # Map SQL column names to standard
        rename_map = {
            "full_name": "name",
            "student_name": "name",
        }
        df = df.rename(columns=rename_map)

        # Compute age from date_of_birth if age missing
        if "age" not in df.columns and "date_of_birth" in df.columns:
            df["date_of_birth"] = pd.to_datetime(df["date_of_birth"], errors="coerce")
            today = pd.Timestamp.now()
            df["age"] = ((today - df["date_of_birth"]).dt.days / 365.25).round().astype("Int64")

        # Type conversions (with .round() to avoid float→int cast errors)
        if "student_id" in df.columns:
            df["student_id"] = (
                pd.to_numeric(df["student_id"], errors="coerce")
                .round()
                .astype("Int64")
            )
        if "age" in df.columns:
            df["age"] = (
                pd.to_numeric(df["age"], errors="coerce")
                .round()
                .astype("Int64")
            )
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

        # Deduplicate
        if "student_id" in df.columns:
            df = df.drop_duplicates(subset=["student_id"])

        return self._standardize(df)

    def validate(self, df: pd.DataFrame) -> None:
        if df.empty:
            raise ValueError("Empty dataset")
        if df["student_id"].isna().any():
            raise ValueError("Null student_id")