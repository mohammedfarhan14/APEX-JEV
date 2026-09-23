"""Level 0 pipeline: raw MT5 CSV -> canonical Parquet + manifest + quality report."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from apex_jev.data import cross_tf
from apex_jev.data.checks import CheckResult, run_all_checks, worst_status
from apex_jev.data.coverage import coverage_of, coverage_tiers
from apex_jev.data.io_csv import load_mt5_csv
from apex_jev.data.normalize import to_canonical
from apex_jev.data.report import render_dataset_section, render_report, write_reports
from apex_jev.data.schema import Timeframe, parse_identity
from apex_jev.data.store import Manifest, build_manifest, load_dataset, write_dataset

INTERPRETATION_NOTES = [
    "Timestamps are candle OPEN times in broker server time, kept naive (ASSUMPTION: offset unverified).",
    "A gap is classified, not judged: weekend/daily_break gaps are expected for XAUUSD CFD feeds; "
    "'extended' gaps require manual review before being called defects.",
    "SPREAD is in MT5 points; the point size for this broker/instrument must be confirmed before "
    "converting to price units.",
    "VOL (real volume) is typically zero for CFD/spot metals; TICKVOL is the usable activity proxy.",
    "Cross-timeframe mismatches are reported, never repaired. Only complete lower-TF buckets are compared.",
    "The final bar of an MT5 export is the bar that was forming at export time and may be incomplete; "
    "consumers should treat the last bar of every dataset as provisional.",
    "FAIL means untrustworthy for research as-is; WARN means documented anomalies; PASS/INFO need no action.",
]


def ingest_file(csv_path: Path, processed_root: Path) -> tuple[Manifest, pd.DataFrame, list[CheckResult]]:
    identity = parse_identity(csv_path)
    raw = load_mt5_csv(csv_path)
    canon, log = to_canonical(raw)
    manifest = build_manifest(identity, csv_path, canon, log)
    write_dataset(processed_root, manifest, canon)
    results = run_all_checks(canon, identity.timeframe)
    # Reload and verify the hash so the manifest is proven, not assumed.
    reloaded, _ = load_dataset(processed_root, identity.dataset_id, verify=True)
    if len(reloaded) != len(canon):
        raise RuntimeError(f"{identity.dataset_id}: reload row count mismatch")
    return manifest, canon, results


def run_pipeline(
    raw_dir: Path, processed_root: Path, report_dir: Path, report_stem: str | None = None
) -> dict:
    csvs = sorted(p for p in Path(raw_dir).glob("*.csv"))
    if not csvs:
        raise FileNotFoundError(f"no CSV files in {raw_dir}")
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    frames: dict[Timeframe, pd.DataFrame] = {}
    datasets: dict[str, dict] = {}
    sections: list[str] = []
    overall_statuses: dict[str, str] = {}
    for p in csvs:
        manifest, canon, results = ingest_file(p, processed_root)
        tf = Timeframe(manifest.timeframe)
        frames[tf] = canon
        overall = worst_status(results)
        overall_statuses[manifest.dataset_id] = overall
        datasets[manifest.dataset_id] = {
            "manifest": asdict(manifest),
            "overall": overall,
            "checks": [r.to_dict() for r in results],
        }
        sections.append(render_dataset_section(manifest.dataset_id, asdict(manifest), results, overall))

    covs = {tf: coverage_of(df, tf) for tf, df in frames.items()}
    coverage = {"datasets": [c.to_dict() for c in covs.values()], "tiers": coverage_tiers(covs)}

    xtf: list[dict] = []
    pairs = [(Timeframe.M15, Timeframe.M30), (Timeframe.M30, Timeframe.H1), (Timeframe.M15, Timeframe.H1)]
    for lo, hi in pairs:
        if lo in frames and hi in frames:
            xtf.append(cross_tf.compare(frames[lo], lo, frames[hi], hi))

    payload = {
        "title": "APEX-JEV Level 0 data quality report",
        "generated_at_utc": generated_at,
        "notes": INTERPRETATION_NOTES,
        "datasets": datasets,
        "coverage": coverage,
        "cross_timeframe": xtf,
        "overall": overall_statuses,
    }
    md = render_report(payload["title"], generated_at, sections, coverage, xtf, INTERPRETATION_NOTES)
    stem = report_stem or f"data_quality_{generated_at[:10]}"
    md_path, js_path = write_reports(report_dir, stem, md, payload)
    payload["report_paths"] = {"markdown": str(md_path), "json": str(js_path)}
    return payload
