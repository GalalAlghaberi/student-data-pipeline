"""
Scraper Pipeline — Unit 7: Data Acquisition (Web Scraping)
============================================================

Acquires data from an HTML page with:
    - BeautifulSoup HTML parsing
    - Safe element extraction (guards against missing nodes)
    - Type conversion (string → int/float)
    - Text normalization
    - Schema normalization to the standard student schema

Data source: data/raw/web_students.html (local fixture)
Realistic scenario: HTML tables from university portals, public directories.

Design notes:
    - Uses a local HTML fixture to avoid ToS / rate-limit issues while still
      teaching the full BeautifulSoup workflow (Unit 7).
    - Inherits from BasePipeline (Template Method pattern).
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

from pipelines.base_pipeline import BasePipeline

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HTML_FILE: Path = Path("data/raw/web_students.html")
TABLE_SELECTOR: str = "table#students tbody tr"
MIN_CELLS_PER_ROW: int = 6


# ---------------------------------------------------------------------------
# HTML Parser
# ---------------------------------------------------------------------------

class StudentTableParser:
    """Parses a students HTML table into a list of dicts."""

    def __init__(self, html_file: Path) -> None:
        self.html_file = html_file

    def parse(self) -> list[dict[str, object]]:
        """Parse the HTML file and return a list of student records."""
        html = self._read_html()
        soup = BeautifulSoup(html, "html.parser")

        rows = soup.select(TABLE_SELECTOR)
        if not rows:
            raise ValueError(
                f"No rows found with selector '{TABLE_SELECTOR}' in {self.html_file}"
            )

        records: list[dict[str, object]] = []
        for idx, row in enumerate(rows, start=1):
            cells = row.find_all("td")
            if len(cells) < MIN_CELLS_PER_ROW:
                logger.warning("Row %d skipped — only %d cells.", idx, len(cells))
                continue

            record = self._extract_record(cells, idx)
            if record is not None:
                records.append(record)

        logger.info("Parsed %d records from %s", len(records), self.html_file)
        return records

    def _read_html(self) -> str:
        if not self.html_file.exists():
            raise FileNotFoundError(f"HTML file not found: {self.html_file}")
        return self.html_file.read_text(encoding="utf-8")

    def _extract_record(
        self,
        cells: list,
        row_number: int,
    ) -> dict[str, object] | None:
        """Convert a row of <td> cells into a normalized dict.

        Column order:
            0: student_id  1: name  2: age  3: gpa  4: attendance  5: city
        """
        try:
            return {
                "student_id": self._to_int(cells[0].get_text(strip=True)),
                "name": self._clean_text(cells[1].get_text(strip=True)),
                "age": self._to_int(cells[2].get_text(strip=True)),
                "gpa": self._to_float(cells[3].get_text(strip=True)),
                "attendance": self._to_float(cells[4].get_text(strip=True)),
                "city": self._clean_text(cells[5].get_text(strip=True)),
            }
        except (ValueError, IndexError) as exc:
            logger.warning("Row %d skipped — %s", row_number, exc)
            return None

    @staticmethod
    def _clean_text(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @staticmethod
    def _to_int(value: str) -> int | None:
        if not value:
            return None
        try:
            return int(float(value))
        except ValueError:
            return None

    @staticmethod
    def _to_float(value: str) -> float | None:
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None


# ---------------------------------------------------------------------------
# Scraper Pipeline
# ---------------------------------------------------------------------------

class ScraperPipeline(BasePipeline):
    """Web scraping pipeline for student data acquisition."""

    SOURCE_NAME: str = "scraper"

    def __init__(self, output_dir: Path, parser: StudentTableParser | None = None) -> None:
        super().__init__(output_dir=output_dir)
        self.parser = parser or StudentTableParser(html_file=HTML_FILE)

    # -- Extract ------------------------------------------------------------

    def extract(self) -> pd.DataFrame:
        """Parse the HTML file and wrap records in a DataFrame."""
        records = self.parser.parse()

        if not records:
            raise ValueError("Scraper pipeline received no records.")

        df = pd.DataFrame(records)
        self.logger.info("Extracted %d raw records from HTML.", len(df))
        return df

    # -- Transform ----------------------------------------------------------

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize types and column order to the standard schema."""
        df = df.copy()

        df["student_id"] = pd.to_numeric(df["student_id"], errors="coerce").astype("Int64")
        df["age"] = pd.to_numeric(df["age"], errors="coerce").astype("Int64")
        df["gpa"] = pd.to_numeric(df["gpa"], errors="coerce").astype("float64")
        df["attendance"] = pd.to_numeric(df["attendance"], errors="coerce").astype("float64")

        df["name"] = df["name"].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
        df["city"] = df["city"].astype("string").str.strip().str.title()

        df = self._standardize(df)

        self.logger.info("Transformed %d rows to standard schema.", len(df))
        return df

    # -- Validate -----------------------------------------------------------

    def validate(self, df: pd.DataFrame) -> None:
        """Enforce quality rules on scraped data."""
        if df.empty:
            raise ValueError("Scraper DataFrame is empty.")

        if df["student_id"].isna().any():
            raise ValueError("student_id contains NULL values.")
        if not df["student_id"].is_unique:
            raise ValueError("student_id must be unique.")

        if df["name"].isna().any():
            raise ValueError("name contains NULL values.")

        if not df["age"].between(16, 80).all():
            raise ValueError("Age contains out-of-range values (16-80).")

        # Scraper source provides gpa/attendance — must be within range
        if not df["gpa"].between(0, 4).all():
            raise ValueError("GPA contains out-of-range values (0-4).")

        if not df["attendance"].between(0, 100).all():
            raise ValueError("Attendance contains out-of-range values (0-100).")

        if df["city"].isna().any():
            raise ValueError("city contains NULL values.")

        self.logger.info("Validation passed for scraper data (%d rows).", len(df))


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    ROOT = Path(__file__).resolve().parent.parent
    pipeline = ScraperPipeline(output_dir=ROOT / "data/processed/scraper")
    result = pipeline.run()

    print()
    print("=" * 60)
    print(f"Source      : {result.source}")
    print(f"Rows in     : {result.rows_in}")
    print(f"Rows out    : {result.rows_out}")
    print(f"Duration    : {result.duration:.2f}s")
    print(f"Output      : {result.output_path}")
    if result.errors:
        print(f"Errors      : {'; '.join(result.errors)}")
    print("=" * 60)