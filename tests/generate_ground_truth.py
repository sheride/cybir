#!/usr/bin/env python
"""Generate ground truth data from the original cornell-dev ExtendedKahlerCone.

Extracts comprehensive per-phase and per-contraction EKC data for all
h11=2 and h11=3 favorable polytopes, storing results as JSON + npz per
polytope.  Two-pass architecture:

  Pass 1 (fundamental domain): All polytopes, ``ignore_sym=True``.
  Pass 2 (full BFS):           Finite Coxeter groups only, ``ignore_sym=False``.

GV invariants are shared between cybir and cornell-dev via a pickle
intermediary during generation (transient test infrastructure, not
ground truth itself).

Usage:
    conda run -n cytools python tests/generate_ground_truth.py --h11 2 --limit 1
    conda run -n cytools python tests/generate_ground_truth.py --h11 all
    conda run -n cytools python tests/generate_ground_truth.py --single 42 --h11 3
"""

import argparse
import json
import logging
import os
import pickle
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

# Silence chatty output during generation
logging.disable(logging.INFO)

# ---- Paths ----------------------------------------------------------------

CORNELL_DEV_ROOT = (
    "/Users/elijahsheridan/Research/string/cytools_code/cornell-dev"
)
CORNELL_DEV_PATH = os.path.join(
    CORNELL_DEV_ROOT, "projects", "vex", "elijah"
)
# misc.py lives here (extended_kahler_cone.py does sys.path.append('../../Elijah'))
CORNELL_DEV_ELIJAH = os.path.join(
    CORNELL_DEV_ROOT, "projects", "Elijah"
)
GROUND_TRUTH_DIR = Path(__file__).parent / "ground_truth"
DEFAULT_CACHE_DIR = str(GROUND_TRUTH_DIR / "gv_cache")

# ---- Category mapping ------------------------------------------------------

_CATEGORY_MAP = {
    "asymptotic": "ASYMPTOTIC",
    "CFT": "CFT",
    "su(2) enhancement": "SU2",
    "symmetric flop": "SYMMETRIC_FLOP",
    "flop": "FLOP",
    "generic flop (I)": "FLOP",
    "generic flop (II)": "FLOP",
    "su(2) enhancement or flop": "SU2_OR_FLOP",
    'potent "flop" wall (insufficient degree)': "UNRESOLVED",
}


def _map_category(category_str):
    """Map an original cornell-dev category string to a standard name."""
    if category_str is None:
        return None
    return _CATEGORY_MAP.get(category_str, category_str)


# ---- GV cache (pickle -- transient test infrastructure) --------------------

def _gv_cache_path(cache_dir, h11, poly_idx):
    """Return the pickle path for a polytope's cached GV invariants."""
    return os.path.join(cache_dir, f"h11_{h11}", f"poly_{poly_idx}.pkl")


def _load_gvs(cache_dir, h11, poly_idx):
    """Load cached GV invariants, or return None."""
    if cache_dir is None:
        return None
    path = _gv_cache_path(cache_dir, h11, poly_idx)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return None


def _save_gvs(cache_dir, h11, poly_idx, gvs):
    """Save GV invariants to cache."""
    if cache_dir is None:
        return
    dirpath = os.path.join(cache_dir, f"h11_{h11}")
    os.makedirs(dirpath, exist_ok=True)
    path = _gv_cache_path(cache_dir, h11, poly_idx)
    with open(path, "wb") as f:
        pickle.dump(gvs, f, protocol=pickle.HIGHEST_PROTOCOL)


# ---- GV injection into cornell-dev ----------------------------------------

def _inject_gvs(ekc_obj, gvs):
    """Inject shared GV invariants into a cornell-dev ExtendedKahlerCone.

    Same pattern as compare_orbit.py:run_original_full lines 53-64.
    """
    cy = ekc_obj.polytope.triangulate().cy()
    gvs_copy = gvs.copy()
    gvs_copy.flop_curves = []
    gvs_copy.precompose = np.eye(cy.h11())

    # Import CY_GV from cornell-dev (already on sys.path)
    from extended_kahler_cone import CY_GV

    ekc_obj.root = CY_GV(cy=cy, gvs=gvs_copy, cob=ekc_obj.cob)
    ekc_obj.root.toric = True
    ekc_obj.gvs = gvs_copy
    ekc_obj.walls.extend(ekc_obj.root.walls)
    ekc_obj.root.curve_signs = dict()
    ekc_obj.cys.append(ekc_obj.root)


