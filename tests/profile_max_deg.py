"""Profile how max_deg affects correctness and runtime for h11=2 polytopes.

For each polytope, runs the pipeline at max_deg = 2, 3, 4, ..., 10 and records:
- Whether the result matches the max_deg=10 reference (phases, inf gens, eff gens, coxeter refs)
- Wall-clock time for setup_root (the expensive part)
- The minimum max_deg that still gives the correct answer
"""

import json
import sys
import time

import numpy as np
import logging

logging.disable(logging.INFO)

sys.path.insert(0, "/Users/elijahsheridan/Research/string/cytools_code/cornell-dev")
sys.path.insert(0, "/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/Elijah")
sys.path.insert(0, "/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah")

from cytools import fetch_polytopes
from cybir.core.ekc import CYBirationalClass
from cybir.core.patch import patch_cytools

patch_cytools()

outpath = "tests/profile_max_deg_results.jsonl"


def _to_plain_set(s):
    return {tuple(int(x) for x in t) for t in s}


def run_at_deg(cy, deg):
    """Run pipeline at given max_deg, return result dict and timing."""
    t0 = time.perf_counter()
    try:
        ekc = CYBirationalClass.from_gv(cy, max_deg=deg, verbose=False, limit=100)
    except Exception as e:
        return None, time.perf_counter() - t0, str(e)
    elapsed = time.perf_counter() - t0

    return {
        "n_phases": len(ekc.phases),
        "inf_gens": _to_plain_set(ekc.infinity_cone_gens),
        "eff_gens": _to_plain_set(ekc.eff_cone_gens),
        "cox_refs": set(ekc.coxeter_refs),
    }, elapsed, None


def results_match(a, b):
    return (a["n_phases"] == b["n_phases"]
            and a["inf_gens"] == b["inf_gens"]
            and a["eff_gens"] == b["eff_gens"]
            and a["cox_refs"] == b["cox_refs"])


if __name__ == "__main__":
    polys = fetch_polytopes(h11=2, lattice="N")
    deg_range = list(range(2, 11))

    print(f"Testing max_deg = {deg_range} on {len(polys)} h11=2 polytopes\n")

    all_results = []

    with open(outpath, "w") as f:
        for i, p in enumerate(polys):
            cy = p.triangulate().get_cy()

            row = {"id": f"h11=2 #{i}", "timings": {}, "matches": {}, "errors": {}}

            # Reference: max_deg=10
            ref, ref_time, ref_err = run_at_deg(cy, 10)
            row["timings"]["10"] = round(ref_time, 4)
            if ref_err:
                row["errors"]["10"] = ref_err
                print(f"  #{i}: ref FAILED — {ref_err}")
                f.write(json.dumps(row) + "\n")
                f.flush()
                continue

            row["ref_phases"] = ref["n_phases"]
            min_deg = 10

            # Test lower degrees
            for deg in deg_range[:-1]:  # 2..9
                result, elapsed, err = run_at_deg(cy, deg)
                row["timings"][str(deg)] = round(elapsed, 4)
                if err:
                    row["matches"][str(deg)] = False
                    row["errors"][str(deg)] = err
                elif result is None:
                    row["matches"][str(deg)] = False
                else:
                    match = results_match(result, ref)
                    row["matches"][str(deg)] = match
                    if match and deg < min_deg:
                        min_deg = deg

            row["min_deg"] = min_deg

            # Find actual minimum (lowest deg that matches)
            actual_min = 10
            for deg in deg_range[:-1]:
                if row["matches"].get(str(deg), False):
                    actual_min = deg
                    break
            row["min_deg"] = actual_min

            all_results.append(row)
            f.write(json.dumps(row) + "\n")
            f.flush()

            timing_str = "  ".join(
                f"d={d}:{row['timings'].get(str(d), '?'):.2f}s"
                for d in [2, 4, 6, 8, 10]
                if str(d) in row["timings"]
            )
            print(f"  #{i}: min_deg={actual_min}  phases={ref['n_phases']}  [{timing_str}]")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    ok = [r for r in all_results if "min_deg" in r]

    # Distribution of minimum degrees
    from collections import Counter
    min_deg_dist = Counter(r["min_deg"] for r in ok)
    print(f"\n  Minimum max_deg needed for correct answer:")
    for deg in sorted(min_deg_dist.keys()):
        print(f"    max_deg={deg}: {min_deg_dist[deg]} polytopes")

    # Average timing by degree
    print(f"\n  Average setup_root time by max_deg:")
    for deg in deg_range:
        times = [r["timings"].get(str(deg), None) for r in ok]
        times = [t for t in times if t is not None]
        if times:
            avg = sum(times) / len(times)
            print(f"    max_deg={deg:2d}: {avg:.3f}s avg  (n={len(times)})")

    # Speedup from using minimum degree
    total_at_10 = sum(r["timings"].get("10", 0) for r in ok)
    total_at_min = sum(
        r["timings"].get(str(r["min_deg"]), r["timings"].get("10", 0))
        for r in ok
    )
    print(f"\n  Total time at max_deg=10:  {total_at_10:.1f}s")
    print(f"  Total time at min needed: {total_at_min:.1f}s")
    if total_at_10 > 0:
        print(f"  Speedup: {total_at_10/total_at_min:.1f}x")

    print(f"\n  Results saved to {outpath}")
