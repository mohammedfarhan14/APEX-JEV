# APEX-JEV Architecture Audit

Date: 2026-09-23
Auditor: Devin (acting as principal engineer for APEX-JEV)
Scope: the APEX-JEV project folder as supplied, the `jev-trader` repository, and the three XAUUSD CSV exports.

Statement classification used throughout: **FACT** (verified by inspection), **INFERENCE** (derived from facts),
**ASSUMPTION** (unverified, must be confirmed), **UNVERIFIED** (could not be inspected).

---

## 1. Current repository structure

**FACT.** At the time of the audit no APEX-JEV source repository existed on GitHub or on the audit machine. The
project folder `C:\Users\Mohammed Farhan\Desktop\APEX-JEV` referenced by the owner was not transferable to the
audit environment; the owner confirmed it contains the three CSV exports and the engineering prompt.

**INFERENCE.** APEX-JEV starts from an empty codebase. There is no existing architecture to preserve, no
documentation/code contradictions to resolve, and no technical debt other than what this session introduces.

The repository created by this audit:

```
APEX-JEV/
  pyproject.toml            Python package `apex_jev` (pandas, numpy, pyarrow, pyyaml)
  src/apex_jev/data/        Level 0 data foundation (the only implemented layer)
  tests/                    pytest + hypothesis suite with synthetic MT5 fixtures
  docs/                     this audit, the implementation plan, DATA_SPEC, FAILURE_MODES, ADRs
  data/raw/                 place MT5 CSV exports here (git-ignored)
  data/processed/           canonical Parquet + manifest per dataset (git-ignored)
  reports/data_quality/     generated quality reports (committed once produced on real data)
```

## 2. Existing components

**FACT.** None pre-existed. Components delivered by this audit session are listed in section 15.

## 3. Existing dependencies

**FACT.** None pre-existed. Chosen for Level 0 (see ADR-0001): Python 3.10+, pandas, numpy, pyarrow, pyyaml;
dev: pytest, hypothesis, ruff, duckdb (ad-hoc analytics only). No database, no message bus, no ML libraries.

## 4. Existing data flow

**FACT.** The only data flow is the one implemented here:

```
data/raw/*.csv (MT5 export)
   -> io_csv.load_mt5_csv        strict header check, typed columns, source line numbers
   -> normalize.to_canonical     drop unparseable/NaN rows (counted), dedupe (logged), sort
   -> checks.run_all_checks      integrity, grid, gaps, spread, sessions, jumps (PASS/WARN/FAIL/INFO)
   -> store.write_dataset        Parquet (zstd) + manifest.json (hashes, versions, normalization log)
   -> store.load_dataset         reload + content-hash verification (proves determinism)
   -> coverage / cross_tf        H1-only / H1+M30 / H1+M30+M15 tiers, lower->higher TF aggregation check
   -> report.write_reports       JSON (source of truth) + Markdown view
```

## 5. Existing Jev integration

**FACT (from `jev-trader`).** `jev-trader` integrates Jev through `@ai-sdk/typesafe-ai` +
`experimental_evaluate` (`src/model.ts`). Jev is asked one versioned-in-code question ("direction": will the
mid be higher or lower after N blocks) over a compact typed `TradeState`; the answer is a choice with
probabilities. A deterministic `MockModel` stand-in implements the same `Model` interface.

**FACT.** APEX-JEV has no Jev integration. Per the maturity model, Jev is Level 3 and is not implemented.

**INFERENCE (transferable ideas).** The `Model` interface with a deterministic stand-in, the structured
state -> typed decision -> probabilities shape, and the "one question, versioned" pattern map directly onto the
APEX Jev design (Sections 22-24 of the prompt). These are recorded in MASTER_IMPLEMENTATION_PLAN.md as Level 3
inputs, not implemented now.

## 6. Existing tests

**FACT.** `jev-trader` contains no automated tests (`bun test` has nothing to run); its `scripts/` are manual
probes/benchmarks. APEX-JEV starts with 34 tests: loader, normalisation policy, every check, gap classification,
pipeline end-to-end, deterministic reload/hash, tamper detection, CLI, coverage tiers, cross-TF aggregation,
property-based OHLC invariants, and point-in-time (lookahead) harness tests.

## 7. Existing security boundaries

**FACT.** APEX-JEV Level 0 has no secrets, no network access, no broker adapters, and executes no generated
code. `.gitignore` excludes `.env*`, raw data, and processed data. `jev-trader` reads `PRIVATE_KEY` from env
and dry-runs when absent; nothing from it is imported here.

