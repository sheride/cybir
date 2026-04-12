# Phase 2: Core Mathematics - Research

**Researched:** 2026-04-12
**Domain:** Birational geometry algorithms — wall-crossing, contraction classification, GV series
**Confidence:** HIGH

## Summary

Phase 2 ports all mathematical algorithms from the original ~2700-line `extended_kahler_cone.py` into cybir's modular structure (`flop.py`, `classify.py`, `gv.py`, plus Coxeter additions to `util.py`), operating on the Phase 1 types (CalabiYauLite, ExtremalContraction, ContractionType). The original code is a single monolithic file mixing class definitions, standalone functions, and CYTools monkey-patches. The math is well-understood and the algorithms are deterministic, making this a direct port with reorganization.

The primary challenge is not algorithmic complexity but **completeness and correctness verification**: ensuring every attribute, every edge case in the classification logic, and every intermediate computation is preserved. The original code has significant state scattered across CY, CY_GV, Wall, Facet, and ExtendedKahlerCone objects — this research systematically catalogs all of it and proposes mappings to cybir's types.

**Primary recommendation:** Port functions bottom-up (standalone helpers first, then the functions that call them), with intermediate-value snapshot tests for all 36 h11=2 polytopes to catch any divergence early.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Split math into multiple modules under `cybir/core/`: `flop.py` (wall-crossing formula), `classify.py` (contraction type classification), `gv.py` (GV series computation, effective GV, potent/nilpotent, nop identification)
- **D-02:** Coxeter reflection functions (`get_coxeter_reflection`, `coxeter_matrix`) go in `util.py`
- **D-03:** `ekc.py` remains a placeholder (Phase 3)
- **D-04:** Standalone functions are the real implementation (e.g., `flop.wall_cross(cy_lite, curve, ...)`)
- **D-05:** Thin convenience methods on CalabiYauLite/ExtremalContraction that delegate to standalone functions
- **D-06:** All math functions must be individually callable
- **D-07:** Intermediate value snapshots for all 36 h11=2 polytopes
- **D-08:** Tests compare cybir's intermediate results against these snapshots
- **D-09:** Preserve ALL information from the original code's data structures (nothing silently dropped)
- **D-10:** Reorganize into cleaner data structures where it makes sense
- **D-11:** Use "classify" terminology throughout (not "diagnose")
- **D-12:** Every math function docstring must cite the relevant equation from arXiv:2212.10573 or arXiv:2303.00757 with equation number, physical context, AND LaTeX

### Claude's Discretion
- Exact function signatures (argument names, return types)
- How to structure test fixtures (JSON, npz, pickle) as long as they capture intermediate values
- Specific reorganization proposals for data structures (subject to D-09: nothing dropped)

### Deferred Ideas (OUT OF SCOPE)
- Tuned complex structure mode (ENH-02)
- Higher-codimension contractions
- BFS pipeline, Weyl expansion, CYTools monkey-patching (Phase 3)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MATH-01 | Wall-crossing formula for intersection numbers and second Chern class | `wall_cross_intnums` and `wall_cross_second_chern_class` in original (lines 220-236); mapped to `flop.py` standalone functions |
| MATH-02 | ExtremalContraction classification — all 5 types | `Wall.diagnose` (lines 1597-1652) classification logic; mapped to `classify.py` |
| MATH-03 | GV series computation and effective GV | `gv_series` and `gv_eff` monkey-patches (lines 2594-2633); mapped to `gv.py` |
| MATH-04 | Potent/nilpotent curve classification and nop identification | Implicit in `diagnose` logic — potent = `gv_series[-1] != 0`, nop = nilpotent outside potent; mapped to `gv.py` |
| MATH-05 | Coxeter reflection computation | `get_coxeter_reflection` (lines 203-218) and `coxeter_matrix` (lines 321-337); mapped to `util.py` |
| MATH-06 | Equation citations in every math function docstring | Paper knowledge base provides equations; see Equation Citation Map section |
</phase_requirements>

## Original Code Attribute Catalog

This section fulfills D-09/D-10: a systematic sweep of every attribute on every class in the original code, with proposed cybir mappings.

### CY (base class, lines 2180-2289)

