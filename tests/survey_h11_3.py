"""h11=3 survey: run all 243 favorable polytopes through the EKC pipeline.

Constructs fundamental domain + Coxeter orbit expansion for each
polytope, saving incremental JSONL results with phase counts,
contraction types, Coxeter data, and timing.

Usage:
    conda run -n cytools python tests/survey_h11_3.py --limit 10
    conda run -n cytools python tests/survey_h11_3.py              # full run
    conda run -n cytools python tests/survey_h11_3.py --start 50   # resume
"""

import argparse
import json
import logging
import time
from collections import Counter

from cytools import fetch_polytopes

from cybir.core.ekc import CYBirationalClass
from cybir.core.types import ContractionType

# Silence chatty CYTools/cybir output during survey
logging.disable(logging.INFO)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run h11=3 EKC survey on all favorable polytopes")
    parser.add_argument("--limit", type=int, default=None,
                        help="Number of polytopes to process (default: all)")
    parser.add_argument("--max-deg", type=int, default=10,
                        help="Initial GV degree (default: 10)")
    parser.add_argument("--outfile", type=str,
                        default="tests/survey_h11_3_results.jsonl",
                        help="Output JSONL path (default: tests/survey_h11_3_results.jsonl)")
    parser.add_argument("--skip-orbit", action="store_true",
                        help="Skip orbit expansion (faster debugging runs)")
    parser.add_argument("--start", type=int, default=0,
                        help="Resume from polytope index N (default: 0)")
    return parser.parse_args()


def survey_one(poly_idx, polytope, max_deg, skip_orbit):
    """Run the EKC pipeline on a single polytope, returning a result dict."""
    t0 = time.time()
    try:
        cy = polytope.triangulate().get_cy()
        ekc = CYBirationalClass.from_gv(
            cy, max_deg=max_deg, verbose=False, validate_stability=True)

        n_phases_fund = len(ekc.phases)

        # Orbit expansion
        if not skip_orbit and ekc.sym_flop_refs:
            ekc.apply_coxeter_orbit(phases=True)

        n_phases_total = ekc._graph.num_phases

        # Contraction type distribution
        type_counts = Counter()
        for c in ekc.contractions:
            if c.contraction_type is not None:
                type_counts[c.contraction_type.name] += 1

        # Coxeter info (serializable)
        cox_type = ekc.coxeter_type
        cox_type_serial = [list(t) for t in cox_type] if cox_type else None

        elapsed = time.time() - t0
        return {
            "poly_id": poly_idx,
            "h11": 3,
            "favorable": True,
            "n_phases_fund": n_phases_fund,
            "n_phases_total": n_phases_total,
            "contraction_types": dict(type_counts),
            "coxeter_type": cox_type_serial,
            "coxeter_order": ekc.coxeter_order,
            "n_sym_flop_refs": len(ekc.sym_flop_refs),
            "n_infinity_gens": len(ekc.infinity_cone_gens),
            "n_eff_gens": len(ekc.eff_cone_gens),
            "n_unresolved": len(ekc._unresolved_walls),
            "time_s": round(elapsed, 2),
            "status": "ok",
            "error": None,
            "stability_validated": True,
        }

    except Exception as e:
        elapsed = time.time() - t0
        return {
            "poly_id": poly_idx,
            "h11": 3,
            "favorable": True,
            "n_phases_fund": None,
            "n_phases_total": None,
            "contraction_types": {},
            "coxeter_type": None,
            "coxeter_order": None,
            "n_sym_flop_refs": None,
            "n_infinity_gens": None,
            "n_eff_gens": None,
            "n_unresolved": None,
            "time_s": round(elapsed, 2),
            "status": "error",
            "error": str(e),
            "stability_validated": False,
        }


def main():
    args = parse_args()

    print(f"Fetching h11=3 polytopes...")
    polys = fetch_polytopes(h11=3, lattice="N")
    print(f"  Fetched {len(polys)} polytopes")

    # Filter to favorable polytopes, tracking non-favorable
    favorable_indices = []
    for i, p in enumerate(polys):
        if p.is_favorable("M"):
            favorable_indices.append(i)
        else:
            print(f"  SKIP polytope #{i}: non-favorable (is_favorable('M') = False)")

    print(f"  Favorable: {len(favorable_indices)} / {len(polys)}")

    # Apply --start and --limit
    work = favorable_indices[args.start:]
    if args.limit is not None:
        work = work[:args.limit]

    print(f"  Processing {len(work)} polytopes "
          f"(start={args.start}, limit={args.limit})")
    print(f"  Output: {args.outfile}")
    print(f"  Max degree: {args.max_deg}")
    print(f"  Skip orbit: {args.skip_orbit}")
    print()

    # Aggregate stats
    n_ok = 0
    n_error = 0
    n_with_orbit = 0
    agg_types = Counter()

    with open(args.outfile, "a" if args.start > 0 else "w") as f:
        for count, poly_idx in enumerate(work, 1):
            p = polys[poly_idx]
            print(f"[{count}/{len(work)}] Polytope #{poly_idx} ... ",
                  end="", flush=True)

            result = survey_one(poly_idx, p, args.max_deg, args.skip_orbit)

            f.write(json.dumps(result) + "\n")
            f.flush()

            if result["status"] == "ok":
                n_ok += 1
                agg_types.update(result["contraction_types"])
                if (result["n_sym_flop_refs"] or 0) > 0:
                    n_with_orbit += 1
                print(f"ok  fund={result['n_phases_fund']} "
                      f"total={result['n_phases_total']} "
                      f"cox={result['coxeter_type']} "
                      f"({result['time_s']:.1f}s)")
            else:
                n_error += 1
                print(f"ERROR: {result['error']} ({result['time_s']:.1f}s)")

    # Final summary
    print()
    print("=" * 60)
    print("SURVEY SUMMARY")
    print("=" * 60)
    print(f"  Processed:    {len(work)}")
    print(f"  OK:           {n_ok}")
    print(f"  Errors:       {n_error}")
    print(f"  With orbit:   {n_with_orbit}")
    print()
    print("  Contraction type distribution:")
    for name, count in agg_types.most_common():
        print(f"    {name}: {count}")
    print()
    print(f"  Results saved to {args.outfile}")


if __name__ == "__main__":
    main()
