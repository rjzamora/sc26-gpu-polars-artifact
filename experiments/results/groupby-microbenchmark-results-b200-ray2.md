| Benchmark | Case | Strategy | Median (s) | Relative to dynamic | Error |
|---|---|---:|---:|---:|---:|
| groupby | groupby-low-cardinality | dynamic | 0.2750 | 1.0000 |  |
| groupby | groupby-low-cardinality | tree | 0.2832 | 1.0296 |  |
| groupby | groupby-low-cardinality | shuffle | 0.3022 | 1.0988 |  |
| groupby | groupby-high-cardinality | dynamic | 0.5982 | 1.0000 |  |
| groupby | groupby-high-cardinality | tree | 3.8128 | 6.3734 |  |
| groupby | groupby-high-cardinality | shuffle | 0.6023 | 1.0069 |  |
