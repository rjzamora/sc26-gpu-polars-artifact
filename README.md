# Dynamic Planning Artifact

This repository contains the sanitized artifact package for the PDSW 2026 paper
"Dynamic Planning for Scalable Data Movement in Accelerated Query Engines."

The artifact captures the scripts, configuration records, summarized results,
and generated figures used for the paper evaluation. It intentionally does not
include working notes, submission notes, LaTeX draft sources, generated input
datasets, or exploratory local-machine outputs.

## Contents

- `experiments/scripts/`: benchmark, plotting, and case-study scripts.
- `experiments/configs/paper-cut-b200.yaml`: hardware and software pin for the
  B200 paper-cut run.
- `experiments/env/`: environment and software-stack runbooks.
- `experiments/queries/tpch_q9_polars.py`: exact Polars LazyFrame expression
  used for the PDS-H Q9 case study.
- `experiments/results/`: summarized paper results and Q9 decision metadata.
- `paper/figures/`: generated PDF figures used by the submitted paper.

## Artifact Availability

The synthetic microbenchmark inputs are generated locally by
`experiments/scripts/run_microbenchmarks.py`.
The PDS-H Q9 inputs are generated locally from the TPC-H data generator and
converted to the Parquet layout expected by the benchmark harness. These
generated inputs are not redistributed with this artifact.

PDS-H is derived from TPC-H, but the reported case study is not an official
audited TPC-H benchmark result.

## Environment

The plotting/document-support environment can be created with:

```sh
conda env create -f environment.yml
conda activate paper-env
```

The benchmark environment is a RAPIDS/cudf development environment that can
import `cudf`, `cudf_polars`, `rapidsmpf`, `ray`, and `polars`.
Use the `paper-dynamic-planning-overrides` cudf branch recorded in
`experiments/env/software-stack.md`.

## Quick Checks

List available microbenchmark cases:

```sh
python -m experiments.scripts.run_microbenchmarks --list-cases
```

Regenerate the Q9 decision figure from the included decision summary:

```sh
make q9-decisions
```

Run a small smoke benchmark from a RAPIDS/cudf environment:

```sh
CUDA_VISIBLE_DEVICES=0 python -m experiments.scripts.run_microbenchmarks \
  --frontend ray \
  --preset smoke \
  --case join-small-build,groupby-low-cardinality \
  --strategies dynamic \
  --iterations 1 \
  --warmup 0 \
  --output experiments/results/raw/smoke.jsonl \
  --cudf-repo /path/to/cudf
```

## Paper-Cut Runs

The full paper-cut synthetic benchmark sweep is driven by:

```sh
GPU_DEVICES=0,1,2,3 \
GPU_LABEL=ray4 \
TITLE="B200, 4 GPUs" \
PYTHON=python \
PLOT_PYTHON=python \
experiments/scripts/run_paper_microbenchmarks.sh
```

The PDS-H Q9 sweep requires locally generated scale-factor 1000 Parquet inputs:

```sh
DATA_DIR=/path/to/generated/pdsh/scale-1000 \
PYTHON=python \
PLOT_PYTHON=python \
RRUN=rrun \
experiments/scripts/run_q9_case_study.sh
```

Both full workflows require suitable multi-GPU hardware. The included Markdown
summaries and PDF figures record the paper results collected on the B200 system.
