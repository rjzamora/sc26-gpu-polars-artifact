| Benchmark | Case | Strategy | Median (s) | Relative to dynamic | Error |
|---|---|---:|---:|---:|---:|
| groupby | groupby-low-cardinality | dynamic | 0.1596 | 1.0000 |  |
| groupby | groupby-low-cardinality | tree | 0.1767 | 1.1070 |  |
| groupby | groupby-low-cardinality | shuffle | 0.1707 | 1.0698 |  |
| groupby | groupby-high-cardinality | dynamic | 0.2818 | 1.0000 |  |
| groupby | groupby-high-cardinality | tree | 6.3071 | 22.3851 |  |
| groupby | groupby-high-cardinality | shuffle | 0.2959 | 1.0503 |  |
