| Benchmark | Case | Strategy | Median (s) | Relative to dynamic | Error |
|---|---|---:|---:|---:|---:|
| join | join-small-build | dynamic | 0.2346 | 1.0000 |  |
| join | join-small-build | broadcast_right | 0.2328 | 0.9925 |  |
| join | join-small-build | shuffle | 0.2947 | 1.2564 |  |
| join | join-balanced | dynamic | 1.0282 | 1.0000 |  |
| join | join-balanced | broadcast_right | 6.0194 | 5.8545 |  |
| join | join-balanced | shuffle | 0.9706 | 0.9440 |  |
