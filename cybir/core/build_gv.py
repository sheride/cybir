"""BFS pipeline builder for extended Kahler cone construction.

Implements ``setup_root`` and ``construct_phases`` -- the core EKC
construction algorithm. The BFS loop iterates over Mori cone walls,
classifies contractions, flops to create new phases, and deduplicates
via curve-sign dictionaries.

This is a faithful translation of the original
``extended_kahler_cone.py`` lines 807-1073 into clean modular code
operating on the Phase 1-2 types.

See arXiv:2212.10573 Section 4 and arXiv:2303.00757 Section 2.
"""

import logging
from collections import deque

import numpy as np

from .classify import classify_contraction
from .flop import flop_phase
from .types import CalabiYauLite, ContractionType, ExtremalContraction
from .util import normalize_curve, tuplify

logger = logging.getLogger("cybir")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _compute_tip(phase):
    """Compute an interior point of the Kahler (dual Mori) cone.

    Uses the CYTools ``tip_of_stretched_cone`` method with a retry
    loop (dividing ``c`` by 10) if it returns ``None``.

    This replicates the original pattern from lines 2212-2218.

    Parameters
    ----------
    phase : CalabiYauLite
        Phase with a ``kahler_cone`` attribute set.

    Returns
    -------
    numpy.ndarray
        An interior point of the Kahler cone.

    Raises
    ------
    RuntimeError
        If no valid tip is found after retries.
    """
    cone = phase.kahler_cone
    if cone is None:
        raise RuntimeError(
            f"Phase {phase.label} has no Kahler cone; "
            "cannot compute tip"
        )
    c = 1.0
    tip = None
    for _ in range(20):  # max 20 retries (c down to 1e-20)
        tip = cone.tip_of_stretched_cone(c)
        if tip is not None:
            return tip / c  # scale back as in original: tip *= 1/c
        c /= 10
    raise RuntimeError(
        f"tip_of_stretched_cone returned None for phase {phase.label} "
        f"after all retries"
    )


def _accumulate_generators(ekc, ctype, result):
    """Accumulate cone generators and reflections on ekc (D-06).

    Updates ``ekc._infinity_cone_gens``, ``ekc._eff_cone_gens``,
    ``ekc._coxeter_refs``, and ``ekc._sym_flop_refs`` based on
    the contraction type and classification result.

    This corresponds to the original post-loop accumulation
    (lines 1039-1066).

    Parameters
    ----------
    ekc : CYBirationalClass
        The orchestrator to update.
    ctype : ContractionType
        Classification of the contraction.
    result : dict
        Classification result from ``classify_contraction``.
    """
    curve_tuple = tuple(result.get("gv_series", []))  # not used for gens

    # Infinity cone generators: asymptotic and CFT walls
    if ctype in (ContractionType.ASYMPTOTIC, ContractionType.CFT):
        if "contraction_curve" in result:
            ekc._infinity_cone_gens.add(result["contraction_curve"])

    # Effective cone generators: CFT and su(2) walls
    if ctype in (ContractionType.CFT, ContractionType.SU2):
        zvd = result.get("zero_vol_divisor")
        if zvd is not None:
            ekc._eff_cone_gens.add(
                tuple(np.round(zvd).astype(int).tolist())
            )

    # Coxeter reflections: su(2) and symmetric flop walls
    if ctype in (ContractionType.SU2, ContractionType.SYMMETRIC_FLOP):
        cox_ref = result.get("coxeter_reflection")
        if cox_ref is not None:
            ekc._coxeter_refs.add(tuplify(np.round(cox_ref).astype(int)))

    # Symmetric flop reflections specifically
    if ctype == ContractionType.SYMMETRIC_FLOP:
        cox_ref = result.get("coxeter_reflection")
        if cox_ref is not None:
            ekc._sym_flop_refs.add(tuplify(np.round(cox_ref).astype(int)))


def _update_all_curve_signs(ekc, curve_signs, new_curve, tips):
    """Update all phases' curve-sign dicts with a new curve.

    When a new flop curve is discovered, ALL existing phases must
    have their curve_signs dictionary updated with the sign of
    ``tip @ new_curve``. This prevents deduplication failures due
    to mismatched key sets.

    See Pitfall 2 in RESEARCH.md.

    Parameters
    ----------
    ekc : CYBirationalClass
        The orchestrator.
    curve_signs : dict[str, dict[tuple, int]]
        Curve-sign dictionaries keyed by phase label.
    new_curve : tuple
        Normalized new curve as a tuple.
    tips : dict[str, numpy.ndarray]
        Kahler cone tips keyed by phase label.
    """
    curve_arr = np.array(new_curve)
    for label in curve_signs:
        tip = tips[label]
        curve_signs[label][new_curve] = int(np.sign(tip @ curve_arr))


