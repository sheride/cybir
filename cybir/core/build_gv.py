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
from .types import (
    CalabiYauLite, ContractionType, ExtremalContraction, InsufficientGVError,
)
from .util import normalize_curve, tuplify

logger = logging.getLogger("cybir")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def check_nongeneric_cs(cy, result):
    """Re-tag symmetric flops whose zero-vol divisor is a prime toric divisor.

    At non-generic complex structure, some walls classified as symmetric
    flops are actually su(2) enhancements. Detection: if the zero-vol
    divisor matches (up to sign and proportionality) any row of the GLSM
    charge matrix, re-tag as SU2_NONGENERIC_CS.

    See D-16 through D-19 in 05-CONTEXT.md.

    Parameters
    ----------
    cy : cytools.CalabiYau
        The Calabi-Yau threefold (provides GLSM charge matrix).
    result : dict
        Classification result from ``classify_contraction``.

    Returns
    -------
    dict
        The result dict, possibly with contraction_type changed.
    """
    if result["contraction_type"] != ContractionType.SYMMETRIC_FLOP:
        return result

    zvd = result.get("zero_vol_divisor")
    if zvd is None:
        return result

    try:
        charges = cy.glsm_charge_matrix(include_origin=False)
    except Exception:
        return result

    zvd_arr = np.round(np.array(zvd)).astype(int)
    zvd_norm = np.linalg.norm(zvd_arr.astype(float))
    if zvd_norm < 1e-12:
        return result

    # GLSM charge matrix has shape (h11, n_points): rows are GLSM charges,
    # columns are toric divisors in the h11 basis. The zero-vol divisor lives
    # in the same h11-dimensional space, so compare against columns.
    for i in range(charges.shape[1]):
        col = charges[:, i].astype(float)
        col_norm = np.linalg.norm(col)
        if col_norm < 1e-12:
            continue
        # Check if zvd is proportional to this column (scalar multiple)
        cross = np.abs(np.dot(zvd_arr.astype(float), col))
        if np.abs(cross - zvd_norm * col_norm) < 1e-8:
            result["contraction_type"] = ContractionType.SU2_NONGENERIC_CS
            return result

    return result


def _check_nongeneric_cs(ekc, result):
    """BFS wrapper: delegates to :func:`check_nongeneric_cs` using ``ekc._cy``."""
    return check_nongeneric_cs(ekc._cy, result)


