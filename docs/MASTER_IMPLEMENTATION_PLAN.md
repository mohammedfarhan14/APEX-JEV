# APEX-JEV Master Implementation Plan

Principle: every component is a hypothesis until empirical evidence demonstrates it is useful. Nothing moves
to the next maturity level until the previous level's acceptance checklist is met on the real data.

Maturity levels (from the engineering charter):

| Level | Name | Gate to leave |
|---|---|---|
| 0 | Data Foundation | checklist below complete on the real XAUUSD exports |
| 1 | Research Foundation | experiment registry + deterministic backtester with reproducibility tests |
| 2 | Baseline Strategies | baselines evaluated honestly (costs, spreads, walk-forward), results recorded even if negative |
| 3 | Jev Integration | Jev as one hypothesis, no production authority, decision logging incl. rejected paths |
| 4 | Evidence Memory | executed + rejected + counterfactual decisions stored and queryable |
| 5 | Regime & Drift | regime hypotheses tested for stability; drift detection with false-alarm evaluation |
| 6 | Controlled Adaptation | reversible challenger promotion under deterministic governance |
| 7 | Governance & Production | fail-closed risk, kill switches, audit trail, shadow -> paper -> limited live |
| 8 | Evolutionary Research | candidate generation, meta-research, only if 0-7 have produced evidence |

---

## NOW (Level 0 — Data Foundation)

Delivered in this repository:

- [x] MT5 CSV loader with strict schema (`io_csv.py`)
- [x] Canonical schema v1.0.0, explicit timezone label, dtype contract (`schema.py`, DATA_SPEC.md)
- [x] Normalisation with an inspectable log: bad timestamps, NaN OHLC, exact/conflicting duplicates (`normalize.py`)
- [x] Integrity checks: order, duplicates, OHLC invariants, positivity, zero-range, spread, volume, grid
      alignment, gap classification, weekday/hour distribution, price jumps (`checks.py`)
- [x] Coverage tiers H1_only / H1_M30 / H1_M30_M15 (`coverage.py`)
- [x] Cross-timeframe aggregation consistency, complete buckets only, report-not-repair (`cross_tf.py`)
- [x] Parquet + manifest with source SHA-256, canonical content hash, versions (`store.py`, `hashing.py`)
- [x] Deterministic reload with hash verification; tamper detection
- [x] Point-in-time causality harness for future features (`pit.py`)
- [x] Markdown + JSON quality report (`report.py`), CLI `apex-data ingest|verify`
- [x] 34 tests incl. property-based and lookahead tests; ruff clean

Level 0 acceptance checklist (status against **real** data):

- [ ] all supplied CSVs load successfully — *pending: real files not yet ingested*
- [x] schemas are documented (DATA_SPEC.md)
- [x] timestamps are validated (parse, order, grid alignment, duplicates)
- [x] timezone semantics are explicitly documented (as an ASSUMPTION, see DATA_SPEC.md)
- [x] duplicates are detected (exact vs conflicting, first-in-file kept, all logged)
- [x] gaps are reported (classified weekend / daily_break / intraweek / extended)
- [x] OHLC integrity is tested (unit + property-based)
- [x] spread values are inspected (zero, negative, extreme; quantiles reported)
- [ ] M15/M30/H1 coverage is documented — *code produces it; real figures pending*
- [x] multi-timeframe intersection is explicit (tiers, never a fabricated unified history)
- [x] future leakage risks are tested (`assert_causal` + tests for shift/centered/full-sample normalisation)
- [x] canonical Parquet is produced
- [x] dataset hashes are recorded (source SHA-256 + canonical content SHA-256)
- [x] deterministic reload works (tested)
- [x] automated tests pass (synthetic fixtures)
- [ ] data quality report is generated — *on real data: pending*
- [ ] documentation matches actual implementation — *re-verify after real ingestion*

Remaining NOW work:
1. Ingest the three real CSVs; commit `reports/data_quality/*.md|json`; update DATA_SPEC.md coverage section.
2. Obtain broker symbol spec (server timezone/DST, point size, sessions). Convert ASSUMPTIONs to FACTs.
3. CI: ruff + pytest on push (added in `.github/workflows/ci.yml`).

## NEXT (Level 1 — Research Foundation)

- Experiment registry (file-based, JSON manifests, then SQLite/Postgres only when needed): code version,
  dataset content hashes, config hash, seed, environment.
- Feature pipeline where every feature declares `available_at = bar close time` and passes `assert_causal`.
- Deterministic event-driven backtester over canonical Parquet: conservative OHLC fill model
  (stop-before-target on same-candle ambiguity, spread-aware entry, configurable slippage), explicit
  session/gap handling, zero/one-trade edge cases, determinism test (same inputs -> identical trade log hash).
- Chronological splits, walk-forward harness, purged/embargoed CV as an option, never shuffled.
- Baseline "null" strategies (random with same trade count, buy-and-hold, always-flat) as the comparison floor.

## LATER (Levels 2-5)

- Level 2: session/breakout/mean-reversion/volatility baselines; robustness (parameter perturbation,
  bootstrap, cost sensitivity); results committed win or lose.
- Level 3: Jev adapter behind a `Model` interface with a deterministic mock (pattern from jev-trader),
  versioned prompts, structured outputs, deterministic risk gates that Jev cannot bypass, rejected-decision logging.
- Level 4: evidence/memory store for executed, rejected, blocked, missed, counterfactual decisions.
- Level 5: regime hypotheses with stability tests; drift detection with false-alarm measurement.

## DEFERRED

- Controlled adaptation, challenger promotion, governance plane, broker adapters, shadow/paper/live
  (Levels 6-7). Preconditions: an evidence base showing at least one baseline with out-of-sample robustness.
- Dashboard (TypeScript/Bun acceptable, per charter) — only once there is something worth observing.
- Docker / infra — a single Python package suffices for research reproducibility today.
- PostgreSQL — no relational workload exists yet.

## REJECTED (for now, with reasons)

- Porting jev-trader's 300 ms block loop to XAUUSD: different market structure, no on-chain book, no
  sub-second decision need. Only its interface patterns are reused.
- Reinforcement learning: no environment simulator exists, and RL without a validated backtester is prestige, not
  research.
- LLM code generation into the strategy library: violates the "no unvalidated generated code" prohibition until
  a sandbox + validation gate exists (Level 8).
- Filling gaps or repairing cross-TF mismatches: destroys the evidence needed to understand the feed.
- Converting timestamps to UTC now: offset unverified; a wrong conversion is worse than a labelled naive time.

---

### Feature -> maturity mapping (summary)

| Feature | Level |
|---|---|
| Canonical data, hashes, quality report | 0 |
| Feature store with `available_at`, causality tests | 1 |
| Backtester, experiment registry, walk-forward | 1 |
| Baseline strategies, robustness suite | 2 |
| Jev adapter, prompt versioning, decision log | 3 |
| Evidence memory, counterfactuals | 4 |
| Regime models, drift detection | 5 |
| Challenger/promotion, reversible adaptation | 6 |
| Governance, kill switches, broker abstraction, live | 7 |
| Candidate generation, meta-research | 8 |