def _find_matching_phase(curve_signs, target_signs):
    """Find a phase label whose curve-signs match the target.

    Parameters
    ----------
    curve_signs : dict[str, dict[tuple, int]]
        Existing phase curve-sign dictionaries.
    target_signs : dict[tuple, int]
        Target curve-sign dictionary to match.

    Returns
    -------
    str or None
        Label of the matching phase, or None if no match.
    """
    for label, signs in curve_signs.items():
        if signs == target_signs:
            return label
    return None


# ---------------------------------------------------------------------------
# Main builder functions
# ---------------------------------------------------------------------------

def setup_root(ekc, max_deg=10):
    """Set up the root phase from the CYTools CalabiYau.

    Computes GV invariants, creates the first ``CalabiYauLite``
    phase, and adds it to the graph.

    Parameters
    ----------
    ekc : CYBirationalClass
        The orchestrator to populate.
    max_deg : int, optional
        Maximum degree for GV computation. Default 10.
    """
    from .patch import patch_cytools

    patch_cytools()

    cy = ekc._cy

    # Extract geometric data
    int_nums = cy.intersection_numbers(in_basis=True, format="dense")
    c2 = cy.second_chern_class(in_basis=True)
    h11 = cy.h11()

    # Compute GV grading vector from toric Mori cone
    toric_mori = cy.mori_cone_cap(in_basis=True)
    grading = toric_mori.find_grading_vector()
    grading = np.array(grading).astype(int)

    # Compute GV invariants (or use pre-computed ones)
    if ekc._root_invariants is not None:
        gvs = ekc._root_invariants
    else:
        gvs = cy.compute_gvs(grading_vec=grading, max_deg=max_deg)
    gvs.flop_curves = []
    gvs.precompose = np.eye(h11)

    # Use GV-reconstructed Mori cone (cone_incl_flop), matching original
    mori_cone = gvs.cone_incl_flop()
    kahler_cone = mori_cone.dual()

    # Create root CalabiYauLite
    root = CalabiYauLite(
        int_nums=int_nums,
        c2=c2,
        kahler_cone=kahler_cone,
        mori_cone=mori_cone,
        gv_invariants=gvs,
        label="CY_0",
    )

    # Store on ekc
    ekc._root_label = "CY_0"
    ekc._root_invariants = gvs
    ekc._graph.add_phase(root)

    n_gvs = len(list(gvs.charges())) if hasattr(gvs, "charges") else 0
    logger.info("Root phase CY_0 set up with %d GV invariants", n_gvs)


