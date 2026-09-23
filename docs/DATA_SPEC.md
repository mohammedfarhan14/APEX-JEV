# APEX-JEV Data Specification (Level 0)

Schema version: **1.0.0** (`apex_jev.data.schema.SCHEMA_VERSION`). Any change to columns, dtypes or
semantics bumps this version and invalidates existing manifests.

Classification of statements: **FACT** (verified on the real exports on 2026-09-23), **INFERENCE**,
**ASSUMPTION**, **DATA ISSUE**.

---

## 1. Raw inputs

Three MetaTrader 5 "Export bars" files, tab separated, header `<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE>
<TICKVOL> <VOL> <SPREAD>`, dates `YYYY.MM.DD`, times `HH:MM:SS`. Stored in `data/raw/` and tracked in git
(≈6 MB each) so that the source SHA-256 in every manifest is reproducible from the repository alone.

| file | rows (FACT) | first bar | last bar | source sha256 (prefix) |
|---|---|---|---|---|
| `XAUUSD_H1_200905180100_202607280400.csv`  | 100,663 | 2009-05-18 01:00 | 2026-07-28 04:00 | `249f80058e6795e7` |
| `XAUUSD_M30_201801240100_202607280400.csv` | 100,156 | 2018-01-24 01:00 | 2026-07-28 04:00 | `fe9609f77eb2053c` |
| `XAUUSD_M15_202204200100_202607280415.csv` | 100,557 | 2022-04-20 01:00 | 2026-07-28 04:15 | `38694e0c0227ecaa` |

Full hashes are in `data/processed/<dataset>/manifest.json` and `reports/data_quality/xauusd_level0.json`.

**INFERENCE.** All three files contain ~100k rows and share the same end instant. Their different start dates
are therefore an artifact of an export row cap (MT5 "Max bars in chart"), not of data availability. Longer M30/M15
history can probably be exported; until then the coverage tiers below are the truth.

The loader (`io_csv.load_mt5_csv`) refuses any header other than the nine columns above (brackets stripped,
case-insensitive, BOM tolerated, tab/comma/semicolon sniffed). Every row keeps its 1-based `line_no` from the
source file for traceability of anomalies.

## 2. Canonical representation

Parquet (zstd) at `data/processed/<SYMBOL>_<TF>/candles.parquet` plus `manifest.json`.

| column | dtype | meaning |
|---|---|---|
| `ts` | `datetime64[ns]`, naive | candle **open** time in broker server time (see §3) |
| `open, high, low, close` | `float64` | prices in USD per troy ounce as exported |
| `tick_volume` | `int64` | number of price changes in the bar (MT5 TICKVOL) |
| `volume` | `int64` | MT5 VOL "real volume"; see §5 |
| `spread` | `int64` | MT5 SPREAD in points; see §5 |

Rows are sorted by `ts`, unique on `ts`. Invariants enforced at ingestion: `high >= max(open, close)`,
`min(open, close) >= low`, prices finite and > 0, `spread >= 0`, timestamps on the timeframe grid.

Normalisation policy (`normalize.to_canonical`), every action counted in the manifest's `normalization` block:
- rows with unparseable timestamps or NaN OHLC are dropped and counted (FACT: zero such rows in all three files);
- exact duplicate rows are dropped and counted (FACT: zero);
- conflicting duplicates (same `ts`, different values) keep the first row in file order, all conflicts are
  logged with line numbers (FACT: zero);
- gaps are never filled; nothing is interpolated; no values are clipped.

## 3. Time semantics

**ASSUMPTION (label `broker_server_time_naive`).** Timestamps are the broker's MT5 server time. The offset to
UTC is not encoded in the export. No conversion to UTC is performed at Level 0.

**INFERENCE from the data (report `hour_distribution`, gap analysis):**
- Trading weeks start Monday 01:00 (877/885 weekend gaps in H1 resume at Monday 01:00) and end Friday
  23:xx (last bar before weekend gaps is at 23:00 in 703/885 cases, 22:00 in 165).
- The daily break is 00:00-01:00 server time (3395/3537 daily gaps in H1 resume at 01:00); from 2020 onward
  a small number of 00:00 bars exist (101 in H1), i.e. the break sometimes falls at 23:00-00:00.
- This pattern matches a server clock at UTC+2 in winter and UTC+3 in summer (the common "EET following US DST"
  MT5 convention, where the 22:00 UTC daily maintenance window lands at 00:00-01:00 server time). Weeks in which
  EU and US DST rules diverge explain the sporadic 00:00 bars.

This inference must be confirmed with the broker before any UTC conversion, session labelling, or news
alignment is attempted. A wrong offset silently corrupts every session-based hypothesis.

