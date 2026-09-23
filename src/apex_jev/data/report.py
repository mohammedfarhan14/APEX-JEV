"""Data quality report rendering (JSON is the source of truth; Markdown is a view of it)."""

from __future__ import annotations

import json
from pathlib import Path

from apex_jev.data.checks import CheckResult


def _fmt_details(details: dict, max_len: int = 1500) -> str:
    text = json.dumps(details, indent=2, default=str)
    if len(text) > max_len:
        text = text[:max_len] + "\n... (truncated; see JSON report)"
    return text


def render_dataset_section(dataset_id: str, manifest: dict, results: list[CheckResult], overall: str) -> str:
    lines = [f"## {dataset_id}  —  overall: **{overall}**", ""]
    lines += [
        f"- source: `{manifest['source_filename']}` (sha256 `{manifest['source_sha256'][:16]}…`, "
        f"{manifest['source_size_bytes']:,} bytes)",
        f"- canonical rows: {manifest['rows']:,}  ({manifest['first_ts']} → {manifest['last_ts']})",
        f"- content sha256: `{manifest['content_sha256']}`",
        f"- schema version: {manifest['schema_version']}; timezone: `{manifest['timezone']}`",
        f"- normalization: {json.dumps(manifest['normalization'] | {'conflicting_examples': '(see JSON)'})}",
        "",
        "| check | status | summary |",
        "|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r.name} | {r.status} | {r.summary.replace('|', '/')} |")
    lines.append("")
    for r in results:
        if r.status in ("WARN", "FAIL") and r.details:
            lines += [
                f"<details><summary>{r.name} details</summary>",
                "",
                "```json",
                _fmt_details(r.details),
                "```",
                "",
                "</details>",
                "",
            ]
    return "\n".join(lines)


def render_report(
    title: str,
    generated_at: str,
    sections: list[str],
    coverage: dict,
    cross_tf: list[dict],
    notes: list[str],
) -> str:
    out = [f"# {title}", "", f"Generated: {generated_at}", ""]
    out += ["## Interpretation notes", ""]
    out += [f"- {n}" for n in notes]
    out += ["", "## Coverage", "", "| timeframe | start | end | rows |", "|---|---|---|---|"]
    for c in coverage.get("datasets", []):
        out.append(f"| {c['timeframe']} | {c['start']} | {c['end']} | {c['rows']:,} |")
    out += [
        "",
        "### Multi-timeframe tiers",
        "",
        "| tier | timeframes | start | end | span (days) | valid |",
        "|---|---|---|---|---|---|",
    ]
    for t in coverage.get("tiers", []):
        tfs = "+".join(t["timeframes"])
        out.append(
            f"| {t['tier']} | {tfs} | {t['start']} | {t['end']} | {t['span_days']:.1f} | {t['valid']} |"
        )
    out += ["", "## Cross-timeframe consistency", ""]
    if not cross_tf:
        out.append("_Not computed (fewer than two timeframes available)._")
    for x in cross_tf:
        out += [
            f"### {x['pair']}  —  {x.get('status', 'n/a')}",
            "",
            "```json",
            _fmt_details(x, 3000),
            "```",
            "",
        ]
    out += sections
    return "\n".join(out) + "\n"


def write_reports(out_dir: str | Path, stem: str, markdown: str, payload: dict) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md = out_dir / f"{stem}.md"
    js = out_dir / f"{stem}.json"
    md.write_text(markdown)
    js.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    return md, js
