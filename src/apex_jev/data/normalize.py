"""Canonicalisation of raw MT5 frames.

Policy (documented in DATA_SPEC.md):
  * rows with unparseable timestamps or NaN OHLC are EXCLUDED from the canonical frame and counted
  * exact duplicate rows (same ts and identical values) are collapsed to one
  * conflicting duplicates (same ts, different values) keep the FIRST occurrence in file order;
    all of them are reported so the decision is inspectable
  * the canonical frame is sorted by ts ascending with a fresh RangeIndex
Nothing else is modified: no forward-fill, no gap-filling, no timezone conversion.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from apex_jev.data.io_csv import parse_timestamps
from apex_jev.data.schema import CANONICAL_COLUMNS, CANONICAL_DTYPES, RAW_TO_CANONICAL


@dataclass
class NormalizationLog:
    rows_in: int = 0
    rows_out: int = 0
    dropped_unparseable_timestamp: int = 0
    dropped_nan_ohlc: int = 0
    exact_duplicates_removed: int = 0
    conflicting_duplicate_groups: int = 0
    conflicting_duplicate_rows_removed: int = 0
    reordered: bool = False
    conflicting_examples: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "rows_in": self.rows_in,
            "rows_out": self.rows_out,
            "dropped_unparseable_timestamp": self.dropped_unparseable_timestamp,
            "dropped_nan_ohlc": self.dropped_nan_ohlc,
            "exact_duplicates_removed": self.exact_duplicates_removed,
            "conflicting_duplicate_groups": self.conflicting_duplicate_groups,
            "conflicting_duplicate_rows_removed": self.conflicting_duplicate_rows_removed,
            "reordered": self.reordered,
            "conflicting_examples": self.conflicting_examples[:20],
        }


def to_canonical(raw: pd.DataFrame) -> tuple[pd.DataFrame, NormalizationLog]:
    log = NormalizationLog(rows_in=len(raw))
    ts = parse_timestamps(raw)

    out = pd.DataFrame({"ts": ts})
    for raw_col, canon in RAW_TO_CANONICAL.items():
        out[canon] = raw[raw_col]
    out["line_no"] = raw["line_no"].to_numpy()

    bad_ts = out["ts"].isna()
    log.dropped_unparseable_timestamp = int(bad_ts.sum())
    out = out.loc[~bad_ts]

    nan_ohlc = out[["open", "high", "low", "close"]].isna().any(axis=1)
    log.dropped_nan_ohlc = int(nan_ohlc.sum())
    out = out.loc[~nan_ohlc]

    # Integer columns: MT5 always writes them; if missing we record 0 but that is visible via checks
    # on the raw frame. Cast after NaN removal so Int64 -> int64 is safe.
    for c in ("tick_volume", "volume", "spread"):
        out[c] = out[c].fillna(0).astype("int64")

    value_cols = [c for c in CANONICAL_COLUMNS if c != "ts"]
    exact_dup = out.duplicated(subset=["ts", *value_cols], keep="first")
    log.exact_duplicates_removed = int(exact_dup.sum())
    out = out.loc[~exact_dup]

    ts_dup = out.duplicated(subset=["ts"], keep=False)
    if ts_dup.any():
        groups = out.loc[ts_dup]
        log.conflicting_duplicate_groups = int(groups["ts"].nunique())
        for _, g in groups.groupby("ts", sort=True):
            log.conflicting_examples.append(
                {
                    "ts": g["ts"].iloc[0].isoformat(),
                    "rows": g[["line_no", *value_cols]].to_dict(orient="records"),
                }
            )
        keep_first = out.duplicated(subset=["ts"], keep="first")
        log.conflicting_duplicate_rows_removed = int(keep_first.sum())
        out = out.loc[~keep_first]

    log.reordered = not out["ts"].is_monotonic_increasing
    out = out.sort_values("ts", kind="mergesort").reset_index(drop=True)

    out = out[[*CANONICAL_COLUMNS, "line_no"]]
    for c, dt in CANONICAL_DTYPES.items():
        out[c] = out[c].astype(dt)
    out["line_no"] = out["line_no"].astype("int64")
    log.rows_out = len(out)
    return out, log
