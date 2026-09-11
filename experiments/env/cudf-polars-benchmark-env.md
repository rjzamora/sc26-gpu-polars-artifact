# cudf-polars Benchmark Environment

This runbook is for collecting paper microbenchmarks on a GPU system such as a
B200 or H100 system. It assumes this artifact repository and an NVIDIA/cudf
checkout are available in the same software environment.

## Required cudf Changes

Clone the public cudf repository and check out the commit used for the initial
B200 production runs:

```sh
git clone --branch paper-dynamic-planning-overrides https://github.com/rjzamora/cudf.git cudf
cd cudf
git checkout 23a2c06a08980fd107a03e04b256a85816f6d668
```

For the first B200 production runs, the selected cudf revision was:

```text
branch: paper-dynamic-planning-overrides
commit: 23a2c06a08980fd107a03e04b256a85816f6d668
upstream/main at merge: 5912b8ec9b87c5d9f618e7d02f56c74006a13ed4
```

The experiment-code snapshot is archived at Zenodo DOI
`10.5281/zenodo.21906536`.

## Python Environment

Use an NVIDIA/cudf development environment that can import `cudf`, `pylibcudf`,
`cudf_polars`, `rapidsmpf`, `ray`, and `polars`. If an equivalent environment
already exists, it can be reused. If creating a new environment from the cudf
checkout, start from the generated RAPIDS environment file that matches the CUDA
stack used for reproduction, for example:

```sh
conda env create -n cudf-polars -f conda/environments/all_cuda-133_arch-x86_64.yaml
conda activate cudf-polars
```

Build the cudf components needed by the GPU Polars benchmark harness:

```sh
cd /path/to/cudf
bash ./build.sh libcudf pylibcudf libcudf_streaming cudf_streaming cudf_polars
```

Then install the local `cudf_polars` package from the selected cudf checkout if
the build did not already place the package in editable/development mode for
your environment:

```sh
cd /path/to/cudf/python/cudf_polars
pip install --no-build-isolation --no-deps -e .
```

Validate that Python imports the local checkout:

```sh
python - <<'PY'
import cudf_polars
import polars as pl
from cudf_polars.engine.ray import RayEngine

print("cudf_polars:", cudf_polars.__file__)
print("polars:", pl.__version__)
print("RayEngine:", RayEngine)
PY
```

The `cudf_polars.__file__` path should point into the selected cudf checkout.

## Artifact Repository Setup

From the artifact repository root:

```sh
cd /path/to/sc26-gpu-polars-artifact
python -m experiments.scripts.run_microbenchmarks --list-cases
```

The benchmark script writes synthetic Parquet inputs under
`experiments/results/generated/` and JSONL output under
`experiments/results/raw/`. These paths are ignored by git.

## Frontend Choice

For local multi-GPU experiments, prefer the Ray frontend unless explicitly
launching the process under `rrun`:

```sh
--frontend ray
```

The Ray frontend starts a local Ray cluster and must be run from an environment
where binding localhost sockets is permitted. If a tool sandbox blocks local
network binds, run the benchmark from a normal shell or approve the benchmark
command to run outside the sandbox. Use `--frontend spmd` for single-rank smoke
tests when Ray is not available.

Control the GPU count with `CUDA_VISIBLE_DEVICES`:

```sh
export CUDA_VISIBLE_DEVICES=0
export CUDA_VISIBLE_DEVICES=0,1
export CUDA_VISIBLE_DEVICES=0,1,2,3
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
```

The `cpu` strategy uses the Polars CPU streaming engine and ignores
`--frontend`.

## Smoke Test

Run this before any paper-large sweep:

```sh
CUDA_VISIBLE_DEVICES=0 python -m experiments.scripts.run_microbenchmarks \
  --frontend ray \
  --preset smoke \
  --case join-small-build,groupby-low-cardinality \
  --strategies dynamic \
  --iterations 1 \
  --warmup 0 \
  --output experiments/results/raw/smoke-benchmark-env.jsonl
```

