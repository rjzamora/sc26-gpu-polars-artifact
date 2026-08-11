| Benchmark | Case | Strategy | Median (s) | Relative to dynamic | Error |
|---|---|---:|---:|---:|---:|
| groupby | groupby-low-cardinality | dynamic | 0.4280 | 1.0000 |  |
| groupby | groupby-low-cardinality | tree | 0.3980 | 0.9299 |  |
| groupby | groupby-low-cardinality | shuffle | 0.4664 | 1.0897 |  |
| groupby | groupby-high-cardinality | dynamic | 1.0332 | 1.0000 |  |
| groupby | groupby-high-cardinality | tree | 3.7761 | 3.6548 |  |
| groupby | groupby-high-cardinality | shuffle | 1.0589 | 1.0249 |  |
