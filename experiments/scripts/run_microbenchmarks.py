#!/usr/bin/env python
"""Run simple dynamic-planning microbenchmarks for the paper.

The benchmark inputs are synthetic Parquet shards. Keeping the data in Parquet
exercises the streaming scan and partitioned actor graph paths we care about for
the paper, while still making the benchmark self-contained.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import time
import traceback
from typing import Any, Iterator

import numpy as np
import polars as pl


DEFAULT_OUTPUT = Path("experiments/results/microbenchmarks.jsonl")
DEFAULT_DATA_DIR = Path("experiments/results/generated/microbenchmarks")


@dataclasses.dataclass(frozen=True)
class Preset:
    """Default scale for a benchmark run."""

    rows: int
    left_rows: int
    right_rows: int
    key_cardinality: int
    partitions: int
    payload_columns: int


@dataclasses.dataclass(frozen=True)
class BenchParams:
    """Resolved data-generation parameters."""

    rows: int
    left_rows: int
    right_rows: int
    key_cardinality: int
    partitions: int
    payload_columns: int


@dataclasses.dataclass(frozen=True)
class Case:
    """Named benchmark case with a specific dynamic-planning story."""

    benchmark: str
    description: str
    strategies: tuple[str, ...]


PRESETS: dict[str, Preset] = {
    "smoke": Preset(
        rows=100_000,
        left_rows=200_000,
        right_rows=20_000,
        key_cardinality=20_000,
        partitions=8,
        payload_columns=2,
    ),
    "medium": Preset(
        rows=2_000_000,
        left_rows=4_000_000,
        right_rows=200_000,
        key_cardinality=200_000,
        partitions=32,
        payload_columns=4,
    ),
    "large": Preset(
        rows=100_000_000,
        left_rows=100_000_000,
        right_rows=1_000_000,
        key_cardinality=10_000_000,
        partitions=256,
        payload_columns=1,
    ),
    "paper-large": Preset(
        rows=1_000_000_000,
        left_rows=1_000_000_000,
        right_rows=1_000_000,
        key_cardinality=100_000_000,
        partitions=512,
        payload_columns=1,
    ),
}


CASES: dict[str, Case] = {
    "groupby-low-cardinality": Case(
        benchmark="groupby",
        description="Large input with compact groupby output, where tree should be viable.",
        strategies=("dynamic", "tree", "shuffle"),
    ),
    "groupby-mid-cardinality": Case(
        benchmark="groupby",
        description="Groupby output near the target-partition-size boundary.",
        strategies=("dynamic", "tree", "shuffle"),
    ),
    "groupby-high-cardinality": Case(
        benchmark="groupby",
        description="High-cardinality groupby output, where shuffle should be favored.",
        strategies=("dynamic", "shuffle", "tree"),
    ),
    "distinct-low-cardinality": Case(
        benchmark="distinct",
        description="Large input with compact distinct output, where tree should be viable.",
        strategies=("dynamic", "tree", "shuffle"),
    ),
    "distinct-high-cardinality": Case(
        benchmark="distinct",
        description="High-cardinality distinct output, where shuffle should be favored.",
        strategies=("dynamic", "shuffle", "tree"),
    ),
    "join-tiny-build": Case(
        benchmark="join",
        description="Large probe side and tiny build side, where broadcast should win.",
        strategies=("dynamic", "broadcast_right", "shuffle"),
    ),
    "join-small-build": Case(
        benchmark="join",
        description="Large probe side and small build side, where broadcast should win.",
        strategies=("dynamic", "broadcast_right", "shuffle"),
    ),
    "join-balanced": Case(
        benchmark="join",
        description="Both join sides large, where shuffle should win.",
        strategies=("dynamic", "shuffle"),
    ),
}


def _parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _partition_bounds(nrows: int, partitions: int) -> Iterator[tuple[int, int]]:
    for part in range(partitions):
        start = (nrows * part) // partitions
        stop = (nrows * (part + 1)) // partitions
        yield start, stop


def _payload_columns(index: np.ndarray, count: int, prefix: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for i in range(count):
        payload[f"{prefix}{i}"] = (
            ((index * (17 + i * 3) + i * 101) % 10_000).astype(np.float64)
            / 100.0
        )
    return payload


def _write_shards(
    directory: Path,
    nrows: int,
    partitions: int,
    key_cardinality: int,
    payload_columns: int,
    *,
    payload_prefix: str = "v",
    key_offset: int = 0,
    seed: int = 0,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for part, (start, stop) in enumerate(_partition_bounds(nrows, partitions)):
        index = np.arange(start, stop, dtype=np.int64)
        keys = (index + key_offset + seed) % key_cardinality
        data: dict[str, Any] = {
            "k": keys.astype(np.int64),
            "row_id": index,
        }
        data.update(_payload_columns(index, payload_columns, payload_prefix))
        pl.DataFrame(data).write_parquet(directory / f"part-{part:04d}.parquet")


def _meta_matches(meta_path: Path, expected: dict[str, Any]) -> bool:
    if not meta_path.exists():
        return False
    try:
        actual = json.loads(meta_path.read_text())
    except json.JSONDecodeError:
        return False
    return actual == expected


def _ensure_dataset(
    directory: Path,
    *,
    nrows: int,
    partitions: int,
    key_cardinality: int,
    payload_columns: int,
    payload_prefix: str,
    key_offset: int,
    seed: int,
    regenerate: bool,
) -> None:
    meta = {
        "nrows": nrows,
        "partitions": partitions,
        "key_cardinality": key_cardinality,
        "payload_columns": payload_columns,
        "payload_prefix": payload_prefix,
        "key_offset": key_offset,
        "seed": seed,
    }
    meta_path = directory / "_meta.json"
    if regenerate and directory.exists():
        shutil.rmtree(directory)
    if _meta_matches(meta_path, meta):
        return
    if directory.exists():
        shutil.rmtree(directory)
    _write_shards(
        directory,
        nrows,
        partitions,
        key_cardinality,
        payload_columns,
        payload_prefix=payload_prefix,
        key_offset=key_offset,
        seed=seed,
    )
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")


def _scan(directory: Path) -> pl.LazyFrame:
    return pl.scan_parquet(str(directory / "part-*.parquet"))


def _build_groupby_query(directory: Path) -> pl.LazyFrame:
    return (
        _scan(directory)
        .group_by("k")
        .agg(
            pl.len().alias("n"),
            pl.col("v0").sum().alias("sum_v0"),
        )
        .select(
            pl.len().alias("groups"),
            pl.col("n").sum().alias("rows"),
            pl.col("sum_v0").sum().alias("sum_v0"),
        )
    )


def _build_distinct_query(directory: Path) -> pl.LazyFrame:
    return (
        _scan(directory)
        .unique(subset=["k"], maintain_order=False)
        .select(
            pl.len().alias("distinct_keys"),
            pl.col("v0").sum().alias("sum_v0"),
        )
    )


def _build_join_query(left: Path, right: Path) -> pl.LazyFrame:
    return (
        _scan(left)
        .join(_scan(right), on="k", how="inner")
        .select(
            pl.len().alias("rows"),
            pl.col("l0").sum().alias("sum_l0"),
            pl.col("r0").sum().alias("sum_r0"),
        )
    )


def _strategy_env(
    benchmark: str,
    strategy: str,
) -> dict[str, str | None]:
    env: dict[str, str | None] = {
        "CUDF_POLARS__EXPERIMENTAL__JOIN_ALGO": None,
        "CUDF_POLARS__EXPERIMENTAL__GROUPBY_ALGO": None,
    }
    if strategy in {"dynamic", "cpu"}:
        return env
    if benchmark == "join":
        env["CUDF_POLARS__EXPERIMENTAL__JOIN_ALGO"] = strategy
    elif benchmark in {"groupby", "distinct"}:
        env["CUDF_POLARS__EXPERIMENTAL__GROUPBY_ALGO"] = strategy
    else:
        raise ValueError(f"Unknown benchmark: {benchmark}")
    return env


@contextlib.contextmanager
def _patched_env(updates: dict[str, str | None]) -> Iterator[None]:
    old = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _make_executor_options(args: argparse.Namespace) -> dict[str, Any]:
    dynamic: dict[str, Any] | None
    if args.dynamic_planning:
        dynamic = {"join_prefilter_threshold": 0.0}
        if args.sample_chunk_count is not None:
            dynamic["sample_chunk_count"] = args.sample_chunk_count
        if args.enable_join_prefilter:
            dynamic.pop("join_prefilter_threshold")
    else:
        dynamic = None

    executor_options: dict[str, Any] = {
        "fallback_mode": "raise",
        "dynamic_planning": dynamic,
    }
    if args.target_partition_size is not None:
        executor_options["target_partition_size"] = args.target_partition_size
    if args.broadcast_limit is not None:
        executor_options["broadcast_limit"] = args.broadcast_limit
    return executor_options


def _make_gpu_engine(args: argparse.Namespace) -> pl.GPUEngine:
    executor_options = _make_executor_options(args)
    engine_options = {"raise_on_fail": True}
    if args.frontend == "spmd":
        from cudf_polars.engine.spmd import SPMDEngine  # noqa: PLC0415

        return SPMDEngine(
            executor_options=executor_options,
            engine_options=engine_options,
        )
    if args.frontend == "ray":
        from cudf_polars.engine.ray import RayEngine  # noqa: PLC0415

        return RayEngine(
            executor_options=executor_options,
            engine_options=engine_options,
        )
    raise ValueError(f"Unsupported frontend: {args.frontend!r}")


@contextlib.contextmanager
def _engine_context(
    args: argparse.Namespace,
    strategy: str,
) -> Iterator[pl.GPUEngine | str]:
    if strategy == "cpu":
        yield "streaming"
        return

    engine = _make_gpu_engine(args)
    with engine:
        yield engine


def _git_info(path: Path) -> dict[str, str | None]:
    if not (path / ".git").exists():
        return {"path": str(path), "branch": None, "commit": None}

    def run(*cmd: str) -> str | None:
        try:
            return subprocess.check_output(
                ["git", "-C", str(path), *cmd],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except Exception:
            return None

    return {
        "path": str(path),
        "branch": run("branch", "--show-current"),
        "commit": run("rev-parse", "HEAD"),
    }


def _versions(cudf_repo: Path) -> dict[str, Any]:
    versions: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "polars": pl.__version__,
        "cudf_repo": _git_info(cudf_repo),
    }
    try:
        import cudf_polars  # noqa: PLC0415

        versions["cudf_polars"] = getattr(cudf_polars, "__version__", None)
    except Exception as exc:
        versions["cudf_polars_import_error"] = repr(exc)
    return versions


def _default_strategies(benchmark: str) -> list[str]:
    if benchmark == "join":
        return ["dynamic", "broadcast_left", "broadcast_right", "shuffle"]
    if benchmark in {"groupby", "distinct"}:
        return ["dynamic", "tree", "shuffle"]
    raise ValueError(f"Unknown benchmark: {benchmark}")


def _valid_strategies(benchmark: str) -> set[str]:
    if benchmark == "join":
        return {"dynamic", "broadcast_left", "broadcast_right", "shuffle", "cpu"}
    if benchmark in {"groupby", "distinct"}:
        return {"dynamic", "tree", "shuffle", "cpu"}
    raise ValueError(f"Unknown benchmark: {benchmark}")


def _strategy_list(benchmark: str, requested: list[str], case_name: str) -> list[str]:
    if requested == ["default"]:
        if case_name != "default":
            return list(CASES[case_name].strategies)
        return _default_strategies(benchmark)
    valid = _valid_strategies(benchmark)
    invalid = sorted(set(requested) - valid)
    if invalid:
        raise ValueError(
            f"Invalid strategies for {benchmark}: {', '.join(invalid)}. "
            f"Valid strategies are: {', '.join(sorted(valid))}."
        )
    return requested


def _base_params(args: argparse.Namespace) -> BenchParams:
    preset = PRESETS[args.preset]
    return BenchParams(
        rows=preset.rows,
        left_rows=preset.left_rows,
        right_rows=preset.right_rows,
        key_cardinality=preset.key_cardinality,
        partitions=preset.partitions,
        payload_columns=preset.payload_columns,
    )


def _replace(params: BenchParams, **kwargs: int) -> BenchParams:
    return dataclasses.replace(params, **kwargs)


def _apply_case(params: BenchParams, case_name: str) -> BenchParams:
    if case_name == "default":
        return params

    rows = params.rows
    left_rows = params.left_rows
    case = CASES[case_name]
    if case.benchmark in {"groupby", "distinct"}:
        if case_name.endswith("low-cardinality"):
            key_cardinality = min(rows, max(1_000, rows // 10_000))
        elif case_name.endswith("mid-cardinality"):
            key_cardinality = min(rows, max(10_000, rows // 16))
        elif case_name.endswith("high-cardinality"):
            key_cardinality = rows
        else:
            raise ValueError(f"Unhandled case: {case_name}")
        return _replace(params, key_cardinality=key_cardinality)

    if case_name == "join-tiny-build":
        right_rows = min(left_rows, max(1_000, left_rows // 1_000_000))
    elif case_name == "join-small-build":
        right_rows = min(left_rows, max(1_000_000, left_rows // 1_000))
    elif case_name == "join-balanced":
        right_rows = left_rows
    else:
        raise ValueError(f"Unhandled case: {case_name}")

    # Keep keys close to one-to-one so join output size stays interpretable.
    key_cardinality = max(left_rows, right_rows)
    return _replace(
        params,
        right_rows=right_rows,
        key_cardinality=key_cardinality,
    )


def _apply_cli_overrides(params: BenchParams, args: argparse.Namespace) -> BenchParams:
    overrides = {}
    for name in (
        "rows",
        "left_rows",
        "right_rows",
        "key_cardinality",
        "partitions",
        "payload_columns",
    ):
        value = getattr(args, name)
        if value is not None:
            overrides[name] = value
    return _replace(params, **overrides) if overrides else params


def _resolve_params(args: argparse.Namespace, case_name: str) -> BenchParams:
    return _apply_cli_overrides(_apply_case(_base_params(args), case_name), args)


def _right_partitions(params: BenchParams) -> int:
    left_rows_per_partition = max(1, params.left_rows // params.partitions)
    scaled = max(1, (params.right_rows + left_rows_per_partition - 1) // left_rows_per_partition)
    return max(1, min(params.partitions, params.right_rows, scaled))


def _prepare_inputs(
    args: argparse.Namespace,
    benchmark: str,
    case_name: str,
) -> dict[str, Path]:
    params = _resolve_params(args, case_name)

    base = args.data_dir / args.preset / case_name
    if benchmark == "join":
        left = base / "join-left"
        right = base / "join-right"
        _ensure_dataset(
            left,
            nrows=params.left_rows,
            partitions=params.partitions,
            key_cardinality=params.key_cardinality,
            payload_columns=params.payload_columns,
            payload_prefix="l",
            key_offset=0,
            seed=args.seed,
            regenerate=args.regenerate,
        )
        _ensure_dataset(
            right,
            nrows=params.right_rows,
            partitions=_right_partitions(params),
            key_cardinality=params.key_cardinality,
            payload_columns=params.payload_columns,
            payload_prefix="r",
            key_offset=0,
            seed=args.seed,
            regenerate=args.regenerate,
        )
        return {"left": left, "right": right}

    directory = base / benchmark
    _ensure_dataset(
        directory,
        nrows=params.rows,
        partitions=params.partitions,
        key_cardinality=params.key_cardinality,
        payload_columns=params.payload_columns,
        payload_prefix="v",
        key_offset=0,
        seed=args.seed,
        regenerate=args.regenerate,
    )
    return {"input": directory}


def _build_query(benchmark: str, inputs: dict[str, Path]) -> pl.LazyFrame:
    if benchmark == "join":
        return _build_join_query(inputs["left"], inputs["right"])
    if benchmark == "groupby":
        return _build_groupby_query(inputs["input"])
    if benchmark == "distinct":
        return _build_distinct_query(inputs["input"])
    raise ValueError(f"Unknown benchmark: {benchmark}")


def _result_summary(df: pl.DataFrame) -> dict[str, Any]:
    return {
        "shape": list(df.shape),
        "columns": df.columns,
        "rows": df.head(3).to_dicts(),
    }


def _collect(
    q: pl.LazyFrame,
    engine: pl.GPUEngine | str,
) -> pl.DataFrame:
    return q.collect(engine=engine)


def _run_iteration(
    *,
    q: pl.LazyFrame,
    engine: pl.GPUEngine | str,
    benchmark: str,
    case_name: str,
    strategy: str,
    iteration: int,
    warmup: bool,
    args: argparse.Namespace,
    inputs: dict[str, Path],
    versions: dict[str, Any],
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = _collect(q, engine)
        duration = time.perf_counter() - started
        return {
            "status": "success",
            "benchmark": benchmark,
            "case": case_name,
            "strategy": strategy,
            "iteration": iteration,
            "warmup": warmup,
            "duration_s": duration,
            "result": _result_summary(result),
            "inputs": {key: str(value) for key, value in inputs.items()},
            "parameters": _record_parameters(args),
            "versions": versions,
        }
    except Exception:
        duration = time.perf_counter() - started
        if args.fail_fast:
            raise
        return {
            "status": "error",
            "benchmark": benchmark,
            "case": case_name,
            "strategy": strategy,
            "iteration": iteration,
            "warmup": warmup,
            "duration_s": duration,
            "traceback": traceback.format_exc(),
            "inputs": {key: str(value) for key, value in inputs.items()},
            "parameters": _record_parameters(args),
            "versions": versions,
        }


def _record_parameters(args: argparse.Namespace) -> dict[str, Any]:
    keys = [
        "preset",
        "cases",
        "rows",
        "left_rows",
        "right_rows",
        "key_cardinality",
        "partitions",
        "payload_columns",
        "frontend",
        "dynamic_planning",
        "sample_chunk_count",
        "enable_join_prefilter",
        "target_partition_size",
        "broadcast_limit",
    ]
    return {key: getattr(args, key) for key in keys}


def _record_resolved_parameters(params: BenchParams) -> dict[str, int]:
    return dataclasses.asdict(params)


def _selected_cases(args: argparse.Namespace) -> list[tuple[str, str]]:
    if args.cases == ["default"]:
        return [(benchmark, "default") for benchmark in args.benchmarks]

    selected = []
    for case_name in args.cases:
        if case_name not in CASES:
            valid = ", ".join(sorted(CASES))
            raise ValueError(f"Unknown case {case_name!r}. Valid cases: {valid}")
        case = CASES[case_name]
        if case.benchmark not in args.benchmarks:
            continue
        selected.append((case.benchmark, case_name))
    if not selected:
        raise ValueError("No benchmark cases selected.")
    return selected


def run(args: argparse.Namespace) -> None:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.data_dir.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.append else "w"
    versions = _versions(args.cudf_repo)

    with args.output.open(mode) as out:
        for benchmark, case_name in _selected_cases(args):
            params = _resolve_params(args, case_name)
            inputs = _prepare_inputs(args, benchmark, case_name)
            q = _build_query(benchmark, inputs)
            if args.explain:
                print(f"\n{benchmark} / {case_name} physical plan")
                print(q.explain())
            for strategy in _strategy_list(benchmark, args.strategies, case_name):
                env = _strategy_env(
                    benchmark,
                    strategy,
                )
                with _patched_env(env):
                    with _engine_context(args, strategy) as engine:
                        for i in range(args.warmup + args.iterations):
                            record = _run_iteration(
                                q=q,
                                engine=engine,
                                benchmark=benchmark,
                                case_name=case_name,
                                strategy=strategy,
                                iteration=i - args.warmup,
                                warmup=i < args.warmup,
                                args=args,
                                inputs=inputs,
                                versions=versions,
                            )
                            record["environment"] = {
                                key: value
                                for key, value in env.items()
                                if value is not None
                            }
                            record["resolved_parameters"] = (
                                _record_resolved_parameters(params)
                            )
                            if case_name != "default":
                                record["case_description"] = CASES[
                                    case_name
                                ].description
                            out.write(json.dumps(record, sort_keys=True) + "\n")
                            out.flush()
                            status = record["status"]
                            duration = record["duration_s"]
                            marker = "warmup" if record["warmup"] else "measure"
                            print(
                                f"{benchmark:8s} {case_name:26s} {strategy:16s} "
                                f"{marker:7s} {status:7s} {duration:.4f}s"
                            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmark",
        "--benchmarks",
        dest="benchmarks",
        type=_parse_csv,
        default=["join", "groupby", "distinct"],
        help="Comma-separated subset: join,groupby,distinct.",
    )
    parser.add_argument(
        "--strategies",
        type=_parse_csv,
        default=["default"],
        help=(
            "Comma-separated strategies. Use 'default' for dynamic plus forced "
            "strategies for each benchmark."
        ),
    )
    parser.add_argument(
        "--case",
        "--cases",
        dest="cases",
        type=_parse_csv,
        default=["default"],
        help=(
            "Comma-separated named cases. Use 'default' for the original "
            "generic benchmark shapes. Use --list-cases to inspect options."
        ),
    )
    parser.add_argument("--preset", choices=sorted(PRESETS), default="smoke")
    parser.add_argument("--rows", type=int, default=None)
    parser.add_argument("--left-rows", type=int, default=None)
    parser.add_argument("--right-rows", type=int, default=None)
    parser.add_argument("--key-cardinality", type=int, default=None)
    parser.add_argument("--partitions", type=int, default=None)
    parser.add_argument("--payload-columns", type=int, default=None)
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--append", action="store_true")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--regenerate", action="store_true")
    parser.add_argument(
        "--frontend",
        choices=["spmd", "ray"],
        default="spmd",
        help="GPU execution frontend. The 'cpu' strategy always uses Polars CPU streaming.",
    )
    parser.add_argument("--dynamic-planning", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--sample-chunk-count", type=int, default=None)
    parser.add_argument("--enable-join-prefilter", action="store_true")
    parser.add_argument("--target-partition-size", type=int, default=None)
    parser.add_argument("--broadcast-limit", type=int, default=None)
    parser.add_argument("--cudf-repo", type=Path, default=Path("../cudf"))
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--list-cases", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.list_cases:
        for name, case in sorted(CASES.items()):
            strategies = ",".join(case.strategies)
            print(f"{name}: benchmark={case.benchmark}, strategies={strategies}")
            print(f"  {case.description}")
        return
    run(args)


if __name__ == "__main__":
    main()
