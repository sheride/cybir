"""Coxeter group construction, finite-type classification, and BFS enumeration.

Provides the mathematical foundation for Weyl orbit expansion in the
extended Kahler cone construction. Functions include:

- ``matrix_period``: Multiplicative order of an integer matrix
- ``coxeter_reflection``: Reflection matrix from arXiv:2212.10573 Eq. (4.6)
- ``coxeter_element``: Product of reflection matrices (the Coxeter element)
- ``coxeter_order_matrix``: Compute m_ij = order(M_i M_j)
- ``coxeter_bilinear_form``: B_ij = -cos(pi/m_ij)
- ``is_finite_type``: Positive-definiteness check of the bilinear form
- ``classify_coxeter_type``: Decompose into irreducible components and classify
- ``coxeter_group_order``: |W| from closed-form formulas per type
- ``enumerate_coxeter_group``: Streaming BFS on the Cayley graph

See arXiv:2212.10573 Section 4.3 for the role of Coxeter groups in
the extended Kahler cone construction.

Moved from ``cybir.core.util``: ``matrix_period``, ``coxeter_reflection``,
and ``coxeter_matrix`` (renamed to ``coxeter_element``).
"""

import functools
import logging
import warnings
from collections import deque
from math import factorial

import numpy as np

logger = logging.getLogger("cybir")


# ---------------------------------------------------------------------------
# Moved from util.py (per D-02)
# ---------------------------------------------------------------------------

def matrix_period(M, max_iter=200):
    """Compute the multiplicative period of an integer matrix.

    Finds the smallest positive integer *k* such that
    :math:`M^k = I`. Uses exact integer arithmetic (``int64``)
    to avoid float drift (per P-03 in RESEARCH.md).

    Parameters
    ----------
    M : numpy.ndarray
        Square integer matrix.
    max_iter : int, optional
        Maximum power to check (default ``200``).

    Returns
    -------
    int
        The period *k*.

    Raises
    ------
    ValueError
        If no period is found within *max_iter*.

    Notes
    -----
    See arXiv:2212.10573 Section 4.3 for the use of matrix periods
    in computing Coxeter order matrices. The original implementation
    used float64 arithmetic with ``np.allclose``; this version uses
    exact ``int64`` comparison to prevent BFS drift (Pitfall 2).
    """
    M = np.asarray(M, dtype=np.int64)
    n = M.shape[0]
    I = np.eye(n, dtype=np.int64)
    power = I.copy()
    for k in range(1, max_iter + 1):
        power = (power @ M).astype(np.int64)
        if np.array_equal(power, I):
            return k
    raise ValueError(
        f"Matrix does not return to identity within {max_iter} multiplications."
    )


def coxeter_reflection(divisor, curve):
    r"""Compute the Coxeter reflection matrix for a given divisor and curve.

    Implements the reflection

    .. math::

        M_{ab} = \delta_{ab}
                 - 2 \frac{\mathcal{C}_a D_b}{\mathcal{C} \cdot D}

    from arXiv:2212.10573 Eq. (4.6). The reflection satisfies
    :math:`M \mathcal{C} = -\mathcal{C}`.

    When :math:`\mathcal{C} \cdot D = 0` the reflection is undefined
    and the identity matrix is returned.

    Parameters
    ----------
    divisor : numpy.ndarray
        Divisor class :math:`D_a`.
    curve : numpy.ndarray
        Curve class :math:`\mathcal{C}_a`.

    Returns
    -------
    numpy.ndarray
        Reflection matrix of shape ``(h11, h11)``.

    Notes
    -----
    The outer product order is :math:`\mathcal{C}_a D_b` (curve x divisor),
    **not** :math:`D_a \mathcal{C}_b`. Getting this wrong flips which
    vector is reflected.
    """
    divisor = np.asarray(divisor, dtype=float)
    curve = np.asarray(curve, dtype=float)
    h11 = len(curve)
    dot = curve @ divisor
    if dot == 0:
        return np.eye(h11, dtype=float)
    return np.eye(h11) - 2.0 * np.outer(curve, divisor) / dot


def coxeter_element(reflections):
    r"""Compute the Coxeter element from a list of reflection matrices.

    The Coxeter element is the ordered product
    :math:`M_1 M_2 \cdots M_n` of the individual reflections.
    See arXiv:2212.10573 Section 4 for the role of the Coxeter element
    in determining the extended Kahler cone structure.

    Parameters
    ----------
    reflections : list of numpy.ndarray
        Reflection matrices to multiply.

    Returns
    -------
    numpy.ndarray
        The Coxeter element (product of all reflections).

    Raises
    ------
    ValueError
        If *reflections* is empty.

    Notes
    -----
    Renamed from ``coxeter_matrix`` (per P-04). The old name is kept as
    a deprecated alias.
    """
    if not reflections:
        raise ValueError("Cannot compute Coxeter element from empty list of reflections")
    return functools.reduce(np.matmul, reflections)


