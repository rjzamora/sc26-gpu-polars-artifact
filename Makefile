PYTHON ?= python

.PHONY: list-cases q9-decisions

list-cases:
	$(PYTHON) -m experiments.scripts.run_microbenchmarks --list-cases

q9-decisions:
	$(PYTHON) experiments/scripts/plot_q9_decisions.py \
	  experiments/results/q9-sf1000-dynamic-decisions.md \
	  --output paper/figures/q9-plan-decisions.pdf
