# APEX-JEV Level 0 data quality report

Generated: 2026-09-23T06:49:44+00:00

## Interpretation notes

- Timestamps are candle OPEN times in broker server time, kept naive (ASSUMPTION: offset unverified).
- A gap is classified, not judged: weekend/daily_break gaps are expected for XAUUSD CFD feeds; 'extended' gaps require manual review before being called defects.
- SPREAD is in MT5 points; the point size for this broker/instrument must be confirmed before converting to price units.
- VOL (real volume) is typically zero for CFD/spot metals; TICKVOL is the usable activity proxy.
- Cross-timeframe mismatches are reported, never repaired. Only complete lower-TF buckets are compared.
- The final bar of an MT5 export is the bar that was forming at export time and may be incomplete; consumers should treat the last bar of every dataset as provisional.
- FAIL means untrustworthy for research as-is; WARN means documented anomalies; PASS/INFO need no action.

## Coverage

| timeframe | start | end | rows |
|---|---|---|---|
| H1 | 2009-05-18 01:00:00 | 2026-07-28 04:00:00 | 100,663 |
| M15 | 2022-04-20 01:00:00 | 2026-07-28 04:15:00 | 100,557 |
| M30 | 2018-01-24 01:00:00 | 2026-07-28 04:00:00 | 100,156 |

### Multi-timeframe tiers

| tier | timeframes | start | end | span (days) | valid |
|---|---|---|---|---|---|
| H1_only | H1 | 2009-05-18 01:00:00 | 2026-07-28 04:00:00 | 6280.1 | True |
| H1_M30 | H1+M30 | 2018-01-24 01:00:00 | 2026-07-28 04:00:00 | 3107.1 | True |
| H1_M30_M15 | H1+M30+M15 | 2022-04-20 01:00:00 | 2026-07-28 04:00:00 | 1560.1 | True |

## Cross-timeframe consistency

### M15->M30  —  WARN

```json
{
  "pair": "M15->M30",
  "complete_buckets": 50261,
  "compared": 50261,
  "overlap_start": "2022-04-20 01:00:00",
  "overlap_end": "2026-07-28 04:00:00",
  "mismatch_counts": {
    "open": 0,
    "high": 0,
    "low": 1,
    "close": 1,
    "tick_volume": 1
  },
  "abs_diff_quantiles": {
    "open": {
      "p50": 0.0,
      "p99": 0.0,
      "max": 0.0
    },
    "high": {
      "p50": 0.0,
      "p99": 0.0,
      "max": 0.0
    },
    "low": {
      "p50": 0.0,
      "p99": 0.0,
      "max": 3.5900000000001455
    },
    "close": {
      "p50": 0.0,
      "p99": 0.0,
      "max": 4.430000000000291
    }
  },
  "tick_volume_abs_diff_p99": 0.0,
  "higher_candles_without_complete_lower_bucket": 35,
  "price_mismatch_fraction": 9.948071069019717e-06,
  "status": "WARN"
}
```

### M30->H1  —  PASS

```json
{
  "pair": "M30->H1",
  "complete_buckets": 50053,
  "compared": 50053,
  "overlap_start": "2018-01-24 01:00:00",
  "overlap_end": "2026-07-28 03:00:00",
  "mismatch_counts": {
    "open": 0,
    "high": 0,
    "low": 0,
    "close": 0,
    "tick_volume": 0
  },
  "abs_diff_quantiles": {
    "open": {
      "p50": 0.0,
      "p99": 0.0,
      "max": 0.0
    },
    "high": {
      "p50": 0.0,
      "p99": 0.0,
      "max": 0.0
    },
    "low": {
      "p50": 0.0,
      "p99": 0.0,
      "max": 0.0
    },
    "close": {
      "p50": 0.0,
      "p99": 0.0,
      "max": 0.0
    }
  },
  "tick_volume_abs_diff_p99": 0.0,
  "higher_candles_without_complete_lower_bucket": 50,
  "price_mismatch_fraction": 0.0,
  "status": "PASS"
}
```

### M15->H1  —  PASS

