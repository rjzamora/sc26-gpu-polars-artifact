# PDS-H Q9 SF1000 Dynamic Decisions

Source trace: `pdsh_results.jsonl` from the single-rank traced dynamic run.
The same query is used for the scaling timings in `q9_sf1000_timing_summary.md`.

| IR id | Operator | Keys | Decision | Output rows | Output chunks |
|---:|---|---|---|---:|---:|
| 1857695698 | Join | `['p_partkey'] = ['ps_partkey']` | broadcast_left | 43484728 | 16 |
| 1868729410 | Join | `['ps_suppkey'] = ['s_suppkey']` | broadcast_right | 43484728 | 16 |
| 1921495396 | Join | `['p_partkey', 'ps_suppkey'] = ['l_partkey', 'l_suppkey']` | broadcast_left | 326147632 | 180 |
| 399402893 | Join | `['l_orderkey'] = ['o_orderkey']` | broadcast_left | 326147632 | 15 |
| 2699710600 | Join | `['s_nationkey'] = ['n_nationkey']` | broadcast_right | 326147632 | 15 |
| 857793687 | GroupBy | `['nation', 'o_year']` | tree_local | 175 | 1 |