| Attribute | Type | Set Where | cybir Mapping |
|-----------|------|-----------|---------------|
| `_int_nums` | ndarray (h11,h11,h11) | constructor | `CalabiYauLite.int_nums` (already exists) |
| `_c2` | ndarray (h11,) | constructor | `CalabiYauLite.c2` (already exists) |
| `var` | sympy symbols | constructor | DROP — only used for `int_poly`/`c2_poly`/`holo_index` display; can be reconstructed on-the-fly |
| `mori_gens` | ndarray | constructor | Derived from `CalabiYauLite.mori_cone.extremal_rays()` |
| `mori` | cytools.Cone | subclass | `CalabiYauLite.mori_cone` (already exists) |
| `tip` | ndarray (h11,) | constructor | New: compute as utility function; needed by BFS (Phase 3) but worth adding to `CalabiYauLite` now |
| `toric` | bool | EKC pipeline | Phase 3 — BFS metadata |
| `fund` | bool | EKC pipeline | Phase 3 — Weyl orbit metadata |
| `orbit_computed` | bool | EKC pipeline | Phase 3 — Weyl orbit metadata |
| `curve_signs` | dict | EKC pipeline | Phase 3 — BFS deduplication |

**Methods on CY:**
- `h11()` → `len(cy_lite.c2)` or `cy_lite.int_nums.shape[0]`
- `kahler()` → `cy_lite.mori_cone.dual()` (already available)
- `int_poly()`, `c2_poly()`, `holo_index()` → Display utilities, defer to Phase 3 or later
- `compute_basis_curve_volumes(t)`, `compute_basis_divisor_volumes(t)`, `compute_divisor_volumes(t)`, `compute_cy_volume(t)`, `compute_inverse_kahler_metric(t)` → Numerical helpers; NOT used by core math algorithms. Defer.

### CY_GV (lines 2291-2359)

| Attribute | Type | Set Where | cybir Mapping |
|-----------|------|-----------|---------------|
| `cy` | cytools.CalabiYau | constructor | `CalabiYauLite.triangulation` (already exists as optional ref) |
| `_gvs` | cytools.Invariants | constructor | `CalabiYauLite.gv_invariants` (already exists) |
| `Q` | ndarray | constructor | `CalabiYauLite.charges` (already exists) |
| `eff` | cytools.Cone | constructor | `CalabiYauLite.eff_cone` (already exists) |
| `walls` | list[Facet] | constructor | Phase 3 — constructed by BFS |

### Wall (lines 1360-2122)

| Attribute | Type | Set Where | cybir Mapping |
|-----------|------|-----------|---------------|
| `curve` | ndarray (h11,) | constructor | `ExtremalContraction.flopping_curve` (exists) |
| `start_cy` | CY | constructor | `ExtremalContraction.start_phase` (exists, stores label) |
| `end_cy` | CY | constructor/BFS | `ExtremalContraction.end_phase` (exists, stores label) |
| `category` | str or None | `diagnose()` | `ExtremalContraction.contraction_type` (exists, uses ContractionType enum) |
| `gvs` | Invariants (copy) | constructor | Stored on CalabiYauLite, not on contraction |
| `gv_series` | list[int] | `compute_gv_eff()` | New field needed on ExtremalContraction: `gv_series` |
| `gv_eff_1` | int | `compute_gv_eff()` | New: store as part of contraction or compute on-the-fly |
| `gv_eff_3` | int | `compute_gv_eff()` | `ExtremalContraction.effective_gv` stores gv_eff_3 (the one used for int_num wall-crossing) |
| `end` | bool | `diagnose()` | Derivable from `contraction_type` (ASYMPTOTIC and CFT and SU2 are ends) |
| `zero_vol_divisor` | ndarray | `find_zero_vol_divisor()` | `ExtremalContraction.zero_vol_divisor` (exists) |
| `coxeter_reflection` | ndarray | `get_coxeter_reflection()` | `ExtremalContraction.coxeter_reflection` (exists) |
| `start_circuit` | Circuit | toric pipeline | Phase 3 / toric pipeline (out of scope) |
| `end_circuit` | Circuit | toric pipeline | Phase 3 / toric pipeline (out of scope) |
| `start_fan` | Fan | toric pipeline | Phase 3 / toric pipeline (out of scope) |
| `end_fan` | Fan | toric pipeline | Phase 3 / toric pipeline (out of scope) |
| `zero_vol_divisor_result` | ndarray/str/None | `diagnose()` | Internal to classification — not stored; result goes to `zero_vol_divisor` |
| `moving_wall` | bool | `diagnose_toric()` | Toric pipeline only (out of scope) |
| `parent` | Wall | Weyl expansion | Phase 3 |

### Facet (extends Wall, lines 2123-2178)

| Attribute | Type | Set Where | cybir Mapping |
|-----------|------|-----------|---------------|
| `facet` | cytools.Cone | `update_facet()` | Not needed for core math — only used for BFS wall deduplication (Phase 3) |
| `cone` | cytools.Cone | constructor | The Kahler cone; used for `update_facet` and CFT check with Kahler parameters |
| `enforce_codim_1` | bool | constructor | Phase 3 detail |

