"""End-to-end tests for the pipeline orchestrator and CLI."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from main import main
from src.orchestrator import run_pipeline


class TestRunPipeline:
    def test_runs_successfully(self, tmp_path: Path, valid_df):
        raw = tmp_path / "raw.csv"
        valid_df.to_csv(raw, index=False)
        out = tmp_path / "out.csv"
        db = tmp_path / "test.db"

        result = run_pipeline(
            raw_file=raw,
            output_file=out,
            db_file=db,
            verify_save=False,
        )

        assert result.success
        assert result.total_rows == 3
        assert out.exists()
        assert db.exists()
        assert not result.quality_report.empty

    def test_raises_on_missing_input(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            run_pipeline(
                raw_file=tmp_path / "nope.csv",
                output_file=tmp_path / "out.csv",
                db_file=tmp_path / "test.db",
            )


class TestMainCLI:
    def test_returns_zero_on_success(self, tmp_path: Path, valid_df):
        raw = tmp_path / "raw.csv"
        valid_df.to_csv(raw, index=False)

        rc = main([
            "--raw", str(raw),
            "--output", str(tmp_path / "out.csv"),
            "--db", str(tmp_path / "test.db"),
            "--no-verify",
        ])
        assert rc == 0
        assert (tmp_path / "out.csv").exists()

    def test_returns_2_on_missing_file(self, tmp_path: Path):
        rc = main([
            "--raw", str(tmp_path / "nope.csv"),
            "--output", str(tmp_path / "out.csv"),
            "--db", str(tmp_path / "test.db"),
        ])
        assert rc == 2

    def test_returns_3_on_validation_error(self, tmp_path: Path):
        # CSV missing required columns
        bad_csv = tmp_path / "bad.csv"
        pd.DataFrame({"a": [1], "b": [2]}).to_csv(bad_csv, index=False)

        rc = main([
            "--raw", str(bad_csv),
            "--output", str(tmp_path / "out.csv"),
            "--db", str(tmp_path / "test.db"),
        ])
        assert rc == 3