# ---- Data extraction -------------------------------------------------------

def _extract_json(poly_idx, h11, ekc_obj, pass_name, cybir_info=None):
    """Extract structured data from a cornell-dev ExtendedKahlerCone as dict.

    Parameters
    ----------
    poly_idx : int
        Polytope index in CYTools database.
    h11 : int
        h^{1,1} of the polytope.
    ekc_obj : ExtendedKahlerCone
        The cornell-dev EKC object after ``construct_phases``.
    pass_name : str
        Either ``"fundamental"`` or ``"full_bfs"``.
    cybir_info : dict or None
        Coxeter type info from cybir (only for fundamental pass).

    Returns
    -------
    dict
        JSON-serializable dictionary with all structured ground truth data.
    """
    # Build per-phase contraction type lists
    # Each CY_GV has a .walls attribute listing its walls (Facet objects)
    per_phase_types = {}
    for i, cy_gv in enumerate(ekc_obj.cys):
        types = []
        for w in cy_gv.walls:
            if w.category is not None:
                types.append(_map_category(w.category))
        per_phase_types[f"phase_{i}"] = types

    # Global contraction type counts (from all walls)
    type_counter = Counter()
    for w in ekc_obj.walls:
        if w.category is not None:
            mapped = _map_category(w.category)
            type_counter[mapped] += 1

    # Infinity cone generators (sorted for determinism)
    inf_gens = sorted([
        [int(x) for x in g] for g in ekc_obj.infinity_cone_gens
    ])

    # Effective cone generators (sorted for determinism)
    eff_gens = sorted([
        [int(x) for x in g] for g in ekc_obj.eff_cone_gens
    ])

    # Per-contraction detail: raw category, mapped type, curve, zvd, phase
    per_contraction = []
    for w in ekc_obj.walls:
        entry = {
            "curve": [int(x) for x in w.curve],
            "orig_category": w.category,
            "mapped_type": _map_category(w.category),
            "gv_series": (
                [int(x) if x is not None else None for x in w.gv_series]
                if w.gv_series else None
            ),
        }
        # Zero-volume divisor (may not exist for all wall types)
        zvd = getattr(w, "zero_vol_divisor", None)
        if zvd is None:
            zvd = getattr(w, "zero_vol_divisor_result", None)
        if zvd is not None and not isinstance(zvd, str):
            entry["zvd"] = [int(x) for x in zvd]
        else:
            entry["zvd"] = None
        # Which phase this wall belongs to
        if w.start_cy is not None:
            try:
                entry["start_phase"] = ekc_obj.cys.index(w.start_cy)
            except ValueError:
                entry["start_phase"] = None
        else:
            entry["start_phase"] = None
        per_contraction.append(entry)

    data = {
        "polytope_idx": int(poly_idx),
        "h11": int(h11),
        "pass": pass_name,
        "n_phases": len(ekc_obj.cys),
        "n_sym_flop_refs": len([
            w for w in ekc_obj.walls if w.category == "symmetric flop"
        ]),
        "n_infinity_gens": len(ekc_obj.infinity_cone_gens),
        "n_eff_gens": len(ekc_obj.eff_cone_gens),
        "n_unresolved": len([
            w for w in ekc_obj.walls if w.category is None
        ]),
        "phase_labels": [f"phase_{i}" for i in range(len(ekc_obj.cys))],
        "per_phase_contraction_types": per_phase_types,
        "contraction_type_counts": dict(type_counter),
        "per_contraction": per_contraction,
        "infinity_cone_gens": inf_gens,
        "eff_cone_gens": eff_gens,
    }

    # Add cybir info if provided (Coxeter type comes from cybir)
    if cybir_info is not None:
        data["has_finite_coxeter"] = cybir_info.get("has_finite_coxeter", False)
        data["coxeter_type"] = cybir_info.get("coxeter_type")
        data["coxeter_order"] = cybir_info.get("coxeter_order")

    return data