```json
{
  "pair": "M15->H1",
  "complete_buckets": 25107,
  "compared": 25107,
  "overlap_start": "2022-04-20 01:00:00",
  "overlap_end": "2026-07-28 03:00:00",
  "mismatch_counts": {
    "open": 0,
    "high": 0,
    "low": 0,
    "close": 0,
    "tick_volume": 0
  },
  "abs_diff_quantiles": {
    "open": {
      "p50": 0.0,
      "p99": 0.0,
      "max": 0.0
    },
    "high": {
      "p50": 0.0,
      "p99": 0.0,
      "max": 0.0
    },
    "low": {
      "p50": 0.0,
      "p99": 0.0,
      "max": 0.0
    },
    "close": {
      "p50": 0.0,
      "p99": 0.0,
      "max": 0.0
    }
  },
  "tick_volume_abs_diff_p99": 0.0,
  "higher_candles_without_complete_lower_bucket": 60,
  "price_mismatch_fraction": 0.0,
  "status": "PASS"
}
```

## XAUUSD_H1  —  overall: **WARN**

- source: `XAUUSD_H1_200905180100_202607280400.csv` (sha256 `249f80058e6795e7…`, 6,390,589 bytes)
- canonical rows: 100,663  (2009-05-18 01:00:00 → 2026-07-28 04:00:00)
- content sha256: `260e1387199ed44989c61a3c24e662899be2364f45734525e444fbfb8a83bb4a`
- schema version: 1.0.0; timezone: `broker_server_time_naive`
- normalization: {"rows_in": 100663, "rows_out": 100663, "dropped_unparseable_timestamp": 0, "dropped_nan_ohlc": 0, "exact_duplicates_removed": 0, "conflicting_duplicate_groups": 0, "conflicting_duplicate_rows_removed": 0, "reordered": false, "conflicting_examples": "(see JSON)"}

| check | status | summary |
|---|---|---|
| schema | PASS | all canonical columns present |
| row_count | INFO | 100663 rows from 2009-05-18 01:00:00 to 2026-07-28 04:00:00 |
| timestamp_order | PASS | timestamps strictly increasing and unique |
| duplicate_timestamps | PASS | no duplicate timestamps |
| grid_alignment | PASS | 0 timestamps not aligned to the H1 grid |
| frequency_and_gaps | WARN | exact_step=96207 sub_step=0 gaps=4455 kinds={'daily_break': 3537, 'weekend': 874, 'extended': 23, 'intraweek': 21} |
| ohlc_integrity | PASS | 0 candles violate high>=max(o,c)>=min(o,c)>=low |
| price_positivity | PASS | 0 candles with non-positive or non-finite prices |
| zero_range_candles | WARN | 24 candles with high == low (0.0238%) |
| spread | WARN | negative=0 zero=12967 extreme(>5x p99)=1 median=15.0 |
| volume | INFO | tick_volume zero=0 negative=0; volume all_zero=False |
| weekday_distribution | PASS | weekend bars=0 (Sat=0, Sun=0) |
| hour_distribution | INFO | bars observed in 24/24 hours of day; first hour=0 |
| price_jumps | WARN | 8 open-vs-previous-close jumps > 12.0x median candle range (3.240000000000009) |

<details><summary>frequency_and_gaps details</summary>

