# Experiments

This directory tracks the scripts, configs, and summarized results used by the paper.

Suggested rule: every figure or table in the paper should point back to a script/config pair here.

## Dynamic-Planning Microbenchmarks

The first synthetic benchmark harness is:

- `scripts/run_microbenchmarks.py`: generate/reuse partitioned Parquet inputs and run join, groupby, and distinct query shapes.
- `scripts/summarize_microbenchmarks.py`: summarize JSONL output into a Markdown table.
- `scripts/plot_microbenchmark_figure.py`: generate the paper microbenchmark figure from one or more JSONL files.
- `scripts/run_paper_microbenchmarks.sh`: run the paper-cut synthetic benchmark set and regenerate the join/groupby figures.

Run these scripts from an environment with `polars`, `cudf-polars`, and the experiment-only strategy-override changes available. This is usually the RAPIDS/cudf development environment, not the minimal LaTeX `paper-env`.
For paper runs, apply the cudf patch included under `experiments/patches/`. See `env/cudf-polars-benchmark-env.md` for the environment runbook and `configs/paper-cut-b200.yaml` for the initial B200 software-stack pin.
GPU runs use `--frontend spmd` by default, which falls back to a single-rank communicator when the script is not launched under `rrun`.
Use `--frontend ray` to run through `cudf_polars.engine.ray.RayEngine`.
The `cpu` strategy uses the Polars CPU streaming engine and ignores the GPU frontend setting.

Example smoke run:

```sh
python -m experiments.scripts.run_microbenchmarks \
  --preset smoke \
  --frontend spmd \
  --iterations 3 \
  --warmup 1 \
  --output experiments/results/raw/microbenchmarks-smoke.jsonl
```

Summarize the result:

```sh
python -m experiments.scripts.summarize_microbenchmarks \
  experiments/results/raw/microbenchmarks-smoke.jsonl \
  --output experiments/results/microbenchmarks-smoke.md
```

Useful focused runs:

```sh
# Join only: dynamic vs forced broadcast/shuffle.
python -m experiments.scripts.run_microbenchmarks \
  --benchmark join \
  --strategies dynamic,broadcast_left,broadcast_right,shuffle \
  --preset medium \
  --output experiments/results/raw/join-medium.jsonl

# GroupBy/distinct only: dynamic vs forced tree/shuffle.
python -m experiments.scripts.run_microbenchmarks \
  --benchmark groupby,distinct \
  --strategies dynamic,tree,shuffle \
  --preset medium \
  --output experiments/results/raw/groupby-distinct-medium.jsonl

# Add the Polars CPU streaming engine when useful for diagnostics.
python -m experiments.scripts.run_microbenchmarks \
  --benchmark groupby \
  --case groupby-low-cardinality,groupby-high-cardinality \
  --strategies dynamic,tree,shuffle,cpu \
  --preset medium \
  --output experiments/results/raw/groupby-medium-with-cpu.jsonl
```

By default the runner disables the join-domain prefilter via dynamic-planning options, because that optimization is not part of the dynamic-planning story for this paper. Pass `--enable-join-prefilter` only for diagnostic runs.

Named cases separate the data-shape story from the data scale. Inspect them with:

```sh
python -m experiments.scripts.run_microbenchmarks --list-cases
```

Recommended first large synthetic sweeps:

```sh
# Before paper-large, use this to check runtime, disk footprint, and decisions.
python -m experiments.scripts.run_microbenchmarks \
  --preset large \
  --case groupby-low-cardinality,groupby-mid-cardinality,groupby-high-cardinality \
  --iterations 3 \
  --warmup 1 \
  --output experiments/results/raw/groupby-large.jsonl

python -m experiments.scripts.run_microbenchmarks \
  --preset large \
  --case join-tiny-build,join-small-build,join-balanced \
  --iterations 3 \
  --warmup 1 \
  --output experiments/results/raw/join-large.jsonl
```

Once the cases look right, repeat with `--preset paper-large`. The `paper-large`
preset uses 1B-row synthetic inputs for the main side of each benchmark. It is
intended for final numbers on 1, 2, 4, and 8 GPUs, not quick iteration.

## Paper-Cut Microbenchmark Set

Keep the main paper focused on one broadcast-favored join, one shuffle-favored
join, one tree-favored groupby, and one shuffle-favored groupby.
`join-tiny-build` is useful for diagnostics, but `join-small-build` is the
better main-paper broadcast case.

Suggested 1-GPU collection commands:

```sh
python -m experiments.scripts.run_microbenchmarks \
  --preset paper-large \
  --case join-small-build \
  --strategies dynamic,broadcast_right,shuffle \
  --iterations 5 \
  --warmup 1 \
  --output experiments/results/raw/join-small-build-paper-large.jsonl

python -m experiments.scripts.run_microbenchmarks \
  --preset paper-large \
  --case join-balanced \
  --strategies dynamic \
  --iterations 5 \
  --warmup 1 \
  --target-partition-size 268435456 \
  --output experiments/results/raw/join-balanced-paper-large-dynamic-tps256m.jsonl

python -m experiments.scripts.run_microbenchmarks \
  --preset paper-large \
  --case join-balanced \
  --strategies shuffle \
  --iterations 5 \
  --warmup 1 \
  --target-partition-size 268435456 \
  --output experiments/results/raw/join-balanced-paper-large-shuffle-tps256m.jsonl

python -m experiments.scripts.run_microbenchmarks \
  --preset paper-large \
  --case groupby-low-cardinality \
  --strategies dynamic,tree,shuffle \
  --iterations 5 \
  --warmup 1 \
  --output experiments/results/raw/groupby-low-paper-large.jsonl

python -m experiments.scripts.run_microbenchmarks \
  --preset paper-large \
  --case groupby-high-cardinality \
  --strategies dynamic,shuffle \
  --iterations 5 \
  --warmup 1 \
  --output experiments/results/raw/groupby-high-paper-large-success.jsonl

python -m experiments.scripts.run_microbenchmarks \
  --preset paper-large \
  --case groupby-high-cardinality \
  --strategies tree \
  --iterations 1 \
  --warmup 0 \
  --output experiments/results/raw/groupby-high-paper-large-tree-fail.jsonl
```

Run expected-failure strategies separately. After a CUDA OOM, the remaining
iterations in the same Python process may not be representative.


## PDS-H Q9 Case Study

The Q9 case study uses the Polars expression in
`queries/tpch_q9_polars.py`. The paper text describes the query shape and
reports the runtime decisions; the exact expression lives here to keep the
main paper compact.

The run script compares dynamic planning against a conservative forced-shuffle
baseline on the SF1000 PDS-H data set. Generate this data locally in the
benchmark layout before running the case study. The generated PDS-H tables are
not redistributed with the artifact. PDS-H is derived from TPC-H, but these are
not official TPC-H benchmark results:

```sh
DATA_DIR=/path/to/generated/pdsh/scale-1000 \
PYTHON=python \
PLOT_PYTHON=python \
RRUN=rrun \
experiments/scripts/run_q9_case_study.sh
```

The script writes raw local-machine output under `experiments/results/raw/q9/`
and regenerates:

- `paper/figures/q9-performance.pdf`
- `experiments/results/q9-sf1000-parsed-timing-summary.md`

The dynamic-decision figure is derived from a traced run and summarized in
`experiments/results/q9-sf1000-dynamic-decisions.md`.
