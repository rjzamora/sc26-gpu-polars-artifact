#!/usr/bin/env python
# SPDX-FileCopyrightText: Copyright (c) 2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Plot the PDS-H Q9 dynamic-decision figure from the markdown summary."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(os.environ.get("TMPDIR", "/tmp")) / "sc26-workshop-gpu-polars-mpl"),
)

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


ACCENT = "#2a9d8f"
EDGE = "#8a8a8a"
TEXT = "#2f2f2f"
PALE = "#eaf5f3"


def _parse_markdown(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in path.read_text().splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells[:1] == ["IR id"]:
            continue
        if len(cells) != 6:
            continue
        rows.append(
            {
                "operator": cells[1],
                "keys": cells[2].strip("`"),
                "decision": cells[3],
                "rows": cells[4],
                "chunks": cells[5],
            }
        )
    if not rows:
        raise ValueError(f"no decision rows found in {path}")
    return rows


def _decision_label(decision: str) -> str:
    return {
        "broadcast_left": "Broadcast left",
        "broadcast_right": "Broadcast right",
        "tree_local": "Tree reduction",
    }.get(decision, decision.replace("_", " "))


def _format_keys(keys: str) -> str:
    keys = keys.replace("'", "").replace("[", "").replace("]", "")
    return keys.replace(",", ", ")


def _format_rows(rows: str) -> str:
    value = int(rows)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M rows"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K rows"
    return f"{value:,} rows"


def _box(ax, *, x: float, y: float, width: float, height: float, row: dict[str, str]) -> None:
    patch = FancyBboxPatch(
        (x - width / 2, y - height / 2),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=0.85,
        facecolor=PALE,
        edgecolor=ACCENT,
    )
    ax.add_patch(patch)

    left = x - width / 2 + 0.030
    right = x + width / 2 - 0.030
    top = y + height * 0.22
    bottom = y - height * 0.25

    ax.text(
        left,
        top,
        row["operator"],
        ha="left",
        va="center",
        color=TEXT,
        fontsize=6.7,
        fontweight="bold",
    )
    ax.text(
        right,
        top,
        _decision_label(row["decision"]),
        ha="right",
        va="center",
        color=ACCENT,
        fontsize=6.1,
        fontweight="bold",
    )
    ax.text(
        left,
        bottom,
        _format_keys(row["keys"]),
        ha="left",
        va="center",
        color=TEXT,
        fontsize=4.9,
    )
    ax.text(
        right,
        bottom,
        _format_rows(row["rows"]),
        ha="right",
        va="center",
        color=TEXT,
        fontsize=5.3,
    )


def plot(rows: list[dict[str, str]], output: Path) -> None:
    fig, ax = plt.subplots(figsize=(3.45, 3.05))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.5,
        0.965,
        "PDS-H Q9 dynamic decisions",
        ha="center",
        va="center",
        fontsize=8.0,
        fontweight="bold",
        color=TEXT,
    )

    y_positions = [0.86, 0.708, 0.556, 0.404, 0.252, 0.100]
    box_width = 0.90
    box_height = 0.100

    for row, y in zip(rows, y_positions, strict=True):
        _box(ax, x=0.5, y=y, width=box_width, height=box_height, row=row)
        if y != y_positions[-1]:
            y_next = y_positions[y_positions.index(y) + 1]
            arrow_x = 0.5
            start = y - box_height / 2
            end = y_next + box_height * 0.30
            ax.plot([arrow_x, arrow_x], [start, end], color=EDGE, linewidth=0.85)
            ax.plot(
                [arrow_x],
                [end],
                marker="v",
                markersize=3.5,
                color=EDGE,
                markeredgewidth=0.0,
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", pad_inches=0.005)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        type=Path,
        default=Path("experiments/results/q9-sf1000-dynamic-decisions.md"),
        nargs="?",
    )
    parser.add_argument("--output", type=Path, default=Path("paper/figures/q9-plan-decisions.pdf"))
    args = parser.parse_args()

    plot(_parse_markdown(args.input), args.output)


if __name__ == "__main__":
    main()
