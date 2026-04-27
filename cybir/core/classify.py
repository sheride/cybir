"""Contraction classification for extremal birational contractions.

Implements the five-type classification algorithm from
arXiv:2212.10573 Section 4: asymptotic, CFT, su(2) enhancement,
symmetric flop, and generic flop.

Each helper predicate is individually callable (D-06) and uses
"classify" terminology throughout (D-11). All docstrings cite
the relevant equations from arXiv:2212.10573 (D-12).
"""

import numpy as np
from scipy.linalg import null_space

from .flop import wall_cross_c2, wall_cross_intnums
from .gv import gv_eff
from .types import ContractionType, InsufficientGVError, PartialClassification
from .coxeter import coxeter_reflection
from .util import (
    minimal_N,
    projected_int_nums,
    projection_matrix,
)


# Contraction types that remain possible when geometry has narrowed to
# "zero-volume divisor exists with integer Coxeter reflection." GVs are
# required to disambiguate.
_MULTI_OPTION_REMAINING = (
    ContractionType.SYMMETRIC_FLOP,
    ContractionType.SU2,
    ContractionType.GROSS_FLOP,
    ContractionType.FLOP,
)

_DISAMBIGUATION_HINT = (
    "Compute GV invariants up to at least degree 3 (GV(C), GV(2C), GV(3C)) "
    "to compute gv_eff_1 and gv_eff_3 for the wall-crossing formulas. "
    "The wall-crossed intersection numbers / second Chern class compared "
    "against their Coxeter-reflected counterparts distinguish symmetric "
    "from generic flops; the source/flopped Kahler-cone match distinguishes "
    "GROSS_FLOP from SYMMETRIC_FLOP; GV signs at low degree distinguish "
    "SYMMETRIC_FLOP from SU2. Higher degrees may be needed for potency "
    "convergence (the final GV in the series must be zero)."
)


def is_asymptotic(int_nums, curve):
    r"""Check whether a contraction is asymptotic (Type III).

    A contraction is **asymptotic** when the fully-projected triple
    intersection numbers vanish:

    .. math::

        \kappa_{abc} \, \Pi^a_\perp \, \Pi^b_\perp \, \Pi^c_\perp = 0

    where :math:`\Pi_\perp` is the projector onto the complement of
    the flopping curve :math:`\mathcal{C}`.

    This means the curve direction has no cubic volume contribution
    transverse to the wall, corresponding to an infinite-distance
    boundary in moduli space.

    See arXiv:2212.10573 Section 2 (asymptotic boundaries).

    Parameters
    ----------
    int_nums : numpy.ndarray
        Triple intersection numbers :math:`\kappa_{ijk}`, shape
        ``(h11, h11, h11)``.
    curve : numpy.ndarray
        Curve class :math:`\mathcal{C}_a`, shape ``(h11,)``.

    Returns
    -------
    bool
        ``True`` if the contraction is asymptotic.
    """
    proj = projected_int_nums(int_nums, curve, n_projected=3)
    return bool(np.allclose(proj, 0))