```json
{
  "expected_step_minutes": 60,
  "exact_step": 96207,
  "sub_step": 0,
  "gap_count": 4455,
  "gap_kinds": {
    "daily_break": 3537,
    "weekend": 874,
    "extended": 23,
    "intraweek": 21
  },
  "missing_bars_total": 50061,
  "missing_bars_non_weekend": 6675,
  "largest_gaps": [
    {
      "gap_start": "2010-11-11 11:00:00",
      "gap_end": "2010-11-15 01:00:00",
      "delta": "3 days 14:00:00",
      "missing_bars": 85,
      "kind": "extended"
    },
    {
      "gap_start": "2011-04-21 21:00:00",
      "gap_end": "2011-04-25 08:00:00",
      "delta": "3 days 11:00:00",
      "missing_bars": 82,
      "kind": "extended"
    },
    {
      "gap_start": "2017-12-22 23:00:00",
      "gap_end": "2017-12-26 09:00:00",
      "delta": "3 days 10:00:00",
      "missing_bars": 81,
      "kind": "weekend"
    },
    {
      "gap_start": "2017-12-29 23:00:00",
      "gap_end": "2018-01-02 09:00:00",
      "delta": "3 days 10:00:00",
      "missing_bars": 81,
      "kind": "weekend"
    },
    {
      "gap_start": "2010-12-10 22:00:00",
      "gap_end": "2010-12-14 06:00:00",
      "delta": "3 days 08:00:00",
      "missing_bars": 79,
      "kind": "weekend"
    },
    {
      "gap_start": "2015-12-31 18:00:00",
      "gap_end": "2016-01-04 01:00:00",
      "delta": "3 days 07:00:00",
      "missing_bars": 78,
      "kind": "extended"
    },
    {
      "gap_start": "2009-12-31 18:00:00",
      "gap_end": "2010-01-04 01:00:00",
      "delta": "3 days 07:00:00",
      "missin
... (truncated; see JSON report)
```

</details>

<details><summary>zero_range_candles details</summary>

```json
{
  "count": 24,
  "fraction": 0.0002384192801724566,
  "examples": [
    {
      "ts": "2009-11-26 21:00:00",
      "open": 1192.03,
      "high": 1192.03,
      "low": 1192.03,
      "close": 1192.03,
      "tick_volume": 1,
      "volume": 0,
      "spread": 0,
      "line_no": 3119
    },
    {
      "ts": "2009-11-26 22:00:00",
      "open": 1191.9,
      "high": 1191.9,
      "low": 1191.9,
      "close": 1191.9,
      "tick_volume": 1,
      "volume": 0,
      "spread": 0,
      "line_no": 3120
    },
    {
      "ts": "2009-11-26 23:00:00",
      "open": 1191.8,
      "high": 1191.8,
      "low": 1191.8,
      "close": 1191.8,
      "tick_volume": 1,
      "volume": 0,
      "spread": 0,
      "line_no": 3121
    },
    {
      "ts": "2010-01-18 21:00:00",
      "open": 1133.21,
      "high": 1133.21,
      "low": 1133.21,
      "close": 1133.21,
      "tick_volume": 1,
      "volume": 0,
      "spread": 0,
      "line_no": 3908
    },
    {
      "ts": "2010-02-15 20:00:00",
      "open": 1100.74,
      "high": 1100.74,
      "low": 1100.74,
      "close": 1100.74,
      "tick_volume": 1,
      "volume": 0,
      "spread": 0,
      "line_no": 4360
    }
  ]
}
```

</details>

<details><summary>spread details</summary>

```json
{
  "negative": 0,
  "zero": 12967,
  "extreme": 1,
  "quantiles": {
    "0.0": 0.0,
    "0.01": 0.0,
    "0.05": 0.0,
    "0.25": 5.0,
    "0.5": 15.0,
    "0.75": 30.0,
    "0.95": 51.0,
    "0.99": 70.0,
    "1.0": 496.0
  },
  "mean": 19.307342320415643,
  "units": "points as exported by MT5 (instrument point size must be confirmed with the broker)",
  "extreme_examples": [
    {
      "ts": "2014-01-20 21:00:00",
      "open": 1250.82,
      "high": 1250.84,
      "low": 1250.74,
      "close": 1250.81,
      "tick_volume": 16,
      "volume": 8000,
      "spread": 496,
      "line_no": 27029
    }
  ]
}
```

</details>

<details><summary>price_jumps details</summary>