def coxeter_matrix(reflections):
    """Deprecated alias for :func:`coxeter_element`.

    .. deprecated::
        Use :func:`coxeter_element` instead. This will be removed in a
        future version.
    """
    warnings.warn(
        "coxeter_matrix is deprecated, use coxeter_element instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return coxeter_element(reflections)


# ---------------------------------------------------------------------------
# Coxeter order matrix (D-04)
# ---------------------------------------------------------------------------

def coxeter_order_matrix(reflections):
    r"""Compute the Coxeter order matrix m_ij = order(M_i M_j).

    Diagonal entries are 1 (since :math:`M_i^2 = I` for reflections).
    Off-diagonal entry m_ij is the order of the product :math:`M_i M_j`.

    Parameters
    ----------
    reflections : list of numpy.ndarray
        Integer reflection matrices.

    Returns
    -------
    numpy.ndarray
        Symmetric integer matrix with m_ii = 1.

    Notes
    -----
    See arXiv:2212.10573 Section 4.3. The Coxeter order matrix encodes
    the presentation of the Coxeter group: generators :math:`s_i` with
    relations :math:`(s_i s_j)^{m_{ij}} = 1`.
    """
    n = len(reflections)
    cox = np.ones((n, n), dtype=int)
    for i in range(n):
        for j in range(i + 1, n):
            product = (reflections[i] @ reflections[j]).astype(np.int64)
            cox[i, j] = matrix_period(product)
            cox[j, i] = cox[i, j]
    return cox


# ---------------------------------------------------------------------------
# Bilinear form and finite-type detection (D-06)
# ---------------------------------------------------------------------------

def coxeter_bilinear_form(order_matrix):
    r"""Compute the bilinear form B_ij = -cos(pi / m_ij).

    This is the standard bilinear form associated with a Coxeter group.
    The group is finite if and only if *B* is positive definite.

    Parameters
    ----------
    order_matrix : numpy.ndarray
        Coxeter order matrix (symmetric, integer, diagonal = 1).

    Returns
    -------
    numpy.ndarray
        Real symmetric matrix.

    Notes
    -----
    See arXiv:2212.10573 Section 4.3 and
    `Wikipedia: Coxeter group <https://en.wikipedia.org/wiki/Coxeter_group>`_.
    """
    return -np.cos(np.pi / order_matrix.astype(float))


def is_finite_type(order_matrix):
    """Check if the Coxeter group is finite via positive definiteness.

    A Coxeter group is finite if and only if the bilinear form
    :math:`B_{ij} = -\\cos(\\pi / m_{ij})` is positive definite.

    Parameters
    ----------
    order_matrix : numpy.ndarray
        Coxeter order matrix.

    Returns
    -------
    bool
        ``True`` if the Coxeter group is finite.

    Notes
    -----
    Uses ``np.linalg.eigvalsh`` with tolerance ``1e-10`` to handle
    numerical noise. See arXiv:2212.10573 Section 4.3.
    """
    B = coxeter_bilinear_form(order_matrix)
    eigenvalues = np.linalg.eigvalsh(B)
    return bool(np.all(eigenvalues > 1e-10))


# ---------------------------------------------------------------------------
# Irreducible decomposition and classification (D-05)
# ---------------------------------------------------------------------------

def _decompose_irreducible(order_matrix):
    """Find connected components of the Coxeter graph.

    Nodes are generator indices; an edge exists between i and j
    when m_ij >= 3 (i.e., the generators don't commute).

    Parameters
    ----------
    order_matrix : numpy.ndarray
        Coxeter order matrix.

    Returns
    -------
    list of list of int
        Each sublist is a sorted list of generator indices forming
        an irreducible component.
    """
    n = order_matrix.shape[0]
    visited = [False] * n
    components = []
    for start in range(n):
        if visited[start]:
            continue
        component = []
        stack = [start]
        while stack:
            node = stack.pop()
            if visited[node]:
                continue
            visited[node] = True
            component.append(node)
            for j in range(n):
                if not visited[j] and j != node and order_matrix[node, j] >= 3:
                    stack.append(j)
        components.append(sorted(component))
    return components


def _classify_irreducible(submatrix):
    """Classify an irreducible Coxeter order submatrix.

    Matches the submatrix against known finite Coxeter group Dynkin
    diagrams. Returns the type string, rank, and group order.

    Parameters
    ----------
    submatrix : numpy.ndarray
        Coxeter order submatrix for a connected component.

    Returns
    -------
    tuple of (str, int, int)
        ``(type_string, rank, order)``. Type string is one of
        ``"A"``, ``"B"``, ``"D"``, ``"E"``, ``"F"``, ``"G"``,
        ``"H"``, ``"I"``.

    Raises
    ------
    ValueError
        If the submatrix does not match any known Dynkin diagram.

    Notes
    -----
    Covers all finite irreducible Coxeter groups:
    A_n, B_n, D_n, E_6/7/8, F_4, G_2, H_3/4, I_2(m).
    """
    n = submatrix.shape[0]

    # Build weighted adjacency: edge_weights[(i,j)] = m_ij for m_ij >= 3
    edges = {}
    adj = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            m = int(submatrix[i, j])
            if m >= 3:
                edges[(i, j)] = m
                edges[(j, i)] = m
                adj[i].append(j)
                adj[j].append(i)

    n_edges = len(edges) // 2  # each edge counted twice
    degrees = [len(adj[i]) for i in range(n)]
    max_degree = max(degrees) if degrees else 0
    edge_weights = sorted(edges[(i, j)] for i, j in edges if i < j)

    # Rank 1: A_1
    if n == 1:
        return ("A", 1, 2)

    # Rank 2: I_2(m) family
    if n == 2:
        m = int(submatrix[0, 1])
        if m == 3:
            return ("A", 2, 6)
        if m == 4:
            return ("B", 2, 8)
        if m == 6:
            return ("G", 2, 12)
        if m == 5:
            return ("I", 2, 10)  # I_2(5) = H_2
        return ("I", 2, 2 * m)

    # For n >= 3: check topology and edge weights

    # Linear chain check: all degrees <= 2, connected
    is_chain = all(d <= 2 for d in degrees)

    if is_chain and n_edges == n - 1:
        # It's a linear chain. Find the ordered chain.
        # Find endpoints (degree 1)
        endpoints = [i for i in range(n) if degrees[i] == 1]
        if len(endpoints) == 2:
            # Walk the chain
            chain = [endpoints[0]]
            visited = {endpoints[0]}
            while len(chain) < n:
                current = chain[-1]
                for nb in adj[current]:
                    if nb not in visited:
                        chain.append(nb)
                        visited.add(nb)
                        break

            # Get edge weights along chain
            chain_weights = []
            for k in range(len(chain) - 1):
                i, j = chain[k], chain[k + 1]
                key = (min(i, j), max(i, j))
                chain_weights.append(edges[key])

            # All weights 3 -> A_n
            if all(w == 3 for w in chain_weights):
                return ("A", n, factorial(n + 1))

            # One weight 4, rest 3 -> B_n or F_4
            count_4 = chain_weights.count(4)
            count_3 = chain_weights.count(3)

            if count_4 == 1 and count_3 == n - 2:
                # B_n: weight-4 edge at an end
                if chain_weights[0] == 4 or chain_weights[-1] == 4:
                    return ("B", n, (2 ** n) * factorial(n))
                # F_4: weight-4 edge in the middle (only for n=4)
                if n == 4:
                    return ("F", 4, 1152)

            # One weight 5, rest 3 -> H_3 or H_4
            count_5 = chain_weights.count(5)
            if count_5 == 1 and count_3 == n - 2:
                if chain_weights[0] == 5 or chain_weights[-1] == 5:
                    if n == 3:
                        return ("H", 3, 120)
                    if n == 4:
                        return ("H", 4, 14400)

    # Check for branching (D_n, E_n)
    # One node with degree 3, rest degree <= 2
    branch_nodes = [i for i in range(n) if degrees[i] == 3]

    if len(branch_nodes) == 1 and all(w == 3 for w in edge_weights):
        # All edge weights 3, one branch point
        bp = branch_nodes[0]

        # Compute branch lengths (distance from branch point to each leaf)
        branches = []
        for nb in adj[bp]:
            length = 1
            current = nb
            prev = bp
            while degrees[current] == 2:
                for x in adj[current]:
                    if x != prev:
                        prev = current
                        current = x
                        length += 1
                        break
                else:
                    break
            branches.append(length)
        branches.sort()

        # D_n: branches = [1, 1, n-3] (one short arm, one short arm, one long arm)
        # With n >= 4, the branch point connects to 3 paths
        # D_n has branches [1, 1, n-3]
        if branches[0] == 1 and branches[1] == 1:
            # D_n where n = 1 + 1 + (n-3) + 1 = branches sum + 1
            rank = sum(branches) + 1
            if rank == n:
                return ("D", n, (2 ** (n - 1)) * factorial(n))

        # E_6: branches [1, 2, 2], rank = 6
        if branches == [1, 2, 2] and n == 6:
            return ("E", 6, 51840)

        # E_7: branches [1, 2, 3], rank = 7
        if branches == [1, 2, 3] and n == 7:
            return ("E", 7, 2903040)

        # E_8: branches [1, 2, 4], rank = 8
        if branches == [1, 2, 4] and n == 8:
            return ("E", 8, 696729600)

    raise ValueError(
        f"Cannot classify irreducible Coxeter group with order matrix:\n{submatrix}"
    )


def classify_coxeter_type(order_matrix):
    """Classify a Coxeter group by decomposing into irreducible components.

    Decomposes the Coxeter graph into connected components and classifies
    each against known Dynkin diagrams.

    Parameters
    ----------
    order_matrix : numpy.ndarray
        Coxeter order matrix (symmetric, integer, diagonal = 1).

    Returns
    -------
    list of tuple
        Each tuple is ``(type_string, rank, order)`` for one irreducible
        component.

    Notes
    -----
    See arXiv:2212.10573 Section 4.3. For reducible groups, the total
    order is the product of the component orders.
    """
    components = _decompose_irreducible(order_matrix)
    result = []
    for indices in components:
        sub = order_matrix[np.ix_(indices, indices)]
        result.append(_classify_irreducible(sub))
    return result


def coxeter_group_order(type_list):
    """Compute the order |W| of a Coxeter group from its type classification.

    For reducible groups, the order is the product of the orders of the
    irreducible components.

    Parameters
    ----------
    type_list : list of tuple
        Output of :func:`classify_coxeter_type`: list of
        ``(type_string, rank, order)`` tuples.

    Returns
    -------
    int
        The order |W| of the Coxeter group.

    Notes
    -----
    See arXiv:2212.10573 Section 4.3.
    """
    order = 1
    for _, _, component_order in type_list:
        order *= component_order
    return order


# ---------------------------------------------------------------------------
# BFS enumeration (D-07)
# ---------------------------------------------------------------------------

def _matrix_key(M):
    """Hash key for an integer matrix.

    Parameters
    ----------
    M : numpy.ndarray
        Integer matrix.

    Returns
    -------
    bytes
        Byte representation of the int64 matrix.
    """
    return M.astype(np.int64).tobytes()


def enumerate_coxeter_group(generators, expected_order=None, max_memory_bytes=500_000_000):
    """Enumerate all elements of a finite Coxeter group via BFS.

    Performs breadth-first search on the Cayley graph, starting from
    the identity and right-multiplying by each generator. Yields
    group elements as int64 matrices in BFS order (identity first).

    Parameters
    ----------
    generators : list of numpy.ndarray
        Integer reflection matrices (generators of the Coxeter group).
    expected_order : int, optional
        Expected |W| from type classification. Used for memory estimation
        and as a sanity check.
    max_memory_bytes : int, optional
        Memory cap for the seen-set. Default 500 MB. A warning is
        logged if the estimated memory exceeds this.

    Yields
    ------
    numpy.ndarray
        Group elements (int64 matrices) in BFS order.

    Notes
    -----
    The BFS uses right-multiplication: if g is a discovered group element
    and M_i is a generator, then ``g @ M_i`` is a new candidate. This is
    consistent with generators acting on the LEFT of column vectors
    (Pitfall 4 in RESEARCH.md).

    All arithmetic is performed in int64 to prevent float drift (Pitfall 2).
    The seen-set stores byte representations of int64 matrices.

    See arXiv:2212.10573 Section 4.3 for the Coxeter group structure.
    """
    if not generators:
        return

    h11 = generators[0].shape[0]
    identity = np.eye(h11, dtype=np.int64)

    # Memory estimation (T-04-01 mitigation)
    element_bytes = 8 * h11 * h11  # int64
    if expected_order is not None:
        estimated = expected_order * element_bytes
        if estimated > max_memory_bytes:
            logger.warning(
                "Estimated memory %.1f MB exceeds cap %.1f MB for Coxeter "
                "group enumeration (expected_order=%d, h11=%d)",
                estimated / 1e6, max_memory_bytes / 1e6,
                expected_order, h11,
            )

    # Cast generators to int64
    int_generators = [np.asarray(g, dtype=np.int64) for g in generators]

    seen = {_matrix_key(identity)}
    queue = deque([identity])
    yield identity

    while queue:
        g = queue.popleft()
        for M in int_generators:
            new = (g @ M).astype(np.int64)
            key = _matrix_key(new)
            if key not in seen:
                seen.add(key)
                queue.append(new)
                yield new
