| Benchmark | Case | Strategy | Median (s) | Relative to dynamic | Error |
|---|---|---:|---:|---:|---:|
| join | join-small-build | dynamic | 0.3351 | 1.0000 |  |
| join | join-small-build | broadcast_right | 0.3540 | 1.0565 |  |
| join | join-small-build | shuffle | 0.4314 | 1.2874 |  |
| join | join-balanced | dynamic | 1.8021 | 1.0000 |  |
| join | join-balanced | broadcast_right | 8.2426 | 4.5738 |  |
| join | join-balanced | shuffle | 1.7345 | 0.9625 |  |