def construct_phases(ekc, verbose=True, limit=100):
    """Run BFS construction of the extended Kahler cone.

    Iterates over undiagnosed Mori cone walls, classifies each,
    flops when appropriate, and deduplicates phases by curve-sign
    dictionaries.

    This is a faithful translation of the original BFS loop
    (lines 871-1073).

    Parameters
    ----------
    ekc : CYBirationalClass
        The orchestrator (must have root set up via ``setup_root``).
    verbose : bool, optional
        Enable info-level logging. Default True.
    limit : int, optional
        Maximum number of phases. Default 100.
    """
    if verbose:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    root = ekc._graph.get_phase(ekc._root_label)

    # Get Mori cone extremal rays as initial walls (matching original)
    mori_gens = root.mori_cone.extremal_rays()

    # Data structures
    known_curves = set()
    curve_signs = {}  # {phase_label: {curve_tuple: +1/-1}}
    flop_chains = {"CY_0": []}  # {phase_label: [curves flopped]}
    tips = {}  # {phase_label: ndarray}
    undiagnosed = deque()
    phase_counter = 1

    # Initialize from root
    root_tip = _compute_tip(root)
    tips["CY_0"] = root_tip
    root._tip = root_tip

    # Initialize known curves from Mori cone generators
    for gen in mori_gens:
        nc = normalize_curve(gen)
        known_curves.add(nc)

    # Initialize curve signs for root
    curve_signs["CY_0"] = {
        c: int(np.sign(root_tip @ np.array(c))) for c in known_curves
    }
    root._curve_signs = dict(curve_signs["CY_0"])

    # Enqueue all Mori cone generators
    for gen in mori_gens:
        undiagnosed.append((np.asarray(gen), "CY_0"))

    # BFS loop
    while undiagnosed and ekc._graph.num_phases < limit:
        wall_curve, source_label = undiagnosed.popleft()
        source = ekc._graph.get_phase(source_label)

        # Get GV series for this wall via flop chain
        chain = flop_chains[source_label]
        gvs_local = ekc._root_invariants.flop_gvs(chain)
        series = gvs_local.gv_series_cybir(wall_curve)

        if not series:
            logger.warning(
                "  Empty GV series for curve %s from %s, skipping",
                normalize_curve(wall_curve), source_label,
            )
            continue

        # Classify
        try:
            result = classify_contraction(
                source.int_nums, source.c2, wall_curve, series
            )
        except Exception as exc:
            logger.warning(
                "  Classification failed for curve %s from %s: %s",
                normalize_curve(wall_curve), source_label, exc,
            )
            continue

        ctype = result["contraction_type"]

        # Build ExtremalContraction
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

        # Log (PIPE-04 / D-05)
        ekc._build_log.append({
            "action": "classify",
            "source": source_label,
            "curve": normalize_curve(wall_curve),
            "type": ctype.value,
        })

        # Accumulate generators (D-06) -- use raw curve for gens
        # (matching original: infinity/eff gens store the raw Mori ray direction)
        result["contraction_curve"] = tuple(int(x) for x in wall_curve)
        _accumulate_generators(ekc, ctype, result)

        # Terminal walls: asymptotic, CFT, su(2)
        if ctype in (
            ContractionType.ASYMPTOTIC,
            ContractionType.CFT,
            ContractionType.SU2,
        ):
            # Self-loop for terminal walls
            ekc._graph.add_contraction(
                contraction, source_label, source_label
            )
            logger.info(
                "  %s: %s", ctype.display_name(), normalize_curve(wall_curve)
            )
            continue

        # Symmetric flop: record but don't explore
        if ctype == ContractionType.SYMMETRIC_FLOP:
            ekc._graph.add_contraction(
                contraction, source_label, source_label
            )
            logger.info(
                "  symmetric flop: %s", normalize_curve(wall_curve)
            )
            continue

        # Generic flop: construct flopped phase
        new_label = f"CY_{phase_counter}"
        flopped = flop_phase(source, wall_curve, series, label=new_label)

        # Compute the flopped Mori cone from flop-adjusted Invariants
        flopped_chain = chain + [wall_curve]
        flopped_gvs = ekc._root_invariants.flop_gvs(flopped_chain)
        try:
            flopped_mori = flopped_gvs.cone_incl_flop()
        except Exception as exc:
            logger.warning(
                "  Could not compute flopped Mori cone for %s: %s",
                new_label, exc,
            )
            continue

        # Set cones on the flopped phase (it was created without them)
        flopped._kahler_cone = flopped_mori.dual()
        flopped._mori_cone = flopped_mori

        # Curve-sign deduplication
        tuple_curve = normalize_curve(wall_curve)
        if tuple_curve not in known_curves:
            known_curves.add(tuple_curve)
            _update_all_curve_signs(ekc, curve_signs, tuple_curve, tips)

        # Compute flopped phase tip and curve signs
        try:
            flopped_tip = _compute_tip(flopped)
        except RuntimeError:
            logger.warning(
                "  Could not compute tip for flopped phase %s, skipping",
                new_label,
            )
            continue

        flopped_signs = {
            c: int(np.sign(flopped_tip @ np.array(c))) for c in known_curves
        }

        existing_label = _find_matching_phase(curve_signs, flopped_signs)

        if existing_label is None:
            # New phase -- persist tip and curve_signs on the phase object (D-15)
            flopped._tip = flopped_tip
            flopped._curve_signs = dict(flopped_signs)

            ekc._graph.add_phase(flopped)
            ekc._graph.add_contraction(
                contraction, source_label, new_label
            )
            curve_signs[new_label] = flopped_signs
            flop_chains[new_label] = flopped_chain
            tips[new_label] = flopped_tip

            # Enqueue new phase's Mori cone walls (extremal rays only)
            for gen in flopped_mori.extremal_rays():
                undiagnosed.append((np.asarray(gen), new_label))

            logger.info(
                "Phase %s: new (flop of %s from %s)",
                new_label, tuple_curve, source_label,
            )
            phase_counter += 1

            # Add Kahler cone rays to effective cone gens
            for ray in flopped._kahler_cone.rays():
                ekc._eff_cone_gens.add(
                    tuple(np.round(ray).astype(int).tolist())
                )
        else:
            # Existing phase: just add edge
            ekc._graph.add_contraction(
                contraction, source_label, existing_label
            )
            logger.info(
                "  re-encountered phase %s via %s",
                existing_label, tuple_curve,
            )

    # Also add root Kahler cone rays to effective cone gens
    if root.kahler_cone is not None:
        for ray in root.kahler_cone.rays():
            ekc._eff_cone_gens.add(
                tuple(np.round(ray).astype(int).tolist())
            )

    logger.info(
        "Construction complete: %d phases, %d contractions",
        ekc._graph.num_phases, ekc._graph.num_contractions,
    )
