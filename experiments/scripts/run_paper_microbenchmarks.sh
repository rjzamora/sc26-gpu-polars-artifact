#!/usr/bin/env bash
# Run the paper-cut microbenchmarks and regenerate the paper figures.

set -euo pipefail

PYTHON=${PYTHON:-python}
PLOT_PYTHON=${PLOT_PYTHON:-$PYTHON}
MAKE=${MAKE:-make}

FRONTEND=${FRONTEND:-ray}
PRESET=${PRESET:-paper-large}
GPU_DEVICES=${GPU_DEVICES:-0,1,2,3}
GPU_LABEL=${GPU_LABEL:-ray4}
TITLE=${TITLE:-B200, 4 GPUs}

ITERATIONS=${ITERATIONS:-5}
WARMUP=${WARMUP:-1}
FAIL_ITERATIONS=${FAIL_ITERATIONS:-1}
FAIL_WARMUP=${FAIL_WARMUP:-0}
JOIN_BALANCED_TARGET_PARTITION_SIZE=${JOIN_BALANCED_TARGET_PARTITION_SIZE:-268435456}

RAW_DIR=${RAW_DIR:-experiments/results/raw}
FIGURE_DIR=${FIGURE_DIR:-paper/figures}
SUMMARY_DIR=${SUMMARY_DIR:-experiments/results}
BUILD_PAPER=${BUILD_PAPER:-0}
REGENERATE=${REGENERATE:-0}

mkdir -p "$RAW_DIR" "$FIGURE_DIR" "$SUMMARY_DIR"

regen_args=()
if [[ "$REGENERATE" == "1" ]]; then
  regen_args+=(--regenerate)
fi

export CUDA_VISIBLE_DEVICES="$GPU_DEVICES"

run_benchmark() {
  "$PYTHON" -m experiments.scripts.run_microbenchmarks "$@"
}

plot_figure() {
  "$PLOT_PYTHON" experiments/scripts/plot_microbenchmark_figure.py "$@"
}

join_small="$RAW_DIR/join-small-build-${PRESET}-${GPU_LABEL}.jsonl"
join_balanced_dynamic="$RAW_DIR/join-balanced-${PRESET}-dynamic-${GPU_LABEL}-tps256m.jsonl"
join_balanced_shuffle="$RAW_DIR/join-balanced-${PRESET}-shuffle-${GPU_LABEL}-tps256m.jsonl"
join_balanced_broadcast_fail="$RAW_DIR/join-balanced-${PRESET}-broadcast-fail-${GPU_LABEL}-tps256m.jsonl"
groupby_low="$RAW_DIR/groupby-low-${PRESET}-${GPU_LABEL}.jsonl"
groupby_high_success="$RAW_DIR/groupby-high-${PRESET}-success-${GPU_LABEL}.jsonl"
groupby_high_tree_fail="$RAW_DIR/groupby-high-${PRESET}-tree-fail-${GPU_LABEL}.jsonl"

echo "Running paper-cut microbenchmarks with CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
echo "Preset=$PRESET frontend=$FRONTEND iterations=$ITERATIONS warmup=$WARMUP"

run_benchmark \
  --frontend "$FRONTEND" \
  --preset "$PRESET" \
  --case join-small-build \
  --strategies dynamic,broadcast_right,shuffle \
  --iterations "$ITERATIONS" \
  --warmup "$WARMUP" \
  --output "$join_small" \
  "${regen_args[@]}"

run_benchmark \
  --frontend "$FRONTEND" \
  --preset "$PRESET" \
  --case join-balanced \
  --strategies dynamic \
  --iterations "$ITERATIONS" \
  --warmup "$WARMUP" \
  --target-partition-size "$JOIN_BALANCED_TARGET_PARTITION_SIZE" \
  --output "$join_balanced_dynamic" \
  "${regen_args[@]}"

run_benchmark \
  --frontend "$FRONTEND" \
  --preset "$PRESET" \
  --case join-balanced \
  --strategies shuffle \
  --iterations "$ITERATIONS" \
  --warmup "$WARMUP" \
  --target-partition-size "$JOIN_BALANCED_TARGET_PARTITION_SIZE" \
  --output "$join_balanced_shuffle" \
  "${regen_args[@]}"

run_benchmark \
  --frontend "$FRONTEND" \
  --preset "$PRESET" \
  --case join-balanced \
  --strategies broadcast_right \
  --iterations "$FAIL_ITERATIONS" \
  --warmup "$FAIL_WARMUP" \
  --target-partition-size "$JOIN_BALANCED_TARGET_PARTITION_SIZE" \
  --output "$join_balanced_broadcast_fail" \
  "${regen_args[@]}"

run_benchmark \
  --frontend "$FRONTEND" \
  --preset "$PRESET" \
  --case groupby-low-cardinality \
  --strategies dynamic,tree,shuffle \
  --iterations "$ITERATIONS" \
  --warmup "$WARMUP" \
  --output "$groupby_low" \
  "${regen_args[@]}"

run_benchmark \
  --frontend "$FRONTEND" \
  --preset "$PRESET" \
  --case groupby-high-cardinality \
  --strategies dynamic,shuffle \
  --iterations "$ITERATIONS" \
  --warmup "$WARMUP" \
  --output "$groupby_high_success" \
  "${regen_args[@]}"

run_benchmark \
  --frontend "$FRONTEND" \
  --preset "$PRESET" \
  --case groupby-high-cardinality \
  --strategies tree \
  --iterations "$FAIL_ITERATIONS" \
  --warmup "$FAIL_WARMUP" \
  --output "$groupby_high_tree_fail" \
  "${regen_args[@]}"

plot_figure \
  "$join_small" \
  "$join_balanced_dynamic" \
  "$join_balanced_shuffle" \
  "$join_balanced_broadcast_fail" \
  --benchmark join \
  --output "$FIGURE_DIR/join-microbenchmark-results.pdf" \
  --summary-output "$SUMMARY_DIR/join-microbenchmark-results-${GPU_LABEL}.md" \
  --title "$TITLE"

plot_figure \
  "$groupby_low" \
  "$groupby_high_success" \
  "$groupby_high_tree_fail" \
  --benchmark groupby \
  --output "$FIGURE_DIR/groupby-microbenchmark-results.pdf" \
  --summary-output "$SUMMARY_DIR/groupby-microbenchmark-results-${GPU_LABEL}.md" \
  --title "$TITLE"

if [[ "$BUILD_PAPER" == "1" ]]; then
  "$MAKE"
fi

echo "Wrote:"
echo "  $FIGURE_DIR/join-microbenchmark-results.pdf"
echo "  $FIGURE_DIR/groupby-microbenchmark-results.pdf"
echo "  $SUMMARY_DIR/join-microbenchmark-results-${GPU_LABEL}.md"
echo "  $SUMMARY_DIR/groupby-microbenchmark-results-${GPU_LABEL}.md"
