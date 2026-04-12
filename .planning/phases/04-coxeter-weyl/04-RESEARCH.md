# Phase 4: Coxeter Group & Weyl Expansion - Research

**Researched:** 2026-04-12
**Domain:** Coxeter group construction, finite-type classification, streaming BFS enumeration, Weyl orbit expansion with correct index conventions
**Confidence:** HIGH

## Summary

This phase replaces the existing `weyl.py` with a unified `coxeter.py` module that handles Coxeter group construction (order matrix computation, finite-type classification, memory-safe enumeration) and orbit expansion acting on all phase data with correct index conventions. The phase also adds `apply_coxeter_orbit`, `invariants_for`, and `to_fundamental_domain` methods to `CYBirationalClass`.

The existing `weyl.py` applies each reflection to each fundamental-domain phase independently and deduplicates by Mori cone. The new design uses proper group enumeration via BFS on the Cayley graph -- each group element acts on ALL fundamental-domain phases, producing a unique reflected phase per (group element, fundamental phase) pair with no deduplication needed (D-11). This is mathematically correct: the Coxeter group acts freely on chambers.

The critical index convention: reflection matrices act on Mori-space (lowered-index) objects. For a general group element g (product of reflections), the Kahler-space action is (g^{-1})^T, and g^{-1} must be computed properly since g^{-1} = M_k ... M_2 M_1 != g for products (even though M_i^{-1} = M_i for individual reflections).

**Primary recommendation:** Implement `coxeter.py` as a single module with three layers: (1) Coxeter matrix and finite-type classification from reflection matrices, (2) streaming BFS group enumeration on the Cayley graph, (3) orbit expansion that creates reflected phases and accumulates generators on the fly.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Delete `weyl.py`. Create `coxeter.py` that combines Coxeter group construction and orbit expansion in one module.
- **D-02:** Move `coxeter_reflection`, `coxeter_matrix` (the order-matrix version), and `matrix_period` from `util.py` into `coxeter.py`. Keep other util functions in place.
- **D-03:** Only symmetric-flop Coxeter matrices are used as generators. su(2) enhancement reflections are excluded.
- **D-04:** Compute the Coxeter order matrix m_ij = order(M_i M_j) from the concrete reflection matrices using `matrix_period`.
- **D-05:** Implement full finite-type classification from the Coxeter order matrix (A_n, B_n, D_n, E_6/7/8, F_4, G_2, H_3/4, I_2(m)). Compute |W| from closed-form formulas per type.
- **D-06:** Finite type detection via positive definiteness of the bilinear form B_ij = -cos(pi/m_ij). Infinite type -> stop and report fundamental domain only.
- **D-07:** Memory estimation before enumeration: |W| x 8 x h11^2 bytes for the seen-set. Warn if estimate exceeds ~500MB. Streaming BFS.
- **D-08:** The reflection matrices act on Mori-space objects (lowered indices). Explicit rules for kappa, c2, Mori rays, Kahler rays, zero-vol divisors.
- **D-09:** For individual reflections M^2 = I so M^{-1} = M, but for products g = M_1 M_2 ... M_k, g^{-1} = M_k ... M_2 M_1 != g in general.
- **D-10:** The method is called `apply_coxeter_orbit` (not `expand_weyl`).
- **D-11:** No deduplication of reflected phases -- if group enumeration is correct, each (group element, fundamental phase) pair is unique.
- **D-12:** Full graph is the Coxeter group orbit of the fundamental domain graph. All flop edges reflected. Terminal walls become self-loops.
- **D-13:** Support `phases=False` mode for cone-generator-only computation.
- **D-14:** After orbit expansion, all cone generators include contributions from ALL phases.
- **D-15:** Don't store separate Invariants per phase. On-demand reconstruction via `ekc.invariants_for(phase_label)`.
- **D-16:** Implement `to_fundamental_domain(point)` -- chamber walk by reflecting through negatively-pairing walls.

