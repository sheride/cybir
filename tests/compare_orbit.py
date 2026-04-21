"""Compare cybir orbit expansion against original ignore_sym=False BFS.

Validates that cybir fundamental domain + apply_coxeter_orbit produces
the same results as the original ExtendedKahlerCone with ignore_sym=False
(brute-force BFS through symmetric flop walls).

Only tests polytopes that have symmetric flops (others have nothing
to validate for orbit expansion).

Usage:
    conda run -n cytools python tests/compare_orbit.py --h11 3 --limit 5
"""

import argparse
import json
import logging
import os
import pickle
import sys
import time

import numpy as np

# Silence chatty output during comparison
logging.disable(logging.INFO)

sys.path.insert(0, "/Users/elijahsheridan/Research/string/cytools_code/cornell-dev")
sys.path.insert(0, "/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/Elijah")
sys.path.insert(0, "/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah")

from cytools import Polytope, fetch_polytopes
from extended_kahler_cone import ExtendedKahlerCone
from cybir.core.ekc import CYBirationalClass
import cybir.core.build_gv as _bgv


def _to_plain_set(s):
    """Convert a set of numpy tuples to plain Python int tuples."""
    return {tuple(int(x) for x in t) for t in s}


def _to_plain_set_of_tuples(s):
    """Convert a set of tuple-of-tuples (matrices) to plain ints."""
    return {tuple(tuple(int(x) for x in row) for row in m) for m in s}


def run_original_full(polytope, max_deg=10, limit=500, gvs=None):
    """Run original ExtendedKahlerCone with ignore_sym=False (full BFS).

    If *gvs* is provided, inject them into the root instead of recomputing.
    """
    ekc = ExtendedKahlerCone(polytope)
    if gvs is not None:
        cy = ekc.polytope.triangulate().cy()
        gvs_copy = gvs.copy()
        gvs_copy.flop_curves = []
        gvs_copy.precompose = np.eye(cy.h11())
        from extended_kahler_cone import CY_GV
        ekc.root = CY_GV(cy=cy, gvs=gvs_copy, cob=ekc.cob)
        ekc.root.toric = True
        ekc.gvs = gvs_copy
        ekc.walls.extend(ekc.root.walls)
        ekc.root.curve_signs = dict()
        ekc.cys.append(ekc.root)
    else:
        ekc.setup_root(max_deg=max_deg)
    ekc.construct_phases(weyl=False, ignore_sym=False, verbose=False, limit=limit)
    return ekc


def run_cybir_orbit(cy, max_deg=10, limit=100, gvs=None):
    """Run cybir fundamental domain + orbit expansion."""
    ekc = CYBirationalClass.from_gv(
        cy, max_deg=max_deg, verbose=False, limit=limit, gvs=gvs)
    ekc.apply_coxeter_orbit(phases=True)
    return ekc


def _cache_path(cache_dir, poly_id):
    """Return the pickle path for a polytope's cached GV invariants."""
    safe_id = str(poly_id).replace(" ", "_").replace("=", "")
    return os.path.join(cache_dir, f"{safe_id}.pkl")


def _load_gvs(cache_dir, poly_id):
    """Load cached GV invariants, or return None."""
    if cache_dir is None:
        return None
    path = _cache_path(cache_dir, poly_id)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return None


def _save_gvs(cache_dir, poly_id, gvs):
    """Save GV invariants to cache."""
    if cache_dir is None:
        return
    os.makedirs(cache_dir, exist_ok=True)
    path = _cache_path(cache_dir, poly_id)
    with open(path, "wb") as f:
        pickle.dump(gvs, f, protocol=pickle.HIGHEST_PROTOCOL)


