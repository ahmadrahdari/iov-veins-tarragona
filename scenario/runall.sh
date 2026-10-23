#!/bin/bash
# Runs the 18 runs (6 densities x 3 seeds) of the three configurations.
cd "$(dirname "$0")"
mkdir -p runlogs
for r in $(seq 0 17); do
  for cfg in Proposed ProposedA Baseline; do
    nice -n 5 ./run.sh $cfg $r > runlogs/${cfg}_$r.txt 2>&1
    echo "done $cfg $r $(date +%T)"
  done
done
echo SIM_ALL_DONE
