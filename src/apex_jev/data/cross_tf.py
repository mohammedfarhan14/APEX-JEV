"""Cross-timeframe consistency: does aggregating a lower timeframe reproduce the higher one?

This is a research-validity check, not a repair step. Broker exports are not guaranteed to be
internally consistent (different tick filtering, session boundaries, or history depth), so results
are reported, never used to "fix" a dataset.

Aggregation rule: a higher-timeframe candle with open time T covers lower-timeframe candles with
open times in [T, T + tf_high). Only *complete* buckets (all expected lower bars present) are compared,
so gaps in the lower timeframe do not produce spurious mismatches.
"""

from __future__ import annotations

import pandas as pd

from apex_jev.data.schema import Timeframe


def aggregate(lower: pd.DataFrame, tf_low: Timeframe, tf_high: Timeframe) -> pd.DataFrame:
    if tf_high.minutes % tf_low.minutes != 0 or tf_high.minutes <= tf_low.minutes:
        raise ValueError(f"{tf_low.value} does not tile {tf_high.value}")
    per_bucket = tf_high.minutes // tf_low.minutes
    bucket = lower["ts"].dt.floor(f"{tf_high.minutes}min")
    g = lower.groupby(bucket, sort=True)
    agg = g.agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        tick_volume=("tick_volume", "sum"),
        volume=("volume", "sum"),
        n=("ts", "size"),
    )
    agg = agg[agg["n"] == per_bucket].drop(columns="n")
    agg.index.name = "ts"
    return agg.reset_index()


def compare(
    lower: pd.DataFrame, tf_low: Timeframe, higher: pd.DataFrame, tf_high: Timeframe, price_tol: float = 1e-9
) -> dict:
    agg = aggregate(lower, tf_low, tf_high)
    merged = agg.merge(higher, on="ts", how="inner", suffixes=("_agg", "_hi"))
    if merged.empty:
        return {
            "pair": f"{tf_low.value}->{tf_high.value}",
            "complete_buckets": int(len(agg)),
            "compared": 0,
            "note": "no overlapping complete buckets",
        }
    out: dict = {
        "pair": f"{tf_low.value}->{tf_high.value}",
        "complete_buckets": int(len(agg)),
        "compared": int(len(merged)),
        "overlap_start": str(merged["ts"].iloc[0]),
        "overlap_end": str(merged["ts"].iloc[-1]),
        "mismatch_counts": {},
        "abs_diff_quantiles": {},
    }
    for c in ("open", "high", "low", "close"):
        diff = (merged[f"{c}_agg"] - merged[f"{c}_hi"]).abs()
        out["mismatch_counts"][c] = int((diff > price_tol).sum())
        out["abs_diff_quantiles"][c] = {
            "p50": float(diff.quantile(0.5)),
            "p99": float(diff.quantile(0.99)),
            "max": float(diff.max()),
        }
    tv_diff = (merged["tick_volume_agg"] - merged["tick_volume_hi"]).abs()
    out["mismatch_counts"]["tick_volume"] = int((tv_diff > 0).sum())
    out["tick_volume_abs_diff_p99"] = float(tv_diff.quantile(0.99))
    # High-timeframe candles whose bucket exists in the lower TF but is incomplete are not compared;
    # count how many higher candles have no comparison at all.
    out["higher_candles_without_complete_lower_bucket"] = int(
        (
            ~higher["ts"].isin(agg["ts"])
            & (higher["ts"] >= lower["ts"].iloc[0])
            & (higher["ts"] <= lower["ts"].iloc[-1])
        ).sum()
    )
    total_price_mismatch = sum(out["mismatch_counts"][c] for c in ("open", "high", "low", "close"))
    out["price_mismatch_fraction"] = float(total_price_mismatch / (4 * len(merged)))
    out["status"] = "PASS" if total_price_mismatch == 0 else "WARN"
    return out
