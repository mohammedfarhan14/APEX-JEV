from __future__ import annotations

import pandas as pd
import pytest

from apex_jev.data.io_csv import RawSchemaError, load_mt5_csv, parse_timestamps
from apex_jev.data.normalize import to_canonical
from apex_jev.data.schema import CANONICAL_COLUMNS, Timeframe, parse_identity
from tests.conftest import HEADER, mt5_name, synthetic_candles, write_mt5_csv


def test_parse_identity_from_filename():
    ident = parse_identity("XAUUSD_M30_201801240100_202607280400.csv")
    assert ident.symbol == "XAUUSD"
    assert ident.timeframe is Timeframe.M30
    assert ident.declared_start == "201801240100"
    assert ident.dataset_id == "XAUUSD_M30"


def test_parse_identity_rejects_unknown():
    with pytest.raises(ValueError):
        parse_identity("gold.csv")


def test_load_roundtrip(tmp_path, h1):
    p = write_mt5_csv(tmp_path / mt5_name("XAUUSD", Timeframe.H1, h1), h1)
    raw = load_mt5_csv(p)
    assert list(raw.columns) == [
        "line_no",
        "DATE",
        "TIME",
        "OPEN",
        "HIGH",
        "LOW",
        "CLOSE",
        "TICKVOL",
        "VOL",
        "SPREAD",
    ]
    assert len(raw) == len(h1)
    assert raw["line_no"].iloc[0] == 2
    ts = parse_timestamps(raw)
    assert (ts.to_numpy() == h1["ts"].to_numpy()).all()


def test_header_mismatch_is_rejected(tmp_path):
    p = tmp_path / "XAUUSD_H1_202401010000_202401020000.csv"
    p.write_text("Date,Open,High,Low,Close\n2024.01.01,1,2,0,1\n")
    with pytest.raises(RawSchemaError):
        load_mt5_csv(p)


def test_bom_and_comma_delimiter_tolerated(tmp_path):
    p = tmp_path / "XAUUSD_H1_202401010000_202401020000.csv"
    p.write_text("\ufeff" + HEADER.replace("\t", ",") + "\n2024.01.01,01:00:00,1.0,2.0,0.5,1.5,10,0,20\n")
    raw = load_mt5_csv(p)
    assert len(raw) == 1 and raw["CLOSE"].iloc[0] == 1.5


def test_canonical_dtypes_and_order(h1):
    raw = _raw_from(h1)
    canon, log = to_canonical(raw)
    assert list(canon.columns) == [*CANONICAL_COLUMNS, "line_no"]
    assert str(canon["ts"].dtype) == "datetime64[ns]"
    assert canon["ts"].is_monotonic_increasing and canon["ts"].is_unique
    assert log.rows_in == log.rows_out == len(h1)
    assert log.exact_duplicates_removed == 0 and not log.reordered


def test_normalize_handles_unsorted_exact_and_conflicting_duplicates(h1):
    shuffled = h1.sample(frac=1.0, random_state=0).reset_index(drop=True)
    exact_dup = h1.iloc[[5]]
    conflict = h1.iloc[[7]].copy()
    conflict["close"] = conflict["close"] + 1.0
    raw = _raw_from(pd.concat([shuffled, exact_dup, conflict], ignore_index=True))
    canon, log = to_canonical(raw)
    assert log.reordered
    assert log.exact_duplicates_removed == 1
    assert log.conflicting_duplicate_groups == 1
    assert log.conflicting_duplicate_rows_removed == 1
    assert len(canon) == len(h1)
    # first occurrence in file order wins: the original row 7 appears in `shuffled` before the conflict
    kept = canon.loc[canon["ts"] == h1["ts"].iloc[7], "close"].iloc[0]
    assert kept == h1["close"].iloc[7]
    assert (
        log.conflicting_examples[0]["rows"][0]["line_no"] < log.conflicting_examples[0]["rows"][1]["line_no"]
    )


def test_normalize_drops_and_counts_bad_rows(tmp_path, h1):
    extra = ["2024.13.45\t01:00:00\t1\t1\t1\t1\t1\t0\t1", "2024.02.05\t01:00:00\t\t1\t1\t1\t1\t0\t1"]
    p = write_mt5_csv(tmp_path / mt5_name("XAUUSD", Timeframe.H1, h1), h1, extra_lines=extra)
    canon, log = to_canonical(load_mt5_csv(p))
    assert log.dropped_unparseable_timestamp == 1
    assert log.dropped_nan_ohlc == 1
    assert len(canon) == len(h1)


def _raw_from(df: pd.DataFrame) -> pd.DataFrame:
    raw = pd.DataFrame(
        {
            "line_no": range(2, len(df) + 2),
            "DATE": df["ts"].dt.strftime("%Y.%m.%d").astype("string"),
            "TIME": df["ts"].dt.strftime("%H:%M:%S").astype("string"),
            "OPEN": df["open"],
            "HIGH": df["high"],
            "LOW": df["low"],
            "CLOSE": df["close"],
            "TICKVOL": df["tick_volume"].astype("Int64"),
            "VOL": df["volume"].astype("Int64"),
            "SPREAD": df["spread"].astype("Int64"),
        }
    )
    return raw


def test_synthetic_generator_is_deterministic():
    a = synthetic_candles(Timeframe.M15, "2024-01-01", 1, seed=9)
    b = synthetic_candles(Timeframe.M15, "2024-01-01", 1, seed=9)
    pd.testing.assert_frame_equal(a, b)