def is_cft(int_nums, curve):
    r"""Check whether a contraction is a CFT boundary (Type II).

    A contraction is a **CFT boundary** when the projected
    intersection-number matrix (one index projected) is
    rank-deficient:

    .. math::

        \operatorname{rank}\bigl(
            \kappa_{ajk} \, \Pi^a_\perp
        \bigr) < h^{1,1} - 1

    This signals that some divisor volumes remain non-vanishing at the
    wall, corresponding to a CFT point in moduli space.

    See arXiv:2212.10573 Section 2 (CFT boundaries).

    Parameters
    ----------
    int_nums : numpy.ndarray
        Triple intersection numbers :math:`\kappa_{ijk}`, shape
        ``(h11, h11, h11)``.
    curve : numpy.ndarray
        Curve class :math:`\mathcal{C}_a`, shape ``(h11,)``.

    Returns
    -------
    bool
        ``True`` if the contraction is a CFT boundary.
    """
    # Match the original code: project only the LAST index (N=1), giving
    # shape (h11, h11, h11-1), then reshape to (h11, -1) and check
    # rank < min(shape) = rank < h11.
    P = np.asarray(projection_matrix(curve), dtype=float)
    int_nums = np.asarray(int_nums, dtype=float)
    h11 = len(curve)
    # Project last index: einsum('abc,zc->abz', intnums, P.T)
    # P has shape (h11-1, h11), so P.T is (h11, h11-1)
    proj = np.einsum("ijk,ak->ija", int_nums, P)  # (h11, h11, h11-1)
    matrix = proj.reshape(h11, -1)  # (h11, h11*(h11-1))
    return bool(np.linalg.matrix_rank(matrix, tol=1e-8) < np.amin(matrix.shape))


def zero_vol_divisor(int_nums, curve):
    r"""Find a divisor that shrinks to zero volume at this wall.

    Computes the null space of the projected intersection matrix
    contracted with the flopping curve:

    .. math::

        M_{\alpha\beta} = \kappa_{ijk} \, \Pi^i_\alpha \,
        \Pi^j_\beta \, \mathcal{C}^k

    where :math:`\Pi` is the projection onto the complement of
    :math:`\mathcal{C}`. If :math:`M` has a null vector
    :math:`v_\alpha`, the zero-volume divisor in the full basis is
    :math:`D_i = \Pi^T_{i\alpha} v_\alpha`, cleaned to integer form.

    **Sign convention:** :math:`D \cdot \mathcal{C} < 0`.

    The zero-volume divisor is defined only up to sign (it spans a 1D
    null space).  The sign is fixed by requiring :math:`D \cdot C < 0`,
    where :math:`C` is the inward-pointing Mori cone generator of the
    source phase.  Physically, this is the divisor that *would become
    effective* if one tuned complex structure to make this wall an su(2)
    enhancement, taking the source phase as the fundamental domain.

    Under the Coxeter reflection :math:`R` associated to the wall,
    :math:`R^{-T} D = -D` (the reflection acting on divisors sends
    :math:`D \to -D`).  This is consistent: viewing the wall from the
    other phase reverses which side is the fundamental domain and
    requires :math:`-D` as the would-be effective divisor.  Thus the
    same wall produces opposite-sign zvds when classified from opposite
    phases — this is expected, not a bug.

    See arXiv:2212.10573 Section 4 (shrinking divisors).

    Parameters
    ----------
    int_nums : numpy.ndarray
        Triple intersection numbers :math:`\kappa_{ijk}`, shape
        ``(h11, h11, h11)``.
    curve : numpy.ndarray
        Curve class :math:`\mathcal{C}_a`, shape ``(h11,)``.

    Returns
    -------
    numpy.ndarray or None
        Integer divisor class with :math:`D \cdot \mathcal{C} < 0`,
        or ``None`` if no zero-volume divisor exists.
    """
    curve = np.asarray(curve, dtype=float)
    int_nums = np.asarray(int_nums, dtype=float)
    h11 = len(curve)

    # Match original: project last 2 indices (N=2), giving shape
    # (h11, h11-1, h11-1), then reshape to (h11, (h11-1)^2).
    P = np.asarray(projection_matrix(curve), dtype=float)  # (h11-1, h11)
    proj2 = np.einsum("ijk,bj,ck->ibc", int_nums, P, P)  # (h11, h11-1, h11-1)
    matrix = proj2.reshape(h11, -1)  # (h11, (h11-1)^2)

    rank = np.linalg.matrix_rank(matrix, tol=1e-8)
    if rank == h11:
        return None
    elif rank == h11 - 1:
        # Null space of matrix.T gives divisor in full h11 basis
        result = null_space(matrix.T)[:, 0]
        result /= max(abs(result))
        result *= minimal_N(result)

        assert np.allclose(result, np.round(result))
        result = np.round(result).astype(int)

        # Sign convention: D . C < 0 (simple dot product works here
        # because D is in the full basis, not the projected subspace)
        sign = np.sign(result @ curve)
        if sign != 0:
            result = -int(sign) * result

        return result.astype(float)
    else:
        # Rank deficit > 1: zero-vol divisor is not unique
        return None


