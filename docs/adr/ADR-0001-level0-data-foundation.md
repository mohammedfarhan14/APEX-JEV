# ADR-0001: Level 0 data foundation — language, storage and normalisation policy

Status: accepted (2026-09-23)

## Context

APEX-JEV starts from an empty codebase and three MT5 CSV exports of XAUUSD (H1, M30, M15) with different
history lengths. The charter forbids proceeding to research, Jev, or ML until the data is trustworthy and
reproducible. The related `jev-trader` project is a Bun/TypeScript on-chain bot whose architecture does not
transfer to daily-session CFD research.

## Decision

1. **Python** (3.10+) with pandas/numpy/pyarrow for all quantitative work. TypeScript/Bun is reserved for a
   future dashboard only.
2. **Parquet + JSON manifest per dataset** as the canonical store; no database. The manifest carries source
   SHA-256, canonical content SHA-256, schema version, normalisation log and library versions.
3. **Naive broker-server timestamps** labelled `broker_server_time_naive`; no UTC conversion until the broker
   offset is confirmed.
4. **Report, never repair**: gaps, spread anomalies, cross-timeframe mismatches and partial bars are recorded
   with counts and line numbers; only unparseable/NaN rows and duplicates are removed, and each removal is counted.
5. **Explicit coverage tiers** (`H1_only`, `H1_M30`, `H1_M30_M15`) instead of one resampled history.
6. **Causality harness** (`pit.assert_causal`) is mandatory for every future feature.
7. Raw CSVs are tracked in git so source hashes are reproducible from the repository alone.

## Consequences

- Reproducibility is verifiable with `apex-data verify` and `pytest`; no external services are needed.
- Session-based research is blocked until the timezone assumption is resolved — this is intentional.
- Zero-spread periods and inconsistent `volume` are documented limitations that Level 1 cost models must
  address explicitly rather than by imputation.
- Tick data, a second data vendor, and a query layer (DuckDB over Parquet) are deferred until a research need
  exists.

## Alternatives rejected

- Porting `jev-trader` (wrong market structure, no tests, no reproducibility layer).
- PostgreSQL/TimescaleDB now (no relational workload; adds operational surface with no evidence of need).
- Filling gaps / repairing feed inconsistencies (destroys evidence about the feed).
- Converting to UTC by guessing the offset (a wrong guess corrupts every session-based hypothesis).