def _compute_tip(phase):
    """Compute an interior point of the Kahler (dual Mori) cone.

    Takes the sum of all extremal rays of the Kahler cone, which is
    guaranteed to lie in the strict interior (since the cone is
    strictly convex and full-dimensional). This matches the original
    code's approach and avoids the convex optimization overhead of
    ``tip_of_stretched_cone``.

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
        If the phase has no Kahler cone or it has no rays.
    """
    cone = phase.kahler_cone
    if cone is None:
        raise RuntimeError(
            f"Phase {phase.label} has no Kahler cone; "
            "cannot compute tip"
        )
    rays = cone.rays()
    if len(rays) == 0:
        raise RuntimeError(
            f"Phase {phase.label} Kahler cone has no rays"
        )
    return np.sum(rays, axis=0).astype(float)


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

    # Paired storage for genuine SU2 (D-04, for HEKC/all orbit expansion)
    if ctype == ContractionType.SU2:
        cox_ref = result.get("coxeter_reflection")
        if cox_ref is not None:
            ref_key = tuplify(np.round(cox_ref).astype(int))
            contr_curve = result.get("contraction_curve")
            if contr_curve is not None:
                curve_arr = np.array(
                    [int(x) for x in contr_curve]
                    if not isinstance(contr_curve, np.ndarray)
                    else np.round(contr_curve).astype(int)
                )
                curve_tuple = tuple(int(x) for x in curve_arr)
                existing_refs = set(r for r, _ in ekc._su2_pairs)
                if ref_key not in existing_refs:
                    ekc._su2_pairs.append((ref_key, curve_tuple))

    # SU2_NONGENERIC_CS: treat like su(2) for generator accumulation
    if ctype == ContractionType.SU2_NONGENERIC_CS:
        cox_ref = result.get("coxeter_reflection")
        if cox_ref is not None:
            ref_key = tuplify(np.round(cox_ref).astype(int))
            ekc._coxeter_refs.add(ref_key)
            # Paired storage for HEKC/all orbit expansion (D-04)
            contr_curve = result.get("contraction_curve")
            if contr_curve is not None:
                curve_arr = np.array(
                    [int(x) for x in contr_curve]
                    if not isinstance(contr_curve, np.ndarray)
                    else np.round(contr_curve).astype(int)
                )
                curve_tuple = tuple(int(x) for x in curve_arr)
                existing_refs = set(r for r, _ in ekc._nongeneric_cs_pairs)
                if ref_key not in existing_refs:
                    ekc._nongeneric_cs_pairs.append((ref_key, curve_tuple))
        zvd = result.get("zero_vol_divisor")
        if zvd is not None:
            ekc._eff_cone_gens.add(
                tuple(np.round(zvd).astype(int).tolist())
            )

    # GROSS_FLOP: no special generator accumulation (behaves like generic FLOP)
    # Intentionally does NOT add to _sym_flop_refs, _sym_flop_pairs, or _coxeter_refs

    # Symmetric flop reflections specifically (WR-04 fix: paired storage)
    if ctype == ContractionType.SYMMETRIC_FLOP:
        cox_ref = result.get("coxeter_reflection")
        if cox_ref is not None:
            ref_key = tuplify(np.round(cox_ref).astype(int))
            contr_curve = result.get("contraction_curve")
            if contr_curve is not None and ref_key not in ekc._sym_flop_refs:
                curve_arr = np.array(
                    [int(x) for x in contr_curve]
                    if not isinstance(contr_curve, np.ndarray)
                    else np.round(contr_curve).astype(int)
                )
                curve_tuple = tuple(int(x) for x in curve_arr)
                ekc._sym_flop_refs.add(ref_key)
                ekc._sym_flop_pairs.append((ref_key, curve_tuple))


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

def setup_root(ekc, max_deg=4):
    """Set up the root phase from the CYTools CalabiYau.

    Computes GV invariants, creates the first ``CalabiYauLite``
    phase, and adds it to the graph.

    Parameters
    ----------
    ekc : CYBirationalClass
        The orchestrator to populate.
    max_deg : int, optional
        Initial maximum degree for GV computation. Default 4.
        The BFS will adaptively recompute to higher degrees if
        needed for wall classification.
    """
    from .patch import patch_cytools

    patch_cytools()

    cy = ekc._cy

    # Guard: non-favorable polytopes cannot compute GV-based EKC
    if hasattr(cy, 'polytope') and callable(cy.polytope):
        poly = cy.polytope()
        if hasattr(poly, 'is_favorable') and not poly.is_favorable('N'):
            poly_id = poly.id() if hasattr(poly, 'id') else "unknown"
            raise ValueError(
                f"Non-favorable polytope (polytope ID {poly_id}): cannot "
                "compute GV-based EKC. The polytope is not favorable in "
                "the N-lattice."
            )

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