def _kahler_cones_match(source_kc, flopped_kc, reflection):
    """Check if Coxeter reflection maps source Kahler cone to flopped Kahler cone.

    Condition (b) for symmetric flop classification: the reflection must
    map the source cone to the flopped cone. Checks bidirectional
    containment of reflected rays.

    Parameters
    ----------
    source_kc : cytools.Cone
        Source phase Kahler cone.
    flopped_kc : cytools.Cone
        Flopped phase Kahler cone.
    reflection : numpy.ndarray
        Coxeter reflection matrix.

    Returns
    -------
    bool
    """
    M_inv = np.round(np.linalg.inv(reflection.astype(float))).astype(int)
    reflected_rays = source_kc.rays() @ M_inv
    # Build cone from reflected rays and check equality via dual containment
    import cytools
    reflected_cone = cytools.Cone(rays=reflected_rays)
    # Two cones equal iff each contains the other's rays
    flopped_rays = flopped_kc.rays()
    for ray in flopped_rays:
        if not all(h @ ray >= -1e-8 for h in reflected_cone.hyperplanes()):
            return False
    for ray in reflected_rays:
        if not all(h @ ray >= -1e-8 for h in flopped_kc.hyperplanes()):
            return False
    return True


def is_symmetric_flop(int_nums, c2, curve, gv_eff_1, gv_eff_3,
                      coxeter_reflection, source_kc=None, flopped_kc=None):
    r"""Check whether a flop is symmetric under the Coxeter reflection.

    A flop is **symmetric** when two conditions hold:

    (a) The wall-crossed intersection numbers and second Chern class
    equal their Coxeter-reflected counterparts:

    .. math::

        \kappa'_{abc} = M_{ai} M_{bj} M_{ck} \, \kappa_{ijk}
        \quad\text{and}\quad
        c'_{2,a} = M^T_{ai} \, c_{2,i}

    (b) The Coxeter reflection maps the source Kahler cone to the
    flopped Kahler cone.

    If condition (a) passes but (b) fails, the flop is a **gross flop**
    (condition (a) satisfied at the level of intersection numbers, but
    the Kahler cones do not match under the reflection).

    See arXiv:2212.10573 Section 4 (symmetric flops).

    Parameters
    ----------
    int_nums : numpy.ndarray
        Triple intersection numbers :math:`\kappa_{ijk}`.
    c2 : numpy.ndarray
        Second Chern class :math:`c_2 \cdot D_a`.
    curve : numpy.ndarray
        Flopping curve class.
    gv_eff_1 : int
        Linear effective GV invariant.
    gv_eff_3 : int
        Cubic effective GV invariant.
    coxeter_reflection : numpy.ndarray
        Coxeter reflection matrix :math:`M_{ab}`.
    source_kc : optional
        Source phase Kahler cone (``cytools.Cone``). If None, condition
        (b) is skipped for backward compatibility.
    flopped_kc : optional
        Flopped phase Kahler cone (``cytools.Cone``). If None, condition
        (b) is skipped for backward compatibility.

    Returns
    -------
    tuple[bool, bool]
        ``(is_symmetric, is_gross_flop)``. If condition (a) fails,
        returns ``(False, False)``. If (a) passes and (b) fails,
        returns ``(False, True)`` (gross flop). If both pass (or cones
        not provided), returns ``(True, False)``.
    """
    # Integrality check: a valid Coxeter reflection must act on the
    # integer lattice. Non-integer reflections cannot generate a
    # finite Coxeter group and indicate a generic (non-symmetric) flop.
    M = coxeter_reflection
    if not np.allclose(M, np.round(M)):
        return (False, False)

    # Wall-crossed quantities
    wc_intnums = wall_cross_intnums(int_nums, curve, gv_eff_3)
    wc_c2 = wall_cross_c2(c2, curve, gv_eff_1)

    # Coxeter-reflected quantities
    cox_intnums = np.einsum("ia,jb,kc,abc->ijk", M, M, M, int_nums)
    cox_c2 = M @ c2

    # Condition (a): intersection numbers and c2 match
    cond_a = bool(
        np.allclose(wc_intnums, cox_intnums)
        and np.allclose(wc_c2, cox_c2)
    )

    if not cond_a:
        return (False, False)

    # Condition (b): Kahler cones match under reflection
    if source_kc is not None and flopped_kc is not None:
        cond_b = _kahler_cones_match(source_kc, flopped_kc, M)
        if not cond_b:
            return (False, True)  # gross flop

    return (True, False)