```json
{
  "count": 8,
  "median_range": 3.240000000000009,
  "examples": [
    {
      "ts": "2010-11-15 01:00:00",
      "open": 1373.08,
      "close": 1373.1,
      "prev_close": 1412.0,
      "jump": 38.92000000000007
    },
    {
      "ts": "2026-02-02 01:00:00",
      "open": 4773.75,
      "close": 4741.7,
      "prev_close": 4894.47,
      "jump": 120.72000000000025
    },
    {
      "ts": "2026-03-02 01:00:00",
      "open": 5363.14,
      "close": 5387.07,
      "prev_close": 5278.77,
      "jump": 84.36999999999989
    },
    {
      "ts": "2026-03-09 01:00:00",
      "open": 5129.95,
      "close": 5076.1,
      "prev_close": 5171.92,
      "jump": 41.970000000000255
    },
    {
      "ts": "2026-04-20 01:00:00",
      "open": 4770.66,
      "close": 4779.37,
      "prev_close": 4854.44,
      "jump": 83.77999999999975
    },
    {
      "ts": "2026-04-22 01:00:00",
      "open": 4718.65,
      "close": 4719.62,
      "prev_close": 4679.43,
      "jump": 39.219999999999345
    },
    {
      "ts": "2026-06-15 01:00:00",
      "open": 4262.55,
      "close": 4285.67,
      "prev_close": 4210.73,
      "jump": 51.82000000000062
    },
    {
      "ts": "2026-07-02 01:00:00",
      "open": 3998.58,
      "close": 4045.07,
      "prev_close": 4038.77,
      "jump": 40.190000000000055
    }
  ]
}
```

</details>

## XAUUSD_M15  —  overall: **WARN**

- source: `XAUUSD_M15_202204200100_202607280415.csv` (sha256 `38694e0c0227ecaa…`, 6,130,184 bytes)
- canonical rows: 100,557  (2022-04-20 01:00:00 → 2026-07-28 04:15:00)
- content sha256: `7c142feb798036b207b6780c57e73b95e98611e9e904cc8b0c24c76bd6cefbfa`
- schema version: 1.0.0; timezone: `broker_server_time_naive`
- normalization: {"rows_in": 100557, "rows_out": 100557, "dropped_unparseable_timestamp": 0, "dropped_nan_ohlc": 0, "exact_duplicates_removed": 0, "conflicting_duplicate_groups": 0, "conflicting_duplicate_rows_removed": 0, "reordered": false, "conflicting_examples": "(see JSON)"}

| check | status | summary |
|---|---|---|
| schema | PASS | all canonical columns present |
| row_count | INFO | 100557 rows from 2022-04-20 01:00:00 to 2026-07-28 04:15:00 |
| timestamp_order | PASS | timestamps strictly increasing and unique |
| duplicate_timestamps | PASS | no duplicate timestamps |
| grid_alignment | PASS | 0 timestamps not aligned to the M15 grid |
| frequency_and_gaps | WARN | exact_step=99435 sub_step=0 gaps=1121 kinds={'daily_break': 894, 'weekend': 219, 'extended': 4, 'intraweek': 4} |
| ohlc_integrity | PASS | 0 candles violate high>=max(o,c)>=min(o,c)>=low |
| price_positivity | PASS | 0 candles with non-positive or non-finite prices |
| zero_range_candles | WARN | 17 candles with high == low (0.0169%) |
| spread | WARN | negative=0 zero=6575 extreme(>5x p99)=4 median=6.0 |
| volume | INFO | tick_volume zero=0 negative=0; volume all_zero=True |
| weekday_distribution | PASS | weekend bars=0 (Sat=0, Sun=0) |
| hour_distribution | INFO | bars observed in 24/24 hours of day; first hour=0 |
| price_jumps | WARN | 14 open-vs-previous-close jumps > 12.0x median candle range (2.6900000000000546) |

<details><summary>frequency_and_gaps details</summary>

