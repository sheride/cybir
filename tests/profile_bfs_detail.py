"""Detailed profiling of construct_phases BFS internals.

Instruments the BFS loop to measure time per operation:
- GV series lookup (flop_gvs + gv_series_cybir)
- Classification (classify_contraction)
- Flop construction (flop_phase)
- Mori cone computation (cone_incl_flop)
- Tip computation (_compute_tip)
- Curve-sign deduplication
"""

import json
import sys
import time
from collections import defaultdict

import numpy as np
import logging

logging.disable(logging.INFO)

from cytools import fetch_polytopes
from cybir.core.patch import patch_cytools
from cybir.core.ekc import CYBirationalClass

patch_cytools()

outpath = "tests/profile_bfs_detail_results.jsonl"


def profile_bfs(polytope, poly_id, max_deg=10):
    """Profile BFS internals for a single polytope."""
    cy = polytope.triangulate().get_cy()

    # Setup root (not profiling this — we know it's GV compute)
    ekc = CYBirationalClass(cy)
    ekc.setup_root(max_deg=max_deg)

    # Now monkey-patch construct_phases to instrument it
    from cybir.core.build_gv import (
        _compute_tip, _accumulate_generators, _update_all_curve_signs,
        _find_matching_phase, normalize_curve
    )
    from cybir.core.classify import classify_contraction
    from cybir.core.flop import flop_phase
    from cybir.core.types import CalabiYauLite, ContractionType, ExtremalContraction
    from collections import deque

    timings = defaultdict(float)
    counts = defaultdict(int)

    root = ekc._graph.get_phase(ekc._root_label)
    mori_gens = root.mori_cone.extremal_rays()

    known_curves = set()
    curve_signs = {}
    flop_chains = {"CY_0": []}
    tips = {}
    undiagnosed = deque()
    phase_counter = 1

    t0 = time.perf_counter()
    root_tip = _compute_tip(root)
    timings["compute_tip"] += time.perf_counter() - t0
    counts["compute_tip"] += 1

    tips["CY_0"] = root_tip
    root._tip = root_tip

    for gen in mori_gens:
        nc = normalize_curve(gen)
        known_curves.add(nc)

    curve_signs["CY_0"] = {
        c: int(np.sign(root_tip @ np.array(c))) for c in known_curves
    }
    root._curve_signs = dict(curve_signs["CY_0"])

    for gen in mori_gens:
        undiagnosed.append((np.asarray(gen), "CY_0"))

    while undiagnosed and ekc._graph.num_phases < 100:
        wall_curve, source_label = undiagnosed.popleft()
        source = ekc._graph.get_phase(source_label)
        chain = flop_chains[source_label]

        # GV series lookup
        t0 = time.perf_counter()
        gvs_local = ekc._root_invariants.flop_gvs(chain)
        series = gvs_local.gv_series_cybir(wall_curve)
        timings["gv_series_lookup"] += time.perf_counter() - t0
        counts["gv_series_lookup"] += 1

        if not series:
            continue

        # Classification
        t0 = time.perf_counter()
        try:
            result = classify_contraction(
                source.int_nums, source.c2, wall_curve, series
            )
        except Exception:
            continue
        timings["classify"] += time.perf_counter() - t0
        counts["classify"] += 1

        ctype = result["contraction_type"]

        contraction = ExtremalContraction(
            contraction_curve=np.array(normalize_curve(wall_curve)),
            contraction_type=ctype,
            gv_invariant=result.get("gv_invariant"),
            effective_gv=result.get("effective_gv"),
            zero_vol_divisor=result.get("zero_vol_divisor"),
            coxeter_reflection=result.get("coxeter_reflection"),
            gv_series=result.get("gv_series"),
            gv_eff_1=result.get("gv_eff_1"),
        )

        result["contraction_curve"] = tuple(int(x) for x in wall_curve)
        _accumulate_generators(ekc, ctype, result)

        if ctype in (ContractionType.ASYMPTOTIC, ContractionType.CFT,
                     ContractionType.SU2, ContractionType.SYMMETRIC_FLOP):
            ekc._graph.add_contraction(contraction, source_label, source_label)
            continue

        # Flop construction
        new_label = f"CY_{phase_counter}"
        t0 = time.perf_counter()
        flopped = flop_phase(source, wall_curve, series, label=new_label)
        timings["flop_phase"] += time.perf_counter() - t0
        counts["flop_phase"] += 1

        # Mori cone computation
        flopped_chain = chain + [wall_curve]
        t0 = time.perf_counter()
        flopped_gvs = ekc._root_invariants.flop_gvs(flopped_chain)
        try:
            flopped_mori = flopped_gvs.cone_incl_flop()
        except Exception:
            continue
        timings["cone_incl_flop"] += time.perf_counter() - t0
        counts["cone_incl_flop"] += 1

        flopped._kahler_cone = flopped_mori.dual()
        flopped._mori_cone = flopped_mori

        # Curve-sign dedup
        tuple_curve = normalize_curve(wall_curve)
        if tuple_curve not in known_curves:
            known_curves.add(tuple_curve)
            t0 = time.perf_counter()
            _update_all_curve_signs(ekc, curve_signs, tuple_curve, tips)
            timings["update_curve_signs"] += time.perf_counter() - t0
            counts["update_curve_signs"] += 1

        # Tip computation for flopped phase
        t0 = time.perf_counter()
        try:
            flopped_tip = _compute_tip(flopped)
        except RuntimeError:
            continue
        timings["compute_tip"] += time.perf_counter() - t0
        counts["compute_tip"] += 1

        flopped_signs = {
            c: int(np.sign(flopped_tip @ np.array(c))) for c in known_curves
        }

        t0 = time.perf_counter()
        existing_label = _find_matching_phase(curve_signs, flopped_signs)
        timings["find_matching"] += time.perf_counter() - t0
        counts["find_matching"] += 1

        if existing_label is None:
            flopped._tip = flopped_tip
            flopped._curve_signs = dict(flopped_signs)
            ekc._graph.add_phase(flopped)
            ekc._graph.add_contraction(contraction, source_label, new_label)
            curve_signs[new_label] = flopped_signs
            flop_chains[new_label] = flopped_chain
            tips[new_label] = flopped_tip

            for gen in flopped_mori.extremal_rays():
                undiagnosed.append((np.asarray(gen), new_label))

            for ray in flopped._kahler_cone.rays():
                ekc._eff_cone_gens.add(tuple(np.round(ray).astype(int).tolist()))

            phase_counter += 1
        else:
            ekc._graph.add_contraction(contraction, source_label, existing_label)

    total_bfs = sum(timings.values())

    return {
        "id": poly_id,
        "n_phases": ekc._graph.num_phases,
        "n_walls_processed": counts.get("gv_series_lookup", 0),
        "total_bfs": total_bfs,
        "timings": dict(timings),
        "counts": dict(counts),
    }


