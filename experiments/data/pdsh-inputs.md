# PDS-H Input Data

The PDS-H Q9 case study requires locally generated scale-factor 1000 Parquet
inputs. The generated data are not redistributed with this artifact.

For the paper runs, the input data were generated with `tpchgen-rs` from:

```text
https://github.com/TomAugspurger/tpchgen-rs/tree/tom/sync-upstream-clean
```

Build or install `tpchgen-cli` from that branch, then generate Parquet input
data at scale factor 1000. The `tpchgen-cli` interface has changed over time,
so check the help text for the checked-out branch. The paper data were generated
as Parquet with a command equivalent to:

```sh
tpchgen-cli \
  -s 1000 \
  --format=parquet \
  --output-dir /path/to/generated/pdsh/scale-1000
```

The Q9 runner expects `DATA_DIR` to point at a directory containing one
subdirectory per table. The paper runs used this table layout:

```text
/path/to/generated/pdsh/scale-1000/
  customer/
    part.0.parquet ... part.1.parquet
  lineitem/
    part.0.parquet ... part.59.parquet
  nation/
    part.0.parquet
  orders/
    part.0.parquet ... part.14.parquet
  part/
    part.0.parquet ... part.1.parquet
  partsupp/
    part.0.parquet ... part.7.parquet
  region/
    part.0.parquet
  supplier/
    part.0.parquet
```

Run the case study with:

```sh
DATA_DIR=/path/to/generated/pdsh/scale-1000 \
experiments/scripts/run_q9_case_study.sh
```

PDS-H is derived from TPC-H, but these are not official audited TPC-H benchmark results. Since these inputs are generated locally, exact file and row-group layout may vary across reproductions. The expected reproduction target is the qualitative dynamic-planning behavior and performance trend, not bitwise-identical timings.