### ExtendedKahlerCone (lines 742-1358)

All attributes are Phase 3 pipeline state (not Phase 2 math):
- `polytope`, `vc`, `cy_cap`, `basis`, `cob`, `Q`, `anticanon` — pipeline setup
- `toric_mov_cone`, `toric_eff_cone` — toric pipeline
- `cys`, `walls`, `explored_signs` — BFS state
- `root` — starting phase
- `infinity_cone_gens`, `eff_cone_gens` — post-construction
- `coxeter_refs`, `sym_flop_refs`, `su2_refs` — post-construction
- `eff_cone` — post-construction

### Proposed New Fields on ExtremalContraction

Based on the catalog above, `ExtremalContraction` needs two additional fields to preserve all information (D-09):

| Field | Type | Purpose |
|-------|------|---------|
| `gv_series` | `list[int]` or `None` | The GV series `[GV(C), GV(2C), GV(3C), ...]` — needed for classification decisions and diagnostic display |
| `gv_eff_1` | `int` or `None` | `sum_n n * GV(nC)` — used in c2 wall-crossing; currently only `effective_gv` (=gv_eff_3) exists |

The existing `gv_invariant` field can store `GV(C)` (the first entry of `gv_series`). The existing `effective_gv` field stores `gv_eff_3`. The `end` boolean from the original code is derivable: `contraction_type in {ASYMPTOTIC, CFT, SU2}` implies the wall is an end of moduli space.

[VERIFIED: reading cybir/core/types.py and original extended_kahler_cone.py]

## Architecture Patterns

### Module Organization (per D-01, D-02)

```
cybir/core/
├── __init__.py       # re-exports (update to include new modules)
├── types.py          # CalabiYauLite, ExtremalContraction, ContractionType (Phase 1, modify)
├── util.py           # existing utils + get_coxeter_reflection, coxeter_matrix (modify)
├── graph.py          # PhaseGraph (Phase 1, unchanged)
├── flop.py           # wall_cross_intnums, wall_cross_c2, flop_phase (new)
├── classify.py       # classify_contraction, is_asymptotic, is_cft, find_zero_vol_divisor, is_symmetric_flop (new)
├── gv.py             # gv_series, gv_eff, is_potent, is_nilpotent, is_nop (new)
└── ekc.py            # placeholder (Phase 3)
```

### Pattern: Standalone Function + Thin Method Wrapper (D-04/D-05/D-06)

**What:** Each mathematical operation is a standalone function operating on primitive numpy arrays and CalabiYauLite objects. Types have thin convenience methods that delegate.

**Example:**

```python
# flop.py — standalone function
def wall_cross_intnums(int_nums, curve, gv_eff_3):
    """Wall-crossing formula for triple intersection numbers.

    Transforms intersection numbers :math:`\\kappa_{abc}` across a flop
    of the curve :math:`[\\mathcal{C}]`:

    .. math::

        \\kappa'_{abc} = \\kappa_{abc} - n^{\\mathrm{eff,3}}_{\\mathcal{C}}
        \\, \\mathcal{C}_a \\mathcal{C}_b \\mathcal{C}_c

    where :math:`n^{\\mathrm{eff,3}}_{\\mathcal{C}} = \\sum_k k^3 \\, n^0_{k[\\mathcal{C}]}`
    is the cubic effective GV invariant.

    See arXiv:2212.10573, below Eq. (2.7); also Eq. (4.4) of arXiv:2212.10573.

    Parameters
    ----------
    int_nums : numpy.ndarray
        Triple intersection numbers, shape ``(h11, h11, h11)``.
    curve : numpy.ndarray
        Flopping curve class, shape ``(h11,)``.
    gv_eff_3 : int
        Cubic effective GV invariant :math:`\\sum_k k^3 n^0_{k[\\mathcal{C}]}`.

    Returns
    -------
    numpy.ndarray
        Transformed intersection numbers, same shape.
    """
    return int_nums - gv_eff_3 * np.einsum('a,b,c', curve, curve, curve)
```

```python
# Thin convenience method (added to CalabiYauLite or as a higher-level helper)
# This is Phase 3 territory for the full pipeline, but the standalone
# function above is Phase 2.
```

### Pattern: Classification as Sequential Predicate Checks

The `Wall.diagnose()` method (original lines 1597-1652) follows a strict sequential check:

