# Dynamic Planning Artifact

This repository contains the artifact package for the PDSW 2026 paper
"Dynamic Planning for Scalable Data Movement in Accelerated Query Engines."

This repository contains the scripts, configuration records, summarized results,
and generated figures used for the paper evaluation. Generated input datasets
and exploratory local-machine outputs are not included.

## Contents

- `experiments/scripts/`: benchmark, plotting, and case-study scripts.
- `experiments/configs/production-b200.yaml`: hardware and software pin for the
  B200 production run.
- `experiments/env/`: environment and software-stack runbooks.
- `experiments/data/pdsh-inputs.md`: PDS-H input-generation notes and expected
  Parquet layout.
- `experiments/queries/tpch_q9_polars.py`: exact Polars LazyFrame expression
  used for the PDS-H Q9 case study.
- `experiments/results/`: summarized paper results and Q9 decision metadata.
- `paper/figures/`: generated PDF figures used by the submitted paper.

## Artifact Availability

The synthetic microbenchmark inputs are generated locally by
`experiments/scripts/run_microbenchmarks.py`.
The PDS-H Q9 inputs must be generated locally as scale-factor 1000 Parquet
inputs in the layout expected by the benchmark harness. These generated inputs
are not redistributed with this artifact. See `experiments/data/pdsh-inputs.md`
for the generator source used in the paper runs and the expected directory
layout.

PDS-H is derived from TPC-H, but the reported case study is not an official
audited TPC-H benchmark result.

## Environment

The plotting/document-support environment can be created with:

```sh
conda env create -f environment.yml
conda activate paper-env
```

The benchmark environment is an NVIDIA/cudf development environment that can
import `cudf`, `cudf_polars`, `rapidsmpf`, `ray`, and `polars`.
Clone the public cudf repository and check out the commit used for the initial
B200 production runs:

```sh
git clone --branch paper-dynamic-planning-overrides https://github.com/rjzamora/cudf.git cudf
cd cudf
git checkout 23a2c06a08980fd107a03e04b256a85816f6d668
```

Then create the NVIDIA/cudf development environment and build the required cudf
components from the cudf checkout, as described in
`experiments/env/cudf-polars-benchmark-env.md`.
The commit is part of the public `paper-dynamic-planning-overrides` branch and
is also recorded in `experiments/env/software-stack.md`.

## Quick Checks

List available microbenchmark cases:

```sh
python -m experiments.scripts.run_microbenchmarks --list-cases
```

Regenerate the Q9 decision figure from the included decision summary:

```sh
make q9-decisions
```

Run a CPU-only wiring check if you want to verify the artifact scripts before
using a GPU:

```sh
python -m experiments.scripts.run_microbenchmarks \
  --preset smoke \
  --case groupby-low-cardinality \
  --strategies cpu \
  --iterations 1 \
  --warmup 0 \
  --output experiments/results/raw/smoke-cpu.jsonl \
  --cudf-repo /path/to/cudf
```

Run a small GPU smoke benchmark from an NVIDIA/cudf environment. The single-rank
SPMD frontend avoids local Ray startup and is sufficient for this smoke test:

```sh
CUDA_VISIBLE_DEVICES=0 python -m experiments.scripts.run_microbenchmarks \
  --frontend spmd \
  --preset smoke \
  --case join-small-build,groupby-low-cardinality \
  --strategies dynamic \
  --iterations 1 \
  --warmup 0 \
  --output experiments/results/raw/smoke.jsonl \
  --cudf-repo /path/to/cudf
```

## Production Runs

The full production synthetic benchmark sweep is driven by:

```sh
GPU_DEVICES=0,1,2,3 \
GPU_LABEL=ray4 \
TITLE="B200, 4 GPUs" \
PYTHON=python \
PLOT_PYTHON=python \
experiments/scripts/run_paper_microbenchmarks.sh
```

The PDS-H Q9 sweep requires locally generated scale-factor 1000 Parquet inputs
in the expected benchmark layout:

```sh
DATA_DIR=/path/to/generated/pdsh/scale-1000 \
PYTHON=python \
PLOT_PYTHON=python \
RRUN=rrun \
experiments/scripts/run_q9_case_study.sh
```

Both full workflows require suitable multi-GPU hardware. The included Markdown
summaries and PDF figures record the paper results collected on the B200 system.