def classify_contraction(int_nums, c2, curve, gv_series):
    r"""Classify an extremal contraction and return all metadata.

    Follows the sequential classification algorithm from
    arXiv:2212.10573, Section 4:

    1. Check if asymptotic (projected volumes vanish)
    2. Check if CFT (rank-deficient projected matrix)
    3. Compute effective GV invariants
    4. Check potency (raise InsufficientGVError if potent)
    5. Find zero-volume divisor
    6. If no zero-vol divisor: generic flop (Type I)
    7. If zero-vol divisor exists:

       a. Compute Coxeter reflection
       b. Check if symmetric flop
       c. If symmetric and GV signs are non-negative: symmetric flop
       d. If symmetric but negative GV: su(2) enhancement
       e. If not symmetric: generic flop (Type II)

    .. math::

        \text{asymptotic} \to \text{CFT} \to \text{potent?}
        \to \text{flop/symmetric/su(2)}

    See arXiv:2212.10573, Section 4 for the full classification algorithm.

    Parameters
    ----------
    int_nums : numpy.ndarray
        Triple intersection numbers, shape ``(h11, h11, h11)``.
    c2 : numpy.ndarray
        Second Chern class, shape ``(h11,)``.
    curve : numpy.ndarray
        Flopping curve class, shape ``(h11,)``.
    gv_series : list[int]
        GV series ``[GV(C), GV(2C), ...]``.

    Returns
    -------
    dict
        Keys: ``contraction_type`` (ContractionType), ``zero_vol_divisor``
        (ndarray or None), ``coxeter_reflection`` (ndarray or None),
        ``gv_invariant`` (int), ``effective_gv`` (int = gv_eff_3),
        ``gv_eff_1`` (int), ``gv_series`` (list[int]).

    Raises
    ------
    InsufficientGVError
        If the GV series appears potent (last entry nonzero).
    """
    int_nums = np.asarray(int_nums, dtype=float)
    c2 = np.asarray(c2, dtype=float)
    curve = np.asarray(curve)

    def _make_result(ctype, zero_vol=None, cox_ref=None,
                     gv_inv=0, eff_gv=0, gv1=0, series=None):
        return {
            "contraction_type": ctype,
            "zero_vol_divisor": zero_vol,
            "coxeter_reflection": cox_ref,
            "gv_invariant": gv_inv,
            "effective_gv": eff_gv,
            "gv_eff_1": gv1,
            "gv_series": series if series is not None else [],
        }

    # 1. Asymptotic check
    if is_asymptotic(int_nums, curve):
        return _make_result(ContractionType.ASYMPTOTIC)

    # 2. CFT check
    if is_cft(int_nums, curve):
        # CFT walls still have a zero-vol divisor needed for eff cone gens
        zvd = zero_vol_divisor(int_nums, curve)
        return _make_result(ContractionType.CFT, zero_vol=zvd)

    # 3. Compute effective GV invariants
    gv_eff_1, gv_eff_3 = gv_eff(gv_series)

    # 4. Potency check
    if gv_series[-1] != 0:
        raise InsufficientGVError(
            f"GV series appears potent: last entry {gv_series[-1]} != 0"
        )

    # 5. Find zero-volume divisor
    zero_vol_div = zero_vol_divisor(int_nums, curve)

    # 6. No zero-vol divisor -> generic flop
    if zero_vol_div is None:
        return _make_result(
            ContractionType.FLOP,
            gv_inv=gv_series[0],
            eff_gv=gv_eff_3,
            gv1=gv_eff_1,
            series=list(gv_series),
        )

    # 7. Zero-vol divisor exists
    coxeter_ref = coxeter_reflection(zero_vol_div, curve)

    symmetric, is_gross = is_symmetric_flop(
        int_nums, c2, curve, gv_eff_1, gv_eff_3, coxeter_ref
    )

    if is_gross:
        ctype = ContractionType.GROSS_FLOP
    elif symmetric:
        gv_signs_ok = (
            gv_series[0] >= 0
            and (len(gv_series) < 2 or gv_series[1] >= 0)
        )
        if gv_signs_ok:
            ctype = ContractionType.SYMMETRIC_FLOP
        else:
            ctype = ContractionType.SU2
    else:
        ctype = ContractionType.FLOP

    return _make_result(
        ctype,
        zero_vol=zero_vol_div,
        cox_ref=coxeter_ref,
        gv_inv=gv_series[0],
        eff_gv=gv_eff_3,
        gv1=gv_eff_1,
        series=list(gv_series),
    )