### Claude's Discretion
- Internal BFS data structures (queue, seen-set representation)
- Hashing strategy for integer matrices in the seen-set
- How to decompose the Coxeter order matrix into irreducible components for type classification
- Test strategy for the Coxeter group enumeration (small known groups as fixtures)
- Whether `to_fundamental_domain` returns just the mapped point or also the group element

### Deferred Ideas (OUT OF SCOPE)
- Toric pipeline (`from_toric`, `build_toric.py`) -- v2
- Infinite Coxeter group handling beyond "bail and report" -- future work
- Serialization/caching of full birational class results (ENH-01)
- Per-phase GV Invariants as stored objects
</user_constraints>

## Project Constraints (from CLAUDE.md)

- Use `cytools` conda environment (Python 3.12); do not install packages from scratch
- Mathematical correctness: algorithms must be bit-for-bit equivalent to original
- Follow dbrane-tools documentation patterns with Sphinx
- Use numpy, scipy, hsnf, sympy, python-flint as core deps (all in env)
- Use ruff for linting, pytest for testing
- No pydantic -- use dataclasses/NamedTuple for structured data
- No pandas, SageMath, poetry, setuptools

## Standard Stack

### Core (already in environment)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | 2.3.5 | Matrix arithmetic, einsum, linalg | All reflection/transformation operations | [VERIFIED: codebase and CLAUDE.md] |
| scipy | 1.17.0 | `ConvexHull` if needed for cone ops | Fallback for cone geometry | [VERIFIED: CLAUDE.md] |
| networkx | (in env) | CYGraph backend | Already used for phase graph | [VERIFIED: graph.py imports nx] |
| cytools | (local) | Cone operations, dual(), rays(), tip_of_stretched_cone | Required for Kahler/Mori cone manipulation | [VERIFIED: build_gv.py] |

### No New Dependencies Needed

This phase is pure numpy linear algebra + the existing cytools Cone API. No new packages required.

## Architecture Patterns

### Module Structure After Phase 4

```
cybir/core/
  coxeter.py       # NEW: replaces weyl.py
  ekc.py           # MODIFIED: new methods
  util.py          # MODIFIED: 3 functions removed
  build_gv.py      # UNCHANGED
  types.py         # UNCHANGED
  graph.py         # UNCHANGED
  classify.py      # UNCHANGED
  flop.py          # UNCHANGED
  gv.py            # UNCHANGED
  patch.py         # UNCHANGED
```

### coxeter.py Internal Structure

```python
# --- Low-level matrix utilities (moved from util.py) ---
def matrix_period(M, max_iter=200): ...
def coxeter_reflection(divisor, curve): ...

# --- Coxeter order matrix ---
def coxeter_order_matrix(reflections): ...  # m_ij = order(M_i M_j), diagonal = 1

# --- Finite type classification ---
def coxeter_bilinear_form(order_matrix): ...  # B_ij = -cos(pi/m_ij)
def is_finite_type(order_matrix): ...         # positive definiteness check
def classify_coxeter_type(order_matrix): ...  # returns list of (type_str, rank)
def coxeter_group_order(type_list): ...       # |W| from type classification

# --- Streaming BFS group enumeration ---
def enumerate_coxeter_group(generators): ...  # yields group elements via BFS

# --- Phase reflection ---
def reflect_phase_data(phase, g): ...         # apply g to int_nums, c2, cones
def reflect_phase_data_kahler(phase, g): ...  # (g^{-1})^T action for Kahler objects

# --- Orbit expansion (top-level API) ---
def apply_coxeter_orbit(ekc, phases=True): ...

# --- Fundamental domain mapping ---
def to_fundamental_domain(point, reflections, ...): ...

# --- On-demand GV reconstruction ---
# (helper for ekc.invariants_for)
```

### Pattern 1: Streaming BFS on the Cayley Graph

