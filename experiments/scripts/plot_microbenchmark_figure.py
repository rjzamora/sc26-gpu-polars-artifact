#!/usr/bin/env python
# SPDX-FileCopyrightText: Copyright (c) 2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Plot the paper microbenchmark figure from JSONL benchmark records."""

from __future__ import annotations

import argparse
from collections import defaultdict
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


CASE_ORDER_BY_BENCHMARK = {
    "join": [
        ("join", "join-small-build", "Small\nbuild"),
        ("join", "join-balanced", "Balanced\ninputs"),
    ],
    "groupby": [
        ("groupby", "groupby-low-cardinality", "Low\ncardinality"),
        ("groupby", "groupby-high-cardinality", "High\ncardinality"),
    ],
}

CASE_ORDER = [
    ("join", "join-small-build", "Join\nsmall build"),
    ("join", "join-balanced", "Join\nbalanced"),
    ("groupby", "groupby-low-cardinality", "GroupBy\nlow card."),
    ("groupby", "groupby-high-cardinality", "GroupBy\nhigh card."),
]

STRATEGIES = [
    ("dynamic", "Dynamic", "#2a9d8f"),
    ("broadcast_right", "Broadcast", "#457b9d"),
    ("tree", "Tree", "#8ab17d"),
    ("shuffle", "Shuffle", "#b8b8b8"),
]

STRATEGIES_BY_BENCHMARK = {
    "all": STRATEGIES,
    "join": [
        ("dynamic", "Dynamic", "#2a9d8f"),
        ("broadcast_right", "Broadcast", "#457b9d"),
        ("shuffle", "Shuffle", "#b8b8b8"),
    ],
    "groupby": [
        ("dynamic", "Dynamic", "#2a9d8f"),
        ("tree", "Tree", "#8ab17d"),
        ("shuffle", "Shuffle", "#b8b8b8"),
    ],
}

GPU_COUNT_RE = re.compile(r"(?:ray|gpu)(\d+)")


