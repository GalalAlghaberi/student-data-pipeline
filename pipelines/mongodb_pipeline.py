"""MongoDB Pipeline — reads from University_Ai.students."""
from pathlib import Path
import pandas as pd
from .base_pipeline import BasePipeline


class MongoDBPipeline(BasePipeline):
    SOURCE_NAME = "mongodb"

    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.uri = "mongodb://localhost:27017/"
        self.db_name = "University_Ai"
        self.collection_name = "students"

    def extract(self) -> pd.DataFrame:
        from pymongo import MongoClient

        client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        try:
            collection = client[self.db_name][self.collection_name]
            docs = list(collection.find({}))
            for d in docs:
                d.pop("_id", None)
            return pd.json_normalize(docs)
        finally:
            client.close()

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        # Flatten nested fields
        rename_map = {
            "personal.name": "name",
            "personal.age": "age",
            "personal.city": "city",
            "academic.gpa": "gpa",
            "academic.attendance": "attendance",
        }
        df = df.rename(columns=rename_map)

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

        # Deduplicate
        if "student_id" in df.columns:
            df = df.drop_duplicates(subset=["student_id"])

        return self._standardize(df)

    def validate(self, df: pd.DataFrame) -> None:
        if df.empty:
            raise ValueError("Empty dataset")
        if df["student_id"].isna().any():
            raise ValueError("Null student_id")