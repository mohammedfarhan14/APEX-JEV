"""Point-in-time (no-lookahead) verification helpers.

A feature function f(frame) -> Series is *causal* if, for every prefix of the data, the values it
produces for that prefix are identical whether or not the future rows are present. This module
provides a generic test for that property. It is used at Level 0 to (a) prove the canonical dataset
contains no implicit future information (row i depends only on rows <= i), and (b) provide the
leakage test every future feature must pass before registration.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

import numpy as np
import pandas as pd

FeatureFn = Callable[[pd.DataFrame], pd.Series]


def assert_causal(
    df: pd.DataFrame,
    fn: FeatureFn,
    cut_points: Iterable[int] | None = None,
    atol: float = 0.0,
) -> None:
    """Raise AssertionError if `fn` uses information from rows after the evaluation row.

    For each cut c, fn(df.iloc[:c]) must equal fn(df).iloc[:c] (NaNs compared as equal).
    """
    full = fn(df).reset_index(drop=True)
    n = len(df)
    if cut_points is None:
        cut_points = sorted(
            {max(1, n // 7), max(1, n // 3), max(1, n // 2), max(1, (3 * n) // 4), max(1, n - 1)}
        )
    for c in cut_points:
        if c <= 0 or c > n:
            continue
        prefix = fn(df.iloc[:c].reset_index(drop=True)).reset_index(drop=True)
        expected = full.iloc[:c]
        if len(prefix) != len(expected):
            raise AssertionError(f"feature length changed at cut={c}: {len(prefix)} vs {len(expected)}")
        a = prefix.to_numpy(dtype="float64", na_value=np.nan)
        b = expected.to_numpy(dtype="float64", na_value=np.nan)
        both_nan = np.isnan(a) & np.isnan(b)
        close = np.isclose(a, b, atol=atol, rtol=0.0, equal_nan=True) | both_nan
        if not close.all():
            first_bad = int(np.argmax(~close))
            raise AssertionError(
                f"lookahead detected at cut={c}: first differing row {first_bad} "
                f"(prefix={a[first_bad]!r}, full={b[first_bad]!r})"
            )


def is_causal(df: pd.DataFrame, fn: FeatureFn, **kw) -> bool:
    try:
        assert_causal(df, fn, **kw)
    except AssertionError:
        return False
    return True
