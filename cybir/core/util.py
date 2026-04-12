"""Utility functions for cybir.

Provides lattice-computation helpers (charge matrix via Smith Normal Form,
projection matrix), moving cone construction, symbolic number cleanup,
array-to-tuple conversion, and curve normalization.

These replace the previous dependencies on cornell-dev's ``lib.util.lattice``
and ``misc`` modules.
"""

import hsnf
import numpy as np
import sympy


def charge_matrix_hsnf(vectors):
    """Compute integer relations among vectors via Smith Normal Form.

    Given a set of integer vectors, finds the integer linear relations
    (kernel basis) using the Smith Normal Form decomposition.

    Parameters
    ----------
    vectors : array_like
        Integer vectors, shape ``(n_vectors, dim)``.

    Returns
    -------
    numpy.ndarray
        Integer relation matrix, shape ``(n_relations, n_vectors)``.
        Each row is an integer linear combination of the input vectors
        that equals zero.

    Examples
    --------
    >>> charge_matrix_hsnf([[1, 0, 1], [0, 1, 1]])
    array(...)  # shape (1, 3), the single relation among 3 points in 2D
    """
    D, U, W = hsnf.smith_normal_form(np.array(vectors).T)
    rank = sum(1 for i in range(min(len(D), len(D[0]))) if D[i, i] != 0)
    relations = W[:, rank:]
    return relations.T


def moving_cone(Q, verbose=False):
    """Compute the moving cone from the charge matrix.

    Iterates over columns of *Q*, computes the cone of remaining columns'
    hyperplanes, and forms their intersection.

    Parameters
    ----------
    Q : numpy.ndarray
        Charge matrix, shape ``(n_relations, n_divisors)``.
    verbose : bool, optional
        If ``True``, print progress (default ``False``).

    Returns
    -------
    cytools.Cone
        The moving cone.

    Notes
    -----
    Adapted from N. Gendler's implementation. See arXiv:2212.10573
    Section 2 for the role of the moving cone in the EKC construction.
    """
    import cytools

    hyps = np.vstack([
        cytools.Cone(rays=np.delete(Q, i, axis=1).T).hyperplanes()
        for i in range(Q.shape[1])
    ])
    return cytools.Cone(hyperplanes=hyps)


def sympy_number_clean(x):
    """Convert a float to its exact rational representation.

    Uses SymPy's ``Rational`` with ``limit_denominator`` to find
    the closest simple fraction.

    Parameters
    ----------
    x : float or int
        Number to convert.

    Returns
    -------
    sympy.Rational
        Exact rational representation.

    Examples
    --------
    >>> sympy_number_clean(0.333333333)
    1/3
    >>> sympy_number_clean(2.5)
    5/2
    """
    return sympy.Rational(x).limit_denominator()


def tuplify(arr):
    """Convert a numpy ndarray into a nested tuple structure.

    Recursively converts arrays and lists into nested tuples,
    suitable for use as dictionary keys or set elements.

    Parameters
    ----------
    arr : numpy.ndarray or list or scalar
        Input to convert.

    Returns
    -------
    tuple or scalar
        Nested tuple structure, or scalar if input is 0-d.

    Examples
    --------
    >>> tuplify(np.array([1, 2, 3]))
    (1, 2, 3)
    >>> tuplify(np.array([[1, 2], [3, 4]]))
    ((1, 2), (3, 4))
    """
    if isinstance(arr, np.ndarray):
        if arr.ndim == 0:
            return arr.item()
        return tuple(tuplify(x) for x in arr.tolist())
    if isinstance(arr, list):
        return tuple(tuplify(x) for x in arr)
    return arr


