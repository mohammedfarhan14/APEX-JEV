"""Canonical Parquet persistence with manifests.

Layout under the processed root:
    <SYMBOL>_<TF>/candles.parquet
    <SYMBOL>_<TF>/manifest.json

The manifest is the provenance record: source file hash, canonical content hash, schema version,
row counts, coverage, normalisation log, and the timezone assumption.
"""

from __future__ import annotations

import json
import platform
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from apex_jev import __version__
from apex_jev.data.hashing import canonical_content_hash, sha256_file
from apex_jev.data.normalize import NormalizationLog
from apex_jev.data.schema import CANONICAL_COLUMNS, SCHEMA_VERSION, TIMEZONE_LABEL, DatasetIdentity


@dataclass(frozen=True)
class Manifest:
    dataset_id: str
    symbol: str
    timeframe: str
    schema_version: str
    timezone: str
    source_filename: str
    source_sha256: str
    source_size_bytes: int
    declared_start: str
    declared_end: str
    content_sha256: str
    rows: int
    first_ts: str
    last_ts: str
    normalization: dict
    created_at_utc: str
    apex_jev_version: str
    pandas_version: str
    pyarrow_version: str
    python_version: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def build_manifest(
    identity: DatasetIdentity, source_path: Path, df: pd.DataFrame, log: NormalizationLog
) -> Manifest:
    return Manifest(
        dataset_id=identity.dataset_id,
        symbol=identity.symbol,
        timeframe=identity.timeframe.value,
        schema_version=SCHEMA_VERSION,
        timezone=TIMEZONE_LABEL,
        source_filename=identity.source_filename,
        source_sha256=sha256_file(source_path),
        source_size_bytes=source_path.stat().st_size,
        declared_start=identity.declared_start,
        declared_end=identity.declared_end,
        content_sha256=canonical_content_hash(df),
        rows=int(len(df)),
        first_ts=str(df["ts"].iloc[0]) if len(df) else "",
        last_ts=str(df["ts"].iloc[-1]) if len(df) else "",
        normalization=log.to_dict(),
        created_at_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        apex_jev_version=__version__,
        pandas_version=pd.__version__,
        pyarrow_version=pa.__version__,
        python_version=platform.python_version(),
    )


def dataset_dir(root: str | Path, dataset_id: str) -> Path:
    return Path(root) / dataset_id


def write_dataset(root: str | Path, manifest: Manifest, df: pd.DataFrame) -> tuple[Path, Path]:
    d = dataset_dir(root, manifest.dataset_id)
    d.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(df[[*CANONICAL_COLUMNS, "line_no"]], preserve_index=False)
    meta = dict(table.schema.metadata or {})
    meta[b"apex_jev.schema_version"] = SCHEMA_VERSION.encode()
    meta[b"apex_jev.content_sha256"] = manifest.content_sha256.encode()
    meta[b"apex_jev.timezone"] = TIMEZONE_LABEL.encode()
    table = table.replace_schema_metadata(meta)
    parquet_path = d / "candles.parquet"
    pq.write_table(table, parquet_path, compression="zstd")
    manifest_path = d / "manifest.json"
    manifest_path.write_text(manifest.to_json() + "\n")
    return parquet_path, manifest_path


def read_manifest(root: str | Path, dataset_id: str) -> Manifest:
    raw = json.loads((dataset_dir(root, dataset_id) / "manifest.json").read_text())
    return Manifest(**raw)


def load_dataset(root: str | Path, dataset_id: str, verify: bool = True) -> tuple[pd.DataFrame, Manifest]:
    """Reload a canonical dataset. With verify=True the content hash is recomputed and must match."""
    manifest = read_manifest(root, dataset_id)
    df = pq.read_table(dataset_dir(root, dataset_id) / "candles.parquet").to_pandas()
    df["ts"] = df["ts"].astype("datetime64[ns]")
    if verify:
        actual = canonical_content_hash(df)
        if actual != manifest.content_sha256:
            raise ValueError(
                f"{dataset_id}: content hash mismatch "
                f"(manifest={manifest.content_sha256[:12]}..., actual={actual[:12]}...)"
            )
        if manifest.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"{dataset_id}: schema version {manifest.schema_version} != code {SCHEMA_VERSION}"
            )
    return df, manifest