def classify_geometric(int_nums, c2, curve):
    r"""Classify an extremal contraction from geometric data alone (no GVs).

    Performs the cheap geometric checks from
    :func:`classify_contraction` -- asymptotic, CFT, zero-volume divisor
    existence, Coxeter-reflection integrality -- and returns a
    :class:`~cybir.core.types.PartialClassification` capturing what
    geometry alone determines.

    Three branches pin the type down without GVs:

    1. **Asymptotic** -- projected triple intersections vanish.
    2. **CFT** -- projected matrix is rank-deficient.
    3. **FLOP** -- no zero-volume divisor, *or* a zero-vol divisor exists
       but the resulting Coxeter reflection has non-integer entries
       (cannot generate a finite Coxeter group).

    When none of these apply, the contraction is one of
    ``{SYMMETRIC_FLOP, SU2, GROSS_FLOP, FLOP}`` and GVs are required to
    disambiguate (see ``needs_for_disambiguation`` on the result).

    See arXiv:2212.10573 Section 4 for the underlying classification.

    Parameters
    ----------
    int_nums : numpy.ndarray
        Triple intersection numbers :math:`\kappa_{ijk}`,
        shape ``(h11, h11, h11)``.
    c2 : numpy.ndarray
        Second Chern class :math:`c_2 \cdot D_a`, shape ``(h11,)``.
    curve : numpy.ndarray
        Curve class, shape ``(h11,)``.

    Returns
    -------
    PartialClassification
        Geometric classification result. Inspect ``.determined`` for
        the unique type when geometry suffices, or ``.remaining_options``
        when GVs are needed.

    Examples
    --------
    >>> partial = classify_geometric(int_nums, c2, [1, 0, -1])
    >>> if partial.determined is not None:
    ...     print(f"Determined: {partial.determined.name}")
    ... else:
    ...     print(f"GVs needed; possibilities: {partial.remaining_options}")
    """
    int_nums = np.asarray(int_nums, dtype=float)
    c2 = np.asarray(c2, dtype=float)
    curve = np.asarray(curve)

    # 1. Asymptotic -- terminal
    if is_asymptotic(int_nums, curve):
        return PartialClassification(
            zero_vol_divisor=None,
            coxeter_reflection=None,
            is_asymptotic=True,
            is_cft=False,
            determined=ContractionType.ASYMPTOTIC,
            remaining_options=(ContractionType.ASYMPTOTIC,),
            needs_for_disambiguation="",
        )

    # 2. CFT -- terminal (with zvd as a useful side-effect for cone gens)
    if is_cft(int_nums, curve):
        zvd = zero_vol_divisor(int_nums, curve)
        return PartialClassification(
            zero_vol_divisor=zvd,
            coxeter_reflection=None,
            is_asymptotic=False,
            is_cft=True,
            determined=ContractionType.CFT,
            remaining_options=(ContractionType.CFT,),
            needs_for_disambiguation="",
        )

    # 3. zero-volume divisor
    zvd = zero_vol_divisor(int_nums, curve)

    # 3a. No zero-vol divisor -- generic FLOP, terminal
    if zvd is None:
        return PartialClassification(
            zero_vol_divisor=None,
            coxeter_reflection=None,
            is_asymptotic=False,
            is_cft=False,
            determined=ContractionType.FLOP,
            remaining_options=(ContractionType.FLOP,),
            needs_for_disambiguation="",
        )

    # 4. Compute Coxeter reflection from zvd + curve (no GVs needed)
    M = coxeter_reflection(zvd, curve)

    # 4a. Non-integer reflection -- can't generate a finite Coxeter group;
    # this is a generic FLOP, terminal. Mirrors the integrality check
    # in is_symmetric_flop.
    if not np.allclose(M, np.round(M)):
        return PartialClassification(
            zero_vol_divisor=zvd,
            coxeter_reflection=M,
            is_asymptotic=False,
            is_cft=False,
            determined=ContractionType.FLOP,
            remaining_options=(ContractionType.FLOP,),
            needs_for_disambiguation="",
        )

    # 5. Multi-option: zvd exists, M is integer. GVs needed.
    return PartialClassification(
        zero_vol_divisor=zvd,
        coxeter_reflection=M,
        is_asymptotic=False,
        is_cft=False,
        determined=None,
        remaining_options=_MULTI_OPTION_REMAINING,
        needs_for_disambiguation=_DISAMBIGUATION_HINT,
    )


