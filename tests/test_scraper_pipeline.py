"""
Tests for pipelines/scraper_pipeline.py
========================================

Coverage:
    - StudentTableParser: HTML parsing, casting, row skipping
    - ScraperPipeline: extract, transform, validate
    - End-to-end: run() using the local HTML fixture

Strategy:
    - No real network calls — everything reads from
      data/raw/web_students.html (the local fixture).
    - Uses tmp_path fixtures for isolated malformed-HTML tests.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from pipelines.scraper_pipeline import (
    HTML_FILE,
    ScraperPipeline,
    StudentTableParser,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def parser() -> StudentTableParser:
    return StudentTableParser(html_file=HTML_FILE)


@pytest.fixture
def scraper_pipeline(tmp_path: Path) -> ScraperPipeline:
    """Return a fresh ScraperPipeline writing to a tmp directory."""
    return ScraperPipeline(output_dir=tmp_path / "scraper")


# ---------------------------------------------------------------------------
# StudentTableParser — Reading HTML
# ---------------------------------------------------------------------------

class TestStudentTableParserReading:

    def test_parse_returns_list_of_dicts(self, parser: StudentTableParser) -> None:
        records = parser.parse()
        assert isinstance(records, list)
        assert len(records) == 10
        assert all(isinstance(r, dict) for r in records)

    def test_parse_returns_expected_keys(self, parser: StudentTableParser) -> None:
        records = parser.parse()
        first = records[0]
        expected_keys = {"student_id", "name", "age", "gpa", "attendance", "city"}
        assert set(first.keys()) == expected_keys

    def test_parse_missing_file_raises(self, tmp_path: Path) -> None:
        parser = StudentTableParser(html_file=tmp_path / "missing.html")
        with pytest.raises(FileNotFoundError):
            parser.parse()

    def test_parse_html_without_target_table_raises(self, tmp_path: Path) -> None:
        html = tmp_path / "empty.html"
        html.write_text("<html><body><p>No table here</p></body></html>", encoding="utf-8")

        parser = StudentTableParser(html_file=html)
        with pytest.raises(ValueError, match="No rows found"):
            parser.parse()


# ---------------------------------------------------------------------------
# StudentTableParser — Type Casting
# ---------------------------------------------------------------------------

class TestStudentTableParserCasting:

    def test_student_id_is_integer(self, parser: StudentTableParser) -> None:
        records = parser.parse()
        for r in records:
            assert isinstance(r["student_id"], int)

    def test_age_is_integer(self, parser: StudentTableParser) -> None:
        records = parser.parse()
        for r in records:
            assert isinstance(r["age"], int)

    def test_gpa_is_float(self, parser: StudentTableParser) -> None:
        records = parser.parse()
        for r in records:
            assert isinstance(r["gpa"], float)

    def test_attendance_is_float(self, parser: StudentTableParser) -> None:
        records = parser.parse()
        for r in records:
            assert isinstance(r["attendance"], float)

    def test_first_student_values(self, parser: StudentTableParser) -> None:
        first = parser.parse()[0]
        assert first["student_id"] == 3001
        assert first["name"] == "Ahmed Al-Sanaani"
        assert first["age"] == 22
        assert first["gpa"] == 3.75
        assert first["attendance"] == 92.0
        assert first["city"] == "Sanaa"

    def test_to_int_handles_decimal_strings(self) -> None:
        assert StudentTableParser._to_int("22.0") == 22
        assert StudentTableParser._to_int("22") == 22

    def test_to_int_handles_invalid(self) -> None:
        assert StudentTableParser._to_int("abc") is None
        assert StudentTableParser._to_int("") is None

    def test_to_float_handles_invalid(self) -> None:
        assert StudentTableParser._to_float("xyz") is None
        assert StudentTableParser._to_float("") is None

    def test_clean_text_strips_whitespace(self) -> None:
        assert StudentTableParser._clean_text("  hello  ") == "hello"
        assert StudentTableParser._clean_text("") is None
        assert StudentTableParser._clean_text(None) is None


# ---------------------------------------------------------------------------
# StudentTableParser — Malformed Rows
# ---------------------------------------------------------------------------

class TestStudentTableParserMalformedRows:

    def test_row_with_too_few_cells_is_skipped(self, tmp_path: Path) -> None:
        html = tmp_path / "malformed.html"
        html.write_text(
            """
            <html><body><table id="students"><tbody>
              <tr>
                <td>3001</td><td>Good Row</td><td>22</td>
                <td>3.5</td><td>90</td><td>Sanaa</td>
              </tr>
              <tr>
                <td>3002</td><td>Too Few</td><td>22</td>
              </tr>
            </tbody></table></body></html>
            """,
            encoding="utf-8",
        )
        parser = StudentTableParser(html_file=html)
        records = parser.parse()
        assert len(records) == 1
        assert records[0]["student_id"] == 3001

    def test_row_with_invalid_numeric_values_returns_none_for_those_fields(
        self, tmp_path: Path
    ) -> None:
        html = tmp_path / "invalid_numeric.html"
        html.write_text(
            """
            <html><body><table id="students"><tbody>
              <tr>
                <td>3001</td><td>Ali</td><td>not-a-number</td>
                <td>also-bad</td><td>85</td><td>Sanaa</td>
              </tr>
            </tbody></table></body></html>
            """,
            encoding="utf-8",
        )
        parser = StudentTableParser(html_file=html)
        records = parser.parse()
        assert len(records) == 1
        assert records[0]["age"] is None
        assert records[0]["gpa"] is None
        assert records[0]["attendance"] == 85.0


# ---------------------------------------------------------------------------
# ScraperPipeline — Extract
# ---------------------------------------------------------------------------

class TestScraperPipelineExtract:

    def test_extract_returns_dataframe(self, scraper_pipeline: ScraperPipeline) -> None:
        df = scraper_pipeline.extract()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10

    def test_extract_preserves_all_columns(self, scraper_pipeline: ScraperPipeline) -> None:
        df = scraper_pipeline.extract()
        for col in ("student_id", "name", "age", "gpa", "attendance", "city"):
            assert col in df.columns


# ---------------------------------------------------------------------------
# ScraperPipeline — Transform
# ---------------------------------------------------------------------------

class TestScraperPipelineTransform:

    def test_transform_enforces_dtypes(self, scraper_pipeline: ScraperPipeline) -> None:
        raw = scraper_pipeline.extract()
        result = scraper_pipeline.transform(raw)
        assert pd.api.types.is_integer_dtype(result["student_id"])
        assert pd.api.types.is_integer_dtype(result["age"])
        assert pd.api.types.is_float_dtype(result["gpa"])
        assert pd.api.types.is_float_dtype(result["attendance"])

    def test_transform_preserves_standard_column_order(self, scraper_pipeline: ScraperPipeline) -> None:
        raw = scraper_pipeline.extract()
        result = scraper_pipeline.transform(raw)
        assert list(result.columns) == scraper_pipeline.STANDARD_COLUMNS

    def test_transform_title_cases_city(self, scraper_pipeline: ScraperPipeline) -> None:
        raw = pd.DataFrame({
            "student_id": [3001],
            "name": ["Ahmed"],
            "age": [22],
            "gpa": [3.5],
            "attendance": [90.0],
            "city": ["sanaa"],
        })
        result = scraper_pipeline.transform(raw)
        assert result["city"].iloc[0] == "Sanaa"

    def test_transform_collapses_whitespace_in_name(self, scraper_pipeline: ScraperPipeline) -> None:
        raw = pd.DataFrame({
            "student_id": [3001],
            "name": ["Ahmed   Al-Sanaani"],
            "age": [22],
            "gpa": [3.5],
            "attendance": [90.0],
            "city": ["Sanaa"],
        })
        result = scraper_pipeline.transform(raw)
        assert result["name"].iloc[0] == "Ahmed Al-Sanaani"


# ---------------------------------------------------------------------------
# ScraperPipeline — Validate
# ---------------------------------------------------------------------------

class TestScraperPipelineValidate:

    def _valid_df(self, pipeline: ScraperPipeline) -> pd.DataFrame:
        return pd.DataFrame({
            "student_id": [3001, 3002],
            "name": ["Ahmed A", "Sara B"],
            "age": [22, 21],
            "gpa": [3.5, 3.8],
            "attendance": [90.0, 96.0],
            "city": ["Sanaa", "Dhamar"],
        })

    def test_validate_accepts_well_formed_data(self, scraper_pipeline: ScraperPipeline) -> None:
        df = self._valid_df(scraper_pipeline)
        scraper_pipeline.validate(df)

    def test_validate_rejects_empty_dataframe(self, scraper_pipeline: ScraperPipeline) -> None:
        empty = pd.DataFrame(columns=scraper_pipeline.STANDARD_COLUMNS)
        with pytest.raises(ValueError, match="empty"):
            scraper_pipeline.validate(empty)

    def test_validate_rejects_duplicate_student_id(self, scraper_pipeline: ScraperPipeline) -> None:
        df = self._valid_df(scraper_pipeline)
        df.loc[1, "student_id"] = 3001
        with pytest.raises(ValueError, match="unique"):
            scraper_pipeline.validate(df)

    def test_validate_rejects_null_student_id(self, scraper_pipeline: ScraperPipeline) -> None:
        df = self._valid_df(scraper_pipeline)
        df.loc[0, "student_id"] = pd.NA
        with pytest.raises(ValueError, match="student_id"):
            scraper_pipeline.validate(df)

    def test_validate_rejects_out_of_range_age(self, scraper_pipeline: ScraperPipeline) -> None:
        df = self._valid_df(scraper_pipeline)
        df.loc[0, "age"] = 150
        with pytest.raises(ValueError, match="Age"):
            scraper_pipeline.validate(df)

    def test_validate_rejects_out_of_range_gpa(self, scraper_pipeline: ScraperPipeline) -> None:
        df = self._valid_df(scraper_pipeline)
        df.loc[0, "gpa"] = 4.5
        with pytest.raises(ValueError, match="GPA"):
            scraper_pipeline.validate(df)

    def test_validate_rejects_out_of_range_attendance(self, scraper_pipeline: ScraperPipeline) -> None:
        df = self._valid_df(scraper_pipeline)
        df.loc[0, "attendance"] = 105.0
        with pytest.raises(ValueError, match="Attendance"):
            scraper_pipeline.validate(df)

    def test_validate_rejects_null_city(self, scraper_pipeline: ScraperPipeline) -> None:
        df = self._valid_df(scraper_pipeline)
        df.loc[0, "city"] = None
        with pytest.raises(ValueError, match="city"):
            scraper_pipeline.validate(df)


# ---------------------------------------------------------------------------
# End-to-End
# ---------------------------------------------------------------------------

class TestScraperPipelineEndToEnd:

    def test_full_pipeline_produces_output(self, scraper_pipeline: ScraperPipeline) -> None:
        result = scraper_pipeline.run()

        assert result.source == "scraper"
        assert result.rows_in == 10
        assert result.rows_out == 10
        assert result.duration >= 0
        assert Path(result.output_path).exists()
        assert result.errors == []

    def test_output_file_is_readable_csv(self, scraper_pipeline: ScraperPipeline) -> None:
        result = scraper_pipeline.run()
        df = pd.read_csv(result.output_path)
        assert len(df) == 10
        assert list(df.columns) == scraper_pipeline.STANDARD_COLUMNS