"""Compare cybir BFS pipeline against original ExtendedKahlerCone.

Runs both implementations on the same CYTools polytopes and compares:
- Number of phases
- Infinity/effective cone generators
- Coxeter reflections
"""

import json
import sys
import time

import numpy as np
import logging

# Silence chatty output during comparison
logging.disable(logging.INFO)

sys.path.insert(0, "/Users/elijahsheridan/Research/string/cytools_code/cornell-dev")
sys.path.insert(0, "/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/Elijah")
sys.path.insert(0, "/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah")

from cytools import Polytope
from extended_kahler_cone import ExtendedKahlerCone
from cybir.core.ekc import CYBirationalClass


def _to_plain_set(s):
    """Convert a set of numpy tuples to plain Python int tuples."""
    return {tuple(int(x) for x in t) for t in s}


def _to_plain_set_of_tuples(s):
    """Convert a set of tuple-of-tuples (matrices) to plain ints."""
    return {tuple(tuple(int(x) for x in row) for row in m) for m in s}


def run_original(polytope, max_deg=10, limit=100):
    """Run original ExtendedKahlerCone."""
    ekc = ExtendedKahlerCone(polytope)
    ekc.setup_root(max_deg=max_deg)
    ekc.construct_phases(weyl=False, verbose=False, limit=limit)
    return ekc


def run_cybir(cy, max_deg=10, limit=100, gvs=None):
    """Run cybir CYBirationalClass."""
    ekc = CYBirationalClass.from_gv(
        cy, max_deg=max_deg, verbose=False, limit=limit, gvs=gvs)
    return ekc


def compare(poly_id, polytope, max_deg=10, limit=100, outfile=None):
    """Run both and compare. Write result line to outfile if given."""
    print(f"\n{'='*60}")
    print(f"Polytope {poly_id} (h11={polytope.h11('N')})")
    print(f"{'='*60}")

    # Run original
    try:
        orig = run_original(polytope, max_deg=max_deg, limit=limit)
    except Exception as e:
        print(f"  Original FAILED: {e}")
        if outfile:
            outfile.write(json.dumps({
                "id": poly_id, "status": "skip", "reason": f"original: {e}"
            }) + "\n")
            outfile.flush()
        return None  # can't compare

    # Run cybir -- share GVs from original to avoid recompute
    try:
        cy = polytope.triangulate().get_cy()
        gvs = orig.root._gvs
        new = run_cybir(cy, max_deg=max_deg, limit=limit, gvs=gvs)
    except Exception as e:
        print(f"  Cybir FAILED: {e}")
        if outfile:
            outfile.write(json.dumps({
                "id": poly_id, "status": "fail", "reason": f"cybir: {e}"
            }) + "\n")
            outfile.flush()
        return False

    # Compare number of phases
    n_orig = len(orig.cys)
    n_new = len(new.phases)
    match_phases = (n_orig == n_new)
    print(f"  Phases:       original={n_orig}, cybir={n_new}  "
          f"{'MATCH' if match_phases else 'MISMATCH'}")

    # Compare infinity cone generators
    orig_inf = _to_plain_set(orig.infinity_cone_gens)
    new_inf = set(new.infinity_cone_gens)  # already frozenset of plain tuples
    match_inf = (orig_inf == new_inf)
    print(f"  Infinity gens: original={len(orig_inf)}, cybir={len(new_inf)}  "
          f"{'MATCH' if match_inf else 'MISMATCH'}")
    if not match_inf:
        print(f"    original: {sorted(orig_inf)}")
        print(f"    cybir:    {sorted(new_inf)}")

    # Compare effective cone generators
    orig_eff = _to_plain_set(orig.eff_cone_gens)
    new_eff = set(new.eff_cone_gens)
    match_eff = (orig_eff == new_eff)
    print(f"  Effective gens: original={len(orig_eff)}, cybir={len(new_eff)}  "
          f"{'MATCH' if match_eff else 'MISMATCH'}")
    if not match_eff:
        print(f"    original: {sorted(orig_eff)}")
        print(f"    cybir:    {sorted(new_eff)}")

    # Compare coxeter reflections
    orig_cox = _to_plain_set_of_tuples(orig.coxeter_refs)
    new_cox = set(new.coxeter_refs)  # already frozenset of tuple-of-tuples
    match_cox = (orig_cox == new_cox)
    print(f"  Coxeter refs: original={len(orig_cox)}, cybir={len(new_cox)}  "
          f"{'MATCH' if match_cox else 'MISMATCH'}")

    ok = match_phases and match_inf and match_eff and match_cox
    status = "pass" if ok else "fail"
    print(f"\n  OVERALL: {status.upper()}")

    if outfile:
        outfile.write(json.dumps({
            "id": poly_id, "status": status,
            "phases_orig": n_orig, "phases_cybir": n_new,
            "inf_match": match_inf, "eff_match": match_eff,
            "cox_match": match_cox,
        }) + "\n")
        outfile.flush()

    return ok


if __name__ == "__main__":
    from cytools import fetch_polytopes

    results = []
    outpath = "tests/compare_bfs_results.jsonl"

    with open(outpath, "w") as f:
        # h11=2: all 36 polytopes
        print("\n" + "#"*60)
        print("# h11=2 polytopes")
        print("#"*60)
        polys_2 = fetch_polytopes(h11=2, lattice="N")
        for i, p in enumerate(polys_2):
            ok = compare(f"h11=2 #{i}", p, max_deg=10, outfile=f)
            results.append(("h11=2", i, ok))

        # h11=3: first 5 (these are slower)
        print("\n" + "#"*60)
        print("# h11=3 polytopes (first 5)")
        print("#"*60)
        polys_3 = fetch_polytopes(h11=3, lattice="N", limit=5)
        for i, p in enumerate(polys_3):
            ok = compare(f"h11=3 #{i}", p, max_deg=10, outfile=f)
            results.append(("h11=3", i, ok))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    passed = sum(1 for _, _, ok in results if ok)
    failed = sum(1 for _, _, ok in results if not ok)
    skipped = sum(1 for _, _, ok in results if ok is None)
    print(f"  Passed: {passed}/{len(results)}")
    print(f"  Failed: {failed}/{len(results)}")
    print(f"  Skipped (original failed): {skipped}/{len(results)}")
    for h, i, ok in results:
        if ok is False:
            print(f"    FAILED: {h} #{i}")
    print(f"\n  Results saved to {outpath}")
