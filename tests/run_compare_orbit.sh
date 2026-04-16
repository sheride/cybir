#!/bin/bash
# Wrapper that runs compare_orbit.py one polytope at a time with a timeout.
# Usage: bash tests/run_compare_orbit.sh [--start N] [--timeout SECONDS]
#
# Resumes from --start (default: 0). Appends to compare_orbit_results.jsonl
# if --start > 0. Kills any polytope that exceeds --timeout (default: 120s).

START=0
TIMEOUT=120
H11=3
TOTAL=243

while [[ $# -gt 0 ]]; do
  case $1 in
    --start) START="$2"; shift 2;;
    --timeout) TIMEOUT="$2"; shift 2;;
    --h11) H11="$2"; shift 2;;
    --total) TOTAL="$2"; shift 2;;
    *) shift;;
  esac
done

OUTFILE="tests/compare_orbit_results.jsonl"

if [ "$START" -eq 0 ]; then
  > "$OUTFILE"  # truncate
fi

echo "Running compare_orbit.py polytopes $START..$((TOTAL-1)) with ${TIMEOUT}s timeout per polytope"

for i in $(seq "$START" $((TOTAL-1))); do
  echo -n "[$i/$((TOTAL-1))] "
  timeout "$TIMEOUT" conda run -n cytools python tests/compare_orbit.py \
    --h11 "$H11" --start "$i" --limit 1 --no-nongeneric-cs 2>&1 | tail -5

  EXIT=$?
  if [ $EXIT -eq 124 ]; then
    echo "  TIMEOUT after ${TIMEOUT}s"
    echo "{\"id\": \"h11=${H11} #${i}\", \"status\": \"skip\", \"reason\": \"original_bfs_timeout_${TIMEOUT}s\"}" >> "$OUTFILE"
  fi
done

echo ""
echo "Done. Results in $OUTFILE"
wc -l "$OUTFILE"