```json
{
  "expected_step_minutes": 15,
  "exact_step": 99435,
  "sub_step": 0,
  "gap_count": 1121,
  "gap_kinds": {
    "daily_break": 894,
    "weekend": 219,
    "extended": 4,
    "intraweek": 4
  },
  "missing_bars_total": 49217,
  "missing_bars_non_weekend": 5760,
  "largest_gaps": [
    {
      "gap_start": "2024-03-28 22:45:00",
      "gap_end": "2024-04-01 01:00:00",
      "delta": "3 days 02:15:00",
      "missing_bars": 296,
      "kind": "extended"
    },
    {
      "gap_start": "2026-04-02 22:45:00",
      "gap_end": "2026-04-06 01:00:00",
      "delta": "3 days 02:15:00",
      "missing_bars": 296,
      "kind": "extended"
    },
    {
      "gap_start": "2023-12-29 23:45:00",
      "gap_end": "2024-01-02 01:00:00",
      "delta": "3 days 01:15:00",
      "missing_bars": 292,
      "kind": "weekend"
    },
    {
      "gap_start": "2023-12-22 23:45:00",
      "gap_end": "2023-12-26 01:00:00",
      "delta": "3 days 01:15:00",
      "missing_bars": 292,
      "kind": "weekend"
    },
    {
      "gap_start": "2025-04-17 23:45:00",
      "gap_end": "2025-04-21 01:00:00",
      "delta": "3 days 01:15:00",
      "missing_bars": 292,
      "kind": "extended"
    },
    {
      "gap_start": "2022-12-23 23:45:00",
      "gap_end": "2022-12-27 01:00:00",
      "delta": "3 days 01:15:00",
      "missing_bars": 292,
      "kind": "weekend"
    },
    {
      "gap_start": "2023-04-06 23:45:00",
      "gap_end": "2023-04-10 01:00:00",
      "delta": "3 days 01:15:00",
      "mis
... (truncated; see JSON report)
```

</details>

<details><summary>zero_range_candles details</summary>

```json
{
  "count": 17,
  "fraction": 0.00016905834501824835,
  "examples": [
    {
      "ts": "2024-07-04 21:30:00",
      "open": 2356.1,
      "high": 2356.1,
      "low": 2356.1,
      "close": 2356.1,
      "tick_volume": 1,
      "volume": 0,
      "spread": 138,
      "line_no": 52337
    },
    {
      "ts": "2025-11-27 21:30:00",
      "open": 4156.82,
      "high": 4156.82,
      "low": 4156.82,
      "close": 4156.82,
      "tick_volume": 9,
      "volume": 0,
      "spread": 132,
      "line_no": 85437
    },
    {
      "ts": "2025-11-27 21:45:00",
      "open": 4156.82,
      "high": 4156.82,
      "low": 4156.82,
      "close": 4156.82,
      "tick_volume": 8,
      "volume": 0,
      "spread": 192,
      "line_no": 85438
    },
    {
      "ts": "2025-12-15 01:00:00",
      "open": 4300.26,
      "high": 4300.26,
      "low": 4300.26,
      "close": 4300.26,
      "tick_volume": 1,
      "volume": 0,
      "spread": 58,
      "line_no": 86450
    },
    {
      "ts": "2025-12-15 01:15:00",
      "open": 4303.03,
      "high": 4303.03,
      "low": 4303.03,
      "close": 4303.03,
      "tick_volume": 1,
      "volume": 0,
      "spread": 33,
      "line_no": 86451
    }
  ]
}
```

</details>

<details><summary>spread details</summary>

```json
{
  "negative": 0,
  "zero": 6575,
  "extreme": 4,
  "quantiles": {
    "0.0": 0.0,
    "0.01": 0.0,
    "0.05": 0.0,
    "0.25": 4.0,
    "0.5": 6.0,
    "0.75": 12.0,
    "0.95": 20.0,
    "0.99": 33.0,
    "1.0": 281.0
  },
  "mean": 8.755213461022107,
  "units": "points as exported by MT5 (instrument point size must be confirmed with the broker)",
  "extreme_examples": [
    {
      "ts": "2025-11-27 21:45:00",
      "open": 4156.82,
      "high": 4156.82,
      "low": 4156.82,
      "close": 4156.82,
      "tick_volume": 8,
      "volume": 0,
      "spread": 192,
      "line_no": 85438
    },
    {
      "ts": "2025-11-28 10:15:00",
      "open": 4165.41,
      "high": 4167.48,
      "low": 4153.9,
      "close": 4158.24,
      "tick_volume": 60,
      "volume": 0,
      "spread": 193,
      "line_no": 85484
    },
    {
      "ts": "2025-11-28 11:45:00",
      "open": 4163.11,
      "high": 4166.25,
      "low": 4161.86,
      "close": 4165.33,
      "tick_volume": 71,
      "volume": 0,
      "spread": 229,
      "line_no": 85490
    },
    {
      "ts": "2026-05-25 21:30:00",
      "open": 4569.39,
      "high": 4569.39,
      "low": 4569.39,
      "close": 4569.39,
      "tick_volume": 1,
      "volume": 0,
      "spread": 281,
      "line_no": 96606
    }
  ]
}
```

