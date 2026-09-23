from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from apex_jev.data import cross_tf
from apex_jev.data.cli import main
from apex_jev.data.coverage import Coverage, coverage_tiers
from apex_jev.data.hashing import canonical_content_hash
from apex_jev.data.pipeline import run_pipeline
from apex_jev.data.schema import Timeframe
from apex_jev.data.store import load_dataset
from tests.conftest import synthetic_candles


def test_pipeline_end_to_end(raw_dir: Path, tmp_path: Path):
    processed = tmp_path / "processed"
    reports = tmp_path / "reports"
    payload = run_pipeline(raw_dir, processed, reports, report_stem="dq")
    assert set(payload["datasets"]) == {"XAUUSD_H1", "XAUUSD_M30", "XAUUSD_M15"}
    assert all(s in ("PASS", "WARN") for s in payload["overall"].values())
    assert (reports / "dq.md").exists() and (reports / "dq.json").exists()
    for ds in payload["datasets"]:
        assert (processed / ds / "candles.parquet").exists()
        assert (processed / ds / "manifest.json").exists()
    tiers = {t["tier"]: t for t in payload["coverage"]["tiers"]}
    assert tiers["H1_only"]["start"] < tiers["H1_M30"]["start"] < tiers["H1_M30_M15"]["start"]
    assert all(t["valid"] for t in tiers.values())
    md = (reports / "dq.md").read_text()
    assert "Multi-timeframe tiers" in md and "XAUUSD_M15" in md
    js = json.loads((reports / "dq.json").read_text())
    assert js["cross_timeframe"]


def test_deterministic_reload_and_hash(raw_dir: Path, tmp_path: Path):
    p1, p2 = tmp_path / "p1", tmp_path / "p2"
    run_pipeline(raw_dir, p1, tmp_path / "r1", report_stem="a")
    run_pipeline(raw_dir, p2, tmp_path / "r2", report_stem="b")
    for ds in ("XAUUSD_H1", "XAUUSD_M30", "XAUUSD_M15"):
        d1, m1 = load_dataset(p1, ds)
        d2, m2 = load_dataset(p2, ds)
        assert (
            m1.content_sha256 == m2.content_sha256 == canonical_content_hash(d1) == canonical_content_hash(d2)
        )
        assert m1.source_sha256 == m2.source_sha256
        pd.testing.assert_frame_equal(d1, d2)
        assert (p1 / ds / "candles.parquet").read_bytes() == (p2 / ds / "candles.parquet").read_bytes()


def test_tampered_parquet_is_detected(raw_dir: Path, tmp_path: Path):
    processed = tmp_path / "processed"
    run_pipeline(raw_dir, processed, tmp_path / "r", report_stem="x")
    df, m = load_dataset(processed, "XAUUSD_H1")
    df.loc[0, "close"] += 1
    import pyarrow as pa
    import pyarrow.parquet as pq

    pq.write_table(
        pa.Table.from_pandas(df, preserve_index=False), processed / "XAUUSD_H1" / "candles.parquet"
    )
    with pytest.raises(ValueError, match="content hash mismatch"):
        load_dataset(processed, "XAUUSD_H1")
    assert main(["verify", "--processed", str(processed)]) == 1


def test_cli_ingest_and_verify(raw_dir: Path, tmp_path: Path, capsys):
    processed = tmp_path / "processed"
    rc = main(
        [
            "ingest",
            "--raw",
            str(raw_dir),
            "--processed",
            str(processed),
            "--reports",
            str(tmp_path / "rep"),
            "--stem",
            "s",
        ]
    )
    assert rc == 0
    rc = main(["verify", "--processed", str(processed)])
    assert rc == 0
    assert "XAUUSD_H1: OK" in capsys.readouterr().out


def test_content_hash_ignores_index_and_extra_columns(h1):
    a = canonical_content_hash(h1)
    b = h1.copy()
    b.index = b.index + 100
    b["junk"] = 1
    assert canonical_content_hash(b) == a
    c = h1.copy()
    c.loc[0, "spread"] += 1
    assert canonical_content_hash(c) != a


def test_coverage_tiers_invalid_when_disjoint():
    covs = {
        Timeframe.H1: Coverage(Timeframe.H1, pd.Timestamp("2009-01-01"), pd.Timestamp("2010-01-01"), 10),
        Timeframe.M30: Coverage(Timeframe.M30, pd.Timestamp("2018-01-01"), pd.Timestamp("2026-01-01"), 10),
    }
    tiers = {t["tier"]: t for t in coverage_tiers(covs)}
    assert tiers["H1_only"]["valid"]
    assert not tiers["H1_M30"]["valid"]
    assert "H1_M30_M15" not in tiers


def test_cross_tf_aggregation_consistent_and_detects_mismatch():
    m15 = synthetic_candles(Timeframe.M15, "2024-01-01", 1, seed=4)
    h1 = cross_tf.aggregate(m15, Timeframe.M15, Timeframe.H1)
    h1["spread"] = 1
    res = cross_tf.compare(m15, Timeframe.M15, h1, Timeframe.H1)
    assert res["status"] == "PASS" and res["compared"] == len(h1) > 0
    # drop one M15 bar -> its H1 bucket is incomplete and must be skipped, not flagged
    m15_gap = m15.drop(index=10).reset_index(drop=True)
    res2 = cross_tf.compare(m15_gap, Timeframe.M15, h1, Timeframe.H1)
    assert res2["compared"] == len(h1) - 1 and res2["status"] == "PASS"
    assert res2["higher_candles_without_complete_lower_bucket"] == 1
    bad = h1.copy()
    bad.loc[3, "high"] += 5
    res3 = cross_tf.compare(m15, Timeframe.M15, bad, Timeframe.H1)
    assert res3["status"] == "WARN" and res3["mismatch_counts"]["high"] == 1


def test_missing_raw_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_pipeline(tmp_path, tmp_path / "p", tmp_path / "r")