Summarize:

```sh
python -m experiments.scripts.summarize_microbenchmarks \
  experiments/results/raw/smoke-benchmark-env.jsonl \
  --output experiments/results/smoke-benchmark-env.md
```

## Quick End-to-End Figure Validation

Use this `medium` run to validate the benchmark and plotting path. Prefer four
GPUs when available because it also checks the multi-rank join path. Use
`CUDA_VISIBLE_DEVICES=0` only as a lighter sanity check. This is a wiring check,
not final paper data.

```sh
CUDA_VISIBLE_DEVICES=0,1,2,3 python -m experiments.scripts.run_microbenchmarks \
  --frontend ray \
  --preset medium \
  --case join-small-build,join-balanced \
  --strategies default \
  --iterations 2 \
  --warmup 1 \
  --output experiments/results/raw/medium-validation-join-ray4.jsonl \
  --data-dir experiments/results/generated/medium-validation-ray4 \
  --regenerate

CUDA_VISIBLE_DEVICES=0,1,2,3 python -m experiments.scripts.run_microbenchmarks \
  --frontend ray \
  --preset medium \
  --case groupby-low-cardinality,groupby-high-cardinality \
  --strategies default \
  --iterations 2 \
  --warmup 1 \
  --output experiments/results/raw/medium-validation-groupby-ray4.jsonl \
  --data-dir experiments/results/generated/medium-validation-ray4
```

Generate the microbenchmark figures from those validation results:

```sh
conda activate paper-env

python experiments/scripts/plot_microbenchmark_figure.py \
  experiments/results/raw/medium-validation-join-ray4.jsonl \
  --benchmark join \
  --output paper/figures/join-microbenchmark-results.pdf \
  --summary-output experiments/results/medium-validation-join-ray4.md \
  --title "Medium validation, 4 GPUs"

python experiments/scripts/plot_microbenchmark_figure.py \
  experiments/results/raw/medium-validation-groupby-ray4.jsonl \
  --benchmark groupby \
  --output paper/figures/groupby-microbenchmark-results.pdf \
  --summary-output experiments/results/medium-validation-groupby-ray4.md \
  --title "Medium validation, 4 GPUs"
```

## Paper-Large Sweep

Use `paper-large` for final synthetic results. Run expected-failure strategies in
separate processes because a CUDA OOM can affect later iterations in the same
Python process.

For the final production microbenchmark sweep, prefer the driver script:

```sh
conda activate cudf-polars

GPU_DEVICES=0,1,2,3 \
GPU_LABEL=ray4 \
TITLE="B200, 4 GPUs" \
PYTHON=python \
PLOT_PYTHON=/path/to/paper-env/bin/python \
experiments/scripts/run_paper_microbenchmarks.sh
```

The script runs the join and groupby paper-large cases, includes the expected
forced-failure runs, and regenerates the join and groupby figure PDFs. The
commands below are the expanded form for debugging or running cases
individually.

Join, broadcast-favored:

```sh
CUDA_VISIBLE_DEVICES=0,1,2,3 python -m experiments.scripts.run_microbenchmarks \
  --frontend ray \
  --preset paper-large \
  --case join-small-build \
  --strategies dynamic,broadcast_right,shuffle \
  --iterations 5 \
  --warmup 1 \
  --output experiments/results/raw/join-small-build-paper-large-ray4.jsonl
```

Join, shuffle-favored:

