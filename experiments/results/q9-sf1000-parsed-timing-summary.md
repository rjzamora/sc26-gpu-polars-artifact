# PDS-H Q9 Parsed Timing Summary

All runs use iteration 0 as a cache warmup; hot timings report iterations greater than 0.

| GPUs | Strategy | Warmup (s) | Hot median (s) | Hot mean (s) | Hot values (s) | Source |
|---:|---|---:|---:|---:|---|---|
| 1 | Conservative shuffle | 232.1548 | 50.8721 | 50.8721 | 50.8721 | `pdsh_q9_sf1000_conservative_shuffle_spmd1.jsonl` |
| 1 | Dynamic | 24.6943 | 28.0704 | 28.0704 | 27.2510, 28.8898 | `pdsh_q9_sf1000_dynamic_spmd1.jsonl` |
| 2 | Conservative shuffle | 11.3803 | 9.7618 | 9.7618 | 9.7618 | `pdsh_q9_sf1000_conservative_shuffle_spmd2.jsonl` |
| 2 | Dynamic | 5.6919 | 5.3326 | 5.3326 | 5.2607, 5.4045 | `pdsh_q9_sf1000_dynamic_spmd2.jsonl` |
| 4 | Conservative shuffle | 4.8738 | 3.4885 | 3.4885 | 3.4885 | `pdsh_q9_sf1000_conservative_shuffle_spmd4.jsonl` |
| 4 | Dynamic | 3.8441 | 3.2572 | 3.2572 | 3.1004, 3.4141 | `pdsh_q9_sf1000_dynamic_spmd4.jsonl` |
| 8 | Conservative shuffle | 5.6513 | 3.3572 | 3.3572 | 3.3572 | `pdsh_q9_sf1000_conservative_shuffle_spmd8.jsonl` |
| 8 | Dynamic | 3.6576 | 2.2006 | 2.2006 | 2.1575, 2.2438 | `pdsh_q9_sf1000_dynamic_spmd8.jsonl` |
