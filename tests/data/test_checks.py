from __future__ import annotations

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

from apex_jev.data import checks
from apex_jev.data.schema import Timeframe


def _by_name(results, name):
    return next(r for r in results if r.name == name)


def test_clean_synthetic_passes_hard_checks(h1):
    res = checks.run_all_checks(h1, Timeframe.H1)
    for name in (
        "schema",
        "timestamp_order",
        "duplicate_timestamps",
        "grid_alignment",
        "ohlc_integrity",
        "price_positivity",
    ):
        assert _by_name(res, name).status == "PASS", name
    assert _by_name(res, "weekday_distribution").status == "PASS"
    assert checks.worst_status(res) in ("PASS", "WARN")


def test_gap_classification_weekend_and_daily_break(h1):
    r = _by_name(checks.run_all_checks(h1, Timeframe.H1), "frequency_and_gaps")
    kinds = r.details["gap_kinds"]
    assert kinds.get("weekend", 0) >= 2  # 3 synthetic weeks
    assert kinds.get("daily_break", 0) >= 10  # one per weekday night
    assert kinds.get("extended", 0) == 0
    assert r.details["sub_step"] == 0
    assert r.status == "WARN"


def test_extended_gap_detected(h1):
    cut = h1[(h1["ts"] < "2024-01-08") | (h1["ts"] >= "2024-01-16")].reset_index(drop=True)
    r = _by_name(checks.run_all_checks(cut, Timeframe.H1), "frequency_and_gaps")
    assert r.details["gap_kinds"].get("extended", 0) == 1
    assert r.details["missing_bars_non_weekend"] > 0


def test_ohlc_violation_fails(h1):
    bad = h1.copy()
    bad.loc[3, "high"] = bad.loc[3, "low"] - 1
    bad.loc[4, "high"] = bad.loc[4, "close"] + 10
    bad.loc[4, "low"] = bad.loc[4, "close"] + 1
    r = checks.check_ohlc_integrity(bad)
    assert r.status == "FAIL"
    assert r.details["counts"]["high_lt_low"] == 1
    assert r.details["counts"]["low_gt_close"] == 1


def test_non_positive_price_fails(h1):
    bad = h1.copy()
    bad.loc[0, "open"] = 0.0
    assert checks.check_price_positivity(bad).status == "FAIL"


def test_duplicates_and_order_fail(h1):
    dup = pd.concat([h1, h1.iloc[[2]]], ignore_index=True)
    assert checks.check_duplicates(dup).status == "FAIL"
    assert checks.check_timestamp_order(dup).status == "FAIL"


def test_grid_alignment_fails_on_off_grid(h1):
    bad = h1.copy()
    bad.loc[1, "ts"] = bad.loc[1, "ts"] + pd.Timedelta(minutes=7)
    assert checks.check_grid_alignment(bad, Timeframe.H1).status == "FAIL"
    assert checks.check_grid_alignment(h1, Timeframe.M15).status == "PASS"  # H1 grid is a subset of M15 grid


def test_spread_statuses(h1):
    assert checks.check_spread(h1).status == "PASS"
    neg = h1.copy()
    neg.loc[0, "spread"] = -1
    assert checks.check_spread(neg).status == "FAIL"
    zero = h1.copy()
    zero.loc[0, "spread"] = 0
    assert checks.check_spread(zero).status == "WARN"
    huge = h1.copy()
    huge.loc[0, "spread"] = 100000
    r = checks.check_spread(huge)
    assert r.status == "WARN" and r.details["extreme"] == 1


def test_weekend_bars_warn(h1):
    wk = h1.copy()
    wk.loc[0, "ts"] = pd.Timestamp("2023-12-31 05:00")  # Sunday
    wk = wk.sort_values("ts").reset_index(drop=True)
    assert checks.check_weekday_distribution(wk).status == "WARN"


def test_price_jump_warns(h1):
    j = h1.copy()
    j.loc[10, "open"] = j.loc[10, "open"] + 500
    j.loc[10, "high"] = j.loc[10, "open"] + 1
    assert checks.check_price_jumps(j).status == "WARN"


def test_empty_and_single_row_edge_cases():
    empty = pd.DataFrame(columns=["ts", "open", "high", "low", "close", "tick_volume", "volume", "spread"])
    res = checks.run_all_checks(empty, Timeframe.H1)
    assert checks.worst_status(res) == "FAIL"
    one = pd.DataFrame(
        {
            "ts": [pd.Timestamp("2024-01-01 01:00")],
            "open": [1.0],
            "high": [2.0],
            "low": [0.5],
            "close": [1.5],
            "tick_volume": [1],
            "volume": [0],
            "spread": [3],
        }
    )
    res = checks.run_all_checks(one, Timeframe.H1)
    assert _by_name(res, "frequency_and_gaps").status == "FAIL"
    assert _by_name(res, "ohlc_integrity").status == "PASS"


@settings(max_examples=100, deadline=None)
@given(
    st.lists(
        st.tuples(
            st.floats(1, 5000, allow_nan=False),
            st.floats(0, 50, allow_nan=False),
            st.floats(0, 50, allow_nan=False),
            st.floats(-50, 50, allow_nan=False),
        ),
        min_size=1,
        max_size=60,
    )
)
def test_ohlc_integrity_property(rows):
    # candles built to satisfy the invariant must PASS; then a random violation must FAIL
    ts = pd.date_range("2024-01-01 01:00", periods=len(rows), freq="1h")
    o = pd.Series([r[0] for r in rows])
    c = o + pd.Series([r[3] for r in rows])
    c = c.clip(lower=0.01)
    h = pd.concat([o, c], axis=1).max(axis=1) + pd.Series([r[1] for r in rows])
    lo = (pd.concat([o, c], axis=1).min(axis=1) - pd.Series([r[2] for r in rows])).clip(lower=0.001)
    df = pd.DataFrame({"ts": ts, "open": o, "high": h, "low": lo, "close": c})
    assert checks.check_ohlc_integrity(df).status == "PASS"
    bad = df.copy()
    bad.loc[0, "high"] = bad.loc[0, "low"] - 1
    assert checks.check_ohlc_integrity(bad).status == "FAIL"