</details>

<details><summary>price_jumps details</summary>

```json
{
  "count": 14,
  "median_range": 2.6900000000000546,
  "examples": [
    {
      "ts": "2025-04-23 01:00:00",
      "open": 3347.99,
      "close": 3335.39,
      "prev_close": 3380.93,
      "jump": 32.940000000000055
    },
    {
      "ts": "2025-05-12 01:00:00",
      "open": 3291.47,
      "close": 3281.93,
      "prev_close": 3327.15,
      "jump": 35.68000000000029
    },
    {
      "ts": "2025-10-27 00:00:00",
      "open": 4079.8,
      "close": 4105.11,
      "prev_close": 4112.21,
      "jump": 32.409999999999854
    },
    {
      "ts": "2026-02-02 01:00:00",
      "open": 4773.75,
      "close": 4741.06,
      "prev_close": 4894.47,
      "jump": 120.72000000000025
    },
    {
      "ts": "2026-03-02 01:00:00",
      "open": 5363.14,
      "close": 5347.82,
      "prev_close": 5278.77,
      "jump": 84.36999999999989
    },
    {
      "ts": "2026-03-09 01:00:00",
      "open": 5129.95,
      "close": 5101.85,
      "prev_close": 5171.92,
      "jump": 41.970000000000255
    },
    {
      "ts": "2026-04-13 01:00:00",
      "open": 4723.61,
      "close": 4676.08,
      "prev_close": 4759.74,
      "jump": 36.13000000000011
    },
    {
      "ts": "2026-04-20 01:00:00",
      "open": 4770.66,
      "close": 4790.29,
      "prev_close": 4854.44,
      "jump": 83.77999999999975
    },
    {
      "ts": "2026-04-22 01:00:00",
      "open": 4718.65,
      "close": 4721.83,
      "prev_close": 4679.43,
      "jump": 39.219999999999345
    },
    {
      "ts": "20
... (truncated; see JSON report)
```

</details>

## XAUUSD_M30  —  overall: **WARN**

- source: `XAUUSD_M30_201801240100_202607280400.csv` (sha256 `fe9609f77eb2053c…`, 6,138,132 bytes)
- canonical rows: 100,156  (2018-01-24 01:00:00 → 2026-07-28 04:00:00)
- content sha256: `7e700415c6481d3f1e2238f294b8f5541af4bbae0c2b71021e15cf0a1d55e94b`
- schema version: 1.0.0; timezone: `broker_server_time_naive`
- normalization: {"rows_in": 100156, "rows_out": 100156, "dropped_unparseable_timestamp": 0, "dropped_nan_ohlc": 0, "exact_duplicates_removed": 0, "conflicting_duplicate_groups": 0, "conflicting_duplicate_rows_removed": 0, "reordered": false, "conflicting_examples": "(see JSON)"}

| check | status | summary |
|---|---|---|
| schema | PASS | all canonical columns present |
| row_count | INFO | 100156 rows from 2018-01-24 01:00:00 to 2026-07-28 04:00:00 |
| timestamp_order | PASS | timestamps strictly increasing and unique |
| duplicate_timestamps | PASS | no duplicate timestamps |
| grid_alignment | PASS | 0 timestamps not aligned to the M30 grid |
| frequency_and_gaps | WARN | exact_step=97948 sub_step=0 gaps=2207 kinds={'daily_break': 1755, 'weekend': 432, 'extended': 12, 'intraweek': 8} |
| ohlc_integrity | PASS | 0 candles violate high>=max(o,c)>=min(o,c)>=low |
| price_positivity | PASS | 0 candles with non-positive or non-finite prices |
| zero_range_candles | WARN | 9 candles with high == low (0.0090%) |
| spread | WARN | negative=0 zero=5752 extreme(>5x p99)=13 median=6.0 |
| volume | INFO | tick_volume zero=0 negative=0; volume all_zero=False |
| weekday_distribution | PASS | weekend bars=0 (Sat=0, Sun=0) |
| hour_distribution | INFO | bars observed in 24/24 hours of day; first hour=0 |
| price_jumps | WARN | 12 open-vs-previous-close jumps > 12.0x median candle range (2.7899999999999636) |

