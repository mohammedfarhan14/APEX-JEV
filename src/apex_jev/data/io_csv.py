"""Reading MetaTrader 5 bar exports.

The loader is deliberately strict: it refuses files whose header does not match the documented
MT5 layout rather than guessing. Anything unexpected is a DATA ISSUE to be documented, not patched.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from apex_jev.data.schema import RAW_COLUMNS


class RawSchemaError(ValueError):
    pass


def _sniff_delimiter(header_line: str) -> str:
    if "\t" in header_line:
        return "\t"
    for cand in (",", ";"):
        if cand in header_line:
            return cand
    return "\t"


def read_header(path: str | Path) -> tuple[list[str], str]:
    """Return (normalised column names, delimiter) from the first line of the file."""
    with open(path, encoding="utf-8-sig") as fh:
        first = fh.readline().rstrip("\r\n")
    delim = _sniff_delimiter(first)
    cols = [c.strip().strip("<>").upper() for c in next(csv.reader([first], delimiter=delim))]
    return cols, delim


def load_mt5_csv(path: str | Path) -> pd.DataFrame:
    """Load an MT5 export as-is (string DATE/TIME preserved, numeric columns typed).

    Returns a frame with exactly RAW_COLUMNS plus a `line_no` column (1-based data line number in the
    source file) so that every anomaly can be traced back to the file.
    """
    path = Path(path)
    cols, delim = read_header(path)
    if tuple(cols) != RAW_COLUMNS:
        raise RawSchemaError(f"{path.name}: header {cols} does not match expected {list(RAW_COLUMNS)}")

    df = pd.read_csv(
        path,
        sep=delim,
        header=0,
        names=list(RAW_COLUMNS),
        dtype={"DATE": "string", "TIME": "string"},
        encoding="utf-8-sig",
        na_values=[""],
        keep_default_na=False,
    )
    df.insert(0, "line_no", range(2, len(df) + 2))
    for c in ("OPEN", "HIGH", "LOW", "CLOSE"):
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    for c in ("TICKVOL", "VOL", "SPREAD"):
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    return df


def parse_timestamps(df: pd.DataFrame) -> pd.Series:
    """Combine DATE (yyyy.mm.dd) and TIME (HH:MM:SS) into a naive datetime64[ns] Series.

    Unparseable rows become NaT and are reported downstream; they are never silently dropped here.
    """
    combined = df["DATE"].fillna("") + " " + df["TIME"].fillna("")
    ts = pd.to_datetime(combined, format="%Y.%m.%d %H:%M:%S", errors="coerce")
    return ts.astype("datetime64[ns]")
