"""Multi-timeframe coverage: which research periods actually exist.

Never fabricate a unified multi-timeframe history. Coverage tiers are derived purely from the first
and last timestamps of each canonical dataset.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from apex_jev.data.schema import Timeframe


@dataclass(frozen=True)
class Coverage:
    timeframe: Timeframe
    start: pd.Timestamp
    end: pd.Timestamp
    rows: int

    def to_dict(self) -> dict:
        return {
            "timeframe": self.timeframe.value,
            "start": str(self.start),
            "end": str(self.end),
            "rows": self.rows,
        }


def coverage_of(df: pd.DataFrame, tf: Timeframe) -> Coverage:
    if df.empty:
        raise ValueError("empty frame has no coverage")
    return Coverage(tf, df["ts"].iloc[0], df["ts"].iloc[-1], int(len(df)))


def coverage_tiers(covs: dict[Timeframe, Coverage]) -> list[dict]:
    """Return the intersection periods for the standard tiers.

    Tiers (only emitted when all member timeframes are present):
      H1_only          : full H1 range
      H1_M30           : intersection of H1 and M30
      H1_M30_M15       : intersection of all three
    """
    tiers: list[dict] = []

    def tier(name: str, members: list[Timeframe]) -> None:
        if not all(m in covs for m in members):
            return
        start = max(covs[m].start for m in members)
        end = min(covs[m].end for m in members)
        tiers.append(
            {
                "tier": name,
                "timeframes": [m.value for m in members],
                "start": str(start),
                "end": str(end),
                "valid": bool(start <= end),
                "span_days": float((end - start).total_seconds() / 86400) if start <= end else 0.0,
            }
        )

    tier("H1_only", [Timeframe.H1])
    tier("H1_M30", [Timeframe.H1, Timeframe.M30])
    tier("H1_M30_M15", [Timeframe.H1, Timeframe.M30, Timeframe.M15])
    return tiers