1. `is_asymptotic_facet(int_nums, curve)` → if True: ASYMPTOTIC
2. `is_cft_facet(int_nums, curve)` → if True: CFT
3. `find_zero_vol_divisor(int_nums, curve)` → None means no shrinking divisor
4. Compute `gv_eff_1`, `gv_eff_3` from `gv_series`
5. Check potency: `gv_series[-1] != 0` → InsufficientGVError
6. If no zero-vol divisor: FLOP (generic, type I — no shrinking divisor)
7. If has zero-vol divisor AND `is_symmetric_flop(...)`:
   - If `gv_series[0] >= 0 and gv_series[1] >= 0`: SYMMETRIC_FLOP
   - Else: SU2
8. If has zero-vol divisor AND NOT symmetric: FLOP (generic, type II — has shrinking divisor but not symmetric)

**cybir mapping:** A single `classify_contraction(cy_lite, curve, gv_series)` function in `classify.py` that returns a populated `ExtremalContraction` (or just the classification result). This encodes the exact logic above.

### Anti-Patterns to Avoid

- **Merging "generic flop (I)" and "generic flop (II)" prematurely:** The original code distinguishes flops with vs. without a zero-volume divisor. Both map to `ContractionType.FLOP` in the enum, but the `zero_vol_divisor` field on `ExtremalContraction` captures the distinction (None vs. an array).
- **Dropping the `gv_series` from the contraction:** The original stores `gv_series` on Wall objects. Tests need it; the display `__str__` uses it; classification logic references it. Must be preserved.
- **Making classification depend on BFS state:** The `classify_contraction` function must be callable with just `(int_nums, c2, curve, gv_series)` — no reference to the EKC or pipeline state.

## Function Catalog and Module Assignment

### `flop.py` — Wall-Crossing

| Function | Original Location | Signature | Notes |
|----------|------------------|-----------|-------|
| `wall_cross_intnums` | line 220 | `(int_nums, curve, gv_eff_3) -> ndarray` | Pure einsum |
| `wall_cross_c2` | line 229 | `(c2, curve, gv_eff_1) -> ndarray` | Pure arithmetic |
| `flop_phase` | `flop_cy` line 238 | `(cy_lite, curve, gv_series) -> CalabiYauLite` | Creates new CalabiYauLite with transformed int_nums, c2. GV invariant handling (flop_gvs) is Phase 3 / INTG territory since it monkey-patches CYTools Invariants. |

### `classify.py` — Contraction Classification

| Function | Original Location | Signature | Notes |
|----------|------------------|-----------|-------|
| `is_asymptotic` | `is_asymptotic_facet` line 136 | `(int_nums, curve) -> bool` | Checks if projected int_nums vanish |
| `is_cft` | `is_cft_facet` line 144 | `(int_nums, curve) -> bool` | Checks rank deficiency. NOTE: original has a `kahler` parameter for Facet-based check; simplify for Phase 2 to use the projection-based check (no `kahler` arg) |
| `find_zero_vol_divisor` | line 178 | `(int_nums, curve) -> ndarray or None` | Returns integer divisor or None |
| `is_symmetric_flop` | line 280 | `(int_nums, c2, gv_eff_1, gv_eff_3, coxeter_reflection, curve) -> bool` | Compares flopped vs Coxeter-reflected int_nums and c2 |
| `classify_contraction` | `Wall.diagnose` line 1597 | `(int_nums, c2, curve, gv_series) -> dict` | Orchestrator: runs the sequential checks, returns contraction_type + all metadata |

**Helper (already in util.py):**
- `projected_int_nums(int_nums, curve, N)` — needs to be added (used by `is_asymptotic`, `is_cft`, `find_zero_vol_divisor`)
- `find_minimal_N(X)` — needs to be added (used by `find_zero_vol_divisor`)

### `gv.py` — GV Series and Curve Classification

