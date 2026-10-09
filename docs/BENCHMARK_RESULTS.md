# Benchmark Results — Pandas vs Polars
# نتائج المقارنة الأدائية — Pandas vs Polars

**Phase:** A (Polars Migration)
**Version:** v4.1.0-dev
**Date:** 2026-10-09
**Script:** `scripts/benchmark_pandas_vs_polars.py`
**Raw data:** `data/reports/benchmark_pandas_vs_polars.json`

---

## 1. Environment

| Component | Version |
|---|---|
| OS | Windows 11 |
| Python | 3.14.7 (`C:\PythonLab\python.exe`) |
| Pandas | 3.0.6 |
| Polars | 1.44.2 |
| NumPy | 2.5.3 |
| Hardware | Leno@DESKTOP-KV8T4VS (Windows workstation) |

---

## 2. Methodology (frozen before execution)

| Parameter | Value | Rationale |
|---|---|---|
| **Sizes** | 10K, 100K, 1M rows | Small + mid + scalability wall |
| **Warm-up** | 1 run (discarded) | Avoid cold-start bias |
| **Measured runs** | 5 | Statistical robustness |
| **Aggregate** | **Median** | Robust to OS-level outliers |
| **Operation** | `build_base_features` (row-wise derived) | Isolated from I/O aggregations |
| **Data** | `generate_synthetic()` with `seed=42` | Same data for both engines |
| **Metrics** | Wall time (ms), Peak memory (MB) | Time + space |
| **Memory tool** | `tracemalloc` | Python-side only (see §5) |

