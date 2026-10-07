"""
API Pipeline — Unit 7: Data Acquisition (REST APIs)
====================================================

Acquires data from a REST API with:
    - Timeout protection
    - Retry with exponential backoff
    - Pagination support
    - Graceful fallback to cached local JSON

Data source: https://dummyjson.com/users
Offline fallback: data/raw/api_students.json

Design notes:
    - The API does NOT provide `gpa` or `attendance`. These will be NaN
      after transformation. This is realistic for third-party APIs (Unit 7).
    - Inherits from BasePipeline (Template Method pattern).
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from pipelines.base_pipeline import BasePipeline

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_URL: str = "https://dummyjson.com/users"
CACHE_FILE: Path = Path("data/raw/api_students.json")

TIMEOUT_SECONDS: float = 10.0
MAX_RETRIES: int = 3
BACKOFF_BASE: float = 2.0  # 2s, 4s, 8s

PAGE_SIZE: int = 10
MAX_PAGES: int = 3


# ---------------------------------------------------------------------------
# API Client
# ---------------------------------------------------------------------------

class APIClient:
    """Minimal REST API client with retry and cache fallback."""

    def __init__(
        self,
        url: str,
        cache_file: Path,
        timeout: float = TIMEOUT_SECONDS,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self.url = url
        self.cache_file = cache_file
        self.timeout = timeout
        self.max_retries = max_retries

    def fetch_all(self, page_size: int = PAGE_SIZE, max_pages: int = MAX_PAGES) -> list[dict[str, Any]]:
        """Fetch all users with pagination + offline fallback."""
        users: list[dict[str, Any]] = []

        for page in range(max_pages):
            skip = page * page_size
            logger.info("Fetching page %d (skip=%d, limit=%d)", page + 1, skip, page_size)

            payload = self._get_with_retry(params={"limit": page_size, "skip": skip})

            if payload is None:
                logger.warning("Network unavailable — falling back to cache.")
                return self._load_from_cache()

            page_users = payload.get("users", [])
            if not page_users:
                logger.info("Empty page — stopping pagination.")
                break

            users.extend(page_users)

        if not users:
            logger.warning("No users from API — falling back to cache.")
            return self._load_from_cache()

        logger.info("Fetched %d users from API.", len(users))
        return users

    def _get_with_retry(self, params: dict[str, Any]) -> dict[str, Any] | None:
        """GET with exponential backoff. Returns None on total failure."""
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(self.url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()

            except requests.Timeout:
                logger.warning("Attempt %d/%d — timeout.", attempt, self.max_retries)
            except requests.ConnectionError:
                logger.warning("Attempt %d/%d — connection error.", attempt, self.max_retries)
            except requests.HTTPError as exc:
                # 4xx are NOT retried
                if 400 <= exc.response.status_code < 500:
                    logger.error("Client error %s — not retrying.", exc.response.status_code)
                    return None
                logger.warning("Attempt %d/%d — HTTP %s.", attempt, self.max_retries, exc.response.status_code)
            except ValueError:
                logger.error("Response is not valid JSON — stopping.")
                return None

            if attempt < self.max_retries:
                sleep_time = BACKOFF_BASE ** attempt
                logger.info("Waiting %.1fs before retry...", sleep_time)
                time.sleep(sleep_time)

        logger.error("All %d retries failed.", self.max_retries)
        return None

    def _load_from_cache(self) -> list[dict[str, Any]]:
        """Load users from the local cached JSON file."""
        if not self.cache_file.exists():
            raise FileNotFoundError(f"Cache file not found: {self.cache_file}")

        with self.cache_file.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        users = payload.get("users", [])
        logger.info("Loaded %d users from cache: %s", len(users), self.cache_file)
        return users


# ---------------------------------------------------------------------------
# API Pipeline
# ---------------------------------------------------------------------------

class APIPipeline(BasePipeline):
    """REST API pipeline for student data acquisition."""

    SOURCE_NAME: str = "api"

    def __init__(self, output_dir: Path, client: APIClient | None = None) -> None:
        super().__init__(output_dir=output_dir)
        self.client = client or APIClient(url=API_URL, cache_file=CACHE_FILE)

    # -- Extract ------------------------------------------------------------

    def extract(self) -> pd.DataFrame:
        """Fetch raw user records from the API (or cache)."""
        raw_users = self.client.fetch_all()

        if not raw_users:
            raise ValueError("API pipeline received no records.")

        df = pd.DataFrame(raw_users)
        self.logger.info("Extracted %d raw records.", len(df))
        return df

    # -- Transform ----------------------------------------------------------

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize API schema to the standard student schema."""
        df = df.copy()

        # id → student_id
        df["student_id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")

        # firstName + lastName → name
        df["name"] = (
            df["firstName"].fillna("").astype(str).str.strip()
            + " "
            + df["lastName"].fillna("").astype(str).str.strip()
        ).str.strip()

        # age
        df["age"] = pd.to_numeric(df["age"], errors="coerce").astype("Int64")

        # nested address.city → city
        df["city"] = df["address"].apply(
            lambda addr: (addr or {}).get("city") if isinstance(addr, dict) else None
        )

        # Fields NOT provided by the API (expected NaN)
        df["gpa"] = pd.NA
        df["attendance"] = pd.NA

        # Ensure standard column order (uses BasePipeline helper)
        df = self._standardize(df)

        self.logger.info("Transformed to standard schema (gpa/attendance = NaN, expected).")
        return df

    # -- Validate -----------------------------------------------------------

    def validate(self, df: pd.DataFrame) -> None:
        """Enforce quality rules for API-sourced data."""
        if df.empty:
            raise ValueError("API DataFrame is empty.")

        if df["student_id"].isna().any():
            raise ValueError("student_id contains NULL values.")
        if not df["student_id"].is_unique:
            raise ValueError("student_id must be unique.")

        if df["name"].isna().any():
            raise ValueError("name contains NULL values.")

        age_series = df["age"].dropna()
        if not age_series.between(16, 80).all():
            raise ValueError("Age contains out-of-range values (16-80).")

        if df["city"].isna().any():
            raise ValueError("city contains NULL values.")

        # gpa + attendance are ALLOWED to be NULL for API sources
        self.logger.info("Validation passed for API data (%d rows).", len(df))


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    ROOT = Path(__file__).resolve().parent.parent
    pipeline = APIPipeline(output_dir=ROOT / "data/processed/api")
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