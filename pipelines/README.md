# Pipeline Architecture — Multi-Source Data Processing

**Project:** Student Data Engineering Pipeline  
**Version:** 3.0.0  
**Date:** 2026-10-05  
**Units Covered:** 5, 6, 7, 8

---

## 📋 Table of Contents

1. [Overview](#1-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Directory Structure](#3-directory-structure)
4. [BasePipeline Contract](#4-basepipeline-contract)
5. [Pipeline Lifecycle](#5-pipeline-lifecycle)
6. [Source-Specific Details](#6-source-specific-details)
7. [Transformations](#7-transformations)
8. [Comparison Report](#8-comparison-report)
9. [Interpretation of Results](#9-interpretation-of-results)
10. [Running the Pipelines](#10-running-the-pipelines)
11. [Adding a New Source](#11-adding-a-new-source)
12. [Engineering Principles](#12-engineering-principles)
13. [Performance Metrics](#13-performance-metrics)
14. [Known Limitations](#14-known-limitations)
15. [MongoDB Integration](#15-mongodb-integration)
16. [Related Documents](#16-related-documents)
17. [References](#17-references)

---

## 1. Overview

This project implements **4 independent source pipelines** that process data from different origins, then compare their outputs. Each pipeline follows the same interface, making the architecture:

- **Modular** — each source is self-contained
- **Testable** — pipelines can be tested independently
- **Comparable** — same interface enables cross-source analysis
- **Extensible** — adding a new source = one new file

### Sources Covered

| # | Source | Type | Records | Location |
|---|--------|------|---------|----------|
| 1 | CSV | Flat file | 8 | `data/raw/students_raw.csv` |
| 2 | SQLite | Relational DB | 8 | `data/raw/university.db` |
| 3 | PostgreSQL | Relational DB | 8 | `university_training` (localhost:5432) |
| 4 | MongoDB | Document DB | 10 | `University_Ai.students` (localhost:27017) |

---

## 2. Architecture Diagram
