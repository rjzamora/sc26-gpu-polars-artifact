# Software Stack

This file records the fixed software stack used for paper experiments.

## Primary Production Run

- Label: b200-production-initial
- Date selected: 2026-07-16
- cudf repository: https://github.com/rjzamora/cudf.git
- cudf branch: paper-dynamic-planning-overrides
- cudf commit: 23a2c06a08980fd107a03e04b256a85816f6d668
- cudf upstream/main commit at merge: 5912b8ec9b87c5d9f618e7d02f56c74006a13ed4
- reviewer reproduction path: clone https://github.com/rjzamora/cudf.git and
  check out 23a2c06a08980fd107a03e04b256a85816f6d668 from the
  paper-dynamic-planning-overrides branch history
- experiment-code DOI: 10.5281/zenodo.21906536
- rapidsmpf repository: cudf dependency
- rapidsmpf branch: provided by the cudf checkout
- rapidsmpf commit: provided by the cudf checkout
- polars version or commit: >=1.35,<1.43
- RAPIDS base image: not used for the reported bare-metal conda runs
- Container image tag: not used for the reported bare-metal conda runs
- Container image digest: not used for the reported bare-metal conda runs
- CUDA version: 13.0
- Driver version: 580.82.07

## Notes

- Prefer an immutable commit SHA and container digest over branch names or mutable tags.
- Use "RAPIDS 26.08 development snapshot" in the paper until the exact release artifact is available and verified.
- Keep experiment-only strategy knobs on a clearly named paper branch.
- Disable or avoid optimizer passes that are not part of the dynamic-planning story.
