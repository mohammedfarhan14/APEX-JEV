# Failure Modes (Level 0 scope)

Each entry: how it fails, how it is detected today, what the system does, what is still open.

| # | Failure mode | Detection | Current behaviour | Open |
|---|---|---|---|---|
| F1 | Wrong or drifting broker time offset | Not detectable from the data alone; hour/gap distribution gives evidence | Timestamps kept naive and labelled; no UTC conversion | Confirm offset with broker before session-based research |
| F2 | Export header/format change | `RawSchemaError` on load | Pipeline stops for that file | None |
| F3 | Duplicate timestamps (exact or conflicting) | Normalisation log + `check_duplicates` | Exact dups dropped; conflicts keep first, all logged; check FAILs if any survive | None |
| F4 | Missing candles / gaps | `check_frequency_and_gaps` classification | Reported, never filled | Session calendar to distinguish holiday from feed outage |
| F5 | OHLC invariant violation | `check_ohlc_integrity` (+ property tests) | FAIL, dataset marked untrustworthy | None |
| F6 | Zero or absurd spread | `check_spread` | WARN with quantiles and examples | Cost model policy for zero-spread periods (2009-2010, 2021-2022, 2026) |
| F7 | Inconsistent real volume | `check_volume` | INFO; `volume` documented as unusable | None |
| F8 | Partial last bar at export time | `cross_tf.compare` catches it when TFs disagree | Documented; last bar treated as provisional by consumers | Optional explicit trim flag |
| F9 | Cross-TF feed inconsistency | `cross_tf.compare` on complete buckets | WARN/FAIL with mismatch counts; nothing repaired | None |
| F10 | Silent corruption of Parquet | Content SHA-256 in manifest; `apex-data verify` | Load fails on mismatch | None |
| F11 | Schema drift between code and stored data | `SCHEMA_VERSION` in manifest and Parquet metadata | Load fails on mismatch | Migration tooling when v2 arrives |
| F12 | Lookahead in derived features | `pit.assert_causal` | Test fails | Must be applied to every feature at Level 1 |
| F13 | Fabricated multi-TF history | Coverage tiers are explicit | Research must pick a tier | None |
| F14 | Export row cap truncating history | Row counts ~100k with identical end instant | Documented as INFERENCE in DATA_SPEC | Re-export with a higher bar limit |

Prohibited responses to any of the above: filling gaps, repairing prices, clipping spreads, inventing volume,
or converting time zones without a confirmed offset.
