"""Point-in-time / leakage tests.

These prove two things at Level 0:
1. The canonical dataset itself carries no implicit future information: every canonical column at
   row i is a function of the raw row i only (trivially causal), and the aggregation used for
   cross-timeframe checks is causal once a bucket is complete.
2. The `assert_causal` harness actually catches lookahead, so future feature work can rely on it.
"""

from __future__ import annotations

import pandas as pd
import pytest

from apex_jev.data.pit import assert_causal, is_causal


def test_canonical_columns_are_causal(h1):
    for col in ("open", "high", "low", "close", "spread", "tick_volume"):
        assert_causal(h1, lambda d, c=col: d[c].astype("float64"))


def test_backward_rolling_is_causal(h1):
    assert is_causal(h1, lambda d: d["close"].rolling(5).mean())
    assert is_causal(h1, lambda d: d["close"].pct_change())
    assert is_causal(h1, lambda d: d["close"].ewm(span=10, adjust=False).mean())
    assert is_causal(h1, lambda d: d["close"].expanding().mean())


def test_lookahead_is_caught(h1):
    with pytest.raises(AssertionError, match="lookahead"):
        assert_causal(h1, lambda d: d["close"].shift(-1))
    with pytest.raises(AssertionError):
        assert_causal(h1, lambda d: d["close"].rolling(5, center=True).mean())
    # full-sample normalisation is a classic leak
    assert not is_causal(h1, lambda d: (d["close"] - d["close"].mean()) / d["close"].std())
    # future-derived label
    assert not is_causal(h1, lambda d: (d["close"].shift(-3) > d["close"]).astype(float))


def test_length_change_is_caught(h1):
    with pytest.raises(AssertionError, match="length"):
        assert_causal(h1, lambda d: d["close"].iloc[1:])


def test_nan_prefix_compares_equal(h1):
    s = pd.Series(float("nan"), index=h1.index)
    assert is_causal(h1, lambda d: s.iloc[: len(d)])
