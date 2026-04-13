"""Profile cybir pipeline on all h11=2 polytopes.

Breaks down wall-clock time per pipeline stage for each polytope,
then aggregates to find the slowest parts.
"""

import json
import sys
import time

import numpy as np
import logging

logging.disable(logging.INFO)

from cytools import fetch_polytopes
from cybir.core.ekc import CYBirationalClass
from cybir.core.patch import patch_cytools

patch_cytools()

outpath = "tests/profile_h11_2_results.jsonl"


def profile_one(polytope, poly_id, max_deg=10):
    """Profile a single polytope through the full pipeline."""
    cy = polytope.triangulate().get_cy()
    timings = {"id": poly_id, "h11": int(polytope.h11("N"))}

    # Stage 1: setup_root (includes GV computation)
    ekc = CYBirationalClass(cy)
    t0 = time.perf_counter()
    ekc.setup_root(max_deg=max_deg)
    timings["setup_root"] = time.perf_counter() - t0

    # Stage 2: construct_phases (BFS)
    t0 = time.perf_counter()
    ekc.construct_phases(verbose=False)
    timings["construct_phases"] = time.perf_counter() - t0

    # Stage 3: apply_coxeter_orbit
    t0 = time.perf_counter()
    ekc.apply_coxeter_orbit()
    timings["apply_coxeter_orbit"] = time.perf_counter() - t0

    # Stats
    timings["n_phases_fund"] = len([
        p for p in ekc.phases if p.label not in ekc._weyl_phases
    ])
    timings["n_phases_total"] = len(ekc.phases)
    timings["n_contractions"] = len(ekc.contractions)
    timings["n_sym_flop_pairs"] = len(ekc._sym_flop_pairs)
    timings["coxeter_type"] = str(ekc.coxeter_type) if ekc.coxeter_type else None
    timings["coxeter_order"] = ekc.coxeter_order
    timings["total"] = timings["setup_root"] + timings["construct_phases"] + timings["apply_coxeter_orbit"]

    return timings


if __name__ == "__main__":
    polys = fetch_polytopes(h11=2, lattice="N")
    print(f"Profiling {len(polys)} h11=2 polytopes...")

    all_timings = []
    with open(outpath, "w") as f:
        for i, p in enumerate(polys):
            try:
                t = profile_one(p, f"h11=2 #{i}")
                all_timings.append(t)
                f.write(json.dumps(t) + "\n")
                f.flush()
                print(f"  #{i}: total={t['total']:.3f}s  "
                      f"(setup={t['setup_root']:.3f}, bfs={t['construct_phases']:.3f}, "
                      f"orbit={t['apply_coxeter_orbit']:.3f})  "
                      f"phases={t['n_phases_fund']}/{t['n_phases_total']}  "
                      f"sym_flops={t['n_sym_flop_pairs']}")
            except Exception as e:
                print(f"  #{i}: FAILED — {e}")
                f.write(json.dumps({"id": f"h11=2 #{i}", "error": str(e)}) + "\n")
                f.flush()

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    ok = [t for t in all_timings if "error" not in t]
    if not ok:
        print("No successful runs.")
        sys.exit(1)

    stages = ["setup_root", "construct_phases", "apply_coxeter_orbit"]
    totals = {s: sum(t[s] for t in ok) for s in stages}
    grand_total = sum(t["total"] for t in ok)

    print(f"\n  Polytopes: {len(ok)}/{len(polys)}")
    print(f"  Grand total: {grand_total:.2f}s")
    print(f"\n  Stage breakdown (total across all polytopes):")
    for s in stages:
        pct = 100 * totals[s] / grand_total if grand_total > 0 else 0
        avg = totals[s] / len(ok)
        print(f"    {s:25s}  {totals[s]:7.2f}s  ({pct:5.1f}%)  avg={avg:.3f}s")

    # Slowest polytopes
    print(f"\n  Slowest 5 polytopes:")
    for t in sorted(ok, key=lambda x: x["total"], reverse=True)[:5]:
        print(f"    {t['id']:15s}  {t['total']:.3f}s  "
              f"(setup={t['setup_root']:.3f}, bfs={t['construct_phases']:.3f}, "
              f"orbit={t['apply_coxeter_orbit']:.3f})  "
              f"phases={t['n_phases_fund']}/{t['n_phases_total']}")

    # Which polytopes have nontrivial Coxeter groups?
    with_orbit = [t for t in ok if t["coxeter_order"] and t["coxeter_order"] > 1]
    if with_orbit:
        print(f"\n  Polytopes with nontrivial Coxeter group: {len(with_orbit)}")
        for t in with_orbit:
            print(f"    {t['id']:15s}  type={t['coxeter_type']}  |W|={t['coxeter_order']}  "
                  f"phases={t['n_phases_fund']}->{t['n_phases_total']}")

    print(f"\n  Results saved to {outpath}")