<details><summary>frequency_and_gaps details</summary>

```json
{
  "expected_step_minutes": 30,
  "exact_step": 97948,
  "sub_step": 0,
  "gap_count": 2207,
  "gap_kinds": {
    "daily_break": 1755,
    "weekend": 432,
    "extended": 12,
    "intraweek": 8
  },
  "missing_bars_total": 48987,
  "missing_bars_non_weekend": 6329,
  "largest_gaps": [
    {
      "gap_start": "2020-12-24 20:30:00",
      "gap_end": "2020-12-28 01:00:00",
      "delta": "3 days 04:30:00",
      "missing_bars": 152,
      "kind": "extended"
    },
    {
      "gap_start": "2020-12-31 20:30:00",
      "gap_end": "2021-01-04 01:00:00",
      "delta": "3 days 04:30:00",
      "missing_bars": 152,
      "kind": "extended"
    },
    {
      "gap_start": "2026-04-02 22:30:00",
      "gap_end": "2026-04-06 01:00:00",
      "delta": "3 days 02:30:00",
      "missing_bars": 148,
      "kind": "extended"
    },
    {
      "gap_start": "2024-03-28 22:30:00",
      "gap_end": "2024-04-01 01:00:00",
      "delta": "3 days 02:30:00",
      "missing_bars": 148,
      "kind": "extended"
    },
    {
      "gap_start": "2023-12-29 23:30:00",
      "gap_end": "2024-01-02 01:00:00",
      "delta": "3 days 01:30:00",
      "missing_bars": 146,
      "kind": "weekend"
    },
    {
      "gap_start": "2021-12-23 23:30:00",
      "gap_end": "2021-12-27 01:00:00",
      "delta": "3 days 01:30:00",
      "missing_bars": 146,
      "kind": "extended"
    },
    {
      "gap_start": "2020-04-09 23:30:00",
      "gap_end": "2020-04-13 01:00:00",
      "delta": "3 days 01:30:00",
      
... (truncated; see JSON report)
```

</details>

<details><summary>zero_range_candles details</summary>

```json
{
  "count": 9,
  "fraction": 8.985981868285475e-05,
  "examples": [
    {
      "ts": "2020-10-27 00:00:00",
      "open": 1902.06,
      "high": 1902.06,
      "low": 1902.06,
      "close": 1902.06,
      "tick_volume": 1,
      "volume": 0,
      "spread": 19,
      "line_no": 32445
    },
    {
      "ts": "2024-07-04 21:30:00",
      "open": 2356.1,
      "high": 2356.1,
      "low": 2356.1,
      "close": 2356.1,
      "tick_volume": 1,
      "volume": 0,
      "spread": 138,
      "line_no": 76032
    },
    {
      "ts": "2025-11-27 21:30:00",
      "open": 4156.82,
      "high": 4156.82,
      "low": 4156.82,
      "close": 4156.82,
      "tick_volume": 17,
      "volume": 0,
      "spread": 132,
      "line_no": 92588
    },
    {
      "ts": "2025-12-18 01:30:00",
      "open": 4341.78,
      "high": 4341.78,
      "low": 4341.78,
      "close": 4341.78,
      "tick_volume": 1,
      "volume": 0,
      "spread": 33,
      "line_no": 93234
    },
    {
      "ts": "2025-12-26 01:30:00",
      "open": 4498.76,
      "high": 4498.76,
      "low": 4498.76,
      "close": 4498.76,
      "tick_volume": 1,
      "volume": 0,
      "spread": 33,
      "line_no": 93457
    }
  ]
}
```