## 4. Coverage and multi-timeframe tiers (FACT)

| tier | timeframes | start | end | span |
|---|---|---|---|---|
| `H1_only` | H1 | 2009-05-18 01:00 | 2026-07-28 04:00 | 6280 days |
| `H1_M30` | H1 + M30 | 2018-01-24 01:00 | 2026-07-28 04:00 | 3107 days |
| `H1_M30_M15` | H1 + M30 + M15 | 2022-04-20 01:00 | 2026-07-28 04:00 | 1560 days |

Research that needs M15 features may only use the `H1_M30_M15` tier; nothing is resampled backwards to
fabricate M15/M30 history where none exists.

Cross-timeframe consistency (`cross_tf.compare`, complete lower-TF buckets only):
- M30 -> H1: 50,053 buckets compared, **0 mismatches** in OHLC and tick volume.
- M15 -> H1: 25,107 buckets compared, **0 mismatches**.
- M15 -> M30: 50,261 buckets compared, **1 mismatch**, at the final bucket 2026-07-28 04:00 (M15 04:15 bar was
  still forming when exported). This is the export-time partial bar, not a feed inconsistency.

**DATA ISSUE.** The last bar of each file is the in-progress bar at export time and is incomplete. Consumers
must treat the final bar of every dataset as provisional (this is stated in the report notes).

## 5. Field-level findings on the real exports (FACT unless marked)

**Gaps.** No sub-grid steps, no off-grid timestamps, no duplicates in any file. All gaps are classified:
H1 has 3,537 daily-break, 874 weekend, 21 intraweek and 23 extended gaps. The extended gaps are long weekends
(Good Friday/Easter Monday, Christmas, New Year) and a few genuine holes (e.g. 2010-11-11 11:00 to 2010-11-15
01:00, with a 38.9 USD open-vs-close jump across it). Missing bars inside the week are listed in the JSON report.

**Spread.** Zero spreads: 100% of 2009 bars, 85% of 2010, 11% of 2011, then <1% until 2020; 16-28% again
in 2021-2022 and 11% of 2026 in all three files. Spread is therefore unusable as a cost input before 2011 and
suspect in 2021-2022 and 2026; a floor/replacement policy must be defined at Level 1 and recorded as an
assumption. Single-bar extremes (e.g. 496 points at 2014-01-20 21:00 H1, 281 at 2026-05-25 21:30 M15) coincide
with illiquid late-session hours.
**INFERENCE.** The per-year median spread is lower on higher timeframes (2024: H1 5, M30 9, M15 12), consistent
with MT5 storing the *minimum* spread observed within a bar. Confirm with the broker/MT5 documentation before
using spread as a typical cost.

**Volume.** `volume` is non-zero only for 2012-2018 in H1 and early 2018 in M30, and is always zero in M15.
It is not a consistent series and must not be used as a feature. `tick_volume` is never zero.

**Zero-range bars** (high == low): 24 in H1, 9 in M30, 17 in M15, all with tick_volume of 1-9 in illiquid hours
(21:00-23:00 or first bar after the daily break). Kept as-is; flagged.

**Price jumps.** All flagged open-vs-previous-close jumps (>12x median range) occur at Monday 01:00, i.e.
across weekend gaps (e.g. 2026-02-02: 4894.47 -> 4773.75). They are market gaps, not data errors, and are a
reminder that stop orders cannot be assumed to fill at their level across a gap.

**Weekend bars.** None (Saturday/Sunday count = 0 in all files).

## 6. Manifest and reproducibility

`manifest.json` records: dataset id, schema version, timezone label, source filename/size/SHA-256, the
filename-declared range, the actual first/last `ts`, row count, canonical content SHA-256 (hash of the canonical
columns in order, independent of index and extra columns), the normalisation log, creation time, and Python /
pandas / pyarrow / apex-jev versions. `apex-data verify` reloads each Parquet file and recomputes the content
hash; a mismatch is an error. The three content hashes for the current exports:

- `XAUUSD_H1`  `260e1387199ed44989c61a3c24e662899be2364f45734525e444fbfb8a83bb4a`
- `XAUUSD_M30` `7e700415c6481d3f1e2238f294b8f5541af4bbae0c2b71021e15cf0a1d55e94b`
- `XAUUSD_M15` `7c142feb798036b207b6780c57e73b95e98611e9e904cc8b0c24c76bd6cefbfa`

## 7. Point-in-time rule for everything built on this data

A bar with open time `ts` and timeframe `tf` is fully known only at `ts + tf`. Every derived feature must
declare its `available_at` and must pass `apex_jev.data.pit.assert_causal`, which recomputes the feature on
historical prefixes and fails if any past value changes when future rows are appended.
