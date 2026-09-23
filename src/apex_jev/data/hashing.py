"""Deterministic hashes for raw files and canonical frames."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from apex_jev.data.schema import CANONICAL_COLUMNS


def sha256_file(path: str | Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def canonical_content_hash(df: pd.DataFrame) -> str:
    """Hash of the canonical column VALUES, independent of index, extra columns, or Parquet metadata.

    Two frames with identical canonical content produce identical hashes regardless of how they were
    loaded, which is what "deterministic reload" means at Level 0.
    """
    sub = df[list(CANONICAL_COLUMNS)].reset_index(drop=True)
    h = hashlib.sha256()
    h.update(",".join(CANONICAL_COLUMNS).encode())
    h.update(sub["ts"].to_numpy("datetime64[ns]").tobytes())
    for c in CANONICAL_COLUMNS[1:]:
        h.update(c.encode())
        h.update(sub[c].to_numpy().tobytes())
    return h.hexdigest()
