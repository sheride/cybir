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
from .types import ContractionType, InsufficientGVError
from .util import (
    minimal_N,
    coxeter_reflection,
    projected_int_nums,
    projection_matrix,
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
    cox_c2 = M @ c2

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