def _load(paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        for line in path.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                rec["_source"] = str(path)
                records.append(rec)
    return records


def _gpu_count_from_source(source: str) -> int | None:
    match = GPU_COUNT_RE.search(Path(source).stem)
    return None if match is None else int(match.group(1))


def _median_successes(
    records: list[dict[str, Any]],
) -> dict[tuple[str, str, str], float]:
    groups: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for rec in records:
        if rec.get("warmup") or rec.get("status") != "success":
            continue
        key = (rec["benchmark"], rec.get("case", "default"), rec["strategy"])
        groups[key].append(float(rec["duration_s"]))
    return {key: statistics.median(values) for key, values in groups.items()}


def _error_labels(records: list[dict[str, Any]]) -> dict[tuple[str, str, str], str]:
    labels: dict[tuple[str, str, str], str] = {}
    for rec in records:
        if rec.get("warmup") or rec.get("status") != "error":
            continue
        key = (rec["benchmark"], rec.get("case", "default"), rec["strategy"])
        traceback_text = rec.get("traceback", "").lower()
        if (
            "out_of_memory" in traceback_text
            or "out of memory" in traceback_text
            or "cudaerrormemoryallocation" in traceback_text
            or "oom" in traceback_text
        ):
            labels[key] = "OOM"
        else:
            labels.setdefault(key, "fail")
    return labels


def _write_summary(
    output: Path,
    medians: dict[tuple[str, str, str], float],
    error_labels: dict[tuple[str, str, str], str],
    case_order: list[tuple[str, str, str]],
    strategies: list[tuple[str, str, str]],
) -> None:
    lines = [
        "| Benchmark | Case | Strategy | Median (s) | Relative to dynamic | Error |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for benchmark, case, _label in case_order:
        dynamic = medians.get((benchmark, case, "dynamic"))
        for strategy, _name, _color in strategies:
            key = (benchmark, case, strategy)
            if key not in medians and key not in error_labels:
                continue
            median = medians.get(key)
            relative = median / dynamic if median is not None and dynamic else None
            lines.append(
                "| {benchmark} | {case} | {strategy} | {median} | {relative} | "
                "{errors} |".format(
                    benchmark=benchmark,
                    case=case,
                    strategy=strategy,
                    median="" if median is None else f"{median:.4f}",
                    relative="" if relative is None else f"{relative:.4f}",
                    errors=error_labels.get(key, ""),
                )
            )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")


def _median_successes_by_gpu(
    records: list[dict[str, Any]],
) -> tuple[dict[tuple[int, str, str, str], float], dict[tuple[int, str, str, str], int]]:
    groups: dict[tuple[int, str, str, str], list[float]] = defaultdict(list)
    for rec in records:
        if rec.get("warmup") or rec.get("status") != "success":
            continue
        gpu_count = _gpu_count_from_source(rec["_source"])
        if gpu_count is None:
            continue
        key = (
            gpu_count,
            rec["benchmark"],
            rec.get("case", "default"),
            rec["strategy"],
        )
        groups[key].append(float(rec["duration_s"]))
    medians = {key: statistics.median(values) for key, values in groups.items()}
    counts = {key: len(values) for key, values in groups.items()}
    return medians, counts


def _error_labels_by_gpu(
    records: list[dict[str, Any]],
) -> dict[tuple[int, str, str, str], str]:
    labels: dict[tuple[int, str, str, str], str] = {}
    for rec in records:
        if rec.get("warmup") or rec.get("status") != "error":
            continue
        gpu_count = _gpu_count_from_source(rec["_source"])
        if gpu_count is None:
            continue
        key = (
            gpu_count,
            rec["benchmark"],
            rec.get("case", "default"),
            rec["strategy"],
        )
        traceback_text = rec.get("traceback", "").lower()
        if (
            "out_of_memory" in traceback_text
            or "out of memory" in traceback_text
            or "cudaerrormemoryallocation" in traceback_text
            or "oom" in traceback_text
        ):
            labels[key] = "OOM"
        else:
            labels.setdefault(key, "fail")
    return labels


def _write_scaling_summary(
    output: Path,
    medians: dict[tuple[int, str, str, str], float],
    counts: dict[tuple[int, str, str, str], int],
    error_labels: dict[tuple[int, str, str, str], str],
    case_order: list[tuple[str, str, str]],
    strategies: list[tuple[str, str, str]],
) -> None:
    gpu_counts = sorted({key[0] for key in medians} | {key[0] for key in error_labels})
    lines = [
        "| GPUs | Benchmark | Case | Strategy | Median (s) | Relative to dynamic | Successes | Error |",
        "|---:|---|---|---|---:|---:|---:|---|",
    ]
    for gpu_count in gpu_counts:
        for benchmark, case, _label in case_order:
            dynamic = medians.get((gpu_count, benchmark, case, "dynamic"))
            for strategy, _name, _color in strategies:
                key = (gpu_count, benchmark, case, strategy)
                if key not in medians and key not in error_labels:
                    continue
                median = medians.get(key)
                relative = median / dynamic if median is not None and dynamic else None
                lines.append(
                    "| {gpu_count} | {benchmark} | {case} | {strategy} | "
                    "{median} | {relative} | {count} | {errors} |".format(
                        gpu_count=gpu_count,
                        benchmark=benchmark,
                        case=case,
                        strategy=strategy,
                        median="" if median is None else f"{median:.4f}",
                        relative="" if relative is None else f"{relative:.4f}",
                        count=counts.get(key, 0),
                        errors=error_labels.get(key, ""),
                    )
                )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")


def plot_scaling(
    records: list[dict[str, Any]],
    *,
    output: Path,
    summary_output: Path | None,
    title: str | None,
    benchmark: str,
) -> None:
    if benchmark == "all":
        raise ValueError("scaling plots should be generated per benchmark")

    medians, counts = _median_successes_by_gpu(records)
    error_labels = _error_labels_by_gpu(records)
    case_order = CASE_ORDER_BY_BENCHMARK[benchmark]
    strategies = STRATEGIES_BY_BENCHMARK[benchmark]
    gpu_counts = sorted({key[0] for key in medians} | {key[0] for key in error_labels})
    if not gpu_counts:
        raise ValueError("could not infer GPU counts from input filenames")

    if summary_output is not None:
        _write_scaling_summary(
            summary_output,
            medians,
            counts,
            error_labels,
            case_order,
            strategies,
        )

    fig, axes = plt.subplots(
        nrows=len(case_order),
        ncols=1,
        figsize=(3.45, 3.0),
        sharex=True,
    )
    if len(case_order) == 1:
        axes = [axes]

    markers = ["o", "s", "^", "D"]
    for ax, (case_benchmark, case, label) in zip(axes, case_order, strict=True):
        for (strategy, name, color), marker in zip(strategies, markers):
            x_values: list[int] = []
            y_values: list[float] = []
            for gpu_count in gpu_counts:
                key = (gpu_count, case_benchmark, case, strategy)
                if key in medians:
                    x_values.append(gpu_count)
                    y_values.append(medians[key])
            if y_values:
                ax.plot(
                    x_values,
                    y_values,
                    marker=marker,
                    label=name,
                    color=color,
                    linewidth=1.35,
                    markersize=3.6,
                )
            for gpu_count in gpu_counts:
                key = (gpu_count, case_benchmark, case, strategy)
                if key not in medians and key in error_labels:
                    ax.text(
                        gpu_count,
                        0.05,
                        error_labels[key],
                        ha="center",
                        va="bottom",
                        rotation=90,
                        fontsize=6.5,
                        color="#e76f51",
                    )

        ax.set_title(label.replace("\n", " "), fontsize=8, pad=2.0)
        ax.set_ylabel("seconds")
        ax.set_xticks(gpu_counts)
        ax.grid(axis="y", color="#dddddd", linewidth=0.6)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    axes[-1].set_xlabel("GPUs")
    axes[0].legend(fontsize=6.5, frameon=False, ncol=len(strategies), loc="upper right")
    if title:
        fig.suptitle(title, fontsize=8, y=1.0)
    fig.tight_layout(pad=0.35, h_pad=0.75)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def plot(
    records: list[dict[str, Any]],
    *,
    output: Path,
    summary_output: Path | None,
    title: str | None,
    benchmark: str,
) -> None:
    medians = _median_successes(records)
    error_labels = _error_labels(records)
    case_order = (
        CASE_ORDER
        if benchmark == "all"
        else CASE_ORDER_BY_BENCHMARK[benchmark]
    )
    strategies = STRATEGIES_BY_BENCHMARK[benchmark]

    if summary_output is not None:
        _write_summary(summary_output, medians, error_labels, case_order, strategies)

    fig, ax = plt.subplots(figsize=(3.45, 2.2))
    width = 0.22 if benchmark != "all" else 0.18
    offsets = [
        (index - (len(strategies) - 1) / 2) * width
        for index in range(len(strategies))
    ]
    x_positions = list(range(len(case_order)))

    for offset, (strategy, name, color) in zip(offsets, strategies, strict=True):
        bar_x: list[float] = []
        heights: list[float] = []
        labels: list[str] = []
        for i, (case_benchmark, case, _label) in enumerate(case_order):
            key = (case_benchmark, case, strategy)
            dynamic = medians.get((case_benchmark, case, "dynamic"))
            if key in medians and dynamic:
                bar_x.append(i + offset)
                heights.append(medians[key] / dynamic)
                labels.append("")
            elif error_labels.get(key):
                bar_x.append(i + offset)
                heights.append(0.04)
                labels.append(error_labels[key])
        if bar_x:
            bars = ax.bar(
                bar_x,
                heights,
                width,
                label=name,
                color=color,
                edgecolor="#222222",
                linewidth=0.4,
            )
            for bar, label in zip(bars, labels, strict=True):
                if label:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        0.08,
                        label,
                        ha="center",
                        va="bottom",
                        rotation=90,
                        fontsize=6.5,
                        color="#e76f51",
                    )

    ax.axhline(1.0, color="#333333", linewidth=0.7)
    ax.set_xticks(x_positions)
    ax.set_xticklabels([label for _benchmark, _case, label in case_order])
    ax.set_ylabel("runtime / dynamic")
    ax.set_ylim(0, 1.45)
    ax.grid(axis="y", color="#dddddd", linewidth=0.6)
    ax.legend(fontsize=6.5, frameon=False, ncol=2, loc="upper left")
    if title:
        ax.set_title(title, fontsize=8)
    fig.tight_layout(pad=0.35)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("paper/figures/microbenchmark-results.pdf"),
    )
    parser.add_argument("--summary-output", type=Path, default=None)
    parser.add_argument("--title", default=None)
    parser.add_argument(
        "--scaling",
        action="store_true",
        help="Plot median runtime by inferred GPU count instead of normalized bars.",
    )
    parser.add_argument(
        "--benchmark",
        choices=["all", "join", "groupby"],
        default="all",
        help="Subset of paper microbenchmark cases to plot.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    records = _load(args.inputs)
    if args.scaling:
        plot_scaling(
            records,
            output=args.output,
            summary_output=args.summary_output,
            title=args.title,
            benchmark=args.benchmark,
        )
    else:
        plot(
            records,
            output=args.output,
            summary_output=args.summary_output,
            title=args.title,
            benchmark=args.benchmark,
        )


if __name__ == "__main__":
    main()