def _run_bfs(ekc, verbose, limit, check_toric=False):
    """Run one pass of BFS construction. Returns (phase_counter, deferred).

    The deferred list contains (wall_curve, source_label, series_len, chain)
    tuples for walls that could not be classified at the current GV degree.
    series_len is the number of GV entries seen, and chain is the flop chain
    for the source phase (needed to compute effective grading degree).

    Parameters
    ----------
    check_toric : bool, optional
        If True, detect FRST phases and compile toric curves
        incrementally during BFS. Default False.
    """
    root = ekc._graph.get_phase(ekc._root_label)
    mori_gens = root.mori_cone.extremal_rays()

    # Data structures
    known_curves = set()
    curve_signs = {}
    flop_chains = {"CY_0": []}
    tips = {}
    undiagnosed = deque()
    deferred = []
    phase_counter = 1
    classified_curves = {}  # D-02: classification invariance check

    # Toric curve compilation (D-07)
    if check_toric:
        from .toric_curves import (
            classify_phase_type, induced_2face_triangulations,
            compute_toric_curves, ToricCurveData,
        )
        from .util import moving_cone as compute_moving_cone

        cy = ekc._cy
        Q = cy.glsm_charge_matrix(include_origin=False)
        mc = compute_moving_cone(Q)
        ekc._moving_cone = mc
        ekc._toric_curve_data = ToricCurveData()
        ekc._frst_triangulations = []
        ekc._seen_2face_triags = set()
        ekc._phase_types = {}  # label -> 'frst'|'vex'|'non_inherited'

    # Initialize from root
    root_tip = _compute_tip(root)
    tips["CY_0"] = root_tip
    root._tip = root_tip

    for gen in mori_gens:
        known_curves.add(normalize_curve(gen))

    curve_signs["CY_0"] = {
        c: int(np.sign(root_tip @ np.array(c))) for c in known_curves
    }
    root._curve_signs = dict(curve_signs["CY_0"])

    for gen in mori_gens:
        undiagnosed.append((np.asarray(gen), "CY_0"))

    # Classify root phase for toric curves
    if check_toric:
        phase_type, fan = classify_phase_type(root.kahler_cone, Q, moving_cone_obj=mc)
        ekc._phase_types["CY_0"] = phase_type
        if phase_type == 'frst' and fan is not None:
            try:
                h = np.linalg.lstsq(Q, root_tip.astype(float), rcond=None)[0]
                triag = cy.triangulate(heights=h)
                ekc._frst_triangulations.append(triag)
                polytope = cy.polytope()
                new_face_triags = induced_2face_triangulations(polytope, [triag])
                new_count = 0
                for face_idx, face_triag_list in enumerate(new_face_triags):
                    for ft in face_triag_list:
                        key = frozenset(tuple(sorted(tuple(s) for s in ft)))
                        if key not in ekc._seen_2face_triags:
                            ekc._seen_2face_triags.add(key)
                            new_count += 1
                if new_count > 0:
                    new_tcd = compute_toric_curves(cy, new_face_triags, tip=root_tip)
                    ekc._toric_curve_data.merge(new_tcd)
                    logger.info("  FRST phase CY_0: %d new toric curves",
                                len(new_tcd.all_curves()))
                # D-09: active Mori verification
                ekc._verify_mori_bounds("CY_0")
            except Exception as exc:
                logger.warning("  Toric curve computation failed for CY_0: %s", exc)

    while undiagnosed and ekc._graph.num_phases < limit:
        wall_curve, source_label = undiagnosed.popleft()
        source = ekc._graph.get_phase(source_label)

        # Get GV series for this wall via flop chain
        chain = flop_chains[source_label]
        gvs_local = ekc._root_invariants.flop_gvs(chain)
        series = gvs_local.gv_series_cybir(wall_curve)

        if not series:
            deferred.append((np.array(wall_curve), source_label, 0, list(chain)))
            continue

        # Classify
        try:
            result = classify_contraction(
                source.int_nums, source.c2, wall_curve, series
            )
        except InsufficientGVError:
            deferred.append((np.array(wall_curve), source_label, len(series), list(chain)))
            continue
        except Exception as exc:
            logger.warning(
                "  Classification failed for curve %s from %s: %s",
                normalize_curve(wall_curve), source_label, exc,
            )
            continue

        # Check for non-generic complex structure re-tagging
        result = _check_nongeneric_cs(ekc, result)

        # D-01: GrossFlop post-check for symmetric flop candidates
        if result["contraction_type"] == ContractionType.SYMMETRIC_FLOP:
            from .classify import _kahler_cones_match
            chain = flop_chains[source_label]
            flopped_chain_check = chain + [wall_curve]
            try:
                flopped_gvs_check = ekc._root_invariants.flop_gvs(
                    flopped_chain_check
                )
                flopped_mori_check = flopped_gvs_check.cone_incl_flop()
                flopped_kc_check = flopped_mori_check.dual()
                if not _kahler_cones_match(
                    source.kahler_cone, flopped_kc_check,
                    result["coxeter_reflection"],
                ):
                    result["contraction_type"] = ContractionType.GROSS_FLOP
                    logger.info(
                        "  GrossFlop detected: %s (condition a passed, "
                        "condition b failed)",
                        normalize_curve(wall_curve),
                    )
            except Exception as exc:
                logger.warning(
                    "  Could not check GrossFlop condition (b) for %s: %s",
                    normalize_curve(wall_curve), exc,
                )

        ctype = result["contraction_type"]

        # D-02: Classification invariance check
        norm_curve = normalize_curve(wall_curve)
        if norm_curve in classified_curves:
            prev_type = classified_curves[norm_curve]
            if prev_type != ctype:
                logger.warning(
                    "Classification invariance: curve %s classified as %s "
                    "from %s but previously as %s from another phase",
                    norm_curve, ctype.value, source_label, prev_type.value,
                )
        else:
            classified_curves[norm_curve] = ctype

        # Build ExtremalContraction.
        # Terminal walls (asymptotic, CFT, su2, symmetric flop) have a
        # canonical curve orientation — we never cross them, so the raw
        # BFS direction is definitive.  Flop edges (including GROSS_FLOP)
        # are bidirectional, so they use the normalized form (first
        # nonzero positive).
        is_terminal = ctype in (
            ContractionType.ASYMPTOTIC,
            ContractionType.CFT,
            ContractionType.SU2,
            ContractionType.SU2_NONGENERIC_CS,
            ContractionType.SYMMETRIC_FLOP,
        )
        curve_for_edge = (
            np.array([int(x) for x in wall_curve])
            if is_terminal
            else np.array(normalize_curve(wall_curve))
        )
        # Determine toric_origin if check_toric is enabled
        toric_origin_val = None
        if check_toric and hasattr(ekc, '_toric_curve_data') and ekc._toric_curve_data:
            curve_tuple_check = tuple(int(x) for x in curve_for_edge)
            neg_tuple_check = tuple(-x for x in curve_tuple_check)
            if curve_tuple_check in ekc._toric_curve_data.gv_dict:
                toric_origin_val = "matched"
            elif neg_tuple_check in ekc._toric_curve_data.gv_dict:
                toric_origin_val = "matched"
        contraction = ExtremalContraction(
            contraction_curve=curve_for_edge,
            contraction_type=ctype,
            gv_invariant=result.get("gv_invariant"),
            effective_gv=result.get("effective_gv"),
            zero_vol_divisor=result.get("zero_vol_divisor"),
            coxeter_reflection=result.get("coxeter_reflection"),
            gv_series=result.get("gv_series"),
            gv_eff_1=result.get("gv_eff_1"),
            toric_origin=toric_origin_val,
        )

        # Log
        ekc._build_log.append({
            "action": "classify",
            "source": source_label,
            "curve": normalize_curve(wall_curve),
            "type": ctype.value,
        })

        # Accumulate generators — use raw curve direction
        result["contraction_curve"] = tuple(int(x) for x in wall_curve)
        _accumulate_generators(ekc, ctype, result)

        # Terminal walls: asymptotic, CFT, su(2), su(2) non-generic CS
        if ctype in (
            ContractionType.ASYMPTOTIC,
            ContractionType.CFT,
            ContractionType.SU2,
            ContractionType.SU2_NONGENERIC_CS,
        ):
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

        flopped._kahler_cone = flopped_mori.dual()
        flopped._mori_cone = flopped_mori

        tuple_curve = normalize_curve(wall_curve)
        if tuple_curve not in known_curves:
            known_curves.add(tuple_curve)
            _update_all_curve_signs(ekc, curve_signs, tuple_curve, tips)

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
            flopped._tip = flopped_tip
            flopped._curve_signs = dict(flopped_signs)

            ekc._graph.add_phase(flopped)
            ekc._graph.add_contraction(
                contraction, source_label, new_label
            )
            curve_signs[new_label] = flopped_signs
            flop_chains[new_label] = flopped_chain
            tips[new_label] = flopped_tip

            for gen in flopped_mori.extremal_rays():
                undiagnosed.append((np.asarray(gen), new_label))

            logger.info(
                "Phase %s: new (flop of %s from %s)",
                new_label, tuple_curve, source_label,
            )
            phase_counter += 1

            # Toric classification for new flopped phase
            if check_toric:
                phase_type, fan = classify_phase_type(
                    flopped._kahler_cone, Q, moving_cone_obj=mc
                )
                ekc._phase_types[new_label] = phase_type
                if phase_type == 'frst' and fan is not None:
                    try:
                        tip_val = tips.get(new_label)
                        if tip_val is not None:
                            h = np.linalg.lstsq(
                                Q, tip_val.astype(float), rcond=None
                            )[0]
                            triag = cy.triangulate(heights=h)
                            ekc._frst_triangulations.append(triag)
                            polytope = cy.polytope()
                            new_face_triags = induced_2face_triangulations(
                                polytope, [triag]
                            )
                            new_count = 0
                            for face_idx, face_triag_list in enumerate(
                                new_face_triags
                            ):
                                for ft in face_triag_list:
                                    key = frozenset(
                                        tuple(sorted(tuple(s) for s in ft))
                                    )
                                    if key not in ekc._seen_2face_triags:
                                        ekc._seen_2face_triags.add(key)
                                        new_count += 1
                            if new_count > 0:
                                new_tcd = compute_toric_curves(
                                    cy, new_face_triags, tip=tip_val
                                )
                                ekc._toric_curve_data.merge(new_tcd)
                                logger.info(
                                    "  FRST phase %s: %d new toric curves",
                                    new_label, len(new_tcd.all_curves()),
                                )
                            # D-09: active Mori verification
                            ekc._verify_mori_bounds(new_label)
                    except Exception as exc:
                        logger.warning(
                            "  Toric curve computation failed for %s: %s",
                            new_label, exc,
                        )

            for ray in flopped._kahler_cone.rays():
                ekc._eff_cone_gens.add(
                    tuple(np.round(ray).astype(int).tolist())
                )
        else:
            ekc._graph.add_contraction(
                contraction, source_label, existing_label
            )
            logger.info(
                "  re-encountered phase %s via %s",
                existing_label, tuple_curve,
            )

    # Add root Kahler cone rays to effective cone gens
    if root.kahler_cone is not None:
        for ray in root.kahler_cone.rays():
            ekc._eff_cone_gens.add(
                tuple(np.round(ray).astype(int).tolist())
            )

    return phase_counter, deferred


