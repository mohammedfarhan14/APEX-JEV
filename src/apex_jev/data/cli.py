"""Command line entry point: `apex-data ingest|verify`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from apex_jev.data.pipeline import run_pipeline
from apex_jev.data.store import load_dataset


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="apex-data", description="APEX-JEV Level 0 data foundation")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ing = sub.add_parser("ingest", help="raw MT5 CSVs -> canonical Parquet + manifests + quality report")
    ing.add_argument("--raw", default="data/raw", type=Path)
    ing.add_argument("--processed", default="data/processed", type=Path)
    ing.add_argument("--reports", default="reports/data_quality", type=Path)
    ing.add_argument("--stem", default=None, help="report file stem (default: data_quality_<date>)")

    ver = sub.add_parser("verify", help="reload canonical datasets and verify content hashes")
    ver.add_argument("--processed", default="data/processed", type=Path)
    ver.add_argument("datasets", nargs="*", help="dataset ids (default: all under --processed)")

    args = ap.parse_args(argv)
    if args.cmd == "ingest":
        payload = run_pipeline(args.raw, args.processed, args.reports, args.stem)
        print(json.dumps({"overall": payload["overall"], "reports": payload["report_paths"]}, indent=2))
        return 0 if all(s != "FAIL" for s in payload["overall"].values()) else 1

    ids = args.datasets or sorted(p.name for p in args.processed.iterdir() if (p / "manifest.json").exists())
    rc = 0
    for ds in ids:
        try:
            df, m = load_dataset(args.processed, ds, verify=True)
            print(f"{ds}: OK rows={len(df)} content_sha256={m.content_sha256[:16]}...")
        except Exception as e:  # noqa: BLE001 - report every dataset, fail at the end
            print(f"{ds}: FAIL {e}", file=sys.stderr)
            rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