</details>

<details><summary>spread details</summary>

```json
{
  "negative": 0,
  "zero": 5752,
  "extreme": 13,
  "quantiles": {
    "0.0": 0.0,
    "0.01": 0.0,
    "0.05": 0.0,
    "0.25": 5.0,
    "0.5": 6.0,
    "0.75": 15.0,
    "0.95": 21.0,
    "0.99": 33.0,
    "1.0": 319.0
  },
  "mean": 9.694376772235312,
  "units": "points as exported by MT5 (instrument point size must be confirmed with the broker)",
  "extreme_examples": [
    {
      "ts": "2020-03-24 10:00:00",
      "open": 1570.97,
      "high": 1589.19,
      "low": 1566.3,
      "close": 1584.79,
      "tick_volume": 3471,
      "volume": 0,
      "spread": 176,
      "line_no": 25411
    },
    {
      "ts": "2020-03-24 14:30:00",
      "open": 1594.91,
      "high": 1603.11,
      "low": 1585.58,
      "close": 1597.36,
      "tick_volume": 2114,
      "volume": 0,
      "spread": 279,
      "line_no": 25420
    },
    {
      "ts": "2020-03-24 15:00:00",
      "open": 1597.36,
      "high": 1608.35,
      "low": 1591.29,
      "close": 1605.42,
      "tick_volume": 873,
      "volume": 0,
      "spread": 319,
      "line_no": 25421
    },
    {
      "ts": "2020-03-24 18:00:00",
      "open": 1614.44,
      "high": 1620.22,
      "low": 1605.62,
      "close": 1619.94,
      "tick_volume": 1707,
      "volume": 0,
      "spread": 232,
      "line_no": 25427
    },
    {
      "ts": "2020-03-24 19:30:00",
      "open": 1620.16,
      "high": 1628.34,
      "low": 1616.78,
      "close": 1626.33,
      "tick_volume": 1966,
      "volume": 0,
      "spread": 206,
   
... (truncated; see JSON report)
```

</details>

<details><summary>price_jumps details</summary>

```json
{
  "count": 12,
  "median_range": 2.7899999999999636,
  "examples": [
    {
      "ts": "2025-05-12 01:00:00",
      "open": 3291.47,
      "close": 3277.94,
      "prev_close": 3327.15,
      "jump": 35.68000000000029
    },
    {
      "ts": "2026-02-02 01:00:00",
      "open": 4773.75,
      "close": 4727.25,
      "prev_close": 4894.47,
      "jump": 120.72000000000025
    },
    {
      "ts": "2026-03-02 01:00:00",
      "open": 5363.14,
      "close": 5354.92,
      "prev_close": 5278.77,
      "jump": 84.36999999999989
    },
    {
      "ts": "2026-03-09 01:00:00",
      "open": 5129.95,
      "close": 5104.57,
      "prev_close": 5171.92,
      "jump": 41.970000000000255
    },
    {
      "ts": "2026-04-13 01:00:00",
      "open": 4723.61,
      "close": 4647.61,
      "prev_close": 4759.74,
      "jump": 36.13000000000011
    },
    {
      "ts": "2026-04-20 01:00:00",
      "open": 4770.66,
      "close": 4785.23,
      "prev_close": 4854.44,
      "jump": 83.77999999999975
    },
    {
      "ts": "2026-04-22 01:00:00",
      "open": 4718.65,
      "close": 4719.02,
      "prev_close": 4679.43,
      "jump": 39.219999999999345
    },
    {
      "ts": "2026-06-15 01:00:00",
      "open": 4262.55,
      "close": 4286.91,
      "prev_close": 4210.73,
      "jump": 51.82000000000062
    },
    {
      "ts": "2026-06-26 01:00:00",
      "open": 3989.99,
      "close": 4024.79,
      "prev_close": 4026.81,
      "jump": 36.820000000000164
    },
    {
      "ts": "20
... (truncated; see JSON report)
```

</details>

