#!/usr/bin/env python
# SPDX-FileCopyrightText: Copyright (c) 2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Plot the PDS-H Q9 case-study figure from pdsh JSONL output."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import statistics
from typing import Any

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(os.environ.get("TMPDIR", "/tmp")) / "sc26-workshop-gpu-polars-mpl"),
)

import matplotlib.pyplot as plt

FILE_RE = re.compile(r"pdsh_q9_(?P<label>.+)_(?P<strategy>dynamic|conservative_shuffle)_spmd(?P<gpus>\d+)\.jsonl$")

STRATEGY_LABELS = {
    "dynamic": "Dynamic",
    "conservative_shuffle": "Conservative shuffle",
}

STRATEGY_STYLE = {
    "dynamic": {"color": "#2a9d8f", "marker": "o"},
    "conservative_shuffle": {"color": "#b8b8b8", "marker": "s"},
}


def _load_latest(path: Path) -> dict[str, Any]:
    objects = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not objects:
        raise ValueError(f"no JSON records found in {path}")
    return objects[-1]


def _timings(path: Path) -> tuple[float | None, list[float]]:
    obj = _load_latest(path)
    records = obj["records"].get("9", [])
    successes = [record for record in records if record.get("status") == "success"]
    warmups = [record["duration"] for record in successes if record.get("iteration") == 0]
    hot = [record["duration"] for record in successes if record.get("iteration", 0) > 0]
    return (warmups[0] if warmups else None), hot


def _collect(input_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(input_dir.glob("pdsh_q9_*_spmd*.jsonl")):
        match = FILE_RE.match(path.name)
        if match is None:
            continue
        warmup, hot = _timings(path)
        if not hot:
            continue
        rows.append(
            {
                "path": path,
                "label": match.group("label"),
                "strategy": match.group("strategy"),
                "gpus": int(match.group("gpus")),
                "warmup": warmup,
                "hot": hot,
                "median": statistics.median(hot),
                "mean": statistics.mean(hot),
            }
        )
    if not rows:
        raise ValueError(f"no Q9 pdsh JSONL files found in {input_dir}")
    return rows


def _write_summary(rows: list[dict[str, Any]], output: Path) -> None:
    lines = [
        "# PDS-H Q9 Parsed Timing Summary",
        "",
        "All runs use iteration 0 as a cache warmup. Hot timings report iterations greater than 0.",
        "",
        "| GPUs | Strategy | Warmup (s) | Hot median (s) | Hot mean (s) | Hot values (s) | Source |",
        "|---:|---|---:|---:|---:|---|---|",
    ]
    for row in sorted(rows, key=lambda item: (item["gpus"], item["strategy"])):
        hot = ", ".join(f"{value:.4f}" for value in row["hot"])
        warmup = "" if row["warmup"] is None else f"{row['warmup']:.4f}"
        lines.append(
            "| {gpus} | {strategy} | {warmup} | {median:.4f} | {mean:.4f} | {hot} | `{source}` |".format(
                gpus=row["gpus"],
                strategy=STRATEGY_LABELS[row["strategy"]],
                warmup=warmup,
                median=row["median"],
                mean=row["mean"],
                hot=hot,
                source=row["path"].name,
            )
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")


def plot(rows: list[dict[str, Any]], output: Path, title: str | None) -> None:
    fig, ax = plt.subplots(figsize=(3.45, 2.2))
    strategies = ["dynamic", "conservative_shuffle"]
    for strategy in strategies:
        subset = sorted((row for row in rows if row["strategy"] == strategy), key=lambda row: row["gpus"])
        if not subset:
            continue
        style = STRATEGY_STYLE[strategy]
        ax.plot(
            [row["gpus"] for row in subset],
            [row["median"] for row in subset],
            marker=style["marker"],
            color=style["color"],
            label=STRATEGY_LABELS[strategy],
            linewidth=1.45,
            markersize=4.0,
        )
    ax.set_yscale("log")
    ax.set_xticks(sorted({row["gpus"] for row in rows}))
    ax.set_xlabel("GPUs")
    ax.set_ylabel("hot median runtime (s)")
    ax.grid(axis="y", color="#dddddd", linewidth=0.6, which="both")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(fontsize=6.5, frameon=False, loc="upper right")
    if title:
        ax.set_title(title, fontsize=8)
    fig.tight_layout(pad=0.35)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("--output", type=Path, default=Path("paper/figures/q9-performance.pdf"))
    parser.add_argument("--summary-output", type=Path, default=Path("experiments/results/q9-sf1000-parsed-timing-summary.md"))
    parser.add_argument("--title", default=None)
    args = parser.parse_args()

    rows = _collect(args.input_dir)
    _write_summary(rows, args.summary_output)
    plot(rows, args.output, args.title)


if __name__ == "__main__":
    main()