def normalize_curve(curve, return_sign=False):
    """Normalize a curve class so first nonzero element is positive.

    This canonical form ensures that a curve and its negation
    map to the same representative, which is essential for
    identifying flopping curves in the EKC construction.

    Parameters
    ----------
    curve : numpy.ndarray
        Array representing a curve class.
    return_sign : bool, optional
        If ``True``, also return the sign factor (default ``False``).

    Returns
    -------
    tuple
        Normalized curve as a tuple. If *return_sign* is ``True``,
        returns ``(tuple, sign)`` where ``sign`` is +1 or -1.

    Examples
    --------
    >>> normalize_curve(np.array([-1, 2, 3]))
    (1, -2, -3)
    >>> normalize_curve(np.array([-1, 0, 0]), return_sign=True)
    ((1, 0, 0), -1)
    """
    first_nonzero = next((c for c in curve if c != 0), None)
    if first_nonzero is None:
        raise ValueError("Cannot normalize the zero curve")
    if first_nonzero > 0:
        to_return = tuple(curve.tolist())
        sign = 1
    else:
        to_return = tuple((-curve).tolist())
        sign = -1
    return (to_return, sign) if return_sign else to_return


def projection_matrix(curve):
    """Return (N-1) x N matrix projecting onto complement of curve.

    Uses Smith Normal Form to find a unimodular change-of-basis
    that maps *curve* to a multiple of the first basis vector,
    then returns the last N-1 rows (the orthogonal complement).

    Parameters
    ----------
    curve : numpy.ndarray
        1D integer array representing a curve class.

    Returns
    -------
    numpy.ndarray
        Integer matrix of shape ``(N-1, N)`` whose rows span the
        sublattice orthogonal to *curve*.

    Notes
    -----
    The result satisfies ``projection_matrix(curve) @ curve == 0``.
    """
    return hsnf.smith_normal_form(np.array([curve]).T)[1][1:]


def projected_int_nums(int_nums, curve, n_projected=3):
    """Project intersection numbers along a curve direction.

    Contracts ``n_projected`` indices of the triple intersection number
    tensor :math:`\\kappa_{ijk}` with the projection matrix
    :math:`P_{\\alpha i}` that maps onto the sublattice orthogonal to
    *curve*.

    This implements the projected volume computation from
    arXiv:2212.10573 Section 2, where the projected intersection numbers
    determine volumes in the reduced Kahler cone after removing the
    flopping-curve direction.

    Parameters
    ----------
    int_nums : numpy.ndarray
        Triple intersection numbers :math:`\\kappa_{ijk}`, shape
        ``(h11, h11, h11)``.
    curve : numpy.ndarray
        1D integer array representing the curve class to project along.
    n_projected : int, optional
        Number of indices to contract with the projector (1, 2, or 3).
        Default is 3 (full contraction).

    Returns
    -------
    numpy.ndarray or scalar
        Projected intersection numbers. Shape depends on *n_projected*:
        3 -> scalar, 2 -> ``(h11-1,)``, 1 -> ``(h11-1, h11-1)``.
    """
    P = projection_matrix(curve)
    if n_projected == 3:
        return np.einsum("ai,bj,ck,ijk", P, P, P, int_nums).squeeze()
    elif n_projected == 2:
        return np.einsum("ai,bj,ijk->abk", P, P, int_nums).squeeze()
    elif n_projected == 1:
        return np.einsum("ai,ijk->ajk", P, int_nums).squeeze()
    else:
        raise ValueError(f"n_projected must be 1, 2, or 3, got {n_projected}")


def minimal_N(X, epsilon=1e-4, max_val=10000):
    """Find the smallest positive integer N such that N*X is integer-valued.

    Useful for determining the minimal multiplicity of a curve class
    that gives integer intersection numbers.

    Parameters
    ----------
    X : numpy.ndarray
        Array of (possibly non-integer) values.
    epsilon : float, optional
        Tolerance for integrality check (default ``1e-4``).
    max_val : int, optional
        Maximum N to try (default ``10000``).

    Returns
    -------
    int
        The smallest positive integer N with all entries of N*X
        within *epsilon* of an integer.

    Raises
    ------
    ValueError
        If no such N is found up to *max_val*.
    """
    X = np.asarray(X, dtype=float).ravel()
    for N in range(1, max_val + 1):
        scaled = N * X
        if np.all(np.abs(scaled - np.round(scaled)) < epsilon):
            return N
    raise ValueError(
        f"No integer N <= {max_val} makes all entries of N*X integer-valued."
    )