def _extract_npz(ekc_obj, prefix=""):
    """Extract numpy arrays from a cornell-dev ExtendedKahlerCone.

    Parameters
    ----------
    ekc_obj : ExtendedKahlerCone
        The cornell-dev EKC object after ``construct_phases``.
    prefix : str
        Key prefix (empty for pass 1, ``"full_"`` for pass 2).

    Returns
    -------
    dict
        Dictionary of numpy arrays suitable for ``np.savez``.
    """
    arrays = {}

    for i, cy_gv in enumerate(ekc_obj.cys):
        # Intersection numbers
        int_nums = np.asarray(cy_gv.int_nums, dtype=np.int64)
        arrays[f"{prefix}phase_{i}_int_nums"] = int_nums

        # Second Chern class
        c2 = np.asarray(cy_gv.c2, dtype=np.int64)
        arrays[f"{prefix}phase_{i}_c2"] = c2

        # Kahler cone rays -- sorted lexicographically for determinism
        try:
            kahler_rays = np.asarray(
                cy_gv.mori.dual().rays(), dtype=np.int64)
            # Sort lexicographically
            if kahler_rays.ndim == 2 and kahler_rays.shape[0] > 1:
                idx = np.lexsort(kahler_rays.T[::-1])
                kahler_rays = kahler_rays[idx]
            arrays[f"{prefix}phase_{i}_kahler_rays"] = kahler_rays
        except Exception:
            # Fallback: empty array if cone rays fail
            pass

        # Tip point
        if cy_gv.tip is not None:
            # Tip may be float-valued (interior point of cone), keep as float
            arrays[f"{prefix}phase_{i}_tip"] = np.asarray(cy_gv.tip)

        # Per-contraction data
        for j, wall in enumerate(cy_gv.walls):
            # Curve vector
            curve = np.asarray(wall.curve, dtype=np.int64)
            arrays[f"{prefix}phase_{i}_contr_{j}_curve"] = curve

            # Zero-vol divisor (if available)
            if hasattr(wall, 'zero_vol_divisor') and wall.zero_vol_divisor is not None:
                zvd = np.asarray(
                    np.round(wall.zero_vol_divisor).astype(int),
                    dtype=np.int64)
                arrays[f"{prefix}phase_{i}_contr_{j}_zvd"] = zvd

    # Global: Coxeter reflections (stacked as 3D array)
    if ekc_obj.coxeter_refs:
        refs_list = sorted([
            np.asarray(
                [[int(x) for x in row] for row in m], dtype=np.int64
            )
            for m in ekc_obj.coxeter_refs
        ], key=lambda a: a.tobytes())
        arrays[f"{prefix}coxeter_refs"] = np.stack(refs_list)

    # Global: symmetric flop reflections
    if ekc_obj.sym_flop_refs:
        sf_list = sorted([
            np.asarray(
                [[int(x) for x in row] for row in m], dtype=np.int64
            )
            for m in ekc_obj.sym_flop_refs
        ], key=lambda a: a.tobytes())
        arrays[f"{prefix}sym_flop_refs"] = np.stack(sf_list)

    return arrays


# ---- Core generation logic -------------------------------------------------

