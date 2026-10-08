"""Feature Engineering Layer — Phase A (v4.0.0-dev).

Uses PEP 562 lazy imports to avoid double-import when running
`python -m src.features.engineering`.
"""

from __future__ import annotations

__all__ = ["FeatureEngineer"]
__version__ = "4.0.0-dev"


def __getattr__(name: str):
    """PEP 562: lazy attribute access."""
    if name == "FeatureEngineer":
        from src.features.engineering import FeatureEngineer
        return FeatureEngineer
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )
