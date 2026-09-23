from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from apex_jev.data.schema import Timeframe

HEADER = "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>"


def synthetic_candles(
    tf: Timeframe, start: str, n_weeks: int, seed: int = 0, price0: float = 1800.0
) -> pd.DataFrame:
    """Deterministic synthetic XAUUSD-like candles: Mon 01:00 .. Fri 23:59 in broker time, weekend closed."""
    rng = np.random.default_rng(seed)
    step = pd.Timedelta(minutes=tf.minutes)
    t0 = pd.Timestamp(start)
    ts: list[pd.Timestamp] = []
    t = t0
    end = t0 + pd.Timedelta(weeks=n_weeks)
    while t < end:
        dow = t.dayofweek
        # broker week: opens Monday 01:00, closes Friday 24:00, daily break 00:00-01:00
        if dow < 5 and t.hour >= 1:
            ts.append(t)
        t += step
    n = len(ts)
    rets = rng.normal(0, 0.0008, n)
    close = price0 * np.exp(np.cumsum(rets))
    open_ = np.r_[price0, close[:-1]]
    wick = np.abs(rng.normal(0, 0.0006, n)) * close
    high = np.maximum(open_, close) + wick
    low = np.minimum(open_, close) - wick
    return pd.DataFrame(
        {
            "ts": pd.to_datetime(ts),
            "open": open_.round(2),
            "high": high.round(2),
            "low": low.round(2),
            "close": close.round(2),
            "tick_volume": rng.integers(50, 5000, n).astype("int64"),
            "volume": np.zeros(n, dtype="int64"),
            "spread": rng.integers(10, 40, n).astype("int64"),
        }
    )


def to_mt5_lines(df: pd.DataFrame) -> list[str]:
    lines = []
    for r in df.itertuples(index=False):
        lines.append(
            f"{r.ts.strftime('%Y.%m.%d')}\t{r.ts.strftime('%H:%M:%S')}\t{r.open:.2f}\t{r.high:.2f}\t"
            f"{r.low:.2f}\t{r.close:.2f}\t{r.tick_volume}\t{r.volume}\t{r.spread}"
        )
    return lines


def write_mt5_csv(path: Path, df: pd.DataFrame, extra_lines: list[str] | None = None) -> Path:
    lines = [HEADER, *to_mt5_lines(df), *(extra_lines or [])]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def mt5_name(symbol: str, tf: Timeframe, df: pd.DataFrame) -> str:
    return f"{symbol}_{tf.value}_{df['ts'].iloc[0]:%Y%m%d%H%M}_{df['ts'].iloc[-1]:%Y%m%d%H%M}.csv"


@pytest.fixture
def h1() -> pd.DataFrame:
    return synthetic_candles(Timeframe.H1, "2024-01-01 00:00", n_weeks=3, seed=1)


@pytest.fixture
def m30() -> pd.DataFrame:
    return synthetic_candles(Timeframe.M30, "2024-01-08 00:00", n_weeks=2, seed=2)


@pytest.fixture
def m15() -> pd.DataFrame:
    return synthetic_candles(Timeframe.M15, "2024-01-15 00:00", n_weeks=1, seed=3)


@pytest.fixture
def raw_dir(tmp_path: Path, h1, m30, m15) -> Path:
    d = tmp_path / "raw"
    d.mkdir()
    for tf, df in ((Timeframe.H1, h1), (Timeframe.M30, m30), (Timeframe.M15, m15)):
        write_mt5_csv(d / mt5_name("XAUUSD", tf, df), df)
    return d