def _generate_one_inner(poly_idx, polytope, h11, cache_dir,
                        skip_full_bfs=False):
    """Generate ground truth for a single polytope (runs in-process).

    Parameters
    ----------
    poly_idx : int
        Polytope index.
    polytope : cytools.Polytope
        The polytope object.
    h11 : int
        h^{1,1} value.
    cache_dir : str or None
        Directory for GV pickle cache.
    skip_full_bfs : bool
        If True, skip pass 2 (full BFS for finite Coxeter groups).

    Returns
    -------
    bool
        True if ground truth was generated successfully.
    """
    from cytools import fetch_polytopes  # noqa: F401

    out_dir = GROUND_TRUTH_DIR / f"h11_{h11}"
    json_path = out_dir / f"poly_{poly_idx}.json"
    npz_path = out_dir / f"poly_{poly_idx}.npz"

    # --- Step A: Load/compute GVs via cybir ---------------------------------
    cached_gvs = _load_gvs(cache_dir, h11, poly_idx)

    try:
        cy = polytope.triangulate().get_cy()
    except Exception as e:
        print(f"    SKIP: CY construction failed: {e}")
        return False

    from cybir.core.ekc import CYBirationalClass

    try:
        ekc_cybir = CYBirationalClass.from_gv(
            cy, max_deg=10, verbose=False, gvs=cached_gvs)
    except Exception as e:
        print(f"    SKIP: cybir fundamental domain failed: {e}")
        return False

    shared_gvs = ekc_cybir._root_invariants

    # --- Step B: Extract cybir Coxeter info ---------------------------------
    # coxeter_order/type are now lazy properties — no need to call
    # apply_coxeter_orbit() just to classify the group.
    _order = ekc_cybir.coxeter_order   # lazy: 1 if trivial, None if infinite
    _type = ekc_cybir.coxeter_type     # lazy: [] if trivial
    _has_sym_flops = len(ekc_cybir.sym_flop_refs) > 0

    cybir_info = {
        "has_finite_coxeter": _order is not None,  # None means infinite
        "has_sym_flops": _has_sym_flops,
        "coxeter_type": (
            [list(t) for t in _type] if _type else None
        ),
        "coxeter_order": int(_order) if _order is not None else None,
    }

    # Cache GVs after cybir run (may have been updated to higher degree)
    _save_gvs(cache_dir, h11, poly_idx, ekc_cybir._root_invariants)

    # --- Step C: Run original code fundamental domain (pass 1) --------------
    # Add cornell-dev paths to sys.path:
    #   root       -> lib.util.lattice
    #   elijah     -> extended_kahler_cone
    #   Elijah     -> misc
    for p in (CORNELL_DEV_ROOT, CORNELL_DEV_PATH, CORNELL_DEV_ELIJAH):
        if p not in sys.path:
            sys.path.insert(0, p)

    from extended_kahler_cone import ExtendedKahlerCone

    try:
        ekc_orig = ExtendedKahlerCone(polytope)
        _inject_gvs(ekc_orig, shared_gvs)
        ekc_orig.construct_phases(
            weyl=False, ignore_sym=True, verbose=False, limit=100)
    except Exception as e:
        print(f"    SKIP: original fundamental domain failed: {e}")
        return False

    # Extract fundamental domain data
    json_data = _extract_json(
        poly_idx, h11, ekc_orig, "fundamental", cybir_info=cybir_info)
    npz_data = _extract_npz(ekc_orig, prefix="")

    # --- Step D: Run original code full BFS (pass 2) ------------------------
    if (not skip_full_bfs
            and cybir_info["has_sym_flops"]
            and cybir_info["has_finite_coxeter"]):
        try:
            ekc_orig2 = ExtendedKahlerCone(polytope)
            _inject_gvs(ekc_orig2, shared_gvs)
            ekc_orig2.construct_phases(
                weyl=False, ignore_sym=False, verbose=False, limit=500)

            # Extract full BFS JSON data
            full_bfs_json = _extract_json(
                poly_idx, h11, ekc_orig2, "full_bfs")
            # Nest under "full_bfs" key (remove redundant top-level fields)
            json_data["full_bfs"] = {
                "n_phases": full_bfs_json["n_phases"],
                "contraction_type_counts": full_bfs_json[
                    "contraction_type_counts"],
                "n_infinity_gens": full_bfs_json["n_infinity_gens"],
                "n_eff_gens": full_bfs_json["n_eff_gens"],
                "infinity_cone_gens": full_bfs_json["infinity_cone_gens"],
                "eff_cone_gens": full_bfs_json["eff_cone_gens"],
            }

            # Extract full BFS npz data (prefix "full_")
            full_npz = _extract_npz(ekc_orig2, prefix="full_")
            npz_data.update(full_npz)

        except Exception as e:
            print(f"    WARNING: full BFS failed: {e}")
            json_data["full_bfs"] = None

    # --- Step E: Save JSON + npz --------------------------------------------
    os.makedirs(out_dir, exist_ok=True)

    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)

    np.savez(npz_path, **npz_data)

    return True


# ---- Subprocess entry point ------------------------------------------------

def _run_single(poly_idx, h11, cache_dir, skip_full_bfs):
    """Run ground truth generation for a single polytope (subprocess mode).

    Called when ``--single`` argument is provided. Imports CYTools,
    fetches the polytope, and calls ``_generate_one_inner``.
    """
    from cytools import fetch_polytopes

    polys = fetch_polytopes(h11=h11, lattice="N")
    favorable = [
        (i, p) for i, p in enumerate(polys) if p.is_favorable("N")
    ]

    # Find the polytope by its index among favorable polytopes
    target = None
    for idx, p in favorable:
        if idx == poly_idx:
            target = p
            break

    if target is None:
        print(f"ERROR: polytope index {poly_idx} not found among "
              f"favorable h11={h11} polytopes")
        sys.exit(1)

    t0 = time.time()
    ok = _generate_one_inner(
        poly_idx, target, h11, cache_dir, skip_full_bfs)
    elapsed = time.time() - t0

    if ok:
        print(f"    Generated poly_{poly_idx} in {elapsed:.1f}s")
    else:
        print(f"    FAILED poly_{poly_idx} after {elapsed:.1f}s")

    sys.exit(0 if ok else 1)