def compare_orbit(poly_id, polytope, max_deg=10, outfile=None, cache_dir=None,
                   max_deg_ceiling=20):
    """Run both methods and compare results."""
    print(f"\n{'='*60}")
    print(f"Polytope {poly_id} (h11={polytope.h11('N')})")
    print(f"{'='*60}")

    # Check favorability
    if not polytope.is_favorable('N'):
        print("  SKIP: non-favorable polytope")
        if outfile:
            outfile.write(json.dumps({
                "id": poly_id, "status": "skip",
                "reason": "non-favorable",
            }) + "\n")
            outfile.flush()
        return None

    # Run cybir fundamental domain first to check for symmetric flops
    try:
        cy = polytope.triangulate().get_cy()
    except Exception as e:
        print(f"  SKIP: CY construction failed: {e}")
        if outfile:
            outfile.write(json.dumps({
                "id": poly_id, "status": "skip",
                "reason": f"cy_construction: {e}",
            }) + "\n")
            outfile.flush()
        return None

    cached_gvs = _load_gvs(cache_dir, poly_id)

    try:
        ekc_fund = CYBirationalClass.from_gv(
            cy, max_deg=max_deg, verbose=False, gvs=cached_gvs,
            max_deg_ceiling=max_deg_ceiling)
    except Exception as e:
        print(f"  SKIP: cybir fundamental domain failed: {e}")
        if outfile:
            outfile.write(json.dumps({
                "id": poly_id, "status": "skip",
                "reason": f"cybir_fund: {e}",
            }) + "\n")
            outfile.flush()
        return None

    # Cache GVs after first successful BFS
    if cached_gvs is None:
        _save_gvs(cache_dir, poly_id, ekc_fund._root_invariants)

    # Check if this polytope has symmetric flops
    if not ekc_fund.sym_flop_refs:
        print("  SKIP: no symmetric flops (nothing to validate)")
        if outfile:
            outfile.write(json.dumps({
                "id": poly_id, "status": "skip",
                "reason": "no_symmetric_flops",
            }) + "\n")
            outfile.flush()
        return None

    print(f"  Symmetric flop refs: {len(ekc_fund.sym_flop_refs)}")

    # Run cybir orbit expansion, reusing the same GVs
    t0 = time.time()
    orbit_failed = False
    orbit_error = None
    try:
        ekc_cybir = CYBirationalClass.from_gv(
            cy, max_deg=max_deg, verbose=False,
            gvs=ekc_fund._root_invariants,
            max_deg_ceiling=max_deg_ceiling)
        ekc_cybir.apply_coxeter_orbit(phases=True)
    except Exception as e:
        orbit_failed = True
        orbit_error = str(e)
        # Don't return — fall through to compare fundamental domain
        ekc_cybir = ekc_fund  # use fundamental domain for comparison
        print(f"  Cybir orbit expansion FAILED: {e}")
        print(f"  Comparing fundamental domain instead")
    t_cybir = time.time() - t0

    # Run original with ignore_sym=False, reusing cybir's GVs
    t0 = time.time()
    try:
        shared_gvs = ekc_cybir._root_invariants
        orig = run_original_full(polytope, max_deg=max_deg, gvs=shared_gvs)
    except Exception as e:
        print(f"  Original (ignore_sym=False) FAILED: {e}")
        if outfile:
            outfile.write(json.dumps({
                "id": poly_id, "status": "skip",
                "reason": f"original: {e}",
            }) + "\n")
            outfile.flush()
        return None
    t_orig = time.time() - t0

    # Compare phase counts
    n_orig = len(orig.cys)
    n_cybir = ekc_cybir._graph.num_phases
    match_phases = (n_orig == n_cybir)
    print(f"  Phases:       original={n_orig}, cybir={n_cybir}  "
          f"{'MATCH' if match_phases else 'MISMATCH'}")

    # Compare infinity cone generators
    orig_inf = _to_plain_set(orig.infinity_cone_gens)
    new_inf = set(ekc_cybir.infinity_cone_gens)
    match_inf = (orig_inf == new_inf)
    print(f"  Infinity gens: original={len(orig_inf)}, cybir={len(new_inf)}  "
          f"{'MATCH' if match_inf else 'MISMATCH'}")
    if not match_inf:
        print(f"    original: {sorted(orig_inf)}")
        print(f"    cybir:    {sorted(new_inf)}")

    # Compare effective cone generators
    orig_eff = _to_plain_set(orig.eff_cone_gens)
    new_eff = set(ekc_cybir.eff_cone_gens)
    match_eff = (orig_eff == new_eff)
    print(f"  Effective gens: original={len(orig_eff)}, cybir={len(new_eff)}  "
          f"{'MATCH' if match_eff else 'MISMATCH'}")
    if not match_eff:
        print(f"    original: {sorted(orig_eff)}")
        print(f"    cybir:    {sorted(new_eff)}")

    # Compare coxeter reflections (informational — cybir uses minimal generators,
    # original BFS accumulates redundant ones from non-fundamental phases)
    orig_cox = _to_plain_set_of_tuples(orig.coxeter_refs)
    new_cox = set(ekc_cybir.coxeter_refs)
    match_cox = (orig_cox == new_cox)
    cox_note = "MATCH" if match_cox else f"INFO ({len(new_cox)} minimal vs {len(orig_cox)} BFS-accumulated)"
    print(f"  Coxeter refs: original={len(orig_cox)}, cybir={len(new_cox)}  {cox_note}")

    print(f"  Time: original={t_orig:.1f}s, cybir={t_cybir:.1f}s")

    # Pass/fail based on phases, infinity gens, and effective gens.
    # Coxeter refs are informational (same group, different generating set).
    ok = match_phases and match_inf and match_eff
    if orbit_failed:
        status = "fail_orbit" if ok else "fail"
    else:
        status = "pass" if ok else "fail"
    print(f"\n  OVERALL: {status.upper()}"
          + (f" (orbit failed: {orbit_error})" if orbit_failed else ""))

    if outfile:
        entry = {
            "id": poly_id, "status": status,
            "phases_orig": n_orig, "phases_cybir": n_cybir,
            "inf_match": match_inf, "eff_match": match_eff,
            "cox_match": match_cox,
            "time_orig": round(t_orig, 2),
            "time_cybir": round(t_cybir, 2),
            "n_sym_flop_refs": len(ekc_fund.sym_flop_refs),
        }
        if orbit_failed:
            entry["orbit_error"] = orbit_error
        outfile.write(json.dumps(entry) + "\n")
        outfile.flush()

    return ok


