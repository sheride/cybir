"""Weyl orbit expansion for the hyperextended Kahler cone.

Applies symmetric-flop Coxeter reflections to fundamental-domain
phases to discover additional phases beyond the fundamental domain.

See arXiv:2212.10573 Section 4.3 for the Weyl orbit expansion
algorithm.
"""

import logging

import numpy as np

from .types import CalabiYauLite, ContractionType, ExtremalContraction
from .util import normalize_curve, tuplify

logger = logging.getLogger("cybir")


def _reflect_phase(phase, reflection_matrix):
    """Create reflected phase data by applying a Coxeter reflection.

    Transforms intersection numbers via the triple einsum contraction
    and the second Chern class via matrix-vector multiplication, matching
    the convention in the original ``sym_flop_cy`` (lines 268-276).

    Parameters
    ----------
    phase : CalabiYauLite
        Phase whose data to reflect.
    reflection_matrix : numpy.ndarray
        Square reflection matrix of shape ``(h11, h11)``.

    Returns
    -------
    dict
        Dictionary with keys ``int_nums``, ``c2``, ``kahler_cone``,
        ``mori_cone``. The cone values are ``None`` if ``cytools`` is
        not available or the phase has no Kahler cone.

    Notes
    -----
    The einsum ``'abc,xa,yb,zc'`` contracts each index of
    :math:`\\kappa_{abc}` with the reflection matrix, implementing

    .. math::

        \\kappa'_{xyz} = M_{xa} M_{yb} M_{zc} \\kappa_{abc}

    The c2 transformation is :math:`c'_x = M_{xa} c_{2,a}`, i.e.
    ``np.einsum('a,xa', c2, M)`` which is equivalent to ``M @ c2``.
    """
    M = np.asarray(reflection_matrix, dtype=float)

    # Validate reflection matrix dimensions
    h11 = phase.int_nums.shape[0]
    if M.shape != (h11, h11):
        raise ValueError(
            f"Reflection matrix shape {M.shape} does not match h11={h11}"
        )

    # Transform intersection numbers: kappa'_xyz = M_xa M_yb M_zc kappa_abc
    new_int_nums = np.einsum("abc,xa,yb,zc", phase.int_nums, M, M, M)

    # Transform second Chern class: c2'_x = M_xa c2_a
    new_c2 = None
    if phase.c2 is not None:
        new_c2 = np.einsum("a,xa", phase.c2, M)

    # Transform Kahler cone if available
    new_kc = None
    new_mori = None
    if phase.kahler_cone is not None:
        try:
            import cytools

            old_rays = phase.kahler_cone.rays()
            new_kc = cytools.Cone(
                rays=old_rays @ np.round(M).astype(int)
            )
            new_mori = new_kc.dual()
        except Exception as exc:
            logger.warning(
                "Failed to transform Kahler cone for %s: %s",
                phase.label,
                exc,
            )

    return {
        "int_nums": new_int_nums,
        "c2": new_c2,
        "kahler_cone": new_kc,
        "mori_cone": new_mori,
    }


def _mori_signature(phase):
    """Extract a hashable signature from a phase's Mori cone generators.

    Parameters
    ----------
    phase : CalabiYauLite
        Phase with a ``mori_cone`` attribute.

    Returns
    -------
    frozenset of tuple or None
        Sorted generator rows as a frozenset of tuples, or ``None``
        if the phase has no Mori cone.
    """
    if phase.mori_cone is None:
        return None
    try:
        rays = phase.mori_cone.rays()
        return frozenset(tuple(int(x) for x in row) for row in rays)
    except Exception:
        return None


def _is_new_phase(existing_signatures, mori_cone):
    """Check whether a Mori cone is distinct from all existing phases.

    Parameters
    ----------
    existing_signatures : set of frozenset
        Mori cone signatures from :func:`_mori_signature` for
        all phases already in the graph.
    mori_cone : cytools.Cone or None
        The Mori cone of the candidate reflected phase.

    Returns
    -------
    bool
        ``True`` if the Mori cone does not match any existing phase.
    """
    if mori_cone is None:
        return False
    try:
        sig = frozenset(tuple(int(x) for x in row) for row in mori_cone.rays())
    except Exception:
        return False
    return sig not in existing_signatures