# ---- Main ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate ground truth EKC data from cornell-dev code")
    parser.add_argument(
        "--h11", type=str, default="all",
        help="h11 value: 2, 3, or 'all' (default: all)")
    parser.add_argument(
        "--start", type=int, default=0,
        help="Start from Nth favorable polytope (default: 0)")
    parser.add_argument(
        "--limit", type=int, default=0,
        help="Max polytopes to process (0=all, default: all)")
    parser.add_argument(
        "--cache-dir", type=str, default=DEFAULT_CACHE_DIR,
        help=f"GV cache directory (default: {DEFAULT_CACHE_DIR})")
    parser.add_argument(
        "--skip-full-bfs", action="store_true",
        help="Skip pass 2 (full BFS for finite Coxeter groups)")
    parser.add_argument(
        "--timeout", type=int, default=180,
        help="Per-polytope timeout in seconds (default: 180)")
    parser.add_argument(
        "--single", type=int, default=None,
        help="Run a single polytope index (subprocess mode)")
    args = parser.parse_args()

    # --- Subprocess mode: run a single polytope directly --------------------
    if args.single is not None:
        h11_val = int(args.h11) if args.h11 != "all" else 3
        _run_single(args.single, h11_val, args.cache_dir, args.skip_full_bfs)
        return

    # --- Main mode: loop over polytopes via subprocess ----------------------
    h11_values = []
    if args.h11 == "all":
        h11_values = [2, 3]
    else:
        h11_values = [int(args.h11)]

    total_ok = 0
    total_fail = 0
    total_skip = 0
    total_timeout = 0

    for h11 in h11_values:
        print(f"\n{'#' * 60}")
        print(f"# h11={h11} ground truth generation")
        print(f"{'#' * 60}")

        # Enumerate favorable polytopes
        from cytools import fetch_polytopes
        polys = fetch_polytopes(h11=h11, lattice="N")
        favorable = [
            (i, p) for i, p in enumerate(polys) if p.is_favorable("N")
        ]
        print(f"  Favorable polytopes: {len(favorable)} / {len(polys)}")

        # Apply --start and --limit
        work = favorable[args.start:]
        if args.limit > 0:
            work = work[:args.limit]

        print(f"  Processing {len(work)} polytopes "
              f"(start={args.start}, limit={args.limit or 'all'})")
        print()

        for count, (poly_idx, _) in enumerate(work, 1):
            print(f"  [{count}/{len(work)}] Polytope #{poly_idx} ... ",
                  end="", flush=True)

            t0 = time.time()
            try:
                cmd = [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--single", str(poly_idx),
                    "--h11", str(h11),
                    "--cache-dir", args.cache_dir,
                ]
                if args.skip_full_bfs:
                    cmd.append("--skip-full-bfs")

                result = subprocess.run(
                    cmd,
                    timeout=args.timeout,
                    capture_output=True,
                    text=True,
                )
                elapsed = time.time() - t0

                if result.returncode == 0:
                    total_ok += 1
                    print(f"OK ({elapsed:.1f}s)")
                else:
                    total_fail += 1
                    # Print last few lines of stderr/stdout for diagnostics
                    output = (result.stdout + result.stderr).strip()
                    last_lines = output.split("\n")[-3:]
                    print(f"FAIL ({elapsed:.1f}s)")
                    for line in last_lines:
                        if line.strip():
                            print(f"    {line.strip()}")

            except subprocess.TimeoutExpired:
                elapsed = time.time() - t0
                total_timeout += 1
                print(f"TIMEOUT ({elapsed:.0f}s)")

    # --- Summary ------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print("GROUND TRUTH GENERATION SUMMARY")
    print(f"{'=' * 60}")
    print(f"  OK:       {total_ok}")
    print(f"  Failed:   {total_fail}")
    print(f"  Timeout:  {total_timeout}")
    print(f"  Total:    {total_ok + total_fail + total_timeout}")
    print(f"\n  Output: {GROUND_TRUTH_DIR}")


if __name__ == "__main__":
    main()