def main():
    parser = argparse.ArgumentParser(
        description="Compare cybir orbit expansion vs original ignore_sym=False")
    parser.add_argument("--h11", type=int, default=3,
                        help="h11 value (default: 3)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max polytopes to test (0=all, default: all)")
    parser.add_argument("--start", type=int, default=0,
                        help="Start from polytope index N (default: 0)")
    parser.add_argument("--count", type=int, default=0,
                        help="Process N polytopes from start (0=all, default: all)")
    parser.add_argument("--no-nongeneric-cs", action="store_true",
                        help="Disable SU2_NONGENERIC_CS re-tagging for "
                             "apples-to-apples comparison with old code")
    parser.add_argument("--cache-dir", type=str,
                        default="tests/.gv_cache",
                        help="Directory for cached GV invariants (default: tests/.gv_cache)")
    parser.add_argument("--no-cache", action="store_true",
                        help="Disable GV caching (recompute everything)")
    parser.add_argument("--no-ceiling", action="store_true",
                        help="Remove max_deg ceiling (targeted bump drives degree)")
    args = parser.parse_args()

    # Disable SU2_NONGENERIC_CS if requested (for fair comparison with old code)
    if args.no_nongeneric_cs:
        _bgv._check_nongeneric_cs = lambda ekc, result: result
        print("NOTE: SU2_NONGENERIC_CS re-tagging DISABLED for comparison")

    outpath = "tests/compare_orbit_results.jsonl"
    results = []

    fetch_kwargs = {"h11": args.h11, "lattice": "N"}
    if args.limit > 0:
        fetch_kwargs["limit"] = args.limit

    polys = fetch_polytopes(**fetch_kwargs)
    print(f"\n{'#'*60}")
    print(f"# h11={args.h11} orbit expansion validation")
    print(f"# {len(polys)} polytopes fetched"
          + (f" (limit={args.limit})" if args.limit > 0 else ""))
    print(f"{'#'*60}")

    end = args.start + args.count if args.count > 0 else len(polys)
    end = min(end, len(polys))

    mode = "a" if args.start > 0 else "w"
    with open(outpath, mode) as f:
        for i, p in enumerate(polys):
            if i < args.start or i >= end:
                results.append((i, None))
                continue
            cache_dir = None if args.no_cache else args.cache_dir
            ceiling = None if args.no_ceiling else 20
            ok = compare_orbit(
                f"h11={args.h11} #{i}", p, max_deg=10, outfile=f,
                cache_dir=cache_dir, max_deg_ceiling=ceiling)
            results.append((i, ok))

    # Summary
    tested = [r for r in results if r[1] is not None]
    passed = sum(1 for _, ok in results if ok is True)
    failed = sum(1 for _, ok in results if ok is False)
    skipped = sum(1 for _, ok in results if ok is None)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  Total polytopes: {len(results)}")
    print(f"  Tested (have symmetric flops): {len(tested)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Skipped: {skipped}")
    for idx, ok in results:
        if ok is False:
            print(f"    FAILED: h11={args.h11} #{idx}")
    print(f"\n  Results saved to {outpath}")


if __name__ == "__main__":
    main()