# Minimum number of populated GV multiples (C, 2C, 3C, 4C) to conclude potency
_POTENCY_THRESHOLD = 4


def construct_phases(ekc, verbose=True, limit=100, max_deg_ceiling=20,
                     deg_step=2, validate_stability=False, check_toric=False):
    """Run BFS construction of the extended Kahler cone.

    Uses adaptive GV degree: starts with the initial degree from
    ``setup_root``, runs a full BFS, and if any walls could not be
    classified (empty series or insufficient GVs), bumps the degree
    and **restarts the entire BFS from scratch** with the new GVs.

    Potent curves are detected by tracking series length across retries.
    If a wall's GV series has >= 4 populated multiples (C, 2C, 3C, 4C)
    and still doesn't terminate, it is flagged as potent and not retried.

    Parameters
    ----------
    ekc : CYBirationalClass
        The orchestrator (must have root set up via ``setup_root``).
    verbose : bool, optional
        Enable info-level logging. Default True.
    limit : int, optional
        Maximum number of phases. Default 100.
    max_deg_ceiling : int, optional
        Maximum degree to recompute GVs to. Default 20.
    deg_step : int, optional
        Degree increment per retry round. Default 2.
    validate_stability : bool, optional
        If True, after the main BFS completes, bump degree by
        ``deg_step`` and re-run the full BFS to verify that results
        are unchanged. If results differ, keep the higher-degree
        result and log a warning. Default False.
    check_toric : bool, optional
        If True, detect FRST phases during BFS and compile toric
        curves incrementally. Enables phase classification
        (FRST/vex/non-inherited) and Mori cone bounds. Default False.
    """
    if verbose:
        logger.setLevel(logging.INFO)

    current_deg = ekc._root_invariants.cutoff if hasattr(
        ekc._root_invariants, "cutoff") else 10

    # Track potent curves across retries: {(curve_tuple, source_label): series_len}
    potent_candidates = {}

    while True:
        # Clear graph and rebuild from scratch (root phase is preserved
        # in setup_root; we need to reset everything else)
        # Save root phase data before clearing
        from .graph import CYGraph
        root_phase = ekc._graph.get_phase(ekc._root_label)
        ekc._graph = CYGraph()
        ekc._graph.add_phase(root_phase)
        ekc._coxeter_refs = set()
        ekc._sym_flop_refs = set()
        ekc._sym_flop_pairs = []
        ekc._nongeneric_cs_pairs = []
        ekc._su2_pairs = []
        ekc._infinity_cone_gens = set()
        ekc._eff_cone_gens = set()
        ekc._build_log = []

        # Reset toric state for fresh BFS pass
        if check_toric:
            from .toric_curves import ToricCurveData
            ekc._toric_curve_data = ToricCurveData()
            ekc._frst_triangulations = []
            ekc._seen_2face_triags = set()
            ekc._phase_types = {}

        phase_counter, deferred = _run_bfs(ekc, verbose, limit,
                                           check_toric=check_toric)

        if not deferred:
            break  # all walls classified successfully

        # Check for potent curves and compute targeted degree bump
        still_deferred = []
        grading = ekc._root_invariants.grading_vec
        required_deg = current_deg

        for wall_curve, source_label, series_len, chain in deferred:
            key = (normalize_curve(wall_curve), source_label)
            prev_len = potent_candidates.get(key, 0)

            if series_len >= _POTENCY_THRESHOLD:
                logger.warning(
                    "  Potent curve detected: %s from %s "
                    "(series length %d >= %d, not retrying)",
                    normalize_curve(wall_curve), source_label,
                    series_len, _POTENCY_THRESHOLD,
                )
                continue  # drop this wall — it's potent

            potent_candidates[key] = series_len
            still_deferred.append(
                (wall_curve, source_label, series_len, chain)
            )

            # Compute the degree needed to resolve the next lattice
            # point along this curve's ray, accounting for the flop
            # chain's sign flips and basis change.
            gvs_local = ekc._root_invariants.flop_gvs(chain)
            c = np.asarray(wall_curve)
            # Apply flop sign correction
            for fc in gvs_local.flop_curves:
                from .patch import _is_aligned
                if _is_aligned(c, fc):
                    c = -c
            c_gv = gvs_local.precompose @ c
            deg_per_mult = int(np.dot(c_gv, grading))
            if deg_per_mult > 0:
                n_current = current_deg // deg_per_mult
                needed = (n_current + 1) * deg_per_mult + 1
                required_deg = max(required_deg, needed)

        if not still_deferred or current_deg >= max_deg_ceiling:
            # Report unresolved walls
            if still_deferred:
                logger.warning(
                    "%d wall(s) unresolved at max_deg=%d:",
                    len(still_deferred), current_deg,
                )
                for wc, sl, _, _ in still_deferred:
                    logger.warning("  curve %s from %s", normalize_curve(wc), sl)
                ekc._unresolved_walls = [
                    (normalize_curve(wc), sl) for wc, sl, _, _ in still_deferred
                ]
            break

        # Targeted degree bump: resolve the next lattice point for
        # the highest-degree deferred curve, clamped to ceiling
        new_deg = min(required_deg, max_deg_ceiling)
        if new_deg <= current_deg:
            # Fallback: if targeted bump didn't increase (e.g. negative
            # degree curves), use deg_step
            new_deg = min(current_deg + deg_step, max_deg_ceiling)

        logger.info(
            "Adaptive GV: deg %d -> %d, restarting BFS (%d deferred walls)",
            current_deg, new_deg, len(still_deferred),
        )

        cy = ekc._cy
        new_gvs = cy.compute_gvs(grading_vec=grading, max_deg=new_deg)
        new_gvs.flop_curves = []
        new_gvs.precompose = np.eye(len(grading))
        ekc._root_invariants = new_gvs

        # Update root phase's Mori/Kahler cones from new GVs
        new_mori = new_gvs.cone_incl_flop()
        root_phase._mori_cone = new_mori
        root_phase._kahler_cone = new_mori.dual()

        current_deg = new_deg

    # --- Stability check (opt-in) ---
    if validate_stability:
        if current_deg >= max_deg_ceiling:
            logger.warning(
                "Cannot validate stability: already at max_deg_ceiling=%d",
                max_deg_ceiling,
            )
        else:
            # 1. Snapshot current results
            snapshot_phases = ekc._graph.num_phases
            snapshot_inf = frozenset(ekc._infinity_cone_gens)
            snapshot_eff = frozenset(ekc._eff_cone_gens)
            snapshot_refs = frozenset(ekc._coxeter_refs)

            # 2. Bump degree
            new_deg = min(current_deg + deg_step, max_deg_ceiling)
            logger.info(
                "Stability check: bumping deg %d -> %d",
                current_deg, new_deg,
            )

            # 3. Recompute GVs at new degree
            cy = ekc._cy
            grading = ekc._root_invariants.grading_vec
            new_gvs = cy.compute_gvs(grading_vec=grading, max_deg=new_deg)
            new_gvs.flop_curves = []
            new_gvs.precompose = np.eye(len(grading))
            ekc._root_invariants = new_gvs

            # Update root phase cones
            root_phase = ekc._graph.get_phase(ekc._root_label)
            new_mori = new_gvs.cone_incl_flop()
            root_phase._mori_cone = new_mori
            root_phase._kahler_cone = new_mori.dual()

            # 4. Clear graph and re-run full BFS
            from .graph import CYGraph
            ekc._graph = CYGraph()
            ekc._graph.add_phase(root_phase)
            ekc._coxeter_refs = set()
            ekc._sym_flop_refs = set()
            ekc._sym_flop_pairs = []
            ekc._nongeneric_cs_pairs = []
            ekc._su2_pairs = []
            ekc._infinity_cone_gens = set()
            ekc._eff_cone_gens = set()
            ekc._build_log = []

            if check_toric:
                from .toric_curves import ToricCurveData
                ekc._toric_curve_data = ToricCurveData()
                ekc._frst_triangulations = []
                ekc._seen_2face_triags = set()
                ekc._phase_types = {}

            _run_bfs(ekc, verbose, limit, check_toric=check_toric)

            # 5. Compare
            stable = (
                ekc._graph.num_phases == snapshot_phases
                and frozenset(ekc._infinity_cone_gens) == snapshot_inf
                and frozenset(ekc._eff_cone_gens) == snapshot_eff
                and frozenset(ekc._coxeter_refs) == snapshot_refs
            )

            if stable:
                logger.info(
                    "Stability check passed: results unchanged at deg %d",
                    new_deg,
                )
            else:
                logger.warning(
                    "Stability check FAILED: results changed at deg %d "
                    "(phases: %d->%d, inf_gens: %d->%d, eff_gens: %d->%d). "
                    "Keeping higher-degree result. Consider running with "
                    "higher max_deg.",
                    new_deg,
                    snapshot_phases, ekc._graph.num_phases,
                    len(snapshot_inf), len(ekc._infinity_cone_gens),
                    len(snapshot_eff), len(ekc._eff_cone_gens),
                )

    logger.info(
        "Construction complete: %d phases, %d contractions",
        ekc._graph.num_phases, ekc._graph.num_contractions,
    )
