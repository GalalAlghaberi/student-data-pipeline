"""
Tests for pipelines/api_pipeline.py
====================================

Coverage:
    - APIClient: cache loading, fallback behavior, HTTP error handling
    - APIPipeline: extract, transform, validate
    - End-to-end: run() with mocked network (uses cached fixture)

Strategy:
    - No real network calls — everything is mocked or read from
      data/raw/api_students.json (the cached fixture).
    - Uses unittest.mock.patch to simulate network behavior.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from pipelines.api_pipeline import APIClient, APIPipeline, CACHE_FILE

pytestmark = pytest.mark.network     # ← ✅ آخر الـ imports

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cached_users() -> list[dict]:
    """Load the cached API fixture for offline tests."""
    with CACHE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)["users"]


@pytest.fixture
def api_client() -> APIClient:
    """Return an APIClient pointed at the standard endpoints."""
    return APIClient(url="https://dummyjson.com/users", cache_file=CACHE_FILE)


@pytest.fixture
def api_pipeline(tmp_path: Path) -> APIPipeline:
    """Return a fresh APIPipeline writing to a tmp directory."""
    return APIPipeline(output_dir=tmp_path / "api")


# ---------------------------------------------------------------------------
# APIClient — Cache Loading
# ---------------------------------------------------------------------------

class TestAPIClientCache:

    def test_load_from_cache_returns_users(self, api_client: APIClient, cached_users: list[dict]) -> None:
        users = api_client._load_from_cache()
        assert isinstance(users, list)
        assert len(users) == len(cached_users)
        assert users[0]["id"] == cached_users[0]["id"]

    def test_load_from_cache_missing_file_raises(self, tmp_path: Path) -> None:
        client = APIClient(
            url="https://dummyjson.com/users",
            cache_file=tmp_path / "nonexistent.json",
        )
        with pytest.raises(FileNotFoundError):
            client._load_from_cache()

    def test_load_from_cache_has_expected_fields(self, api_client: APIClient) -> None:
        users = api_client._load_from_cache()
        first = users[0]
        for key in ("id", "firstName", "lastName", "age", "address"):
            assert key in first, f"Missing key: {key}"
        assert "city" in first["address"]


# ---------------------------------------------------------------------------
# APIClient — Fetch All (with mocked network)
# ---------------------------------------------------------------------------

class TestAPIClientFetch:

    def test_fetch_all_uses_network_when_available(self, api_client: APIClient) -> None:
        """When network succeeds, it should return users from the API."""
        mock_payload = {
            "users": [{"id": 9999, "firstName": "Test", "lastName": "User",
                       "age": 22, "address": {"city": "TestCity"}}],
            "total": 1, "skip": 0, "limit": 1,
        }

        with patch("pipelines.api_pipeline.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_payload
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            users = api_client.fetch_all(page_size=10, max_pages=1)

        assert len(users) == 1
        assert users[0]["id"] == 9999
        mock_get.assert_called()

    def test_fetch_all_falls_back_to_cache_on_timeout(self, api_client: APIClient) -> None:
        """When all retries fail with timeout, it should fall back to cache."""
        with patch("pipelines.api_pipeline.requests.get") as mock_get, \
             patch("pipelines.api_pipeline.time.sleep"):
            mock_get.side_effect = requests.Timeout("simulated timeout")

            users = api_client.fetch_all(page_size=10, max_pages=1)

        assert len(users) == 10
        assert users[0]["id"] == 3001

    def test_fetch_all_falls_back_to_cache_on_connection_error(self, api_client: APIClient) -> None:
        with patch("pipelines.api_pipeline.requests.get") as mock_get, \
             patch("pipelines.api_pipeline.time.sleep"):
            mock_get.side_effect = requests.ConnectionError("no network")

            users = api_client.fetch_all(page_size=10, max_pages=1)

        assert len(users) == 10

    def test_fetch_all_does_not_retry_on_4xx(self, api_client: APIClient) -> None:
        """4xx client errors should NOT be retried — immediate cache fallback."""
        with patch("pipelines.api_pipeline.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            http_error = requests.HTTPError("404 not found")
            http_error.response = mock_response
            mock_response.raise_for_status.side_effect = http_error
            mock_get.return_value = mock_response

            users = api_client.fetch_all(page_size=10, max_pages=1)

        # Should have attempted only ONCE (no retries)
        assert mock_get.call_count == 1
        # And fallen back to cache
        assert len(users) == 10

    def test_fetch_all_returns_empty_when_cache_missing_and_network_fails(
        self, tmp_path: Path
    ) -> None:
        client = APIClient(
            url="https://dummyjson.com/users",
            cache_file=tmp_path / "missing.json",
        )
        with patch("pipelines.api_pipeline.requests.get") as mock_get, \
             patch("pipelines.api_pipeline.time.sleep"):
            mock_get.side_effect = requests.Timeout("no network")

            with pytest.raises(FileNotFoundError):
                client.fetch_all(page_size=10, max_pages=1)


# ---------------------------------------------------------------------------
# APIPipeline — Extract
# ---------------------------------------------------------------------------

class TestAPIPipelineExtract:

    def test_extract_returns_dataframe(self, api_pipeline: APIPipeline) -> None:
        """Extract should return a non-empty DataFrame (via cache fallback)."""
        with patch("pipelines.api_pipeline.requests.get") as mock_get, \
             patch("pipelines.api_pipeline.time.sleep"):
            mock_get.side_effect = requests.ConnectionError("offline")

            df = api_pipeline.extract()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
        assert "id" in df.columns
        assert "firstName" in df.columns
        assert "address" in df.columns


# ---------------------------------------------------------------------------
# APIPipeline — Transform
# ---------------------------------------------------------------------------

class TestAPIPipelineTransform:

    def _raw_df(self) -> pd.DataFrame:
        """Build a raw DataFrame that mimics what extract() returns."""
        return pd.DataFrame([
            {
                "id": 3001, "firstName": "Ahmed", "lastName": "Al-Sanaani",
                "age": 22, "address": {"city": "Sanaa"},
            },
            {
                "id": 3002, "firstName": "Sara", "lastName": "Al-Dhamari",
                "age": 21, "address": {"city": "Dhamar"},
            },
        ])

    def test_transform_maps_id_to_student_id(self, api_pipeline: APIPipeline) -> None:
        result = api_pipeline.transform(self._raw_df())
        assert "student_id" in result.columns
        assert result["student_id"].tolist() == [3001, 3002]
        assert "id" not in result.columns

    def test_transform_combines_first_and_last_name(self, api_pipeline: APIPipeline) -> None:
        result = api_pipeline.transform(self._raw_df())
        assert result["name"].tolist() == ["Ahmed Al-Sanaani", "Sara Al-Dhamari"]

    def test_transform_extracts_city_from_nested_address(self, api_pipeline: APIPipeline) -> None:
        result = api_pipeline.transform(self._raw_df())
        assert result["city"].tolist() == ["Sanaa", "Dhamar"]

    def test_transform_sets_gpa_and_attendance_to_na(self, api_pipeline: APIPipeline) -> None:
        """DummyJSON does not provide academic fields — they must be NA."""
        result = api_pipeline.transform(self._raw_df())
        assert result["gpa"].isna().all()
        assert result["attendance"].isna().all()

    def test_transform_preserves_standard_column_order(self, api_pipeline: APIPipeline) -> None:
        result = api_pipeline.transform(self._raw_df())
        assert list(result.columns) == api_pipeline.STANDARD_COLUMNS

    def test_transform_handles_missing_address(self, api_pipeline: APIPipeline) -> None:
        """If address is missing, city should be None (not crash)."""
        raw = pd.DataFrame([
            {"id": 3001, "firstName": "X", "lastName": "Y", "age": 22, "address": None},
        ])
        result = api_pipeline.transform(raw)
        assert pd.isna(result["city"].iloc[0])


# ---------------------------------------------------------------------------
# APIPipeline — Validate
# ---------------------------------------------------------------------------

class TestAPIPipelineValidate:

    def test_validate_accepts_well_formed_data(self, api_pipeline: APIPipeline) -> None:
        df = pd.DataFrame({
            "student_id": [3001, 3002],
            "name": ["Ahmed A", "Sara B"],
            "age": [22, 21],
            "gpa": [pd.NA, pd.NA],
            "attendance": [pd.NA, pd.NA],
            "city": ["Sanaa", "Dhamar"],
        })
        # Should not raise
        api_pipeline.validate(df)

    def test_validate_rejects_empty_dataframe(self, api_pipeline: APIPipeline) -> None:
        empty = pd.DataFrame(columns=api_pipeline.STANDARD_COLUMNS)
        with pytest.raises(ValueError, match="empty"):
            api_pipeline.validate(empty)

    def test_validate_rejects_duplicate_student_id(self, api_pipeline: APIPipeline) -> None:
        df = pd.DataFrame({
            "student_id": [3001, 3001],
            "name": ["A", "B"],
            "age": [22, 22],
            "gpa": [pd.NA, pd.NA],
            "attendance": [pd.NA, pd.NA],
            "city": ["Sanaa", "Sanaa"],
        })
        with pytest.raises(ValueError, match="unique"):
            api_pipeline.validate(df)

    def test_validate_rejects_null_student_id(self, api_pipeline: APIPipeline) -> None:
        df = pd.DataFrame({
            "student_id": [pd.NA, 3002],
            "name": ["A", "B"],
            "age": [22, 22],
            "gpa": [pd.NA, pd.NA],
            "attendance": [pd.NA, pd.NA],
            "city": ["Sanaa", "Dhamar"],
        })
        with pytest.raises(ValueError, match="student_id"):
            api_pipeline.validate(df)

    def test_validate_rejects_out_of_range_age(self, api_pipeline: APIPipeline) -> None:
        df = pd.DataFrame({
            "student_id": [3001, 3002],
            "name": ["A", "B"],
            "age": [150, 22],
            "gpa": [pd.NA, pd.NA],
            "attendance": [pd.NA, pd.NA],
            "city": ["Sanaa", "Dhamar"],
        })
        with pytest.raises(ValueError, match="Age"):
            api_pipeline.validate(df)

    def test_validate_rejects_null_city(self, api_pipeline: APIPipeline) -> None:
        df = pd.DataFrame({
            "student_id": [3001, 3002],
            "name": ["A", "B"],
            "age": [22, 22],
            "gpa": [pd.NA, pd.NA],
            "attendance": [pd.NA, pd.NA],
            "city": ["Sanaa", None],
        })
        with pytest.raises(ValueError, match="city"):
            api_pipeline.validate(df)


# ---------------------------------------------------------------------------
# End-to-End (offline)
# ---------------------------------------------------------------------------

class TestAPIPipelineEndToEnd:

    def test_full_pipeline_offline_produces_output(self, api_pipeline: APIPipeline) -> None:
        """Simulate network failure → cache fallback → full pipeline run."""
        with patch("pipelines.api_pipeline.requests.get") as mock_get, \
             patch("pipelines.api_pipeline.time.sleep"):
            mock_get.side_effect = requests.ConnectionError("offline")

            result = api_pipeline.run()

        # PipelineResult contract (matches v3.0.0 pipelines)
        assert result.source == "api"
        assert result.rows_in == 10
        assert result.rows_out == 10
        assert result.duration >= 0
        assert Path(result.output_path).exists()
        assert result.errors == []