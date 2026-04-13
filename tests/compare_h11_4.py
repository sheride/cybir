"""Compare cybir (adaptive + fixed deg) against original at h11=4.

For each polytope, runs three configurations:
1. Original ExtendedKahlerCone (deg=10)
2. Cybir adaptive (start deg=4, ceiling=20)
3. Cybir fixed (deg=20)

Compares phases, infinity gens, effective gens, coxeter refs.
Saves results incrementally to JSONL.
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
from extended_kahler_cone import ExtendedKahlerCone
from cybir.core.ekc import CYBirationalClass
from cybir.core.patch import patch_cytools

patch_cytools()


def _to_plain_set(s):
    return {tuple(int(x) for x in t) for t in s}


def _to_plain_tup(s):
    return {tuple(tuple(int(x) for x in row) for row in m) for m in s}


def extract_result(ekc):
    return {
        "n_phases": len(ekc.phases),
        "inf_gens": _to_plain_set(ekc.infinity_cone_gens),
        "eff_gens": _to_plain_set(ekc.eff_cone_gens),
        "cox_refs": _to_plain_tup(ekc.coxeter_refs),
    }


def results_match(a, b):
    return (a["n_phases"] == b["n_phases"]
            and a["inf_gens"] == b["inf_gens"]
            and a["eff_gens"] == b["eff_gens"]
            and a["cox_refs"] == b["cox_refs"])


def run_original(polytope, max_deg=10):
    t0 = time.perf_counter()
    ekc = ExtendedKahlerCone(polytope)
    ekc.setup_root(max_deg=max_deg)
    ekc.construct_phases(weyl=False, verbose=False)
    elapsed = time.perf_counter() - t0
    return {
        "n_phases": len(ekc.cys),
        "inf_gens": _to_plain_set(ekc.infinity_cone_gens),
        "eff_gens": _to_plain_set(ekc.eff_cone_gens),
        "cox_refs": _to_plain_tup(ekc.coxeter_refs),
    }, elapsed, ekc.root._gvs


def run_cybir_adaptive(cy, gvs=None):
    t0 = time.perf_counter()
    ekc = CYBirationalClass.from_gv(
        cy, max_deg=4, verbose=False, max_deg_ceiling=20, gvs=gvs)
    elapsed = time.perf_counter() - t0
    return extract_result(ekc), elapsed, len(ekc._unresolved_walls)


def run_cybir_fixed(cy, gvs=None):
    t0 = time.perf_counter()
    ekc = CYBirationalClass.from_gv(
        cy, max_deg=20, verbose=False, max_deg_ceiling=20, gvs=gvs)
    elapsed = time.perf_counter() - t0
    return extract_result(ekc), elapsed, len(ekc._unresolved_walls)


if __name__ == "__main__":
    n_polys = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    outpath = "tests/compare_h11_4_results.jsonl"

    polys = fetch_polytopes(h11=4, lattice="N", limit=n_polys)
    print(f"Testing {len(polys)} h11=4 polytopes\n", flush=True)

    results = []
    with open(outpath, "w") as f:
        for i, p in enumerate(polys):
            row = {"id": f"h11=4 #{i}"}

            # Original
            try:
                orig_res, orig_time, orig_gvs = run_original(p, max_deg=10)
                row["orig_time"] = round(orig_time, 2)
                row["orig_phases"] = orig_res["n_phases"]
            except Exception as e:
                row["orig_error"] = str(e)
                orig_res = None
                orig_gvs = None
                row["orig_time"] = None

            cy = p.triangulate().get_cy()

            # Cybir adaptive (no GV sharing — full adaptive test)
            try:
                adapt_res, adapt_time, adapt_unresolved = run_cybir_adaptive(cy)
                row["adapt_time"] = round(adapt_time, 2)
                row["adapt_phases"] = adapt_res["n_phases"]
                row["adapt_unresolved"] = adapt_unresolved
            except Exception as e:
                row["adapt_error"] = str(e)
                adapt_res = None
                row["adapt_time"] = None

            # Cybir fixed deg=20 (no GV sharing)
            try:
                fixed_res, fixed_time, fixed_unresolved = run_cybir_fixed(cy)
                row["fixed_time"] = round(fixed_time, 2)
                row["fixed_phases"] = fixed_res["n_phases"]
                row["fixed_unresolved"] = fixed_unresolved
            except Exception as e:
                row["fixed_error"] = str(e)
                fixed_res = None
                row["fixed_time"] = None

            # Comparisons
            if orig_res and adapt_res:
                row["adapt_vs_orig"] = results_match(adapt_res, orig_res)
            if orig_res and fixed_res:
                row["fixed_vs_orig"] = results_match(fixed_res, orig_res)
            if adapt_res and fixed_res:
                row["adapt_vs_fixed"] = results_match(adapt_res, fixed_res)

            results.append(row)
            f.write(json.dumps(row) + "\n")
            f.flush()

            print(
                f"  #{i}: "
                f"orig={row.get('orig_time', 'ERR')}s/{row.get('orig_phases', '?')}ph  "
                f"adapt={row.get('adapt_time', 'ERR')}s/{row.get('adapt_phases', '?')}ph  "
                f"fixed={row.get('fixed_time', 'ERR')}s/{row.get('fixed_phases', '?')}ph  "
                f"match={row.get('adapt_vs_orig', '?')}/{row.get('fixed_vs_orig', '?')}",
                flush=True,
            )

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    n = len(results)
    adapt_match = sum(1 for r in results if r.get("adapt_vs_orig"))
    fixed_match = sum(1 for r in results if r.get("fixed_vs_orig"))
    adapt_times = [r["adapt_time"] for r in results if r.get("adapt_time") is not None]
    fixed_times = [r["fixed_time"] for r in results if r.get("fixed_time") is not None]
    orig_times = [r["orig_time"] for r in results if r.get("orig_time") is not None]

    print(f"\n  Polytopes: {n}")
    print(f"  Adaptive vs original: {adapt_match}/{n} match")
    print(f"  Fixed vs original:    {fixed_match}/{n} match")
    if orig_times:
        print(f"\n  Original (deg=10):  avg={sum(orig_times)/len(orig_times):.2f}s  total={sum(orig_times):.1f}s")
    if adapt_times:
        print(f"  Adaptive (deg=4+):  avg={sum(adapt_times)/len(adapt_times):.2f}s  total={sum(adapt_times):.1f}s")
    if fixed_times:
        print(f"  Fixed (deg=20):     avg={sum(fixed_times)/len(fixed_times):.2f}s  total={sum(fixed_times):.1f}s")
    if orig_times and adapt_times:
        print(f"\n  Adaptive speedup: {sum(orig_times)/sum(adapt_times):.1f}x vs original")

    print(f"\n  Results saved to {outpath}")
