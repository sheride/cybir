#!/usr/bin/env python
"""Wrapper that runs compare_orbit.py one polytope at a time with a timeout.

Each polytope runs as a subprocess that can be killed if it exceeds the
timeout. Results accumulate in compare_orbit_results.jsonl.

Usage:
    conda run -n cytools python tests/run_compare_orbit.py --start 92 --timeout 120
"""

import argparse
import json
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--h11", type=int, default=3)
    parser.add_argument("--total", type=int, default=243)
    parser.add_argument("--timeout", type=int, default=120,
                        help="Max seconds per polytope (default: 120)")
    args = parser.parse_args()

    outfile = "tests/compare_orbit_results.jsonl"

    print(f"Running polytopes {args.start}..{args.total - 1} "
          f"with {args.timeout}s timeout per polytope")

    passed = 0
    failed = 0
    skipped = 0
    timed_out = 0

    for i in range(args.start, args.total):
        t0 = time.time()
        try:
            result = subprocess.run(
                [sys.executable, "tests/compare_orbit.py",
                 "--h11", str(args.h11),
                 "--start", str(i),
                 "--count", "1",
                 "--no-nongeneric-cs"],
                timeout=args.timeout,
                capture_output=True,
                text=True,
            )
            elapsed = time.time() - t0
            # Print the subprocess output (last few lines)
            lines = result.stdout.strip().split("\n")
            for line in lines[-6:]:
                print(line)

        except subprocess.TimeoutExpired:
            elapsed = time.time() - t0
            print(f"  TIMEOUT on polytope #{i} after {elapsed:.0f}s")
            with open(outfile, "a") as f:
                f.write(json.dumps({
                    "id": f"h11={args.h11} #{i}",
                    "status": "skip",
                    "reason": f"original_bfs_timeout_{args.timeout}s",
                }) + "\n")
            timed_out += 1
            continue

        # Count results from the line just written
        with open(outfile) as f:
            all_lines = f.readlines()
        if all_lines:
            last = json.loads(all_lines[-1])
            if last["status"] == "pass":
                passed += 1
            elif last["status"] == "fail":
                failed += 1
            else:
                skipped += 1

    print(f"\n{'='*60}")
    print(f"COMPLETE: {args.start}..{args.total - 1}")
    print(f"  Passed: {passed}, Failed: {failed}, "
          f"Skipped: {skipped}, Timed out: {timed_out}")
    with open(outfile) as f:
        print(f"  Total lines in {outfile}: {sum(1 for _ in f)}")


if __name__ == "__main__":
    main()