```sh
CUDA_VISIBLE_DEVICES=0,1,2,3 python -m experiments.scripts.run_microbenchmarks \
  --frontend ray \
  --preset paper-large \
  --case join-balanced \
  --strategies dynamic \
  --iterations 5 \
  --warmup 1 \
  --target-partition-size 268435456 \
  --output experiments/results/raw/join-balanced-paper-large-dynamic-ray4-tps256m.jsonl

CUDA_VISIBLE_DEVICES=0,1,2,3 python -m experiments.scripts.run_microbenchmarks \
  --frontend ray \
  --preset paper-large \
  --case join-balanced \
  --strategies shuffle \
  --iterations 5 \
  --warmup 1 \
  --target-partition-size 268435456 \
  --output experiments/results/raw/join-balanced-paper-large-shuffle-ray4-tps256m.jsonl

CUDA_VISIBLE_DEVICES=0,1,2,3 python -m experiments.scripts.run_microbenchmarks \
  --frontend ray \
  --preset paper-large \
  --case join-balanced \
  --strategies broadcast_right \
  --iterations 1 \
  --warmup 0 \
  --target-partition-size 268435456 \
  --output experiments/results/raw/join-balanced-paper-large-broadcast-fail-ray4-tps256m.jsonl
```

GroupBy, compact-output case:

```sh
CUDA_VISIBLE_DEVICES=0,1,2,3 python -m experiments.scripts.run_microbenchmarks \
  --frontend ray \
  --preset paper-large \
  --case groupby-low-cardinality \
  --strategies dynamic,tree,shuffle \
  --iterations 5 \
  --warmup 1 \
  --output experiments/results/raw/groupby-low-paper-large-ray4.jsonl
```

GroupBy, high-cardinality case:

```sh
CUDA_VISIBLE_DEVICES=0,1,2,3 python -m experiments.scripts.run_microbenchmarks \
  --frontend ray \
  --preset paper-large \
  --case groupby-high-cardinality \
  --strategies dynamic,shuffle \
  --iterations 5 \
  --warmup 1 \
  --output experiments/results/raw/groupby-high-paper-large-success-ray4.jsonl

CUDA_VISIBLE_DEVICES=0,1,2,3 python -m experiments.scripts.run_microbenchmarks \
  --frontend ray \
  --preset paper-large \
  --case groupby-high-cardinality \
  --strategies tree \
  --iterations 1 \
  --warmup 0 \
  --output experiments/results/raw/groupby-high-paper-large-tree-fail-ray4.jsonl
```

Repeat the successful cases for 1, 2, 4, and 8 GPUs by changing
`CUDA_VISIBLE_DEVICES`. Record the hardware and software stack before moving raw
results into paper tables or plots.

## Generate Microbenchmark Figures

The evaluation section contains separate microbenchmark figures for joins and
groupbys:

```text
paper/figures/join-microbenchmark-results.pdf
paper/figures/groupby-microbenchmark-results.pdf
```

After collecting the raw JSONL files, generate the figures from the paper
environment, or any Python environment with Matplotlib:

```sh
conda activate paper-env

python experiments/scripts/plot_microbenchmark_figure.py \
  experiments/results/raw/join-small-build-paper-large-ray4.jsonl \
  experiments/results/raw/join-balanced-paper-large-dynamic-ray4-tps256m.jsonl \
  experiments/results/raw/join-balanced-paper-large-shuffle-ray4-tps256m.jsonl \
  experiments/results/raw/join-balanced-paper-large-broadcast-fail-ray4-tps256m.jsonl \
  --benchmark join \
  --output paper/figures/join-microbenchmark-results.pdf \
  --summary-output experiments/results/join-microbenchmark-results-b200-ray4.md \
  --title "B200, 4 GPUs"

python experiments/scripts/plot_microbenchmark_figure.py \
  experiments/results/raw/groupby-low-paper-large-ray4.jsonl \
  experiments/results/raw/groupby-high-paper-large-success-ray4.jsonl \
  experiments/results/raw/groupby-high-paper-large-tree-fail-ray4.jsonl \
  --benchmark groupby \
  --output paper/figures/groupby-microbenchmark-results.pdf \
  --summary-output experiments/results/groupby-microbenchmark-results-b200-ray4.md \
  --title "B200, 4 GPUs"
```

The script normalizes each case by the median dynamic runtime and marks forced
strategies that only produced errors as `fail`. Use the Markdown summaries to
check exact median times before copying numbers into the paper text.

Final paper numbers should come from one consistent B200 or H100 stack and
should be regenerated from fresh raw JSONL files.
