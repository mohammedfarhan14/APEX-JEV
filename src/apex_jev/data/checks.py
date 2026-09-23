"""Data quality checks on a canonical candle frame.

Every check returns a CheckResult. Statuses:
  PASS  the property holds
  WARN  anomalies exist that need documentation but are plausibly legitimate (e.g. market closures)
  FAIL  a hard integrity violation that makes the data untrustworthy for research as-is
  INFO  descriptive statistics, no judgement attached

A gap is not an error merely because it exists (markets close, holidays happen). Gaps are classified
and described; deciding whether a gap is a defect is a documented research decision, not a heuristic
buried in code.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from apex_jev.data.schema import CANONICAL_COLUMNS, Timeframe


@dataclass
class CheckResult:
    name: str
    status: str  # PASS | WARN | FAIL | INFO
    summary: str
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"name": self.name, "status": self.status, "summary": self.summary, "details": self.details}


def _examples(df: pd.DataFrame, mask: pd.Series, n: int = 10) -> list[dict]:
    sub = df.loc[mask].head(n).copy()
    if "ts" in sub:
        sub["ts"] = sub["ts"].astype(str)
    return sub.to_dict(orient="records")


def check_schema(df: pd.DataFrame) -> CheckResult:
    missing = [c for c in CANONICAL_COLUMNS if c not in df.columns]
    if missing:
        return CheckResult("schema", "FAIL", f"missing canonical columns: {missing}", {"missing": missing})
    return CheckResult("schema", "PASS", "all canonical columns present", {"columns": list(df.columns)})


def check_row_count(df: pd.DataFrame) -> CheckResult:
    if df.empty:
        return CheckResult("row_count", "FAIL", "empty frame", {"rows": 0})
    return CheckResult(
        "row_count",
        "INFO",
        f"{len(df)} rows from {df['ts'].iloc[0]} to {df['ts'].iloc[-1]}",
        {"rows": int(len(df)), "first_ts": str(df["ts"].iloc[0]), "last_ts": str(df["ts"].iloc[-1])},
    )


def check_timestamp_order(df: pd.DataFrame) -> CheckResult:
    if df.empty:
        return CheckResult("timestamp_order", "FAIL", "empty frame")
    strictly = df["ts"].is_monotonic_increasing and df["ts"].is_unique
    if strictly:
        return CheckResult("timestamp_order", "PASS", "timestamps strictly increasing and unique")
    dups = int(df["ts"].duplicated().sum())
    return CheckResult(
        "timestamp_order",
        "FAIL",
        f"timestamps not strictly increasing (duplicates={dups})",
        {"duplicates": dups, "monotonic": bool(df["ts"].is_monotonic_increasing)},
    )


def check_duplicates(df: pd.DataFrame) -> CheckResult:
    dup_mask = df["ts"].duplicated(keep=False)
    n = int(dup_mask.sum())
    if n == 0:
        return CheckResult("duplicate_timestamps", "PASS", "no duplicate timestamps")
    return CheckResult(
        "duplicate_timestamps", "FAIL", f"{n} rows share a timestamp", {"examples": _examples(df, dup_mask)}
    )


def check_ohlc_integrity(df: pd.DataFrame) -> CheckResult:
    o, h, lo, c = df["open"], df["high"], df["low"], df["close"]
    viol = {
        "high_lt_low": h < lo,
        "high_lt_open": h < o,
        "high_lt_close": h < c,
        "low_gt_open": lo > o,
        "low_gt_close": lo > c,
    }
    counts = {k: int(v.sum()) for k, v in viol.items()}
    any_mask = pd.Series(False, index=df.index)
    for v in viol.values():
        any_mask |= v
    total = int(any_mask.sum())
    status = "PASS" if total == 0 else "FAIL"
    return CheckResult(
        "ohlc_integrity",
        status,
        f"{total} candles violate high>=max(o,c)>=min(o,c)>=low",
        {"counts": counts, "examples": _examples(df, any_mask)},
    )


def check_price_positivity(df: pd.DataFrame) -> CheckResult:
    mask = (df[["open", "high", "low", "close"]] <= 0).any(axis=1) | ~np.isfinite(
        df[["open", "high", "low", "close"]]
    ).all(axis=1)
    n = int(mask.sum())
    return CheckResult(
        "price_positivity",
        "PASS" if n == 0 else "FAIL",
        f"{n} candles with non-positive or non-finite prices",
        {"examples": _examples(df, mask)},
    )


def check_zero_range(df: pd.DataFrame) -> CheckResult:
    mask = df["high"] == df["low"]
    n = int(mask.sum())
    return CheckResult(
        "zero_range_candles",
        "INFO" if n == 0 else "WARN",
        f"{n} candles with high == low ({n / max(len(df), 1):.4%})",
        {"count": n, "fraction": n / max(len(df), 1), "examples": _examples(df, mask, 5)},
    )


def check_spread(df: pd.DataFrame) -> CheckResult:
    s = df["spread"]
    negative = int((s < 0).sum())
    zero = int((s == 0).sum())
    q = s.quantile([0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0]).to_dict()
    q99 = q[0.99]
    extreme_mask = s > max(q99 * 5, 1)
    extreme = int(extreme_mask.sum())
    status = "FAIL" if negative else ("WARN" if zero or extreme else "PASS")
    return CheckResult(
        "spread",
        status,
        f"negative={negative} zero={zero} extreme(>5x p99)={extreme} median={q[0.5]}",
        {
            "negative": negative,
            "zero": zero,
            "extreme": extreme,
            "quantiles": {str(k): float(v) for k, v in q.items()},
            "mean": float(s.mean()) if len(s) else None,
            "units": "points as exported by MT5 (instrument point size must be confirmed with the broker)",
            "extreme_examples": _examples(df, extreme_mask, 5),
        },
    )


def check_volume(df: pd.DataFrame) -> CheckResult:
    tv, v = df["tick_volume"], df["volume"]
    return CheckResult(
        "volume",
        "INFO",
        f"tick_volume zero={int((tv == 0).sum())} negative={int((tv < 0).sum())}; "
        f"volume all_zero={bool((v == 0).all())}",
        {
            "tick_volume_zero": int((tv == 0).sum()),
            "tick_volume_negative": int((tv < 0).sum()),
            "tick_volume_quantiles": {
                str(k): float(x) for k, x in tv.quantile([0.01, 0.5, 0.99]).to_dict().items()
            },
            "volume_all_zero": bool((v == 0).all()),
            "volume_nonzero_rows": int((v != 0).sum()),
        },
    )


def check_grid_alignment(df: pd.DataFrame, tf: Timeframe) -> CheckResult:
    minutes = df["ts"].dt.hour * 60 + df["ts"].dt.minute
    seconds = df["ts"].dt.second
    mask = (minutes % tf.minutes != 0) | (seconds != 0)
    n = int(mask.sum())
    return CheckResult(
        "grid_alignment",
        "PASS" if n == 0 else "FAIL",
        f"{n} timestamps not aligned to the {tf.value} grid",
        {"examples": _examples(df, mask)},
    )


def classify_gaps(df: pd.DataFrame, tf: Timeframe) -> pd.DataFrame:
    """Return one row per gap (consecutive delta > timeframe) with a coarse classification.

    Classification is descriptive only:
      weekend      gap starts Friday and ends Sunday/Monday (typical FX/CFD weekend close)
      daily_break  gap < 24h fully inside a weekday (broker daily maintenance / rollover)
      intraweek    other gap < 3 days on weekdays
      extended     >= 3 days (holidays, feed outage, or missing history)
    """
    if len(df) < 2:
        return pd.DataFrame(columns=["gap_start", "gap_end", "delta", "missing_bars", "kind"])
    ts = df["ts"]
    delta = ts.diff()
    expected = pd.Timedelta(minutes=tf.minutes)
    gap_mask = delta > expected
    gap_end = ts[gap_mask]
    gap_start = ts.shift(1)[gap_mask]
    d = delta[gap_mask]
    missing = (d / expected - 1).round().astype("int64")
    start_dow = gap_start.dt.dayofweek
    end_dow = gap_end.dt.dayofweek
    kind = np.where(
        (start_dow >= 4) & (end_dow <= 1) & (d < pd.Timedelta(days=4)),
        "weekend",
        np.where(
            d < pd.Timedelta(hours=24),
            "daily_break",
            np.where(d < pd.Timedelta(days=3), "intraweek", "extended"),
        ),
    )
    return pd.DataFrame(
        {
            "gap_start": gap_start.to_numpy(),
            "gap_end": gap_end.to_numpy(),
            "delta": d.to_numpy(),
            "missing_bars": missing.to_numpy(),
            "kind": kind,
        }
    ).reset_index(drop=True)


def check_frequency_and_gaps(df: pd.DataFrame, tf: Timeframe) -> CheckResult:
    if len(df) < 2:
        return CheckResult("frequency_and_gaps", "FAIL", "fewer than 2 rows")
    delta = df["ts"].diff().dropna()
    expected = pd.Timedelta(minutes=tf.minutes)
    too_small = int((delta < expected).sum())
    exact = int((delta == expected).sum())
    gaps = classify_gaps(df, tf)
    kinds = gaps["kind"].value_counts().to_dict() if len(gaps) else {}
    biggest = gaps.sort_values("delta", ascending=False).head(10).copy()
    for c in ("gap_start", "gap_end"):
        biggest[c] = biggest[c].astype(str)
    biggest["delta"] = biggest["delta"].astype(str)
    status = "FAIL" if too_small else ("WARN" if len(gaps) else "PASS")
    return CheckResult(
        "frequency_and_gaps",
        status,
        f"exact_step={exact} sub_step={too_small} gaps={len(gaps)} kinds={kinds}",
        {
            "expected_step_minutes": tf.minutes,
            "exact_step": exact,
            "sub_step": too_small,
            "gap_count": int(len(gaps)),
            "gap_kinds": {str(k): int(v) for k, v in kinds.items()},
            "missing_bars_total": int(gaps["missing_bars"].sum()) if len(gaps) else 0,
            "missing_bars_non_weekend": int(gaps.loc[gaps["kind"] != "weekend", "missing_bars"].sum())
            if len(gaps)
            else 0,
            "largest_gaps": biggest.to_dict(orient="records"),
        },
    )


def check_weekday_distribution(df: pd.DataFrame) -> CheckResult:
    dow = df["ts"].dt.dayofweek.value_counts().sort_index()
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    dist = {names[i]: int(dow.get(i, 0)) for i in range(7)}
    weekend = dist["Sat"] + dist["Sun"]
    status = "WARN" if weekend else "PASS"
    return CheckResult(
        "weekday_distribution",
        status,
        f"weekend bars={weekend} (Sat={dist['Sat']}, Sun={dist['Sun']})",
        {"bars_per_weekday": dist},
    )


def check_hour_distribution(df: pd.DataFrame) -> CheckResult:
    hours = df["ts"].dt.hour.value_counts().sort_index()
    dist = {int(h): int(hours.get(h, 0)) for h in range(24)}
    present = [h for h, n in dist.items() if n > 0]
    return CheckResult(
        "hour_distribution",
        "INFO",
        f"bars observed in {len(present)}/24 hours of day; first hour={min(present) if present else None}",
        {"bars_per_hour": dist, "hours_with_data": present},
    )


def check_price_jumps(df: pd.DataFrame, z: float = 12.0) -> CheckResult:
    """Flag close-to-open jumps far outside the typical intrabar range (descriptive, not a verdict)."""
    if len(df) < 3:
        return CheckResult("price_jumps", "INFO", "insufficient rows")
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    typical = rng.median()
    jump = (df["open"] - df["close"].shift(1)).abs()
    mask = jump > z * typical
    n = int(mask.sum())
    ex = df.loc[mask, ["ts", "open", "close"]].copy()
    ex["prev_close"] = df["close"].shift(1)[mask]
    ex["jump"] = jump[mask]
    ex["ts"] = ex["ts"].astype(str)
    return CheckResult(
        "price_jumps",
        "INFO" if n == 0 else "WARN",
        f"{n} open-vs-previous-close jumps > {z}x median candle range ({typical})",
        {
            "count": n,
            "median_range": float(typical) if pd.notna(typical) else None,
            "examples": ex.head(10).to_dict("records"),
        },
    )


def run_all_checks(df: pd.DataFrame, tf: Timeframe) -> list[CheckResult]:
    results = [check_schema(df), check_row_count(df)]
    if df.empty or results[0].status == "FAIL":
        return results
    results += [
        check_timestamp_order(df),
        check_duplicates(df),
        check_grid_alignment(df, tf),
        check_frequency_and_gaps(df, tf),
        check_ohlc_integrity(df),
        check_price_positivity(df),
        check_zero_range(df),
        check_spread(df),
        check_volume(df),
        check_weekday_distribution(df),
        check_hour_distribution(df),
        check_price_jumps(df),
    ]
    return results


def worst_status(results: list[CheckResult]) -> str:
    order = {"INFO": 0, "PASS": 0, "WARN": 1, "FAIL": 2}
    worst = max(results, key=lambda r: order[r.status])
    return {0: "PASS", 1: "WARN", 2: "FAIL"}[order[worst.status]]
