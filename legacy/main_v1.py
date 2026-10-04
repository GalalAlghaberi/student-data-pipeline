"""
Student Performance Data Pipeline
----------------------------------
End-to-End Data Engineering Pipeline
Raw Student Data → Cleaned + Validated + ML-ready Dataset

Course: Data Engineering and Databases for AI - Unit 1
"""


from pathlib import Path
import logging
import sqlite3
import pandas as pd


# ============================================================
# Configuration (الإعدادات)
# ============================================================
RAW_FILE = Path("data/raw/students_raw.csv")
OUTPUT_FILE = Path("data/processed/students_ml_ready.csv")
LOG_FILE = Path("logs/pipeline.log")
DB_FILE = Path("student_data.db")

REQUIRED_COLUMNS = {
    "student_id",
    "name",
    "age",
    "gpa",
    "attendance",
    "city",
}


# ============================================================
# Logging Setup (إعداد التسجيل)
# ============================================================
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,

    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================
# 1) LOAD (التحميل)
# ============================================================
def load_data(file_path: Path) -> pd.DataFrame:
    """Load CSV data into a pandas DataFrame."""
    logger.info("Loading data from %s", file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    try:
        df = pd.read_csv(file_path)
    except pd.errors.ParserError as exc:
        raise ValueError("Invalid CSV format.") from exc

    if df.empty:
        raise ValueError("Input dataset is empty.")

    logger.info("Loaded %d rows and %d columns", len(df), len(df.columns))
    return df


# ============================================================
# 2) SCHEMA VALIDATION (التحقق من المخطط)
# ============================================================
def validate_schema(df: pd.DataFrame) -> None:
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing columns: {sorted(missing_columns)}")
    logger.info("Schema validation passed.")


# ============================================================
# 3) TYPE CONVERSION (تحويل الأنواع)
# ============================================================
def convert_data_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    numeric_columns = ["student_id", "age", "gpa", "attendance"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


# ============================================================
# 4) CLEANING (التنظيف)
# ============================================================
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # إزالة الصفوف المكررة تماماً
    before = len(df)
    df = df.drop_duplicates()
    logger.info("Removed %d exact duplicate rows", before - len(df))

    # إزالة معرفات الطلاب المكررة
    df = df.drop_duplicates(subset=["student_id"], keep="first")

    # تنظيف الحقول النصية
    df["name"] = df["name"].astype("string").str.strip()
    df["city"] = df["city"].astype("string").str.strip().str.title()

    # معالجة القيم غير الصالحة
    df.loc[~df["gpa"].between(0, 4), "gpa"] = pd.NA
    df.loc[~df["age"].between(16, 80), "age"] = pd.NA
    df.loc[~df["attendance"].between(0, 100), "attendance"] = pd.NA

    # ملء القيم الرقمية المفقودة بالوسيط
    for column in ["age", "gpa", "attendance"]:
        df[column] = df[column].fillna(df[column].median())

    return df


# ============================================================
# 5) VALIDATION (التحقق النهائي)
# ============================================================
def validate_data(df: pd.DataFrame) -> None:
    errors = []

    if df.empty:
        errors.append("Dataset is empty.")
    if df["student_id"].isnull().any():
        errors.append("student_id contains NULL.")
    if df["student_id"].duplicated().any():
        errors.append("student_id is not unique.")
    if df["name"].isnull().any():
        errors.append("name contains NULL.")
    if not df["age"].between(16, 80).all():
        errors.append("Invalid age values.")
    if not df["gpa"].between(0, 4).all():
        errors.append("Invalid GPA values.")
    if not df["attendance"].between(0, 100).all():
        errors.append("Invalid attendance values.")

    if errors:
        raise ValueError(
            "Validation failed:\n" + "\n".join(f"- {e}" for e in errors)
        )

    logger.info("Data validation passed.")


# ============================================================
# 6) SAVE (الحفظ)
# ============================================================
def save_data(df: pd.DataFrame, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info("Saved processed data to %s", output_file)


# ============================================================
# 7) SQLITE STORAGE (تخزين SQLite)
# ============================================================
def save_to_sqlite(df: pd.DataFrame, db_file: Path) -> None:
    connection = sqlite3.connect(db_file)
    df.to_sql("students", connection, if_exists="replace", index=False)
    connection.close()
    logger.info("Saved data to SQLite database: %s", db_file)


# ============================================================
# 8) QUALITY REPORT (تقرير الجودة)
# ============================================================
def generate_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    report = pd.DataFrame({
        "column": df.columns,
        "data_type": [str(dtype) for dtype in df.dtypes],
        "missing_count": [df[col].isnull().sum() for col in df.columns],
        "unique_count": [df[col].nunique() for col in df.columns],
    })
    report["missing_percentage"] = (
        report["missing_count"] / len(df) * 100
    ).round(2)
    return report


# ============================================================
# 9) PIPELINE (خط الأنابيب الرئيسي)
# ============================================================
def run_pipeline() -> None:
    try:
        logger.info("=" * 50)
        logger.info("Pipeline started.")

        # Extract
        df = load_data(RAW_FILE)

        # Validate schema
        validate_schema(df)

        # Transform
        df = convert_data_types(df)

        # Clean
        df = clean_data(df)

        # Validate final data
        validate_data(df)

        # Save to CSV
        save_data(df, OUTPUT_FILE)

        # Save to SQLite
        save_to_sqlite(df, DB_FILE)

        # Quality report
        report = generate_quality_report(df)
        print("\n" + "=" * 60)
        print("=== DATA QUALITY REPORT ===")
        print("=" * 60)
        print(report.to_string(index=False))

        print("\n" + "=" * 60)
        print("=== FINAL DATASET (ML-READY) ===")
        print("=" * 60)
        print(df.to_string(index=False))

        print("\n" + "=" * 60)
        print("Pipeline completed successfully.")
        print("=" * 60)

        logger.info("Pipeline completed successfully.")

    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        print(f"\n❌ Pipeline failed: {exc}")
        raise


# ============================================================
# Entry Point (نقطة الدخول)
# ============================================================
if __name__ == "__main__":
    run_pipeline()