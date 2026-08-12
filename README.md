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
- `experiments/patches/`: patch containing the experiment-only cudf changes
  used for the paper.
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
Clone NVIDIA/cudf, check out the recorded upstream commit, and apply the
included patch:

```sh
git clone https://github.com/NVIDIA/cudf.git cudf
cd cudf
git checkout 5912b8ec9b87c5d9f618e7d02f56c74006a13ed4
git apply /path/to/sc26-gpu-polars-artifact/experiments/patches/cudf-paper-dynamic-planning-overrides.patch
```

Then create the NVIDIA/cudf development environment and build the required cudf
components from the cudf checkout, as described in
`experiments/env/cudf-polars-benchmark-env.md`.
The original paper runs were collected from the
`paper-dynamic-planning-overrides` branch recorded in
`experiments/env/software-stack.md`.
That branch is provenance, while the patch is the reviewer-facing reproduction path.

## Quick Checks

List available microbenchmark cases:

```sh
python -m experiments.scripts.run_microbenchmarks --list-cases
```

Regenerate the Q9 decision figure from the included decision summary:

```sh
make q9-decisions
```

Run a small smoke benchmark from an NVIDIA/cudf environment:

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
