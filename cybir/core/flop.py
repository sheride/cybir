"""Wall-crossing formula implementations for birational flops.

Provides functions to transform intersection numbers and second Chern
class across a wall in the extended Kahler cone, and a convenience
function to create a new CalabiYauLite representing the flopped phase.
"""

import numpy as np

from .gv import compute_gv_eff
from .types import CalabiYauLite


def wall_cross_intnums(int_nums, curve, gv_eff_3):
    r"""Transform intersection numbers across a wall-crossing.

    Applies the wall-crossing formula for triple intersection numbers
    when flopping a curve :math:`\mathcal{C}`:

    .. math::

        \kappa'_{abc} = \kappa_{abc}
        - n^{\mathrm{eff,3}}_{\mathcal{C}} \,
          \mathcal{C}_a \, \mathcal{C}_b \, \mathcal{C}_c

    where :math:`n^{\mathrm{eff,3}}_{\mathcal{C}}` is the cubic
    effective GV invariant.

    See arXiv:2212.10573 below Eq. (2.7) and Eq. (4.4).

    Parameters
    ----------
    int_nums : numpy.ndarray
        Triple intersection numbers :math:`\kappa_{abc}`.
    curve : array_like
        Curve class :math:`\mathcal{C}_a` in the Mori cone basis.
    gv_eff_3 : int
        Cubic effective GV invariant
        :math:`n^{\mathrm{eff,3}}_{\mathcal{C}}`.

    Returns
    -------
    numpy.ndarray
        Transformed intersection numbers :math:`\kappa'_{abc}`.
    """
    curve = np.asarray(curve)
    return int_nums - gv_eff_3 * np.einsum("a,b,c", curve, curve, curve)


def wall_cross_c2(c2, curve, gv_eff_1):
    r"""Transform second Chern class across a wall-crossing.

    Applies the wall-crossing formula for the second Chern class
    when flopping a curve :math:`\mathcal{C}`:

    .. math::

        c'_a = c_a + 2 \, n^{\mathrm{eff,1}}_{\mathcal{C}} \,
        \mathcal{C}_a

    where :math:`n^{\mathrm{eff,1}}_{\mathcal{C}}` is the linear
    effective GV invariant.

    See arXiv:2212.10573 below Eq. (2.7) and Eq. (4.4).

    Parameters
    ----------
    c2 : numpy.ndarray
        Second Chern class :math:`c_2 \cdot D_a`.
    curve : array_like
        Curve class :math:`\mathcal{C}_a` in the Mori cone basis.
    gv_eff_1 : int
        Linear effective GV invariant
        :math:`n^{\mathrm{eff,1}}_{\mathcal{C}}`.

    Returns
    -------
    numpy.ndarray
        Transformed second Chern class :math:`c'_a`.
    """
    curve = np.asarray(curve)
    return c2 + 2 * gv_eff_1 * curve


def flop_phase(cy_lite, curve, gv_series, label=None):
    r"""Create a new CalabiYauLite by flopping across a wall.

    Computes the effective GV invariants from the GV series, then
    applies the wall-crossing formula to the intersection numbers
    and second Chern class to produce a new phase.

    The Kahler cone, Mori cone, and other cone data are NOT copied
    because they change under the flop (computed in Phase 3).
    The GV invariants are also not set because transforming them
    requires CYTools Invariants manipulation (Phase 3 / INTG-01).

    Parameters
    ----------
    cy_lite : CalabiYauLite
        The source phase.
    curve : array_like
        Curve class :math:`\mathcal{C}_a` being flopped.
    gv_series : list[int]
        GV series :math:`[n^0_{[\mathcal{C}]}, n^0_{2[\mathcal{C}]},
        \ldots]`.
    label : str, optional
        Phase label for the new CalabiYauLite.

    Returns
    -------
    CalabiYauLite
        A new phase with transformed intersection numbers and c2.
    """
    curve = np.asarray(curve)
    gv_eff_1, gv_eff_3 = compute_gv_eff(gv_series)

    new_int_nums = wall_cross_intnums(cy_lite.int_nums, curve, gv_eff_3)

    new_c2 = None
    if cy_lite.c2 is not None:
        new_c2 = wall_cross_c2(cy_lite.c2, curve, gv_eff_1)

    return CalabiYauLite(int_nums=new_int_nums, c2=new_c2, label=label)