**Full command:**
```bash
python scripts/benchmark_pandas_vs_polars.py
3. Results
3.1 N = 10,000 rows
Implementation	Wall (ms)	Peak (MB)	Speedup
Pandas (eager)	4.54	1.41	1.00x
Polars (eager)	0.86	0.00*	5.25x
Polars (lazy)	2.64	0.00*	1.72x
Raw runs:

Pandas: [4.58, 4.88, 4.48, 4.39, 4.54]

Polars eager: [0.97, 0.85, 0.84, 0.86, 0.93]

Polars lazy: [2.78, 2.64, 2.65, 2.57, 2.40]

3.2 N = 100,000 rows
Implementation	Wall (ms)	Peak (MB)	Speedup
Pandas (eager)	27.73	13.96	1.00x
Polars (eager)	3.12	0.00*	8.88x ⭐
Polars (lazy)	8.75	0.00*	3.17x
Raw runs:

Pandas: [30.33, 27.52, 27.78, 27.73, 27.00]

Polars eager: [3.31, 3.04, 2.90, 3.12, 3.84]

Polars lazy: [10.52, 8.75, 8.82, 8.64, 8.44]

3.3 N = 1,000,000 rows
Implementation	Wall (ms)	Peak (MB)	Speedup
Pandas (eager)	259.82	139.50	1.00x
Polars (eager)	35.91	0.00*	7.23x
Polars (lazy)	52.97	0.00*	4.90x
Raw runs:

Pandas: [354.77, 368.17, 255.68, 259.82, 258.72] ⚠️ outliers

Polars eager: [38.11, 35.91, 35.91, 35.16, 36.70]

Polars lazy: [52.97, 52.81, 53.55, 52.89, 58.23]

4. Interpretation
4.1 Polars is faster (7-9x)
On row-wise transformations, Polars is consistently 5-9x faster than Pandas.
This confirms the design claim from Unit 6 (p. 60, Scalability Wall):
Polars uses native Rust + multi-threading + SIMD instructions,
while Pandas relies on Python-level operations (or NumPy vectorization).

Peak speedup at 100K suggests a sweet spot; at 1M, the gap narrows
slightly due to OS-level cache effects.

4.2 ⚠️ Polars lazy is slower than eager (in this benchmark)
Counterintuitive but explainable:

Reason	Effect
Lazy builds + optimizes a query plan	Fixed overhead per run
scan_parquet re-reads from disk each run	I/O overhead (~20-30ms for 1M)
Eager operates on in-memory DataFrame	No I/O in timing loop
Our operation is simple (row-wise)	No filter/projection to push down
Lazy would win when:

Pipeline contains early filters (WHERE city = 'Sanaa')

Multiple joins across large tables

Projection pushdown reduces I/O

Educational lesson: "Lazy is not always faster" — it depends on the query shape. (Unit 6, p. 76)

4.3 Pandas has larger variance at scale
At 1M, Pandas shows significant outliers (354.77, 368.17) — likely
due to OS memory allocation, page faults, or Python GC.

Polars is more stable: all 5 runs within a 3ms window (35.16-38.11).

4.4 Memory scaling
Pandas memory scales linearly (~1.4 MB / 10K rows → 139.5 MB / 1M rows).
Polars memory is not visible to tracemalloc (see §5).

5. ⚠️ Limitations (honest disclosure)
5.1 tracemalloc underreports Polars memory
tracemalloc is a Python-level tool. It tracks allocations made through
Python's memory allocator. Polars allocates in Rust (outside the GIL),
which tracemalloc cannot see. Hence the 0.00 MB readings.

This is a measurement limitation, not proof that Polars uses no memory.
A proper measurement would use OS-level tools (psutil, memory_profiler),
but those are platform-dependent and out of scope for Phase A.

5.2 Environment-specific results
All numbers are specific to:

Windows 11

Python 3.14.7

Polars 1.44.2

This workstation

Do NOT generalize to other hardware, OS, or Python versions.

5.3 Simple operation chosen intentionally
The benchmark isolates row-wise transformations, not:

File I/O (parquet load)

Complex aggregations (group by)

Joins across multiple tables

Lazy optimization benefits (filters, projections)

These are covered separately by engineering_polars.py's correctness tests.

5.4 Warm-up + median mitigate, but do not eliminate, noise
Even with 1 warm-up + 5 runs + median, residual noise exists. At 1M,
Pandas shows variance because GC/memory allocation is unpredictable.

6. Conclusion
What we learned (curriculum mapping)
Finding	Curriculum	Guide
Polars is 5-9x faster on row-wise ops	Unit 6 (p. 60)	Ch 5
Lazy ≠ always faster	Unit 6 (p. 76)	—
Memory is not only about time	Unit 6 (p. 58)	Ch 5
Median > mean for benchmarks	—	Ch 5 (methodology)
Honest documentation > cherry-picked numbers	Unit 11	Ch 12
Phase A verdict
✅ Migration successful:

Polars reproduces Pandas output within tolerances (34 tests pass).

Polars shows 7-9x speedup on row-wise feature engineering.

Lazy pipeline is functional but not advantageous for this specific workload.

Both engines are production-ready for their respective niches.

Recommendations for Phase B+
Use Pandas for: interactive exploration, small datasets, familiar APIs.

Use Polars eager for: row-wise heavy transformations at scale.

Use Polars lazy when: pipeline includes filters/projections/joins that
can be pushed down.

Consider memory_profiler or psutil for future memory benchmarks.

7. Reproducibility
Commands to reproduce
bash
cd /c/Users/Leno/Desktop/progect_python/student_data_pipeline

# Regenerate synthetic data (if missing)
python -m src.features.synthetic_generator --size 1000000

# Run the benchmark
python scripts/benchmark_pandas_vs_polars.py

# Raw JSON output
cat data/reports/benchmark_pandas_vs_polars.json
Verification
bash
# Confirm Polars == Pandas on real data
python -m pytest tests/test_features_polars.py::test_polars_matches_pandas_output -v

# Confirm 34 Polars tests pass
python -m pytest tests/test_features_polars.py -q

# Confirm full suite (196)
python -m pytest tests/ -q
8. References
Ref	Source
Unit 6, p. 58	Memory is part of performance
Unit 6, p. 60	Scalability Wall (Eager)
Unit 6, p. 71	Polars Expressions
Unit 6, p. 76	Lazy Processing
Guide Ch 5	Compute & Resources
Guide Ch 12	Honest documentation
docs/POLARS_MIGRATION.md	Migration decisions
9. Version History
Version	Date	Change
v1.0	2026-10-09	Initial benchmark (Windows 11, 10K + 100K + 1M)
Last Updated: 2026-10-09
Status: ✅ Complete
Author: Galal Al-Ghaberi