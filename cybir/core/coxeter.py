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
- ``coxeter_group_order``: :math:`|W|` from closed-form formulas per type
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
    divisor = np.asarray(divisor)
    curve = np.asarray(curve)
    h11 = len(curve)
    dot = int(curve @ divisor)
    if dot == 0:
        return np.eye(h11, dtype=np.int64)
    # M_ab = delta_ab - 2 * C_a * D_b / (C . D)
    # Use exact integer arithmetic when 2 * C_a * D_b is divisible by C . D
    numerator = 2 * np.outer(curve, divisor)
    if np.all(numerator % dot == 0):
        return np.eye(h11, dtype=np.int64) - (numerator // dot).astype(np.int64)
    # Fall back to float (may produce non-integer reflection)
    return np.eye(h11, dtype=float) - numerator.astype(float) / dot


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
        if m <= 1:
            raise ValueError(
                f"Invalid Coxeter order matrix entry m_12={m} (must be >= 2)"
            )
        if m == 2:
            raise ValueError(
                "Rank-2 submatrix with m_12=2 is reducible (A_1 x A_1). "
                "It should have been decomposed before classification."
            )
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
    """Compute the order :math:`|W|` of a Coxeter group from its type classification.

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
        The order :math:`|W|` of the Coxeter group.

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


def _edges_snapshot(graph):
    """Snapshot all edges in the graph as (label_a, label_b, edge_data) triples.

    Parameters
    ----------
    graph : CYGraph
        The phase graph.

    Returns
    -------
    list of tuple
        Each tuple is (label_a, label_b, edge_data_dict).
    """
    return graph.edges(data=True)


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
        Expected :math:`|W|` from type classification. Used for memory estimation
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


# ---------------------------------------------------------------------------
# Phase reflection (D-08, D-09)
# ---------------------------------------------------------------------------

def reflect_phase_data(phase, g, label=None):
    r"""Apply a Coxeter group element to a CalabiYauLite phase.

    Transforms intersection numbers, second Chern class, and cones
    according to the index conventions in D-08/D-09:

    - :math:`\kappa'_{xyz} = g_{xa}\, g_{yb}\, g_{zc}\, \kappa_{abc}`
      (g acts on Mori-space indices)
    - :math:`c'_2 = g \cdot c_2`
    - Kahler cone rays: ``old_rays @ inv(g)`` (row-vector convention)
    - Mori cone: dual of the new Kahler cone

    For individual reflections ``g^{-1} = g``, but for products
    ``g^{-1} \neq g`` in general (D-09).

    Parameters
    ----------
    phase : CalabiYauLite
        Phase to reflect.
    g : numpy.ndarray
        Integer group element matrix of shape ``(h11, h11)``.
    label : str, optional
        Label for the new phase.

    Returns
    -------
    CalabiYauLite
        New phase with transformed data.

    Raises
    ------
    AssertionError
        If ``inv(g)`` is not an integer matrix (T-04-04 mitigation).

    Notes
    -----
    See arXiv:2212.10573 Section 4.3 and D-08, D-09 in CONTEXT.md.
    """
    from .types import CalabiYauLite as CYL

    g = np.asarray(g, dtype=np.int64)

    # Compute g^{-1} and verify integrality (T-04-04)
    g_inv_float = np.linalg.inv(g.astype(float))
    g_inv_int = np.round(g_inv_float).astype(int)
    assert np.allclose(g_inv_float, g_inv_int), (
        f"inv(g) is not an integer matrix:\n{g_inv_float}"
    )

    # Transform intersection numbers: kappa'_xyz = g_xa g_yb g_zc kappa_abc
    g_float = g.astype(float)
    new_kappa = np.einsum("abc,xa,yb,zc", phase.int_nums, g_float, g_float, g_float)
    new_kappa = np.round(new_kappa).astype(int)

    # Transform c2
    new_c2 = None
    if phase.c2 is not None:
        new_c2 = (g @ phase.c2.astype(int)).astype(int)

    # Transform Kahler cone: rays @ inv(g) (D-08)
    new_kc = None
    new_mori = None
    if phase.kahler_cone is not None:
        import cytools
        old_rays = phase.kahler_cone.rays()
        new_rays = (old_rays @ g_inv_int)
        new_kc = cytools.Cone(rays=new_rays)
        new_mori = new_kc.dual()

    return CYL(
        int_nums=new_kappa,
        c2=new_c2,
        kahler_cone=new_kc,
        mori_cone=new_mori,
        label=label,
    )


# ---------------------------------------------------------------------------
# Orbit expansion (D-10 through D-14)
# ---------------------------------------------------------------------------

def apply_coxeter_orbit(ekc, reflections='ekc', phases=True):
    r"""Expand the fundamental domain via Coxeter group orbit.

    Enumerates the full Coxeter group from the selected reflection set
    and applies every non-identity group element to every fundamental-
    domain phase and edge, producing the extended/hyperextended Kahler cone.

    Parameters
    ----------
    ekc : CYBirationalClass
        Must have ``construct_phases`` completed. Modified in place.
    reflections : str or iterable, optional
        Which reflections to use for orbit expansion:

        - ``'ekc'`` (default): symmetric flop reflections only (produces EKC)
        - ``'hekc'``: sym flop + SU2_NONGENERIC_CS (produces HEKC)
        - ``'all'``: all Coxeter reflections (full group)
        - Custom iterable of reflection matrices
    phases : bool, optional
        If ``True`` (default), create full reflected phase objects and
        graph edges. If ``False``, only accumulate cone generators
        (faster, less memory). See D-13.

    Notes
    -----
    The algorithm (per D-10 through D-14):

    1. Select reflection set based on ``reflections`` parameter (D-04)
    2. Check finite type via positive definiteness (D-06)
    3. Classify and compute expected order (D-05)
    4. Memory estimation (D-07)
    5. Streaming BFS: for each group element g (skip identity):
       - Reflect each fundamental phase (phases=True only)
       - Accumulate Kahler rays, terminal wall curves, zero-vol divisors
       - Reflect each fundamental edge (D-12)

    No deduplication of reflected phases (D-11).

    See arXiv:2212.10573 Section 4.3.
    """
    from .types import CalabiYauLite, ContractionType, CoxeterGroup, ExtremalContraction

    # Resolve reflection set (D-04)
    if isinstance(reflections, str):
        reflections_mode = reflections
        if reflections == 'ekc':
            # Symmetric flop reflections only -> EKC
            ref_pairs = list(ekc._sym_flop_pairs)
            reflection_matrices = [np.array(r) for r, _ in ref_pairs]
        elif reflections == 'hekc':
            # Sym flop + SU2_NONGENERIC_CS -> HEKC
            ref_pairs = list(ekc._sym_flop_pairs)
            sym_flop_ref_keys = set(r for r, _ in ref_pairs)
            for r, c in getattr(ekc, '_nongeneric_cs_pairs', []):
                if r not in sym_flop_ref_keys:
                    ref_pairs.append((r, c))
            reflection_matrices = [np.array(r) for r, _ in ref_pairs]
        elif reflections == 'all':
            # All Coxeter reflections (sym flop + nongeneric CS + genuine su(2))
            all_pairs = list(ekc._sym_flop_pairs) + list(getattr(ekc, '_nongeneric_cs_pairs', []))
            all_pairs += list(getattr(ekc, '_su2_pairs', []))
            ref_keys_seen = set()
            ref_pairs = []
            for r, c in all_pairs:
                if r not in ref_keys_seen:
                    ref_keys_seen.add(r)
                    ref_pairs.append((r, c))
            reflection_matrices = [np.array(r) for r, _ in ref_pairs]
        else:
            raise ValueError(f"Unknown reflections mode: {reflections!r}. "
                             f"Use 'ekc', 'hekc', 'all', or a list of matrices.")
    elif hasattr(reflections, '__iter__'):
        reflections_mode = 'custom'
        reflection_matrices = [np.asarray(r, dtype=np.int64) for r in reflections]
        ref_pairs = None
    else:
        raise TypeError(f"reflections must be str or iterable, got {type(reflections)}")

    if not reflection_matrices:
        logger.info("No symmetric-flop reflections; skipping orbit expansion")
        return

    # Compute order matrix and check finiteness (D-06)
    order_mat = coxeter_order_matrix(reflection_matrices)
    if not is_finite_type(order_mat):
        logger.warning(
            "Infinite-type Coxeter group detected; skipping orbit expansion. "
            "Only the fundamental domain is available."
        )
        return

    # Classify and compute expected order (D-05)
    type_list = classify_coxeter_type(order_mat)
    expected_order = coxeter_group_order(type_list)

    # Large group warning (T-06-04)
    if expected_order > 1000:
        logger.warning(
            "Large Coxeter group |W|=%d detected for reflections=%r. "
            "Consider using phases=False for faster execution.",
            expected_order,
            reflections_mode,
        )

    # Build and store CoxeterGroup dataclass
    coxeter_group = CoxeterGroup(
        factors=tuple(type_list),
        order_matrix=order_mat,
        reflections=tuple(np.array(r) for r in reflection_matrices),
    )
    ekc._coxeter_group = coxeter_group
    # Keep backward compat
    ekc._coxeter_type_info = type_list
    ekc._coxeter_order = expected_order

    # Memory estimation (D-07, T-04-05)
    h11 = reflection_matrices[0].shape[0]
    mem_estimate = expected_order * 8 * h11 * h11
    if mem_estimate > 500_000_000:
        logger.warning(
            "Estimated memory %.1f MB for Coxeter group enumeration "
            "(|W|=%d, h11=%d)",
            mem_estimate / 1e6, expected_order, h11,
        )

    # Snapshot fundamental-domain phases, edges, and cone generators.
    # We snapshot cone generators here because the edge data stores
    # normalized curves (first nonzero positive) which may differ in
    # sign from the raw curves stored in _infinity_cone_gens by the
    # BFS accumulator.  Reflecting the stored generators directly
    # preserves the correct sign convention.
    fund_phases = list(ekc._graph.phases)
    fund_edges = _edges_snapshot(ekc._graph)
    fund_inf_gens = set(ekc._infinity_cone_gens)
    fund_eff_zvds = set(ekc._eff_cone_gens)  # includes both zvds and Kahler rays
    phase_counter = ekc._graph.num_phases

    # Build label mapping: fundamental label -> list of (g, new_label)
    # for connecting reflected flop edges
    label_map = {}  # (g_key, fund_label) -> new_label

    for g in enumerate_coxeter_group(reflection_matrices, expected_order):
        g = g.astype(np.int64)
        if np.array_equal(g, np.eye(h11, dtype=np.int64)):
            continue  # skip identity

        g_inv_float = np.linalg.inv(g.astype(float))
        g_inv_int = np.round(g_inv_float).astype(np.int64)
        if not np.allclose(g_inv_float, g_inv_int, atol=1e-6):
            raise ValueError(
                f"Group element inverse is not integer: max deviation "
                f"{np.max(np.abs(g_inv_float - g_inv_int)):.2e}"
            )
        g_key = _matrix_key(g)

        for fund_phase in fund_phases:
            if phases:
                # Create reflected phase via reflect_phase_data
                new_label = f"CY_{phase_counter}"
                new_phase = reflect_phase_data(fund_phase, g, label=new_label)

                # Compute curve_signs for reflected phase (SC-4 gap fix)
                # tip in Kahler space transforms as g_inv^T @ fund_tip (D-08)
                if fund_phase.tip is not None:
                    reflected_tip = g_inv_int.T.astype(float) @ fund_phase.tip.astype(float)
                    new_phase._tip = reflected_tip

                    # Use root phase's curve_signs keys as canonical curve set
                    root_phase = ekc._graph.get_phase(ekc._root_label)
                    if root_phase.curve_signs is not None:
                        new_phase._curve_signs = {
                            c: int(np.sign(reflected_tip @ np.array(c)))
                            for c in root_phase.curve_signs
                        }

                ekc._graph.add_phase(new_phase)
                ekc._weyl_phases.append(new_label)
                label_map[(g_key, fund_phase.label)] = new_label
                phase_counter += 1

            # Accumulate eff_cone_gens: reflected Kahler rays (D-14)
            if fund_phase.kahler_cone is not None:
                for ray in fund_phase.kahler_cone.rays():
                    reflected_ray = (ray @ g_inv_int)
                    ekc._eff_cone_gens.add(
                        tuple(int(x) for x in reflected_ray)
                    )

        # Reflect fundamental edges
        for u, v, data in fund_edges:
            contr = data["contraction"]
            ctype = contr.contraction_type

            # Reflected contraction curve: g @ (sign * curve)
            curve = np.asarray(contr.contraction_curve, dtype=int)
            reflected_curve = (g @ curve).astype(int)

            if phases:
                # Build reflected ExtremalContraction
                reflected_zvd = None
                if contr.zero_vol_divisor is not None:
                    reflected_zvd = (g_inv_int.T @ np.asarray(contr.zero_vol_divisor, dtype=int)).astype(int)

                reflected_contr = ExtremalContraction(
                    contraction_curve=reflected_curve,
                    contraction_type=ctype,
                    gv_invariant=contr.gv_invariant,
                    gv_series=contr.gv_series,
                    zero_vol_divisor=reflected_zvd,
                )

                if ctype == ContractionType.FLOP and u != v:
                    # Flop between two different phases: connect g(A) to g(B) (D-12)
                    new_u = label_map.get((g_key, u))
                    new_v = label_map.get((g_key, v))
                    if new_u is not None and new_v is not None:
                        ekc._graph.add_contraction(
                            reflected_contr, new_u, new_v,
                            curve_sign_a=data.get("curve_sign_a", 1),
                            curve_sign_b=data.get("curve_sign_b", -1),
                        )
                else:
                    # Terminal wall or self-loop: self-loop on reflected phase
                    # For self-loops (u == v), map to g(u)
                    fund_label = u
                    new_label = label_map.get((g_key, fund_label))
                    if new_label is not None:
                        ekc._graph.add_contraction(
                            reflected_contr, new_label, new_label,
                            curve_sign_a=data.get("curve_sign_a", 1),
                            curve_sign_b=data.get("curve_sign_b", -1),
                        )

        # Accumulate reflected cone generators from fundamental-domain
        # snapshots (not edge data, which uses normalized curve signs).
        # Curves (N-lattice) transform as g @; divisors (M-lattice) as g^{-T} @.
        for gen in fund_inf_gens:
            reflected = (g @ np.asarray(gen, dtype=int)).astype(int)
            ekc._infinity_cone_gens.add(tuple(int(x) for x in reflected))

        for gen in fund_eff_zvds:
            reflected = (g_inv_int.T @ np.asarray(gen, dtype=int)).astype(int)
            ekc._eff_cone_gens.add(tuple(int(x) for x in reflected))

    logger.info(
        "Coxeter orbit expansion (%s): %d total phases (from %d fundamental), "
        "|W| = %d, type = %s",
        reflections_mode,
        ekc._graph.num_phases,
        len(fund_phases),
        expected_order,
        repr(coxeter_group),
    )


# ---------------------------------------------------------------------------
# Chamber walk: to_fundamental_domain (D-18)
# ---------------------------------------------------------------------------

def to_fundamental_domain(point, reflections, curves, max_iter=1000):
    r"""Map a point to the fundamental domain via chamber walk.

    Repeatedly scans the wall-defining curves; if ``point @ curve < 0``
    for any curve, reflects the point through that wall (and accumulates
    the group element). Stops when the point has non-negative pairing
    with all curves.

    Parameters
    ----------
    point : array_like
        Point in Mori space.
    reflections : list of numpy.ndarray
        Symmetric-flop reflection matrices, one per wall.
    curves : list of array_like
        Contraction curves defining the walls (same order as *reflections*).
    max_iter : int, optional
        Maximum number of reflections before raising. Default 1000.

    Returns
    -------
    (numpy.ndarray, numpy.ndarray)
        ``(fundamental_domain_point, group_element)`` where the group
        element *g* satisfies ``g @ fundamental_domain_point == original_point``.

    Raises
    ------
    RuntimeError
        If *max_iter* is exceeded (safety bound, T-04-07 mitigation).

    Notes
    -----
    See arXiv:2212.10573 Section 4.3 for the chamber walk algorithm.
    The fundamental domain is the region where ``point @ curve >= 0``
    for all symmetric-flop contraction curves.
    """
    point = np.asarray(point, dtype=float).copy()
    n = point.shape[0]
    g = np.eye(n, dtype=np.int64)
    curves_arr = [np.asarray(c, dtype=float) for c in curves]
    reflections_int = [np.asarray(r, dtype=np.int64) for r in reflections]

    for iters in range(1, max_iter + 1):
        reflected = False
        for i, c in enumerate(curves_arr):
            if point @ c < 0:
                M = reflections_int[i]
                # Track: original = g @ point at all times.
                # After reflecting: new_point = M @ point
                # original = g @ point = g @ M^{-1} @ new_point
                # For generators M^{-1} = M, so new_g = g @ M
                g = (g @ M).astype(np.int64)
                point = (M.astype(float) @ point)
                reflected = True
                break  # restart scan
        if not reflected:
            return point, g
    raise RuntimeError(
        f"to_fundamental_domain exceeded max_iter={max_iter}"
    )


# ---------------------------------------------------------------------------
# On-demand GV reconstruction (D-17)
# ---------------------------------------------------------------------------

def _invariants_for_impl(ekc, phase_label):
    """Reconstruct GV invariants for a phase on demand.

    Compares the phase's ``curve_signs`` to the root phase's
    ``curve_signs``. Curves where the signs differ are flopped
    via ``root_invariants.flop_gvs``.

    Parameters
    ----------
    ekc : CYBirationalClass
        Must have ``construct_phases`` completed.
    phase_label : str
        Label of the target phase.

    Returns
    -------
    Invariants
        CYTools Invariants object with flop curves reoriented for
        this phase.

    Notes
    -----
    Per D-17: compare ``phase.curve_signs`` to ``root.curve_signs``,
    collect curves where signs differ, return
    ``root_invariants.flop_gvs(those_curves)``.

    See arXiv:2212.10573 Section 4.3.
    """
    root_invariants = ekc._root_invariants
    root_phase = ekc._graph.get_phase(ekc._root_label)
    target_phase = ekc._graph.get_phase(phase_label)

    root_signs = root_phase.curve_signs
    target_signs = target_phase.curve_signs

    # If same phase or no curve_signs data, return root invariants
    if root_signs is None or target_signs is None:
        if target_signs is None and phase_label in getattr(ekc, "_weyl_phases", []):
            logger.warning(
                "invariants_for: phase %s is Weyl-expanded but has no "
                "curve_signs; returning root invariants (may be incorrect)",
                phase_label,
            )
        return root_invariants
    if phase_label == ekc._root_label:
        return root_invariants

    # Find curves where signs differ
    flop_curves = []
    for curve_tuple, root_sign in root_signs.items():
        target_sign = target_signs.get(curve_tuple, root_sign)
        if target_sign != root_sign:
            flop_curves.append(np.array(curve_tuple))

    if not flop_curves:
        return root_invariants

    # Flop the differing curves via CYTools Invariants API
    return root_invariants.flop_gvs(flop_curves)
