| Benchmark | Case | Strategy | Median (s) | Relative to dynamic | Error |
|---|---|---:|---:|---:|---:|
| join | join-small-build | dynamic | 0.5718 | 1.0000 |  |
| join | join-small-build | broadcast_right | 0.5687 | 0.9946 |  |
| join | join-small-build | shuffle | 0.7588 | 1.3269 |  |
| join | join-balanced | dynamic | 2.9682 | 1.0000 |  |
| join | join-balanced | broadcast_right | 15.9956 | 5.3890 |  |
| join | join-balanced | shuffle | 3.0342 | 1.0222 |  |
