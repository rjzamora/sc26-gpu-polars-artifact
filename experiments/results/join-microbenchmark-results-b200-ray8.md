| Benchmark | Case | Strategy | Median (s) | Relative to dynamic | Error |
|---|---|---:|---:|---:|---:|
| join | join-small-build | dynamic | 0.1633 | 1.0000 |  |
| join | join-small-build | broadcast_right | 0.1559 | 0.9550 |  |
| join | join-small-build | shuffle | 0.2017 | 1.2357 |  |
| join | join-balanced | dynamic | 0.5541 | 1.0000 |  |
| join | join-balanced | broadcast_right | 7.1622 | 12.9251 |  |
| join | join-balanced | shuffle | 0.6010 | 1.0846 |  |
