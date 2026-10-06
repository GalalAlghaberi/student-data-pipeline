# Pipeline Comparison Report

**Generated:** 2026-10-05T19:35:14.497341+00:00

## Summary

| source   | status   |   rows |   columns | column_names                            |   missing_values |   unique_ids |
|:---------|:---------|-------:|----------:|:----------------------------------------|-----------------:|-------------:|
| csv      | OK       |      8 |         6 | student_id,name,age,gpa,attendance,city |                0 |            8 |
| sqlite   | OK       |      8 |         6 | student_id,name,age,gpa,attendance,city |               16 |            8 |
| postgres | OK       |      8 |         6 | student_id,name,age,gpa,attendance,city |               16 |            8 |
| mongodb  | OK       |     10 |         6 | student_id,name,age,gpa,attendance,city |                0 |           10 |
| json     | OK       |      3 |         6 | student_id,name,age,gpa,attendance,city |                0 |            3 |

## Observations

- **csv**: 8 rows, 6 cols, 0 missing
- **sqlite**: 8 rows, 6 cols, 16 missing
- **postgres**: 8 rows, 6 cols, 16 missing
- **mongodb**: 10 rows, 6 cols, 0 missing
- **json**: 3 rows, 6 cols, 0 missing