def expand_weyl(ekc):
    """Expand the fundamental domain via Weyl orbit reflections.

    Applies each symmetric-flop Coxeter reflection to each
    fundamental-domain phase. New phases (identified by distinct
    Mori cones) are added to the graph with ``SYMMETRIC_FLOP``
    contraction edges.

    This is a faithful translation of the original Weyl orbit loop
    (lines 977-1035 of ``extended_kahler_cone.py``).

    Parameters
    ----------
    ekc : CYBirationalClass
        The EKC object, already populated by ``construct_phases``.
        Modified in place.
    """
    reflections = [np.array(r) for r in ekc._sym_flop_refs]
    if not reflections:
        logger.info("No symmetric-flop reflections; skipping Weyl expansion")
        return

    # Snapshot fundamental-domain phases before expansion
    fund_phases = list(ekc._graph.phases)
    phase_counter = ekc._graph.num_phases

    # Build set of existing Mori cone signatures for deduplication
    existing_sigs = set()
    for p in fund_phases:
        sig = _mori_signature(p)
        if sig is not None:
            existing_sigs.add(sig)

    new_count = 0

    for phase in fund_phases:
        for M in reflections:
            reflected = _reflect_phase(phase, M)

            # Defensive check: verify reflected phase has valid Mori cone
            if reflected["mori_cone"] is None:
                logger.warning(
                    "Reflected phase from %s has no Mori cone; skipping",
                    phase.label,
                )
                continue

            # Check for degenerate Mori cone
            try:
                mori_rays = reflected["mori_cone"].rays()
                if len(mori_rays) == 0:
                    logger.warning(
                        "Reflected phase from %s has empty Mori cone; skipping",
                        phase.label,
                    )
                    continue
            except Exception:
                logger.warning(
                    "Cannot read Mori cone rays for reflected phase from %s; skipping",
                    phase.label,
                )
                continue

            if not _is_new_phase(existing_sigs, reflected["mori_cone"]):
                continue

            # Create new phase
            new_label = f"CY_{phase_counter}"
            new_phase = CalabiYauLite(
                int_nums=reflected["int_nums"],
                c2=reflected["c2"],
                kahler_cone=reflected["kahler_cone"],
                mori_cone=reflected["mori_cone"],
                label=new_label,
            )

            ekc._graph.add_phase(new_phase)

            # Add symmetric-flop contraction edge between original and reflected
            contraction = ExtremalContraction(
                contraction_curve=np.zeros(reflected["int_nums"].shape[0]),
                contraction_type=ContractionType.SYMMETRIC_FLOP,
            )
            ekc._graph.add_contraction(
                contraction,
                phase.label,
                new_label,
                curve_sign_a=1,
                curve_sign_b=1,
            )

            ekc._weyl_phases.append(new_label)

            # Update deduplication set
            sig = frozenset(
                tuple(int(x) for x in row) for row in mori_rays
            )
            existing_sigs.add(sig)

            # Inherit wall classifications from the original phase
            _inherit_contractions(ekc, phase, new_phase, M)

            phase_counter += 1
            new_count += 1

    logger.info(
        "Weyl expansion: %d new phases from %d fundamental phases "
        "and %d reflections",
        new_count,
        len(fund_phases),
        len(reflections),
    )


def _inherit_contractions(ekc, parent_phase, reflected_phase, reflection_matrix):
    """Inherit wall classifications from parent to reflected phase.

    For each contraction from the parent phase, creates a corresponding
    contraction on the reflected phase with the same type. The flopping
    curve is transformed by the reflection matrix.

    Parameters
    ----------
    ekc : CYBirationalClass
        The EKC object.
    parent_phase : CalabiYauLite
        The original fundamental-domain phase.
    reflected_phase : CalabiYauLite
        The newly created reflected phase.
    reflection_matrix : numpy.ndarray
        The reflection matrix used to create the reflected phase.
    """
    M = np.asarray(reflection_matrix, dtype=float)
    parent_contractions = ekc._graph.contractions_from(parent_phase.label)

    for parent_contraction, sign in parent_contractions:
        # Skip self-loops that are already symmetric flops
        if parent_contraction.contraction_type == ContractionType.SYMMETRIC_FLOP:
            continue

        # Transform the flopping curve
        reflected_curve = M @ (sign * parent_contraction.contraction_curve)

        # Create inherited contraction with same type as self-loop on reflected phase
        inherited = ExtremalContraction(
            contraction_curve=reflected_curve,
            contraction_type=parent_contraction.contraction_type,
            gv_invariant=parent_contraction.gv_invariant,
            gv_series=parent_contraction.gv_series,
            coxeter_reflection=parent_contraction.coxeter_reflection,
        )
        # Terminal walls (asymptotic, CFT, su2) become self-loops
        if parent_contraction.contraction_type in (
            ContractionType.ASYMPTOTIC,
            ContractionType.CFT,
            ContractionType.SU2,
        ):
            ekc._graph.add_contraction(
                inherited,
                reflected_phase.label,
                reflected_phase.label,
                curve_sign_a=1,
                curve_sign_b=-1,
            )
