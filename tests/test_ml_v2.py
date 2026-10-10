"""ML v2 tests — Phase B.7 (Scale-Up).

Covers data_v2.py (B.7.2). Subsequent sections (split_v2, trainer_v2,
pipeline_v2) will add tests in later sub-steps.

Reference: docs/ML_EXPERIMENTS_SCALE.md §3, §4, §9
"""

from __future__ import annotations

import pytest

from src.ml import data_v2


# ═══════════════════════════════════════════════════════════════
# Test 1 — UCI-only row count
# ═══════════════════════════════════════════════════════════════

def test_load_uci_only_returns_1044():
    """Silver dataset filter must yield exactly 1,044 UCI rows."""
    df = data_v2.load_uci_only()
    assert len(df) == 1044
    assert set(df["source"].unique()) == {"uci"}


# ═══════════════════════════════════════════════════════════════
# Test 2 — no NaN target in UCI rows
# ═══════════════════════════════════════════════════════════════

def test_load_uci_only_no_nan_gpa():
    """UCI rows must have complete gpa (unlike api/postgres/sqlite)."""
    df = data_v2.load_uci_only()
    assert df["gpa"].notna().all()
    assert df["gpa"].between(0.0, 4.0).all()
    assert df["student_id"].notna().all()


# ═══════════════════════════════════════════════════════════════
# Test 3 — leaky columns never appear in any FS
# ═══════════════════════════════════════════════════════════════

@pytest.mark.parametrize("fs", ["A", "B"])
def test_no_leaky_features_in_fs(fs):
    """score_final and score_change must be absent from FS-A and FS-B."""
    df = data_v2.load_uci_only()
    X, _, _ = data_v2.build_feature_matrix_v2(df, fs=fs)
    forbidden = set(data_v2.EXCLUDED_LEAKY)
    assert forbidden.isdisjoint(set(X.columns)), (
        f"Leaky columns leaked into FS-{fs}: "
        f"{sorted(forbidden & set(X.columns))}"
    )


# ═══════════════════════════════════════════════════════════════
# Test 4 — feature-set shapes (5 vs 7 columns)
# ═══════════════════════════════════════════════════════════════

def test_fs_a_has_5_features():
    """FS-A = 2 numeric + 3 categorical."""
    df = data_v2.load_uci_only()
    X, y, groups = data_v2.build_feature_matrix_v2(df, fs="A")
    assert X.shape == (1044, 5)
    assert y.shape == (1044,)
    assert groups.shape == (1044,)
    assert list(X.columns) == [
        "attendance_rate", "age", "gender", "city", "course",
    ]


def test_fs_b_has_7_features():
    """FS-B = FS-A + score_1 + score_2."""
    df = data_v2.load_uci_only()
    X, _, _ = data_v2.build_feature_matrix_v2(df, fs="B")
    assert X.shape == (1044, 7)
    assert list(X.columns) == [
        "attendance_rate", "age", "score_1", "score_2",
        "gender", "city", "course",
    ]


# ═══════════════════════════════════════════════════════════════
# Test 5 — groups column has 662 unique students
# ═══════════════════════════════════════════════════════════════

def test_groups_has_662_unique_students():
    """student_id must have exactly 662 unique values (GroupKFold groups)."""
    df = data_v2.load_uci_only()
    _, _, groups = data_v2.build_feature_matrix_v2(df, fs="A")
    assert groups.nunique() == 662
    # Every student has at least one record
    assert groups.value_counts().min() >= 1
    # 369 multi-record students (from UCI_ETL.md §3.4)
    n_multi = int((groups.value_counts() >= 2).sum())
    assert n_multi == 369