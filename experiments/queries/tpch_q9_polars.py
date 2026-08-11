"""PDS-H Q9 expressed with the Polars LazyFrame API.

This query is the case-study workload used in the paper. PDS-H is derived from
TPC-H, but these results are not official TPC-H benchmark results. The
expression mirrors the implementation in ``cudf_polars.streaming.benchmarks.pdsh``
for query 9.
"""

from __future__ import annotations

import polars as pl


def query(
    part: pl.LazyFrame,
    partsupp: pl.LazyFrame,
    supplier: pl.LazyFrame,
    lineitem: pl.LazyFrame,
    orders: pl.LazyFrame,
    nation: pl.LazyFrame,
) -> pl.LazyFrame:
    return (
        part.join(partsupp, left_on="p_partkey", right_on="ps_partkey")
        .join(supplier, left_on="ps_suppkey", right_on="s_suppkey")
        .join(
            lineitem,
            left_on=["p_partkey", "ps_suppkey"],
            right_on=["l_partkey", "l_suppkey"],
        )
        .join(orders, left_on="l_orderkey", right_on="o_orderkey")
        .join(nation, left_on="s_nationkey", right_on="n_nationkey")
        .filter(pl.col("p_name").str.contains("green"))
        .select(
            pl.col("n_name").alias("nation"),
            pl.col("o_orderdate").dt.year().alias("o_year"),
            (
                pl.col("l_extendedprice") * (1 - pl.col("l_discount"))
                - pl.col("ps_supplycost") * pl.col("l_quantity")
            ).alias("amount"),
        )
        .group_by("nation", "o_year")
        .agg(pl.sum("amount").round(2).alias("sum_profit"))
        .sort(by=["nation", "o_year"], descending=[False, True])
    )
