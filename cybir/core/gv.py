"""GV series computation and curve classification.

Provides functions for extracting Gopakumar-Vafa series from a CYTools
Invariants object, computing effective GV invariants, and classifying
curves as potent or nilpotent.
"""

import numpy as np


def gv_series(gv_invariants, curve):
    r"""Extract the GV series for multiples of a curve class.

    Queries the CYTools Invariants object for
    :math:`n^0_{k[\mathcal{C}]}` with :math:`k = 1, 2, 3, \ldots`,
    stopping when the result is ``None`` (degree exceeds computed
    range).

    See arXiv:2303.00757 Section 2 for the GV extraction procedure.

    Parameters
    ----------
    gv_invariants : cytools.Invariants
        A CYTools Invariants object with a ``gv(curve)`` method.
    curve : array_like
        Curve class :math:`[\mathcal{C}]` in the Mori cone basis.

    Returns
    -------
    list[int]
        GV series :math:`[n^0_{[\mathcal{C}]}, n^0_{2[\mathcal{C}]},
        \ldots]`. Empty if the first query returns ``None``.
    """
    curve = np.asarray(curve)
    series = []
    k = 1
    while True:
        val = gv_invariants.gv(k * curve)
        if val is None:
            break
        series.append(int(val))
        k += 1
    return series


def gv_eff(gv_series):
    r"""Compute effective GV invariants from a GV series.

    The effective GV invariants are weighted sums over the series
    of multiples:

    .. math::

        n^{\mathrm{eff},p}_{\mathcal{C}}
        = \sum_k k^p \, n^0_{k[\mathcal{C}]}

    This function returns the :math:`p=1` (linear) and :math:`p=3`
    (cubic) effective invariants, which enter the wall-crossing
    formulas for :math:`c_2` and :math:`\kappa_{abc}` respectively.

    See arXiv:2212.10573 below Eq. (2.7).

    Parameters
    ----------
    gv_series : list[int]
        GV series :math:`[n^0_{[\mathcal{C}]}, n^0_{2[\mathcal{C}]},
        \ldots]`.

    Returns
    -------
    tuple[int, int]
        ``(gv_eff_1, gv_eff_3)`` — the linear and cubic effective
        GV invariants.

    Raises
    ------
    ValueError
        If ``gv_series`` is empty.
    """
    if not gv_series:
        raise ValueError("gv_series must be non-empty")
    gv_eff_1 = sum(k * gv for k, gv in enumerate(gv_series, 1))
    gv_eff_3 = sum(k**3 * gv for k, gv in enumerate(gv_series, 1))
    return (gv_eff_1, gv_eff_3)


def is_potent(gv_series):
    r"""Check if a curve is potent based on its GV series.

    A curve is **potent** if the last computed GV invariant in the
    series is nonzero, indicating that the series has not yet
    terminated and the curve contributes unboundedly to the
    prepotential.

    See arXiv:2212.10573 Section 3.1 for the potent/nilpotent
    classification.

    Parameters
    ----------
    gv_series : list[int]
        GV series :math:`[n^0_{[\mathcal{C}]}, n^0_{2[\mathcal{C}]},
        \ldots]`.

    Returns
    -------
    bool
        ``True`` if the curve is potent.
    """
    return len(gv_series) > 0 and gv_series[-1] != 0


def is_nilpotent(gv_series):
    r"""Check if a curve is nilpotent based on its GV series.

    A curve is **nilpotent** if the last computed GV invariant in
    the series is zero, indicating that the series has terminated
    (or is terminating) and the curve's contribution to the
    prepotential is finite.

    See arXiv:2212.10573 Section 3.1 for the potent/nilpotent
    classification.

    Parameters
    ----------
    gv_series : list[int]
        GV series :math:`[n^0_{[\mathcal{C}]}, n^0_{2[\mathcal{C}]},
        \ldots]`.

    Returns
    -------
    bool
        ``True`` if the curve is nilpotent.
    """
    return len(gv_series) > 0 and gv_series[-1] == 0
