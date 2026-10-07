"""
Warehouse Layer — OLAP + Parquet
=================================

This package implements the OLAP (Online Analytical Processing) layer
of the pipeline. It converts cleaned (silver) data from OLTP sources
into Star Schema fact + dimension tables stored as Parquet files.

Design principles (Ch 4 + Ch 7 of the Data Engineering Guide):
    - Column-based storage (Parquet) for analytical queries
    - Star Schema (Fact + Dimensions) for dimensional modeling
    - Explicit grain documentation for every table
    - Denormalization as a deliberate analytical trade-off

Layers:
    Bronze (Raw)    → data/raw/, data/bronze/
    Silver (Clean)  → data/processed/
    Gold (OLAP)     → data/gold/*.parquet   ← this package
"""

__version__ = "4.0.0-dev"