**What:** Enumerate all elements of a finite Coxeter group by BFS on the Cayley graph, starting from the identity and multiplying by each generator. The seen-set uses hashed integer matrices. As each new element is discovered, immediately apply it to all fundamental-domain phases (streaming -- don't accumulate the full group first).

**When to use:** Always, for Weyl orbit expansion.

**Example:**
```python
# Source: algorithm design from D-07, D-11
from collections import deque

def _matrix_key(M):
    """Hash key for an integer matrix -- bytes of the int array."""
    return M.astype(np.int64).tobytes()

def enumerate_coxeter_group(generators, expected_order=None, max_memory_bytes=500_000_000):
    """Yield group elements via BFS on Cayley graph.
    
    Parameters
    ----------
    generators : list of ndarray
        Integer reflection matrices (generators of the Coxeter group).
    expected_order : int, optional
        Expected |W| from type classification (for early termination check).
    max_memory_bytes : int
        Memory cap for seen-set. Default 500MB.
    
    Yields
    ------
    ndarray
        Group elements in BFS order (identity first).
    """
    h11 = generators[0].shape[0]
    identity = np.eye(h11, dtype=np.int64)
    
    # Memory check
    element_bytes = 8 * h11 * h11  # int64
    if expected_order is not None:
        estimated = expected_order * element_bytes
        if estimated > max_memory_bytes:
            logger.warning(
                "Estimated memory %.1f MB exceeds cap %.1f MB",
                estimated / 1e6, max_memory_bytes / 1e6,
            )
    
    seen = {_matrix_key(identity)}
    queue = deque([identity])
    yield identity
    
    while queue:
        g = queue.popleft()
        for M in generators:
            new = (g @ M).astype(np.int64)  # right-multiply by generator
            key = _matrix_key(new)
            if key not in seen:
                seen.add(key)
                queue.append(new)
                yield new
```

### Pattern 2: Finite Type Classification via Connected Components

**What:** Decompose the Coxeter order matrix into irreducible components by treating generators as nodes in a graph, connecting i-j when m_ij >= 3 (i.e., the generators don't commute). Each connected component is classified independently against the known Dynkin diagram shapes.

**When to use:** After computing the order matrix, before enumeration.

**Example:**
```python
# Source: standard Coxeter group theory [CITED: en.wikipedia.org/wiki/Coxeter_group]
def _decompose_irreducible(order_matrix):
    """Find connected components of the Coxeter graph.
    
    Nodes = generator indices, edges where m_ij >= 3.
    Returns list of index-sets, one per irreducible component.
    """
    n = order_matrix.shape[0]
    # Build adjacency
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
```

### Pattern 3: Index Convention Implementation

**What:** Reflection matrices M act natively on Mori space (lowered indices). For Kahler space objects, the action is (g^{-1})^T. For individual reflections M^T = M (symmetric) and M^{-1} = M (involution), so M acts on Kahler too. But for products g = M_1 M_2 ... M_k, g^{-1} = M_k ... M_2 M_1 (reverse order), and (g^{-1})^T != g.

**Critical detail:** The `_reflect_phase` in the current `weyl.py` uses `M` for everything, which is ONLY correct for single reflections. For general group elements (products), the Kahler cone transformation must use `np.linalg.inv(g)` or explicitly compute the reverse product.

**Example:**
```python
# Source: D-08, D-09
def reflect_phase_data(phase, g):
    """Apply group element g to phase data.
    
    g acts on Mori-space objects (lowered indices):
    - kappa: einsum('abc,xa,yb,zc', kappa, g, g, g)
    - c2: g @ c2
    - Mori rays: g @ ray
    
    For Kahler rays: ray @ inv(g), equivalently (g^{-T}) @ ray
    """
    g_int = np.round(g).astype(int)
    g_inv = np.linalg.inv(g)  # exact for integer matrices
    g_inv_int = np.round(g_inv).astype(int)
    
    new_kappa = np.einsum('abc,xa,yb,zc', phase.int_nums, g, g, g)
    new_c2 = g @ phase.c2
    
    # Kahler cone: rays transform by (g^{-1})^T, 
    # i.e. new_ray = old_ray @ g_inv (row vectors)
    import cytools
    new_kc = cytools.Cone(rays=phase.kahler_cone.rays() @ g_inv_int)
    new_mori = new_kc.dual()
    
    return new_kappa, new_c2, new_kc, new_mori
```

### Pattern 4: Chamber Walk for `to_fundamental_domain`

**What:** Given a point in Kahler (or Mori) space, walk it back to the fundamental domain by checking which symmetric-flop contraction curves pair negatively with the point, and reflecting through those walls. Repeat until no wall pairs negatively.

**Example:**
```python
# Source: D-16, standard Coxeter group theory
def to_fundamental_domain(point, reflections, curves, max_iter=1000):
    """Walk a point to the fundamental domain.
    
    Parameters
    ----------
    point : ndarray
        Point in Mori space.
    reflections : list of ndarray
        Symmetric-flop reflection matrices.
    curves : list of ndarray  
        Contraction curves defining the walls (same order as reflections).
    max_iter : int
        Safety bound on iterations.
    
    Returns
    -------
    (ndarray, ndarray)
        (mapped_point, group_element) where group_element maps the
        fundamental domain point to the input point.
    """
    current = point.copy()
    g = np.eye(len(point), dtype=int)  # accumulated group element
    
    for _ in range(max_iter):
        reflected = False
        for M, curve in zip(reflections, curves):
            if current @ curve < 0:  # point pairs negatively with wall
                current = M @ current
                g = M @ g
                reflected = True
                break  # restart scan after reflection
        if not reflected:
            return current, g
    
    raise RuntimeError("Chamber walk did not converge")
```

### Anti-Patterns to Avoid

- **Anti-pattern: Computing g^{-1} as g for products.** Individual reflections are involutions (M^{-1} = M), but products of reflections are NOT. Always use `np.linalg.inv(g)` for general group elements.
- **Anti-pattern: Deduplicating reflected phases by Mori cone.** The current `weyl.py` does this with `_is_new_phase`. With correct BFS enumeration, every (g, fundamental_phase) pair produces a unique phase (D-11). Deduplication is a symptom of incorrect enumeration.
- **Anti-pattern: Applying single reflections to phases instead of group elements.** The current code applies each M in `sym_flop_refs` to each fundamental phase. This only generates images under generators, not the full group orbit. BFS on the Cayley graph generates ALL group elements.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Positive definiteness check | Manual eigenvalue analysis | `np.linalg.eigvalsh(B)` and check all > 0 | Numerically stable, handles edge cases |
| Matrix inverse | Manual Gauss elimination | `np.linalg.inv(g)` | Exact for integer matrices at the dimensions we encounter (h11 < ~20) |
| Connected components | Custom graph traversal | `scipy.sparse.csgraph.connected_components` or simple DFS | Standard algorithm, but DFS is fine for n < 20 generators |
| Cone dualization | Manual halfspace computation | `cytools.Cone(rays=...).dual()` | CYTools handles all the PPL/CGAL backend |

## Common Pitfalls

### Pitfall 1: Forgetting g^{-1} != g for Products
**What goes wrong:** Kahler cone rays get transformed incorrectly, leading to wrong phase cones.
**Why it happens:** Each reflection M satisfies M^{-1} = M (involution), so during testing with single reflections, using g directly works. The bug only appears with multi-generator products.
**How to avoid:** Always compute `np.linalg.inv(g)` for Kahler transformations. Add a test with a product of two non-commuting reflections that verifies the Kahler cone is correct.
**Warning signs:** Kahler cone rays that don't lie in the expected half-spaces.

### Pitfall 2: Float Drift in Integer Matrix BFS
**What goes wrong:** After many matrix multiplications, float drift causes the seen-set to treat the same group element as distinct, leading to infinite enumeration.
**Why it happens:** numpy float64 accumulates rounding errors.
**How to avoid:** Round to integer and cast to `int64` at every multiplication step. The reflection matrices are exact integers, and all products of integer matrices are integer matrices. Assert integrality.
**Warning signs:** BFS discovering more elements than expected |W|.

### Pitfall 3: Coxeter Order Matrix vs Coxeter Element
**What goes wrong:** The existing `coxeter_matrix` function in `util.py` computes the Coxeter ELEMENT (product M_1 M_2 ... M_n), not the Coxeter order matrix.
**Why it happens:** Naming confusion -- both are called "Coxeter matrix" in different contexts.
**How to avoid:** D-02 renames clearly. The order matrix function should be called `coxeter_order_matrix` and the element function (if kept) should be `coxeter_element`. The current `coxeter_matrix` in util.py should either be renamed or removed since the order matrix is what's actually needed.

### Pitfall 4: Right vs Left Multiplication in BFS
**What goes wrong:** BFS generates elements by multiplying g * M_i (right multiplication). The Cayley graph convention must be consistent: if generators act on the LEFT of Mori vectors (g @ v), then BFS should right-multiply (g @ M_i) to get new elements, so that (g @ M_i) @ v = g @ (M_i @ v).
**Why it happens:** Convention ambiguity in group theory.
**How to avoid:** Be explicit: we represent group elements as matrices that left-multiply column vectors. BFS extends by right-multiplying generators. Document this clearly.

### Pitfall 5: `to_fundamental_domain` Infinite Loop
**What goes wrong:** If the Coxeter group is infinite (not detected), the chamber walk loops forever.
**Why it happens:** Infinite-type Coxeter groups have infinitely many chambers.
**How to avoid:** D-06 requires finite-type detection BEFORE enumeration. `to_fundamental_domain` should only be called when finite type is confirmed. Add a max_iter safety bound regardless.

### Pitfall 6: Generator Accumulation After Reflection
**What goes wrong:** Reflected phases' Kahler cone rays and terminal wall curves are not added to eff_cone_gens and infinity_cone_gens.
**Why it happens:** The original code (lines 1038-1070) accumulates generators from ALL phases after the Weyl loop. The current `weyl.py` does NOT do this.
**How to avoid:** D-14 explicitly requires this. In the streaming BFS, accumulate generators as each reflected phase is created:
- Reflected Kahler cone rays -> eff_cone_gens
- Reflected terminal wall curves (asymptotic, CFT) -> infinity_cone_gens
- Reflected zero-vol divisors (CFT, su(2)) -> eff_cone_gens

## Finite Coxeter Group Type Classification

### Algorithm [CITED: en.wikipedia.org/wiki/Coxeter_group]

1. **Compute order matrix** m_ij = order(M_i @ M_j). Diagonal entries are 1 (M_i^2 = I for reflections).
2. **Check finite type:** Compute bilinear form B_ij = -cos(pi/m_ij). If B is positive definite (all eigenvalues > 0), the group is finite.
3. **Decompose into irreducibles:** Build graph with edge i-j when m_ij >= 3. Find connected components.
4. **Classify each component:** Match the submatrix of m against known Dynkin diagram patterns:

### Type Identification Rules [ASSUMED]

For an irreducible component of rank n (n generators), examine the edge weights (m_ij values) and graph topology:

| Type | Rank | Graph Shape | Edge Weights | |W| |
|------|------|-------------|--------------|-----|
| A_n | n >= 1 | Linear chain | All edges = 3 | (n+1)! |
| B_n | n >= 2 | Linear chain | One end edge = 4, rest = 3 | 2^n * n! |
| D_n | n >= 4 | Fork (one branch of length 1 at one end) | All edges = 3 | 2^{n-1} * n! |
| E_6 | 6 | T-shaped (branch at node 3 from one end) | All edges = 3 | 51,840 |
| E_7 | 7 | T-shaped (branch at node 3 from one end) | All edges = 3 | 2,903,040 |
| E_8 | 8 | T-shaped (branch at node 3 from one end) | All edges = 3 | 696,729,600 |
| F_4 | 4 | Linear chain | Middle edge = 4 | 1,152 |
| G_2 | 2 | Single edge | m = 6 | 12 |
| H_3 | 3 | Linear chain | One end edge = 5 | 120 |
| H_4 | 4 | Linear chain | One end edge = 5, rest = 3 | 14,400 |
| I_2(m) | 2 | Single edge | m >= 5 (not 6) | 2m |

For reducible groups: |W| = product of |W_i| for each irreducible component.

### Classification Algorithm Sketch

```python
def _classify_irreducible(submatrix):
    """Classify an irreducible Coxeter order matrix.
    
    Returns (type_string, rank, order) or None if unrecognized.
    """
    n = submatrix.shape[0]
    
    # Build weighted edge list
    edges = {}
    for i in range(n):
        for j in range(i+1, n):
            if submatrix[i, j] >= 3:
                edges[(i, j)] = submatrix[i, j]
    
    # Rank 1: trivial group
    if n == 1:
        return ("A", 1, 2)
    
    # Rank 2: I_2(m)
    if n == 2:
        m = submatrix[0, 1]
        if m == 3: return ("A", 2, 6)
        if m == 4: return ("B", 2, 8)
        if m == 6: return ("G", 2, 12)
        return ("I", 2, 2 * m)
    
    # Build adjacency and check topology
    # ... pattern matching against known Dynkin diagrams
    # Key: check degree sequence, edge weights, graph shape
```

## Code Examples

### Coxeter Order Matrix Computation
```python
# Source: D-04, original code line 321-337
def coxeter_order_matrix(reflections):
    """Compute the Coxeter order matrix m_ij = order(M_i M_j).
    
    Parameters
    ----------
    reflections : list of ndarray
        Integer reflection matrices.
    
    Returns
    -------
    ndarray
        Symmetric integer matrix with m_ii = 1.
    """
    n = len(reflections)
    cox = np.ones((n, n), dtype=int)
    for i in range(n):
        for j in range(i + 1, n):
            cox[i, j] = matrix_period(reflections[i] @ reflections[j])
            cox[j, i] = cox[i, j]
    return cox
```

### Bilinear Form and Finite-Type Check
```python
# Source: D-06, [CITED: en.wikipedia.org/wiki/Coxeter_group]
def coxeter_bilinear_form(order_matrix):
    """Compute B_ij = -cos(pi / m_ij)."""
    return -np.cos(np.pi / order_matrix.astype(float))

def is_finite_type(order_matrix):
    """Check if the Coxeter group is finite via positive definiteness."""
    B = coxeter_bilinear_form(order_matrix)
    eigenvalues = np.linalg.eigvalsh(B)
    return np.all(eigenvalues > -1e-10)  # tolerance for numerical noise
```

### Orbit Expansion with Streaming BFS
```python
# Source: D-10 through D-14
def apply_coxeter_orbit(ekc, phases=True):
    """Expand fundamental domain via Coxeter group orbit.
    
    Parameters
    ----------
    ekc : CYBirationalClass
        Must have construct_phases completed.
    phases : bool
        If True, create full phase objects. If False, only
        accumulate cone generators.
    """
    reflections = [np.array(r) for r in ekc._sym_flop_refs]
    if not reflections:
        return
    
    # Compute order matrix and check finiteness
    order_mat = coxeter_order_matrix(reflections)
    if not is_finite_type(order_mat):
        logger.warning("Infinite Coxeter group -- skipping orbit expansion")
        return
    
    # Classify and compute expected order
    type_list = classify_coxeter_type(order_mat)
    expected_order = coxeter_group_order(type_list)
    
    # Memory check
    h11 = reflections[0].shape[0]
    mem_estimate = expected_order * 8 * h11 * h11
    if mem_estimate > 500_000_000:
        logger.warning("Estimated memory %.1f MB", mem_estimate / 1e6)
    
    fund_phases = list(ekc._graph.phases)
    phase_counter = ekc._graph.num_phases
    
    for g in enumerate_coxeter_group(reflections, expected_order):
        if np.allclose(g, np.eye(h11)):
            continue  # skip identity
        
        g_inv = np.linalg.inv(g)
        g_inv_int = np.round(g_inv).astype(int)
        
        for fund_phase in fund_phases:
            if phases:
                # Create reflected phase
                new_kappa = np.einsum('abc,xa,yb,zc',
                    fund_phase.int_nums, g, g, g)
                new_c2 = g @ fund_phase.c2
                
                import cytools
                new_kc = cytools.Cone(
                    rays=fund_phase.kahler_cone.rays() @ g_inv_int)
                new_mori = new_kc.dual()
                
                label = f"CY_{phase_counter}"
                new_phase = CalabiYauLite(
                    int_nums=new_kappa, c2=new_c2,
                    kahler_cone=new_kc, mori_cone=new_mori,
                    label=label)
                
                ekc._graph.add_phase(new_phase)
                # ... add contraction edges, accumulate generators
                phase_counter += 1
            
            # Accumulate generators (both modes)
            # Reflected Kahler cone rays -> eff_cone_gens
            for ray in fund_phase.kahler_cone.rays():
                reflected_ray = (ray @ g_inv_int)
                ekc._eff_cone_gens.add(tuple(reflected_ray.tolist()))
            
            # Reflect terminal wall data
            for contr, sign in ekc._graph.contractions_from(fund_phase.label):
                curve = sign * contr.contraction_curve
                reflected_curve = g @ curve
                rc_int = np.round(reflected_curve).astype(int)
                
                if contr.contraction_type in (
                    ContractionType.ASYMPTOTIC, ContractionType.CFT):
                    ekc._infinity_cone_gens.add(tuple(rc_int.tolist()))
                
                if contr.contraction_type in (
                    ContractionType.CFT, ContractionType.SU2):
                    zvd = contr.zero_vol_divisor
                    if zvd is not None:
                        reflected_zvd = g @ np.array(zvd)
                        ekc._eff_cone_gens.add(
                            tuple(np.round(reflected_zvd).astype(int).tolist()))
```

### On-Demand GV Reconstruction
```python
# Source: D-15
def invariants_for(ekc, phase_label):
    """Reconstruct GV invariants for a given phase on demand.
    
    Picks a tip point in the phase's Kahler cone, then re-orients
    all flop curves that pair negatively with that point.
    """
    phase = ekc._graph.get_phase(phase_label)
    tip = _compute_tip(phase)  # from build_gv
    
    # Start from root invariants
    gvs = ekc._root_invariants
    
    # Find which root flop curves pair negatively with this phase's tip
    flop_curves = []
    for contr in ekc.contractions:
        if contr.contraction_type == ContractionType.FLOP:
            curve = np.array(contr.contraction_curve)
            if tip @ curve < 0:
                flop_curves.append(curve)
    
    return gvs.flop_gvs(flop_curves)
```

## State of the Art

| Old Approach (weyl.py) | New Approach (coxeter.py) | Impact |
|------------------------|--------------------------|--------|
| Apply each reflection independently | BFS on Cayley graph for full group | Correct: gets ALL group elements, not just generators |
| Deduplicate by Mori cone | No deduplication needed | Cleaner, faster, mathematically correct |
| `expand_weyl` name | `apply_coxeter_orbit` name | Reflects actual mathematical operation |
| No type classification | Full finite-type classification | Enables memory estimation, early infinite-type bail |
| M used for both Mori and Kahler | g for Mori, (g^{-1})^T for Kahler | Correct for product group elements |
| No generator accumulation from reflected phases | Full accumulation (D-14) | Correct effective/infinity cone computation |
| No `invariants_for` | On-demand GV reconstruction | Avoids storing redundant per-phase Invariants objects |
| No `to_fundamental_domain` | Chamber walk algorithm | Enables point-to-phase mapping |

## Integration Points

### ekc.py Changes
The orchestrator needs three new public methods and a renamed private call:

1. `apply_coxeter_orbit(phases=True)` -- replaces `expand_weyl()`, lazy import from coxeter
2. `invariants_for(phase_label)` -- new public API
3. `to_fundamental_domain(point)` -- new public API
4. Keep `expand_weyl()` as deprecated alias initially or remove directly (user preference)

### __init__.py Changes
- Remove: `from .weyl import ...` (no public API was exported from weyl)
- Add: `coxeter_order_matrix`, `classify_coxeter_type`, `is_finite_type` to public API (optional, could keep internal)
- Update: `coxeter_reflection`, `coxeter_matrix`, `matrix_period` imports change from util to coxeter

### util.py Changes
- Remove: `matrix_period`, `coxeter_reflection`, `coxeter_matrix` (moved to coxeter.py)
- Keep: all other functions (charge_matrix_hsnf, moving_cone, sympy_number_clean, tuplify, normalize_curve, projection_matrix, projected_int_nums, minimal_N)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Type identification rules for matching Dynkin diagrams from order matrix are standard and complete | Finite Coxeter Group Type Classification | LOW -- well-established math; implementation details may need refinement for edge cases |
| A2 | `np.linalg.inv(g)` is exact enough for integer matrices at h11 < ~20 | Architecture Patterns (Pattern 3) | LOW -- for small integer matrices the inverse is exact in float64; could use `np.linalg.solve` or round+verify as safety |
| A3 | Right-multiplication BFS convention (g @ M_i) is the correct one for left-acting matrices | Common Pitfalls (Pitfall 4) | MEDIUM -- if wrong, all group elements are incorrect. Test with known A_2 or B_2 example. |
| A4 | `to_fundamental_domain` always terminates for finite groups | Architecture Patterns (Pattern 4) | LOW -- guaranteed by Coxeter group theory, but floating-point edge cases could cause issues |
| A5 | The `invariants_for` on-demand reconstruction via flop_gvs chain is correct | Code Examples | MEDIUM -- the mapping from an arbitrary reflected phase back to a flop chain needs careful design |

## Open Questions

1. **Edge graph structure for reflected phases**
   - What we know: D-12 says all flop edges between fundamental-domain phases should be reflected, terminal walls become self-loops.
   - What's unclear: How exactly to connect reflected phases to each other via flop edges. If fundamental phases A and B are connected by a flop, then g(A) and g(B) should be connected by the g-reflected flop edge. But we need to track which fundamental-domain edge maps to which reflected edge.
   - Recommendation: For each group element g, iterate over all edges in the fundamental domain graph and create the corresponding edge between g(A) and g(B).

2. **`invariants_for` implementation details**
   - What we know: D-15 says pick a tip point and re-orient flop curves.
   - What's unclear: For a reflected phase g(P), the flop chain from root to P is known, but the additional transformation by g changes which curves pair negatively. The correct approach may be to compute the flop chain to the fundamental-domain preimage, then let the GV machinery handle the rest.
   - Recommendation: Implement as "find the fundamental domain phase that maps to this label, get its flop chain, apply flop_gvs". Defer if complex.

3. **Backward compatibility of `coxeter_matrix` / `coxeter_reflection` imports**
   - What we know: These are currently exported from `util.py` and `cybir/__init__.py`.
   - What's unclear: Whether external users import them directly.
   - Recommendation: Re-export from the new location in `__init__.py` so the public API is unchanged.

## Sources

### Primary (HIGH confidence)
- Original code: `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/extended_kahler_cone.py` lines 43-52, 203-218, 268-276, 321-337, 977-1070
- Current cybir code: `cybir/core/weyl.py`, `cybir/core/util.py`, `cybir/core/ekc.py`, `cybir/core/build_gv.py`, `cybir/core/graph.py`
- CONTEXT.md decisions D-01 through D-16

### Secondary (MEDIUM confidence)
- [Wikipedia: Coxeter group](https://en.wikipedia.org/wiki/Coxeter_group) -- finite type classification, order formulas, bilinear form criterion
- Knowledge base: `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/literature/2212.10573/paper.md` -- Weyl orbit expansion algorithm

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all numpy/cytools
- Architecture: HIGH -- algorithm well-understood from original code and Coxeter theory
- Pitfalls: HIGH -- identified from concrete code analysis and index convention math
- Type classification: MEDIUM -- algorithm is standard math but implementation details (Dynkin diagram matching) need careful testing

**Research date:** 2026-04-12
**Valid until:** 2026-05-12 (stable mathematical content, unlikely to change)
