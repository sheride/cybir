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
from .gv import compute_gv_eff
from .types import ContractionType, InsufficientGVError
from .util import (
    find_minimal_N,
    get_coxeter_reflection,
    projected_int_nums,
    projection_matrix,
    sympy_number_clean,
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
    # Compute the projection without squeeze to preserve the projected
    # dimension (h11-1). projected_int_nums uses .squeeze() which drops
    # size-1 dimensions and loses the projected basis size for h11=2.
    P = np.asarray(projection_matrix(curve), dtype=float)
    h11m1 = P.shape[0]
    int_nums = np.asarray(int_nums, dtype=float)
    proj = np.einsum("ax,xyz->ayz", P, int_nums)  # (h11-1, h11, h11)
    proj = proj.reshape(h11m1, -1)  # (h11-1, h11*h11)
    return bool(np.linalg.matrix_rank(proj) < h11m1)


def find_zero_vol_divisor(int_nums, curve):
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

    The sign convention is :math:`D \cdot \mathcal{C} < 0`
    (Pitfall 3 in Phase 2 RESEARCH.md).

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
    P = np.asarray(projection_matrix(curve), dtype=float)  # shape (h11-1, h11)
    int_nums = np.asarray(int_nums, dtype=float)

    # Project two indices: shape (h11-1, h11-1, h11)
    # Use unique subscript letters to avoid numpy 2.x einsum ambiguity
    proj2 = np.einsum("ax,by,xyz->abz", P, P, int_nums)

    # Contract with curve: shape (h11-1, h11-1)
    M = np.einsum("abk,k->ab", proj2, curve)

    # Find null space
    ns = null_space(M)

    if ns.shape[1] == 0:
        return None

    # Take first null vector
    null_vec = ns[:, 0]

    # Lift back to full basis
    result = P.T @ null_vec

    # Clean to integer
    N = find_minimal_N(result)
    result = N * result
    result = np.array([float(sympy_number_clean(x)) for x in result])

    # Sign convention: divisor @ curve < 0 using the intersection pairing.
    # Since D is found via projection orthogonal to C, the simple dot
    # product D.C vanishes identically. Instead use the triple
    # intersection number kappa_{ijk} D_i D_j C_k as the sign indicator:
    # this is the volume form that determines whether D shrinks at the wall.
    vol = np.einsum("ijk,i,j,k", int_nums, result, result, curve)
    if vol > 0:
        result = -result
    elif np.isclose(vol, 0):
        # Fallback: ensure first nonzero entry is positive
        first_nz = next((x for x in result if not np.isclose(x, 0)), 1)
        if first_nz < 0:
            result = -result

    return result


def is_symmetric_flop(int_nums, c2, curve, gv_eff_1, gv_eff_3,
                      coxeter_reflection):
    r"""Check whether a flop is symmetric under the Coxeter reflection.

    A flop is **symmetric** when the wall-crossed intersection numbers
    and second Chern class equal their Coxeter-reflected counterparts:

    .. math::

        \kappa'_{abc} = M_{ai} M_{bj} M_{ck} \, \kappa_{ijk}
        \quad\text{and}\quad
        c'_{2,a} = M^T_{ai} \, c_{2,i}

    where :math:`M` is the Coxeter reflection matrix from
    arXiv:2212.10573 Eq. (4.6).

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

    Returns
    -------
    bool
        ``True`` if the flop is symmetric.
    """
    # Wall-crossed quantities
    wc_intnums = wall_cross_intnums(int_nums, curve, gv_eff_3)
    wc_c2 = wall_cross_c2(c2, curve, gv_eff_1)

    # Coxeter-reflected quantities
    M = coxeter_reflection
    cox_intnums = np.einsum("ia,jb,kc,abc->ijk", M, M, M, int_nums)
    cox_c2 = M.T @ c2

    return bool(
        np.allclose(wc_intnums, cox_intnums)
        and np.allclose(wc_c2, cox_c2)
    )


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
        return _make_result(ContractionType.CFT)

    # 3. Compute effective GV invariants
    gv_eff_1, gv_eff_3 = compute_gv_eff(gv_series)

    # 4. Potency check
    if gv_series[-1] != 0:
        raise InsufficientGVError(
            f"GV series appears potent: last entry {gv_series[-1]} != 0"
        )

    # 5. Find zero-volume divisor
    zero_vol_div = find_zero_vol_divisor(int_nums, curve)

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
    coxeter_ref = get_coxeter_reflection(zero_vol_div, curve)

    symmetric = is_symmetric_flop(
        int_nums, c2, curve, gv_eff_1, gv_eff_3, coxeter_ref
    )

    if symmetric:
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
