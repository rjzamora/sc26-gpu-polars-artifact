| GPUs | Benchmark | Case | Strategy | Median (s) | Relative to dynamic | Successes | Error |
|---:|---|---|---|---:|---:|---:|---|
| 1 | join | join-small-build | dynamic | 0.5718 | 1.0000 | 5 |  |
| 1 | join | join-small-build | broadcast_right | 0.5687 | 0.9946 | 5 |  |
| 1 | join | join-small-build | shuffle | 0.7588 | 1.3269 | 5 |  |
| 1 | join | join-balanced | dynamic | 2.9682 | 1.0000 | 5 |  |
| 1 | join | join-balanced | broadcast_right | 15.9956 | 5.3890 | 1 |  |
| 1 | join | join-balanced | shuffle | 3.0342 | 1.0222 | 5 |  |
| 2 | join | join-small-build | dynamic | 0.3351 | 1.0000 | 5 |  |
| 2 | join | join-small-build | broadcast_right | 0.3540 | 1.0565 | 5 |  |
| 2 | join | join-small-build | shuffle | 0.4314 | 1.2874 | 5 |  |
| 2 | join | join-balanced | dynamic | 1.8021 | 1.0000 | 5 |  |
| 2 | join | join-balanced | broadcast_right | 8.2426 | 4.5738 | 1 |  |
| 2 | join | join-balanced | shuffle | 1.7345 | 0.9625 | 5 |  |
| 4 | join | join-small-build | dynamic | 0.2346 | 1.0000 | 5 |  |
| 4 | join | join-small-build | broadcast_right | 0.2328 | 0.9925 | 5 |  |
| 4 | join | join-small-build | shuffle | 0.2947 | 1.2564 | 5 |  |
| 4 | join | join-balanced | dynamic | 1.0282 | 1.0000 | 5 |  |
| 4 | join | join-balanced | broadcast_right | 6.0194 | 5.8545 | 1 |  |
| 4 | join | join-balanced | shuffle | 0.9706 | 0.9440 | 5 |  |
| 8 | join | join-small-build | dynamic | 0.1633 | 1.0000 | 5 |  |
| 8 | join | join-small-build | broadcast_right | 0.1559 | 0.9550 | 5 |  |
| 8 | join | join-small-build | shuffle | 0.2017 | 1.2357 | 5 |  |
| 8 | join | join-balanced | dynamic | 0.5541 | 1.0000 | 5 |  |
| 8 | join | join-balanced | broadcast_right | 7.1622 | 12.9251 | 1 |  |
| 8 | join | join-balanced | shuffle | 0.6010 | 1.0846 | 5 |  |