## 8. Existing technical debt

**FACT.** None inherited. Debt introduced knowingly this session:
- Timezone is an unverified assumption (see DATA_SPEC.md). Resolving it needs broker information.
- `spread` is kept in MT5 points; point size is unknown until the broker symbol spec is obtained.
- Gap classification thresholds (24h daily-break, 3-day extended) are descriptive heuristics, documented,
  not validated against the broker's session calendar.

## 9. Contradictions between documentation and code

**FACT.** No pre-existing documentation. The engineering prompt states the CSVs have fields
`DATE TIME OPEN HIGH LOW CLOSE TICKVOL VOL SPREAD`; the loader enforces exactly this header (with the MT5
`<...>` brackets stripped) and refuses anything else, so a mismatch becomes a visible DATA ISSUE rather than a
silent reinterpretation. **UNVERIFIED** against the real files until they are ingested.

## 10. Missing components (relative to the long-term vision)

Everything above Level 0: feature pipeline, experiment registry, backtester, strategies, Jev, evidence
store, regimes, ML, memory, allocation, drift, governance, dashboard, broker abstraction. All intentionally
absent; see MASTER_IMPLEMENTATION_PLAN.md for the level each belongs to.

## 11. Risks

| # | Risk | Class | Confidence | Mitigation |
|---|---|---|---|---|
| R1 | Broker server time offset unknown; DST behaviour unknown | DATA ISSUE / RESEARCH RISK | high that it is unknown | Documented as ASSUMPTION; session/hour distribution in the report gives evidence to infer it; do not convert to UTC until confirmed |
| R2 | M15/M30/H1 exports come from the same broker feed but may be internally inconsistent | DATA ISSUE | medium | Cross-TF consistency check reports mismatches; nothing is repaired |
| R3 | Filename-declared ranges may not match content | DATA ISSUE | low | Manifest records both; report shows actual first/last |
| R4 | Real VOL is likely all zeros for CFD gold | DATA ISSUE | high | Reported; TICKVOL used as activity proxy |
| R5 | Owner may be tempted to skip to Jev/ML | RESEARCH RISK | medium | Maturity gates in the plan; Level 0 acceptance checklist |
| R6 | Only one data vendor/broker; no independent cross-check | RESEARCH RISK | high | Flagged for Level 0.5 follow-up: obtain a second source or the broker symbol specification |

## 12. Duplicate functionality

**FACT.** None.

## 13. Architectural strengths (of the delivered foundation)

- Single-process, dependency-light, deterministic; every artifact hashed and versioned.
- Anomalies are counted and exemplified with source line numbers; nothing is silently repaired.
- The `assert_causal` harness gives every future feature a mandatory leakage test.
- Coverage tiers make the multi-timeframe history explicit and impossible to fabricate accidentally.

## 14. Architectural weaknesses

- pandas in-memory processing: fine for ~10^5-10^6 candles (the XAUUSD files), not for tick data.
- Markdown report is a rendering of JSON; there is no query interface yet (DuckDB over Parquet is available
  ad hoc and is the intended Level 1 path).
- No schema-evolution tooling beyond `SCHEMA_VERSION` and the hash check.

## 15. Recommended preservation

Everything in `src/apex_jev/data/` as the Level 0 contract; `tests/` as the regression floor; the
timezone assumption and normalisation policy exactly as documented until evidence changes them.

## 16. Recommended changes (immediate)

1. Ingest the real CSVs and commit `reports/data_quality/` so the audit is grounded in FACTs, not fixtures.
2. Obtain the broker/symbol specification (server timezone, point size, contract size, sessions) and
   turn ASSUMPTIONs in DATA_SPEC.md into FACTs or explicit corrections.
3. Add CI (ruff + pytest) on every push.

## 17. Items that should be deferred

PostgreSQL (nothing needs a database until the experiment registry exists), DuckDB as a hard dependency,
any indicator/feature library, any backtester, Jev, LLM agents, regime models, ML, RL, allocation, drift,
strategy evolution, dashboard, broker adapters, Docker. Each is mapped to a level in the plan.

---

### Maturity assignment

**CURRENT MATURITY LEVEL = 0 (Data Foundation), in progress.** The pipeline and tests exist; the acceptance
checklist in `docs/MASTER_IMPLEMENTATION_PLAN.md` is not complete until the real datasets have been ingested
and their report reviewed.
