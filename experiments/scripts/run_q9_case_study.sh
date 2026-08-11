#!/usr/bin/env bash
# Run the PDS-H Q9 case-study sweep and regenerate the Q9 performance figure.

set -euo pipefail

PYTHON=${PYTHON:-python}
PLOT_PYTHON=${PLOT_PYTHON:-$PYTHON}
RRUN=${RRUN:-rrun}
DATA_DIR=${DATA_DIR:-}
: "${DATA_DIR:?Set DATA_DIR to the generated PDS-H scale-factor 1000 Parquet input directory}"
GPU_COUNTS=${GPU_COUNTS:-"1 2 4 8"}
DYNAMIC_ITERATIONS=${DYNAMIC_ITERATIONS:-3}
CONSERVATIVE_ITERATIONS=${CONSERVATIVE_ITERATIONS:-2}
IO_MODE=${IO_MODE:-hot}
CONSERVATIVE_TIMEOUT=${CONSERVATIVE_TIMEOUT:-600s}
RAW_DIR=${RAW_DIR:-experiments/results/raw/q9}
SUMMARY_DIR=${SUMMARY_DIR:-experiments/results}
FIGURE_DIR=${FIGURE_DIR:-paper/figures}
TITLE=${TITLE:-PDS-H Q9 SF1000 on B200 GPUs}

mkdir -p "$RAW_DIR" "$SUMMARY_DIR" "$FIGURE_DIR"

run_pdsh() {
  local strategy=$1
  local nranks=$2
  local iterations=$3
  local timeout_value=$4
  local join_algo=$5
  local groupby_algo=$6
  local gpus
  gpus=$(seq -s, 0 $((nranks - 1)))
  local out="$RAW_DIR/pdsh_q9_sf1000_${strategy}_spmd${nranks}.jsonl"
  local summary="$RAW_DIR/summary_q9_sf1000_${strategy}_spmd${nranks}.out"
  local status="$RAW_DIR/status_q9_sf1000_${strategy}_spmd${nranks}.txt"

  echo "[$(date --iso-8601=seconds)] START ${strategy} nranks=${nranks} gpus=${gpus}"
  set +e
  if [[ -n "$timeout_value" ]]; then
    /usr/bin/timeout --kill-after=30s "$timeout_value" \
      "$RRUN" -n "$nranks" -g "$gpus" \
        -x CUDF_POLARS_LOG_TRACES=0 \
        -x CUDF_POLARS_LOG_TRACES_MEMORY=0 \
        -x CUDF_POLARS__EXPERIMENTAL__JOIN_ALGO="$join_algo" \
        -x CUDF_POLARS__EXPERIMENTAL__GROUPBY_ALGO="$groupby_algo" \
        "$PYTHON" -m cudf_polars.streaming.benchmarks.pdsh \
          --path "$DATA_DIR" \
          --suffix "" \
          --frontend spmd \
          --iterations "$iterations" \
          --io-mode "$IO_MODE" \
          --no-collect-traces \
          --no-explain \
          --no-print-results \
          --capture-env-vars CUDF_POLARS__EXPERIMENTAL__JOIN_ALGO,CUDF_POLARS__EXPERIMENTAL__GROUPBY_ALGO \
          -o "$out" \
          9 > "$summary" 2>&1
  else
    "$RRUN" -n "$nranks" -g "$gpus" \
      -x CUDF_POLARS_LOG_TRACES=0 \
      -x CUDF_POLARS_LOG_TRACES_MEMORY=0 \
      -x CUDF_POLARS__EXPERIMENTAL__JOIN_ALGO="$join_algo" \
      -x CUDF_POLARS__EXPERIMENTAL__GROUPBY_ALGO="$groupby_algo" \
      "$PYTHON" -m cudf_polars.streaming.benchmarks.pdsh \
        --path "$DATA_DIR" \
        --suffix "" \
        --frontend spmd \
        --iterations "$iterations" \
        --io-mode "$IO_MODE" \
        --no-collect-traces \
        --no-explain \
        --no-print-results \
        --capture-env-vars CUDF_POLARS__EXPERIMENTAL__JOIN_ALGO,CUDF_POLARS__EXPERIMENTAL__GROUPBY_ALGO \
        -o "$out" \
        9 > "$summary" 2>&1
  fi
  local rc=$?
  set -e

  if [[ $rc -eq 124 || $rc -eq 137 ]]; then
    echo "timeout ${timeout_value}" > "$status"
    echo "[$(date --iso-8601=seconds)] TIMEOUT ${strategy} nranks=${nranks}"
  elif [[ $rc -ne 0 ]]; then
    echo "error ${rc}" > "$status"
    echo "[$(date --iso-8601=seconds)] ERROR ${strategy} nranks=${nranks} rc=${rc}"
  else
    echo "success" > "$status"
    echo "[$(date --iso-8601=seconds)] DONE ${strategy} nranks=${nranks} out=${out}"
  fi
}

read -r -a counts <<< "$GPU_COUNTS"
for nranks in "${counts[@]}"; do
  run_pdsh dynamic "$nranks" "$DYNAMIC_ITERATIONS" "" dynamic dynamic
  run_pdsh conservative_shuffle "$nranks" "$CONSERVATIVE_ITERATIONS" "$CONSERVATIVE_TIMEOUT" shuffle shuffle
done

"$PLOT_PYTHON" experiments/scripts/plot_q9_case_study.py "$RAW_DIR" \
  --output "$FIGURE_DIR/q9-performance.pdf" \
  --summary-output "$SUMMARY_DIR/q9-sf1000-parsed-timing-summary.md" \
  --title "$TITLE"

echo "Wrote:"
echo "  $FIGURE_DIR/q9-performance.pdf"
echo "  $SUMMARY_DIR/q9-sf1000-parsed-timing-summary.md"
