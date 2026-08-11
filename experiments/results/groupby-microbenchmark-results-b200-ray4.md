| Benchmark | Case | Strategy | Median (s) | Relative to dynamic | Error |
|---|---|---:|---:|---:|---:|
| groupby | groupby-low-cardinality | dynamic | 0.1856 | 1.0000 |  |
| groupby | groupby-low-cardinality | tree | 0.1957 | 1.0540 |  |
| groupby | groupby-low-cardinality | shuffle | 0.2107 | 1.1349 |  |
| groupby | groupby-high-cardinality | dynamic | 0.3936 | 1.0000 |  |
| groupby | groupby-high-cardinality | tree | 4.4539 | 11.3157 |  |
| groupby | groupby-high-cardinality | shuffle | 0.3647 | 0.9265 |  |