def gv_degrees_needed(int_nums, c2, curve):
    """Return the minimum GV degree needed to fully classify a curve.

    Wraps :func:`classify_geometric` and returns ``0`` when geometry
    alone determines the contraction type, ``3`` when GVs are needed.
    Useful for callers with expensive ``compute_gvs`` budgets who want
    to skip the call entirely when geometry suffices.

    Note that ``3`` is a *minimum*: in practice you may want a longer
    series so the trailing GV is zero (the potency-check convergence
    requirement in :func:`classify_contraction`).

    Parameters
    ----------
    int_nums : numpy.ndarray
        Triple intersection numbers, shape ``(h11, h11, h11)``.
    c2 : numpy.ndarray
        Second Chern class, shape ``(h11,)``.
    curve : numpy.ndarray
        Curve class, shape ``(h11,)``.

    Returns
    -------
    int
        ``0`` when geometry alone classifies the curve (``ASYMPTOTIC``,
        ``CFT``, or ``FLOP`` from no-zvd / non-integer-reflection paths).
        ``3`` when GVs are required to disambiguate among
        ``{SYMMETRIC_FLOP, SU2, GROSS_FLOP, FLOP}``.

    Examples
    --------
    >>> n = gv_degrees_needed(int_nums, c2, curve)
    >>> if n == 0:
    ...     result = diagnose_curve(cy, curve, compute_gvs=False)
    ... else:
    ...     gvs = cy.compute_gvs(max_deg=max(n, 10))
    ...     result = diagnose_curve(cy, curve, gvs=gvs)
    """
    partial = classify_geometric(int_nums, c2, curve)
    return 0 if partial.determined is not None else 3
