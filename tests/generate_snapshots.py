"""Generate test fixtures by running the original extended_kahler_cone.py on h11=2 polytopes.

This script imports the original EKC code from cornell-dev and captures
intermediate values (intersection numbers, c2, flopping curves, GV series,
effective GV invariants, contraction types, zero-vol divisors, Coxeter
reflections, and wall-crossed quantities) for each wall encountered during
``construct_phases``.

The output is a JSON file per polytope in ``tests/fixtures/h11_2/``.

Usage
-----
    # Pass the path to extended_kahler_cone.py explicitly:
    conda run -n cytools python tests/generate_snapshots.py /path/to/extended_kahler_cone.py

    # Or set the environment variable:
    export CORNELL_DEV_EKC=/path/to/extended_kahler_cone.py
    conda run -n cytools python tests/generate_snapshots.py

    # Other options:
    conda run -n cytools python tests/generate_snapshots.py --polytope-ids 0 1 5
    conda run -n cytools python tests/generate_snapshots.py --max-deg 12
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import pathlib
import sys
import traceback

import numpy as np

# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------
FIXTURES_DIR = pathlib.Path(__file__).resolve().parent / "fixtures" / "h11_2"

# Default path (author's machine) — override via CLI arg or CORNELL_DEV_EKC env var
_DEFAULT_EKC_PATH = (
    "/Users/elijahsheridan/Research/string/cytools_code"
    "/cornell-dev/projects/vex/elijah/extended_kahler_cone.py"
)


def _resolve_ekc_path(cli_path=None):
    """Resolve the path to extended_kahler_cone.py from CLI arg, env var, or default."""
    path_str = cli_path or os.environ.get("CORNELL_DEV_EKC") or _DEFAULT_EKC_PATH
    path = pathlib.Path(path_str).resolve()
    if not path.exists():
        raise FileNotFoundError(
            f"extended_kahler_cone.py not found at: {path}\n"
            "Pass the path as the first argument or set CORNELL_DEV_EKC."
        )
    return path


def _load_ekc(ekc_path):
    """Import extended_kahler_cone.py and its dependencies from the resolved path."""
    ekc_dir = ekc_path.parent
    cornell_dev_root = ekc_dir.parents[2]  # .../cornell-dev
    elijah_dir = cornell_dev_root / "projects" / "Elijah"

    for p in (ekc_dir, cornell_dev_root, elijah_dir):
        if p.exists() and str(p) not in sys.path:
            sys.path.insert(0, str(p))

    spec = importlib.util.spec_from_file_location("extended_kahler_cone", str(ekc_path))
    ekc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ekc)
    return ekc


def _to_list(arr):
    """Convert numpy arrays (or None) to JSON-serialisable nested lists."""
    if arr is None:
        return None
    return np.array(arr).tolist()


def generate_snapshots(ekc, polytope_ids=None, max_deg=10, verbose=True):
    """Run the original EKC pipeline on h11=2 polytopes and save snapshots.

    Parameters
    ----------
    ekc : module
        The imported extended_kahler_cone module.
    polytope_ids : list[int] | None
        Which polytope IDs to process.  ``None`` means all 36.
    max_deg : int
        Maximum degree for GV computation (passed to ``setup_root``).
    verbose : bool
        Print progress messages.
    """
    import cytools  # noqa: F811

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    all_polytopes = cytools.fetch_polytopes(h11=2, lattice="N")

    if polytope_ids is not None:
        polytopes = [(pid, all_polytopes[pid]) for pid in polytope_ids]
    else:
        polytopes = list(enumerate(all_polytopes))

    results = []

    for pid, poly in polytopes:
        if verbose:
            print(f"\n--- Polytope {pid} ---")
        try:
            snapshot = _process_polytope(ekc, pid, poly, max_deg=max_deg, verbose=verbose)
            results.append(snapshot)

            out_path = FIXTURES_DIR / f"polytope_{pid}.json"
            with open(out_path, "w") as fp:
                json.dump(snapshot, fp, indent=2)
            if verbose:
                print(f"  Saved {out_path.name} ({len(snapshot['walls'])} walls)")

        except Exception:
            traceback.print_exc()
            if verbose:
                print(f"  FAILED for polytope {pid}, skipping")

    if verbose:
        print(f"\nDone. Generated {len(results)} fixture files in {FIXTURES_DIR}")
    return results


def _process_polytope(ekc, pid, poly, max_deg=10, verbose=False):
    """Run EKC construction on one polytope and capture wall data."""
    ekc_obj = ekc.ExtendedKahlerCone(poly)
    ekc_obj.setup_root(max_deg=max_deg)
    ekc_obj.construct_phases(verbose=verbose, limit=50)

    root_cy = ekc_obj.root
    snapshot = {
        "polytope_id": pid,
        "h11": 2,
        "int_nums": _to_list(root_cy.int_nums),
        "c2": _to_list(root_cy.c2),
        "mori_rays": _to_list(root_cy.mori_gens),
        "walls": [],
    }

    for wall in ekc_obj.walls:
        wall_data = _extract_wall_data(ekc, wall)
        if wall_data is not None:
            snapshot["walls"].append(wall_data)

    return snapshot


def _extract_wall_data(ekc, wall):
    """Extract intermediate values from a diagnosed Wall object."""
    if wall.category is None:
        return None

    # Source-side intersection numbers and c2
    start_cy = wall.start_cy
    if start_cy is None:
        return None

    int_nums = start_cy.int_nums
    c2 = start_cy.c2

    data = {
        "curve": _to_list(wall.curve),
        "contraction_type": wall.category,
        "gv_series": _to_list(wall.gv_series) if wall.gv_series is not None else None,
        "gv_eff_1": int(wall.gv_eff_1) if wall.gv_eff_1 is not None else None,
        "gv_eff_3": int(wall.gv_eff_3) if wall.gv_eff_3 is not None else None,
        "int_nums": _to_list(int_nums),
        "c2": _to_list(c2),
    }

    # Zero-volume divisor (stored on wall by diagnose -> find_zero_vol_divisor)
    if hasattr(wall, "zero_vol_divisor") and wall.zero_vol_divisor is not None:
        data["zero_vol_divisor"] = _to_list(wall.zero_vol_divisor)
    else:
        data["zero_vol_divisor"] = None

    # Coxeter reflection
    if hasattr(wall, "coxeter_reflection") and wall.coxeter_reflection is not None:
        data["coxeter_reflection"] = _to_list(wall.coxeter_reflection)
    else:
        data["coxeter_reflection"] = None

    # Wall-crossed quantities (only for flop-type walls)
    if wall.category not in ("asymptotic", "CFT") and wall.gv_eff_3 is not None:
        try:
            flopped_intnums = ekc.wall_cross_intnums(
                int_nums, wall.curve, wall.gv_eff_3
            )
            flopped_c2 = ekc.wall_cross_second_chern_class(
                c2, wall.curve, wall.gv_eff_1
            )
            data["flopped_int_nums"] = _to_list(flopped_intnums)
            data["flopped_c2"] = _to_list(flopped_c2)
        except Exception:
            data["flopped_int_nums"] = None
            data["flopped_c2"] = None
    else:
        data["flopped_int_nums"] = None
        data["flopped_c2"] = None

    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate snapshot fixtures from original EKC code."
    )
    parser.add_argument(
        "ekc_path",
        nargs="?",
        default=None,
        help=(
            "Path to extended_kahler_cone.py. "
            "Falls back to CORNELL_DEV_EKC env var, then built-in default."
        ),
    )
    parser.add_argument(
        "--polytope-ids",
        type=int,
        nargs="*",
        default=None,
        help="Specific polytope IDs to process (default: all 36).",
    )
    parser.add_argument(
        "--max-deg",
        type=int,
        default=10,
        help="Maximum GV degree (default: 10).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages.",
    )
    args = parser.parse_args()

    ekc_path = _resolve_ekc_path(args.ekc_path)
    print(f"Loading EKC from: {ekc_path}")
    ekc_module = _load_ekc(ekc_path)

    generate_snapshots(
        ekc_module,
        polytope_ids=args.polytope_ids,
        max_deg=args.max_deg,
        verbose=not args.quiet,
    )
