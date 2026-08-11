#!/usr/bin/env python
"""Summarize microbenchmark JSONL output as Markdown."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
from typing import Any


def _load(path: Path) -> list[dict[str, Any]]:
    records = []
    for line in path.read_text().splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4f}"


def _summaries(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        if rec.get("warmup") or rec.get("status") != "success":
            continue
        groups[(rec["benchmark"], rec.get("case", "default"), rec["strategy"])].append(
            rec
        )

    rows = []
    for (benchmark, case_name, strategy), recs in sorted(groups.items()):
        durations = [float(rec["duration_s"]) for rec in recs]
        rows.append(
            {
                "benchmark": benchmark,
                "case": case_name,
                "strategy": strategy,
                "n": len(durations),
                "min_s": min(durations),
                "median_s": statistics.median(durations),
                "mean_s": statistics.mean(durations),
                "stdev_s": statistics.stdev(durations) if len(durations) > 1 else 0.0,
            }
        )

    dynamic_medians = {
        (row["benchmark"], row["case"]): row["median_s"]
        for row in rows
        if row["strategy"] == "dynamic"
    }
    for row in rows:
        baseline = dynamic_medians.get((row["benchmark"], row["case"]))
        row["relative_to_dynamic"] = (
            row["median_s"] / baseline if baseline and baseline > 0 else None
        )
    return rows


def _error_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors = []
    for rec in records:
        if rec.get("warmup") or rec.get("status") != "error":
            continue
        errors.append(
            {
                "benchmark": rec["benchmark"],
                "case": rec.get("case", "default"),
                "strategy": rec["strategy"],
                "iteration": rec["iteration"],
                "traceback": rec.get("traceback", "").splitlines()[-1:],
            }
        )
    return errors


def _markdown(rows: list[dict[str, Any]], errors: list[dict[str, Any]]) -> str:
    lines = [
        "| Benchmark | Case | Strategy | N | Min (s) | Median (s) | Mean (s) | Stdev (s) | Median / Dynamic |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {benchmark} | {case} | {strategy} | {n} | {min_s} | {median_s} | "
            "{mean_s} | {stdev_s} | {relative} |".format(
                benchmark=row["benchmark"],
                case=row["case"],
                strategy=row["strategy"],
                n=row["n"],
                min_s=_fmt(row["min_s"]),
                median_s=_fmt(row["median_s"]),
                mean_s=_fmt(row["mean_s"]),
                stdev_s=_fmt(row["stdev_s"]),
                relative=_fmt(row["relative_to_dynamic"]),
            )
        )

    if errors:
        lines.extend(["", "Errors:", ""])
        for err in errors:
            tail = err["traceback"][0] if err["traceback"] else "unknown error"
            lines.append(
                f"- {err['benchmark']} / {err['case']} / {err['strategy']} / "
                f"iteration {err['iteration']}: `{tail}`"
            )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    records = _load(args.input)
    text = _markdown(_summaries(records), _error_rows(records))
    if args.output is None:
        print(text, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)


if __name__ == "__main__":
    main()
