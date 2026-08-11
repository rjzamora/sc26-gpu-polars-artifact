| GPUs | Benchmark | Case | Strategy | Median (s) | Relative to dynamic | Successes | Error |
|---:|---|---|---|---:|---:|---:|---|
| 1 | groupby | groupby-low-cardinality | dynamic | 0.4280 | 1.0000 | 5 |  |
| 1 | groupby | groupby-low-cardinality | tree | 0.3980 | 0.9299 | 5 |  |
| 1 | groupby | groupby-low-cardinality | shuffle | 0.4664 | 1.0897 | 5 |  |
| 1 | groupby | groupby-high-cardinality | dynamic | 1.0332 | 1.0000 | 5 |  |
| 1 | groupby | groupby-high-cardinality | tree | 3.7761 | 3.6548 | 1 |  |
| 1 | groupby | groupby-high-cardinality | shuffle | 1.0589 | 1.0249 | 5 |  |
| 2 | groupby | groupby-low-cardinality | dynamic | 0.2750 | 1.0000 | 5 |  |
| 2 | groupby | groupby-low-cardinality | tree | 0.2832 | 1.0296 | 5 |  |
| 2 | groupby | groupby-low-cardinality | shuffle | 0.3022 | 1.0988 | 5 |  |
| 2 | groupby | groupby-high-cardinality | dynamic | 0.5982 | 1.0000 | 5 |  |
| 2 | groupby | groupby-high-cardinality | tree | 3.8128 | 6.3734 | 1 |  |
| 2 | groupby | groupby-high-cardinality | shuffle | 0.6023 | 1.0069 | 5 |  |
| 4 | groupby | groupby-low-cardinality | dynamic | 0.1856 | 1.0000 | 5 |  |
| 4 | groupby | groupby-low-cardinality | tree | 0.1957 | 1.0540 | 5 |  |
| 4 | groupby | groupby-low-cardinality | shuffle | 0.2107 | 1.1349 | 5 |  |
| 4 | groupby | groupby-high-cardinality | dynamic | 0.3936 | 1.0000 | 5 |  |
| 4 | groupby | groupby-high-cardinality | tree | 4.4539 | 11.3157 | 1 |  |
| 4 | groupby | groupby-high-cardinality | shuffle | 0.3647 | 0.9265 | 5 |  |
| 8 | groupby | groupby-low-cardinality | dynamic | 0.1596 | 1.0000 | 5 |  |
| 8 | groupby | groupby-low-cardinality | tree | 0.1767 | 1.1070 | 5 |  |
| 8 | groupby | groupby-low-cardinality | shuffle | 0.1707 | 1.0698 | 5 |  |
| 8 | groupby | groupby-high-cardinality | dynamic | 0.2818 | 1.0000 | 5 |  |
| 8 | groupby | groupby-high-cardinality | tree | 6.3071 | 22.3851 | 1 |  |
| 8 | groupby | groupby-high-cardinality | shuffle | 0.2959 | 1.0503 | 5 |  |
