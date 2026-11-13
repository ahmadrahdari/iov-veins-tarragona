#!/bin/bash
# Runs all configurations (Proposed, ProposedA, Baseline) x 18 runs, JOBS (default 2) at a time.
cd "$(dirname "$0")"
mkdir -p runlogs
jobs=""
for r in 17 16 15 14 13 12 11 10 9 8 7 6 5 4 3 2 1 0; do
  for cfg in Proposed ProposedA Baseline; do jobs="$jobs $cfg:$r"; done
done
printf "%s\n" $jobs | xargs -P ${JOBS:-2} -I{} bash -c 'c=${1%%:*}; r=${1##*:}; ./run.sh $c $r > runlogs/${c}_$r.txt 2>&1; echo "done $c $r $(date +%T)"' _ {}
echo SIM_ALL_DONE