| Function | Original Location | Signature | Notes |
|----------|------------------|-----------|-------|
| `compute_gv_series` | monkey-patch line 2594 | `(gv_invariants, curve) -> list[int]` | Iterates `gv_invariants.gv(n*curve)` for n=1,2,... until None |
| `compute_gv_eff` | monkey-patch line 2614 / Wall.compute_gv_eff line 1437 | `(gv_series) -> (int, int)` | Returns `(gv_eff_1, gv_eff_3)` — pure arithmetic on the series |
| `is_potent` | implicit in diagnose | `(gv_series) -> bool` | `gv_series[-1] != 0` (series doesn't terminate in computed range) |
| `is_nilpotent` | implicit in diagnose | `(gv_series) -> bool` | `not is_potent(gv_series)` |

**Note on `ensure_nilpotency`:** This function (original line 2530) recomputes GVs to higher degree when the series hasn't terminated. It depends heavily on CYTools Invariants internals (`._cy.compute_gvs`, `.grading_vec`, `.cutoff`, `.flop_curves`, `.precompose`). This is an **INTG** function (Phase 3). For Phase 2, `compute_gv_series` assumes GVs are already computed to sufficient degree. If the series doesn't terminate, the caller gets a potent classification.

**Note on `flop_gvs`, `gv_incl_flop`, `cone_incl_flop`, `copy`:** These are all CYTools Invariants monkey-patches (lines 2635-2692). They are Phase 3 / INTG-01 scope.

### `util.py` — Additions

| Function | Original Location | Signature | Notes |
|----------|------------------|-----------|-------|
| `get_coxeter_reflection` | line 203 | `(divisor, curve) -> ndarray` | Coxeter/Weyl reflection matrix |
| `coxeter_matrix` | line 321 | `(reflections) -> ndarray` | Coxeter matrix from a set of reflections |
| `matrix_period` | line 43 | `(M, max_iter) -> int` | Period of a matrix (used by `coxeter_matrix`) |
| `projected_int_nums` | line 121 | `(int_nums, curve, N) -> ndarray` | Projected intersection numbers |
| `find_minimal_N` | line 57 | `(X, epsilon, max_val) -> int` | Smallest N such that N*X is integer |

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Smith Normal Form | Custom SNF | `hsnf.smith_normal_form` | Already used in `projection_matrix`; exact integer arithmetic |
| Null space finding | Custom null space | `scipy.linalg.null_space` | Used in `find_zero_vol_divisor`; numerically stable |
| Rational number cleanup | Manual rounding | `sympy.Rational(...).limit_denominator()` via `sympy_number_clean` | Already in util.py |
| Cone operations | Custom cone code | `cytools.Cone` | Already the project standard |
| Matrix period detection | Custom eigenvalue approach | Direct matrix power iteration (as in original) | Simple and correct for small matrices |

**Key insight:** The mathematical operations here are simple linear algebra (einsum contractions, null spaces, matrix products). The complexity is in the classification *logic*, not the numerical methods. Don't over-engineer the numerics.

## Common Pitfalls

### Pitfall 1: gv_eff_1 vs gv_eff_3 Confusion
**What goes wrong:** The wall-crossing formula for intersection numbers uses `gv_eff_3 = sum(k^3 * GV(kC))`, while the c2 formula uses `gv_eff_1 = sum(k * GV(kC))`. Swapping them silently produces wrong results that look plausible.
**Why it happens:** The original code names these `gv_eff_1` and `gv_eff_3` but the variable names don't always make clear which goes where.
**How to avoid:** Use explicit parameter names in function signatures. The docstrings must cite the exact equations.
**Warning signs:** c2 values that don't match snapshots; intersection numbers that are off by a multiplicative factor.

### Pitfall 2: Coxeter Reflection Argument Order
**What goes wrong:** `get_coxeter_reflection(divisor, curve)` takes divisor first, curve second. The formula is `I - 2 * (C tensor D) / (C dot D)`. Swapping arguments transposes the reflection matrix.
**Why it happens:** The original code has a comment noting the tensor product was flipped from Eq. 4.6. The convention is: the reflection acts on the Kahler cone (divisor space), so the outer product is `curve (x) divisor`.
**How to avoid:** Write explicit tests checking that the reflection satisfies `M @ curve = -curve` (when `D.C = 1`).
**Warning signs:** Symmetric flop detection failing on known symmetric-flop examples.

### Pitfall 3: Sign Convention for zero_vol_divisor
**What goes wrong:** `find_zero_vol_divisor` returns a divisor with sign chosen so that `divisor @ curve < 0` (original line 196: `return -np.sign(zero_vol_divisor @ curve) * zero_vol_divisor`). Getting this wrong breaks `is_symmetric_flop`.
**Why it happens:** The sign convention is physically motivated (the shrinking divisor has negative volume on the wall side) but easy to overlook.
**How to avoid:** Snapshot tests that capture the exact divisor values.
**Warning signs:** `is_symmetric_flop` returning False on known symmetric flops.

### Pitfall 4: Projected Intersection Numbers Dimension Parameter
**What goes wrong:** `projected_int_nums(int_nums, curve, N)` has an `N` parameter controlling how many indices are projected (N=3 projects all three, N=2 projects two, N=1 projects one). Using the wrong N gives arrays of unexpected shape.
**Why it happens:** The function serves different purposes: N=3 for asymptotic check, N=2 for zero-vol divisor, N=1 for CFT check.
**How to avoid:** Each calling function should clearly document which N it uses and why.

### Pitfall 5: Potent vs Insufficient-Degree Confusion
**What goes wrong:** A curve that appears nilpotent (GV series terminates within computed range) might actually be potent if GVs weren't computed to high enough degree.
**Why it happens:** The GV computation has a finite cutoff. A potent curve may have `GV(nC) = 0` for several consecutive n before becoming nonzero again.
**How to avoid:** The original raises `InsufficientGVError` (in the refactored version) or sets a special category string. Phase 2 should raise `InsufficientGVError` when `gv_series[-1] != 0`.

## Equation Citation Map (for MATH-06)

Each function must cite equations from these papers. The paper knowledge base (`paper.md`) provides the key formulas:

| Function | Paper | Equation / Section | LaTeX |
|----------|-------|-------------------|-------|
| `wall_cross_intnums` | arXiv:2212.10573 | Below Eq. (2.7), Eq. (4.4) | `\kappa'_{abc} = \kappa_{abc} - n^{\mathrm{eff,3}}_\mathcal{C} \mathcal{C}_a \mathcal{C}_b \mathcal{C}_c` |
| `wall_cross_c2` | arXiv:2212.10573 | Below Eq. (2.7), Eq. (4.4) | `c'_a = c_a + 2 n^{\mathrm{eff,1}}_\mathcal{C} \mathcal{C}_a` |
| `get_coxeter_reflection` | arXiv:2212.10573 | Eq. (4.6) | `M_{ab} = \delta_{ab} - 2 \frac{\mathcal{C}_a D_b}{\mathcal{C} \cdot D}` |
| `is_asymptotic` | arXiv:2212.10573 | Section 2, discussion of asymptotic boundaries | Volume vanishes: `\kappa_{abc} \Pi^a_\perp \Pi^b_\perp \Pi^c_\perp = 0` |
| `is_cft` | arXiv:2212.10573 | Section 2, CFT boundaries | Divisor volume vanishes: rank-deficient matrix |
| `is_symmetric_flop` | arXiv:2212.10573 | Section 4, symmetric flops | Coxeter reflection reproduces wall-crossing |
| `compute_gv_series` | arXiv:2303.00757 | Section 2 (GV extraction from prepotential) | `n^0_{k[\mathcal{C}]}` for `k = 1, 2, 3, \ldots` |
| `compute_gv_eff` | arXiv:2212.10573 | Below Eq. (2.7) | `n^{\mathrm{eff},p}_\mathcal{C} = \sum_k k^p n^0_{k[\mathcal{C}]}` |
| `is_potent` / `is_nilpotent` | arXiv:2212.10573 | Section 3.1 | Potent: infinite GV sequence; Nilpotent: finite |
| `classify_contraction` | arXiv:2212.10573 | Section 4 (full classification algorithm) | Sequential: asymptotic → CFT → su(2)/sym-flop/flop |

[VERIFIED: reading paper.md knowledge base files and original source code]

## Code Examples

### Wall-Crossing (original, verified from source lines 220-236)

```python
# Original — exact implementation to port
def wall_cross_intnums(intnums, curve, gv_eff):
    return intnums - gv_eff * np.einsum('a,b,c', curve, curve, curve)

def wall_cross_second_chern_class(c2, curve, gv_eff):
    return c2 + 2 * gv_eff * curve
```

### Classification Logic (original, verified from source lines 1597-1652)

```python
# Original Wall.diagnose() — core logic to port to classify.py
def diagnose(self, start=True, recompute=False, verbose=False):
    if self.is_asymptotic_facet(start=start):
        self.end = True
        self.category = 'asymptotic'
    elif self.is_cft_facet(start=start):
        self.end = True
        self.category = 'CFT'
    else:
        self.zero_vol_divisor_result = self.find_zero_vol_divisor(start=start)
        self.compute_gv_eff(verbose=verbose)
        
        if self.gv_series[-1] != 0:
            # Potent wall — insufficient GV degree
            raise InsufficientGVError(...)
            
        if self.zero_vol_divisor_result is None:
            self.category = 'generic flop (I)'  # -> ContractionType.FLOP
        else:
            if self.is_symmetric():
                if self.gv_series[0] >= 0 and self.gv_series[1] >= 0:
                    self.category = 'symmetric flop'  # -> ContractionType.SYMMETRIC_FLOP
                else:
                    self.category = 'su(2) enhancement'  # -> ContractionType.SU2
            else:
                self.category = 'generic flop (II)'  # -> ContractionType.FLOP
```

### Coxeter Reflection (original, verified from source lines 203-218)

```python
def get_coxeter_reflection(divisor, curve):
    h11 = len(curve)
    DtensorC = np.tensordot(curve, divisor, axes=0)
    DdotC = curve @ divisor
    if DdotC == 0:
        return np.identity(h11)
    else:
        return np.identity(h11) - 2 * DtensorC / DdotC
```

### GV Effective Computation (original, verified from source lines 1437-1456)

```python
def compute_gv_eff(self):
    # gv_series = [GV(C), GV(2C), GV(3C), ...]
    self.gv_eff_1 = np.array(range(1, len(self.gv_series)+1)) @ self.gv_series
    self.gv_eff_3 = np.array(range(1, len(self.gv_series)+1))**3 @ self.gv_series
```

## Proposed Function Signatures

### `flop.py`

```python
def wall_cross_intnums(
    int_nums: np.ndarray,    # (h11, h11, h11)
    curve: np.ndarray,        # (h11,)
    gv_eff_3: int,
) -> np.ndarray:
    ...

def wall_cross_c2(
    c2: np.ndarray,           # (h11,)
    curve: np.ndarray,        # (h11,)
    gv_eff_1: int,
) -> np.ndarray:
    ...

def flop_phase(
    cy_lite: CalabiYauLite,
    curve: np.ndarray,
    gv_series: list[int],
    label: str | None = None,
) -> CalabiYauLite:
    """Create a new CalabiYauLite by flopping across a wall.

    Computes gv_eff_1 and gv_eff_3 from gv_series internally.
    Does NOT transform GV invariants (that requires CYTools Invariants
    manipulation, which is Phase 3 / INTG-01).
    """
    ...
```

### `classify.py`

```python
def is_asymptotic(int_nums: np.ndarray, curve: np.ndarray) -> bool:
    ...

def is_cft(int_nums: np.ndarray, curve: np.ndarray) -> bool:
    ...

def find_zero_vol_divisor(
    int_nums: np.ndarray,
    curve: np.ndarray,
) -> np.ndarray | None:
    ...

def is_symmetric_flop(
    int_nums: np.ndarray,
    c2: np.ndarray,
    curve: np.ndarray,
    gv_eff_1: int,
    gv_eff_3: int,
    coxeter_reflection: np.ndarray,
) -> bool:
    ...

def classify_contraction(
    int_nums: np.ndarray,
    c2: np.ndarray,
    curve: np.ndarray,
    gv_series: list[int],
) -> dict:
    """Classify a contraction and return all metadata.

    Returns
    -------
    dict with keys:
        contraction_type : ContractionType
        zero_vol_divisor : np.ndarray or None
        coxeter_reflection : np.ndarray or None
        gv_invariant : int (= gv_series[0])
        effective_gv : int (= gv_eff_3)
        gv_eff_1 : int
        gv_series : list[int]
    """
    ...
```

### `gv.py`

```python
def compute_gv_series(
    gv_invariants,  # CYTools Invariants object
    curve: np.ndarray,
) -> list[int]:
    """Extract GV(C), GV(2C), ... until the series terminates."""
    ...

def compute_gv_eff(gv_series: list[int]) -> tuple[int, int]:
    """Compute (gv_eff_1, gv_eff_3) from a GV series."""
    ...

def is_potent(gv_series: list[int]) -> bool:
    """True if the GV series has not terminated (last entry nonzero)."""
    ...

def is_nilpotent(gv_series: list[int]) -> bool:
    """True if the GV series terminates (last entry is zero)."""
    ...
```

### `util.py` additions

```python
def get_coxeter_reflection(
    divisor: np.ndarray,
    curve: np.ndarray,
) -> np.ndarray:
    ...

def coxeter_matrix(reflections: list[np.ndarray]) -> np.ndarray:
    ...

def matrix_period(M: np.ndarray, max_iter: int = 200) -> int:
    ...

def projected_int_nums(
    int_nums: np.ndarray,
    curve: np.ndarray,
    n_projected: int = 3,
) -> np.ndarray:
    ...

def find_minimal_N(
    X: np.ndarray,
    epsilon: float = 1e-4,
    max_val: int = 10000,
) -> int:
    ...
```

## Test Strategy

### Fixture Format Recommendation: JSON [ASSUMED]

Use JSON files for test fixtures because:
- Human-readable and diffable in git
- No pickle security concerns
- Numpy arrays serialize cleanly as nested lists
- Easy to inspect and debug when tests fail

Structure: `tests/fixtures/h11_2/polytope_{id}.json` with fields:
```json
{
    "polytope_id": 0,
    "h11": 2,
    "int_nums": [[[...]]],
    "c2": [...],
    "mori_rays": [[...]],
    "walls": [
        {
            "curve": [...],
            "contraction_type": "flop",
            "gv_series": [...],
            "gv_eff_1": ...,
            "gv_eff_3": ...,
            "zero_vol_divisor": null,
            "coxeter_reflection": null,
            "flopped_int_nums": [[[...]]],
            "flopped_c2": [...]
        }
    ]
}
```

### Snapshot Generation

A separate script (not part of cybir package) runs the original `extended_kahler_cone.py` on all 36 h11=2 polytopes and captures intermediate values at each stage. This script lives in `tests/generate_snapshots.py` and outputs to `tests/fixtures/`.

### Test Organization

```
tests/
├── conftest.py                 # shared fixtures (exists)
├── fixtures/
│   └── h11_2/                  # snapshot data
│       ├── polytope_0.json
│       └── ...
├── test_flop.py                # wall_cross_intnums, wall_cross_c2, flop_phase
├── test_classify.py            # is_asymptotic, is_cft, find_zero_vol_divisor, etc.
├── test_gv.py                  # compute_gv_series, compute_gv_eff, is_potent
├── test_util_coxeter.py        # get_coxeter_reflection, coxeter_matrix
└── generate_snapshots.py       # snapshot generation script (runs original code)
```

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | JSON is the best fixture format for intermediate value snapshots | Test Strategy | Low — could switch to npz; JSON is simpler but verbose for large arrays |
| A2 | `compute_gv_series` can simply iterate `gv_invariants.gv(n*curve)` without calling `ensure_nilpotency` in Phase 2 | Function Catalog | Medium — if tests require nilpotency enforcement, the function boundary with Phase 3 INTG code may need adjustment |
| A3 | The `kahler` parameter path in `is_cft_facet` (using actual Kahler cone rays) is not needed for Phase 2 | Function Catalog | Low — the projection-based check (no `kahler` arg) is the primary path used by `Wall.diagnose()` |
| A4 | The 36 h11=2 polytopes provide sufficient coverage for all 5 contraction types | Test Strategy | Medium — need to verify that all 5 types appear in h11=2 examples; su(2) may require h11=3 |

## Open Questions

1. **Do all 5 contraction types appear among h11=2 polytopes?**
   - What we know: h11=2 polytopes have relatively simple Kahler cones. Asymptotic, CFT, and flop types are common. Symmetric flop and su(2) enhancement may require higher h11.
   - What's unclear: Whether the 36 h11=2 polytopes cover su(2) and symmetric flop cases.
   - Recommendation: Generate snapshots for h11=2 first; if any type is missing, add a few h11=3 examples to cover it. The snapshot generator can handle both.

2. **How should `flop_phase` handle GV invariants?**
   - What we know: The original `flop_cy` calls `gvs.flop_gvs([curve])` which is a CYTools Invariants monkey-patch. This is INTG-01 territory.
   - What's unclear: Whether `flop_phase` should accept a pre-flopped Invariants object or leave gv_invariants as None on the new phase.
   - Recommendation: `flop_phase` creates a new CalabiYauLite with transformed int_nums and c2 but with `gv_invariants=None`. The caller (Phase 3 pipeline) is responsible for attaching flopped GV invariants.

3. **Should `classify_contraction` return a dict or an ExtremalContraction?**
   - What we know: D-04 says standalone functions are the real implementation. D-05 says thin convenience methods delegate to them.
   - Recommendation: Return a dict of classification results. The caller constructs the `ExtremalContraction`. This keeps the function pure and testable without depending on the type system.

## Project Constraints (from CLAUDE.md)

- Mathematical correctness: All algorithms must remain bit-for-bit equivalent to the original
- CYTools compatibility: Must work with the CYTools version in the `cytools` conda environment
- Package structure: Follow `cybir/core/` pattern
- Python 3.12 runtime
- Use numpy, scipy, python-flint, hsnf, sympy (all in conda env)
- Do NOT use pydantic, attrs, pandas, SageMath
- Use ruff for linting/formatting
- pytest for testing
- Every docstring should reference equations from 2212.10573 and 2303.00757

## Sources

### Primary (HIGH confidence)
- Original source code: `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/extended_kahler_cone.py` — all function implementations verified by direct reading
- Phase 1 types: `cybir/core/types.py`, `cybir/core/util.py`, `cybir/core/graph.py` — all fields and patterns verified
- Prior refactor notes: `cornell-dev/projects/vex/elijah/claude/CHANGES.md` — verified

### Secondary (MEDIUM confidence)
- Knowledge base paper summaries: `knowledge-base/literature/2212.10573/paper.md` and `2303.00757/paper.md` — equation references verified against paper summaries
- CONTEXT.md decisions — directly provided by user

### Tertiary (LOW confidence)
- None — all claims are verified from source code or user-provided context

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in conda env, verified in Phase 1
- Architecture: HIGH — module split is a locked decision; function catalog derived from direct source reading
- Pitfalls: HIGH — identified from direct code reading and prior refactor notes

**Research date:** 2026-04-12
**Valid until:** 2026-05-12 (stable domain — math algorithms don't change)
