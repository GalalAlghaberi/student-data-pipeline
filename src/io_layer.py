"""I/O Layer — Load and Save operations (Sources & Sinks)."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.config import DEFAULT_ENCODING

logger = logging.getLogger(__name__)


def load_data(
    file_path: Path,
    encoding: str = DEFAULT_ENCODING,
    chunksize: int | None = None,
) -> pd.DataFrame:
    """
    Load a CSV file into a DataFrame with strict pre-flight checks.

    Raises:
        FileNotFoundError: file missing.
        ValueError: wrong extension, malformed CSV, encoding error, empty data.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a regular file: {file_path}")

    if file_path.suffix.lower() != ".csv":
        raise ValueError(f"Expected a .csv file, got '{file_path.suffix}'")

    logger.info("Loading data from %s", file_path)

    try:
        if chunksize:
            df = pd.concat(
                pd.read_csv(
                    file_path,
                    encoding=encoding,
                    chunksize=chunksize,
                    ignore_index=True,
                ),
                ignore_index=True,
            )
        else:
            df = pd.read_csv(file_path, encoding=encoding)
    except pd.errors.EmptyDataError as exc:
        raise ValueError("CSV file is empty or has no columns.") from exc
    except pd.errors.ParserError as exc:
        raise ValueError("Malformed CSV format.") from exc
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"Encoding error with '{encoding}'. Try 'utf-8-sig' or 'latin-1'."
        ) from exc

    if df.empty:
        raise ValueError("Input dataset contains no rows.")

    logger.info("Loaded %d rows × %d columns", len(df), df.shape[1])
    return df


def save_data(
    df: pd.DataFrame,
    output_file: Path,
    verify: bool = True,
) -> None:
    """
    Save DataFrame to CSV. Optionally verify by re-reading.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_csv(output_file, index=False, encoding=DEFAULT_ENCODING)
    except PermissionError as exc:
        raise PermissionError(
            f"Cannot write to {output_file}. Check permissions."
        ) from exc
    except OSError as exc:
        raise OSError(f"Failed to save {output_file}: {exc}") from exc

    if verify:
        if not output_file.exists():
            raise RuntimeError(f"Output file vanished: {output_file}")

        saved = pd.read_csv(output_file, encoding=DEFAULT_ENCODING)
        if len(saved) != len(df):
            raise RuntimeError(
                f"Row count mismatch after save: "
                f"expected {len(df)}, got {len(saved)}"
            )

    logger.info("Saved %d rows → %s", len(df), output_file)