if __name__ == "__main__":
    polys = fetch_polytopes(h11=2, lattice="N")
    print(f"Profiling BFS internals for {len(polys)} h11=2 polytopes...\n")

    all_results = []
    agg_timings = defaultdict(float)
    agg_counts = defaultdict(int)

    with open(outpath, "w") as f:
        for i, p in enumerate(polys):
            try:
                r = profile_bfs(p, f"h11=2 #{i}")
                all_results.append(r)
                f.write(json.dumps(r) + "\n")
                f.flush()

                for k, v in r["timings"].items():
                    agg_timings[k] += v
                for k, v in r["counts"].items():
                    agg_counts[k] += v

                top = sorted(r["timings"].items(), key=lambda x: x[1], reverse=True)
                top_str = ", ".join(f"{k}={v:.3f}s" for k, v in top[:3])
                print(f"  #{i}: bfs={r['total_bfs']:.3f}s  walls={r['n_walls_processed']}  phases={r['n_phases']}  [{top_str}]")
            except Exception as e:
                print(f"  #{i}: FAILED — {e}")

    grand_total = sum(agg_timings.values())

    print(f"\n{'='*70}")
    print("BFS INTERNAL BREAKDOWN (aggregated across all polytopes)")
    print(f"{'='*70}")
    print(f"\n  Grand total BFS time: {grand_total:.3f}s")
    print(f"  Total walls processed: {agg_counts.get('gv_series_lookup', 0)}")
    print()

    for k, v in sorted(agg_timings.items(), key=lambda x: x[1], reverse=True):
        pct = 100 * v / grand_total if grand_total > 0 else 0
        cnt = agg_counts.get(k, 0)
        avg = v / cnt if cnt > 0 else 0
        print(f"    {k:25s}  {v:7.3f}s  ({pct:5.1f}%)  n={cnt:4d}  avg={avg*1000:.2f}ms")

    print(f"\n  Results saved to {outpath}")
