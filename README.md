# APEX-JEV

Research-driven adaptive trading intelligence platform for XAUUSD.

**Current maturity level: 0 — Data Foundation.** Nothing here trades, predicts, or claims an edge. The
repository currently provides trustworthy, reproducible market data and the tests that prove it.

Every component is a hypothesis until empirical evidence demonstrates that it is useful.

## What exists

- `src/apex_jev/data/` — MT5 CSV ingestion, strict schema, normalisation with audit log, integrity checks,
  gap classification, coverage tiers, cross-timeframe consistency, Parquet + hashed manifests, deterministic
  reload, point-in-time (lookahead) harness, Markdown/JSON quality report, CLI.
- `data/raw/` — the three XAUUSD exports (H1 2009-2026, M30 2018-2026, M15 2022-2026).
- `reports/data_quality/xauusd_level0.{md,json}` — the quality report generated from those exports.
- `docs/` — architecture audit, master implementation plan, data specification, failure modes, ADRs.
- `tests/` — pytest + hypothesis suite with synthetic MT5 fixtures.

## Quick start

```bash
python -m pip install -e ".[dev]"
pytest                                   # 34 tests
ruff check . && ruff format --check .

apex-data ingest --raw data/raw --processed data/processed --reports reports/data_quality --stem xauusd_level0
apex-data verify --processed data/processed
```

`ingest` writes `data/processed/<SYMBOL>_<TF>/{candles.parquet,manifest.json}` and the reports.
`verify` reloads each Parquet file and recomputes its content hash.

Loading data in code:

```python
from apex_jev.data.store import load_dataset

h1, manifest = load_dataset("data/processed", "XAUUSD_H1")  # verifies the content hash
```

## Read before using the data

- `docs/DATA_SPEC.md` — schema, time semantics (naive broker time; offset unverified), coverage tiers, and the
  findings on the real exports (zero-spread periods, unusable `volume`, partial final bar, export row cap).
- `docs/FAILURE_MODES.md` — what can go wrong and what the system does about it.
- `docs/MASTER_IMPLEMENTATION_PLAN.md` — NOW / NEXT / LATER / DEFERRED / REJECTED and the Level 0 checklist.

## Non-goals at this level

No indicators, strategies, backtests, Jev/LLM calls, ML, RL, regime models, adaptation, broker connectivity,
or live trading. See the plan for the level at which each is considered.
