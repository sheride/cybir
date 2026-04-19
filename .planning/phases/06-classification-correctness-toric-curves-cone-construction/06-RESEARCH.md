# Phase 6: Classification Correctness, Toric Curves & Cone Construction - Research

**Researched:** 2026-04-19
**Domain:** Birational geometry classification fixes, toric curve computation, cone construction
**Confidence:** HIGH

## Summary

Phase 6 is a large feature phase with four interrelated workstreams: (1) fixing GrossFlop misclassification by adding the Kahler cone check to `is_symmetric_flop`, (2) porting toric curve computation from cornell-dev with FRST detection via regfans, (3) adding cone construction methods (movable, EKC, HEKC, effective, infinity), and (4) several API improvements (CoxeterGroup dataclass, flexible orbit expansion, diagnose_curve, phase classification exposure). All 14 decisions in CONTEXT.md are locked.

The source code to port is well-understood: `compute_toric_curves_old` (698 lines in cornell-dev/lib/geom/curves/toric.py) and `induced_2face_triangulations_old` (44 lines in cornell-dev/lib_axion/cytools_ext/polytopeface_ext.py). The moving cone function is already in `cybir/core/util.py`. The regfans library is installed in the cytools conda env and provides `VectorConfiguration.triangulate()` and `Fan.respects_ptconfig()` for the FRST detection trichotomy.

**Primary recommendation:** Implement in dependency order: GrossFlop fix first (enables re-validation), then CoxeterGroup dataclass and flexible orbit expansion (modify existing code), then toric curves module (new code, largest piece), then cone construction and convenience APIs, and finally the h11=3 re-validation.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: GrossFlop classification -- add Kahler cone check (condition b) to is_symmetric_flop; new GROSS_FLOP enum member for cases where (a) passes but (b) fails
- D-02: Classification invariance sanity check -- log warning if curve re-classified differently from a different phase
- D-03: CoxeterGroup frozen dataclass in types.py with factors, order, rank, repr, order_matrix, reflections
- D-04: Flexible orbit expansion via `reflections` parameter ('ekc', 'hekc', 'all', or custom set)
- D-05: Toric curve module `cybir/core/toric_curves.py` split into curve enumeration and diagnosis
- D-06: FRST detection trichotomy (moving cone intersection -> height vector -> regfans check)
- D-07: Incremental toric curve compilation during BFS with deduplication at 2-face triangulation level
- D-08: Optional `toric_origin` field on ExtremalContraction
- D-09: Inner/outer Mori cone bounds from toric curves
- D-10: Toric curve canonical orientation with per-phase re-orientation
- D-11: Cone construction methods on CYBirationalClass (movable, EKC, HEKC, effective, infinity)
- D-12: diagnose_curve convenience function accepting CYTools Invariants or plain list
- D-13: Re-validate h11=3 survey after GrossFlop fix
- D-14: Phase classification exposure (phase_type, frst_phases, vex_phases, non_inherited_phases)

### Claude's Discretion
None explicitly stated -- all items are locked decisions.

### Deferred Ideas (OUT OF SCOPE)
None -- all items from the discussion are in scope.
</user_constraints>

## Standard Stack

No new dependencies required. All tools are already in the cytools conda env.

### Core (existing)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | 2.3.5 | Array operations, linear algebra | Already used throughout cybir | [VERIFIED: conda env]
| scipy | 1.17.0 | ConvexHull, linear algebra | Already used in classify.py | [VERIFIED: conda env]
| cytools | local | Cone objects, CY geometry | Core dependency | [VERIFIED: conda env]
| regfans | local | Fan, VectorConfiguration | FRST detection via respects_ptconfig() | [VERIFIED: conda env]
| itertools | stdlib | Combinatorics for 2-face curves | Used in compute_toric_curves_old | [VERIFIED: stdlib]

### No New Packages Required
The toric curve computation is pure numpy/combinatorics. The FRST detection uses regfans which is already installed. Cone construction uses CYTools Cone which is already a dependency.

## Architecture Patterns

### New Module: `cybir/core/toric_curves.py`

```
cybir/core/
    toric_curves.py     # NEW: toric curve enumeration + diagnosis
    types.py            # MODIFIED: add GROSS_FLOP enum, CoxeterGroup dataclass, ToricCurveData
    classify.py         # MODIFIED: GrossFlop check in is_symmetric_flop + classify_contraction
    ekc.py              # MODIFIED: cone construction, phase_type, toric methods, diagnose_curve
    coxeter.py          # MODIFIED: flexible orbit expansion
    build_gv.py         # MODIFIED: incremental toric curve compilation, classification invariance check
    __init__.py         # MODIFIED: export new public API
```

### Pattern 1: GrossFlop Fix in classify.py

**What:** Add a `kahler_cone` and `flopped_kahler_cone` parameter path to `is_symmetric_flop` to check condition (b). [VERIFIED: codebase inspection of classify.py]

**When to use:** Called during `classify_contraction` when a wall passes the existing symmetric flop check (condition a). The flopped Kahler cone must be computed BEFORE the symmetric flop check can complete.

**Key insight:** The current `is_symmetric_flop` only checks condition (a): wall-crossed data matches Coxeter-reflected data. Condition (b) requires checking that the Coxeter reflection maps the source Kahler cone to the flopped Kahler cone. This requires access to both cones, which means `classify_contraction` (or the BFS caller) must supply them.

**Implementation approach:** Since `classify_contraction` currently doesn't have access to the Kahler cones (it works with raw arrays), the cleanest approach is:
1. Add a `kahler_cone` parameter to `classify_contraction` (optional, for backward compat)
2. When a wall passes condition (a) AND kahler_cone is provided, compute the flopped Kahler cone and check condition (b)
3. If (a) passes but (b) fails, classify as `GROSS_FLOP` instead of `SYMMETRIC_FLOP`
4. The BFS in `build_gv.py` already has access to cones and can pass them through

```python
# Condition (b) check sketch:
# Source Kahler cone rays, reflected: rays @ M^{-1} (row-vector convention)
# Check if reflected rays span the same cone as flopped Kahler cone rays
def _kahler_cones_match_under_reflection(source_kc, flopped_kc, reflection):
    """Check if M maps source Kahler cone to flopped Kahler cone."""
    M_inv = np.round(np.linalg.inv(reflection.astype(float))).astype(int)
    reflected_rays = source_kc.rays() @ M_inv
    # Check containment both ways using cone containment
    reflected_cone = cytools.Cone(rays=reflected_rays)
    # Two cones are equal iff they contain each other
    return (reflected_cone.contains(flopped_kc)
            and flopped_kc.contains(reflected_cone))
```
[VERIFIED: CYTools Cone has `contains()` method -- confirmed via `dir(cytools.Cone(...))` in conda env]

### Pattern 2: FRST Detection Trichotomy

**What:** Determine if a phase's Kahler cone corresponds to an FRST, vex triangulation, or non-inherited phase. [VERIFIED: regfans API, CONTEXT.md D-06]

**Step-by-step:**
1. Compute moving cone from charge matrix Q (already in `util.py`): `moving_cone(Q)` [VERIFIED: util.py line 45]
2. Check if phase's Kahler cone has solid intersection with moving cone (non-empty interior)
3. If no intersection: **non-inherited**
4. If intersection: find an interior point J, solve `Qx = J` for heights h
5. Create `VectorConfiguration(Q.T)` and `vc.triangulate(heights=h)` to get a `Fan` [VERIFIED: regfans API]
6. Check `fan.respects_ptconfig()` [VERIFIED: regfans API]
7. If True: **FRST** -- also store the CYTools Triangulation
8. If False: **vex**

**Cone intersection check:** CYTools Cone supports `intersection()` and `is_solid()`. [VERIFIED: `dir(cytools.Cone(...))` confirms both methods exist]

### Pattern 3: Toric Curve Enumeration (from compute_toric_curves_old)

**What:** Port the cornell-dev toric curve computation. [VERIFIED: source code read of toric.py lines 564-698]

**Key algorithm:**
1. For each 2-face of the polytope, for each induced 2-face triangulation:
   - Find all edges (pairs of points in simplices)
   - Classify edges as twoface (shared by 2 simplices) or oneface (in 1 simplex)
   - Compute double intersection numbers from polytope geometry
   - Compute normal bundles (reversed double intersection numbers)
   - Find enveloping divisors
   - Classify by enveloping divisor position (vertex, 1-face interior, 2-face interior)
   - Compute charges in GLSM basis using local intersection numbers
   - Orient using Kahler tip sign

**Critical indexing fix:** Must use `intersection_numbers(in_basis=False)` for raw point indices, NOT `in_basis=True`. [VERIFIED: memory note about March 5 2026 fix]

### Pattern 4: Incremental Compilation During BFS

**What:** As BFS discovers new FRST phases, compute toric curves incrementally. [VERIFIED: CONTEXT.md D-07]

**Data flow:**
1. BFS discovers a new phase
2. Check if phase is FRST (via trichotomy)
3. If FRST: compute induced 2-face triangulations for this FRST only
4. Deduplicate 2-face triangulations against `_seen_2face_triags` set
5. Run curve enumeration + diagnosis only for new 2-face triangulations
6. Merge into running `ToricCurveData` on CYBirationalClass

**Deduplication key:** `frozenset(frozenset(tuple(simplex) for simplex in face_triag) for face_triag in triag_list)` -- dedup at the level of individual 2-face triangulations. [VERIFIED: induced_2face_triangulations_old returns deduplicated sets]

### Anti-Patterns to Avoid
- **Using in_basis=True for toric curve intersection numbers:** This is wrong -- toric curves need raw point-index intersection numbers. [VERIFIED: March 2026 fix]
- **Creating Fan from point configuration instead of vector configuration:** VectorConfiguration takes Q.T (columns of charge matrix), not polytope points. [VERIFIED: regfans API]
- **Modifying ExtremalContraction after construction:** It's frozen by default. The `toric_origin` field must be set during construction. [VERIFIED: types.py line 384]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cone containment | Custom ray comparison | CYTools `Cone.contains()` | Handles degenerate cases, numerical tolerance |
| Cone intersection | Manual hyperplane check | CYTools `Cone.intersection()` | PPL backend handles all edge cases |
| Full-dimensionality check | Manual rank computation | CYTools `Cone.is_solid()` | Consistent with Cone API |
| FRST detection | Custom height-vector subdivision | `regfans.VectorConfiguration.triangulate(heights=h)` + `Fan.respects_ptconfig()` | Correct handling of secondary fan, numerical tolerance |
| Induced 2-face triangulations | New algorithm | Port `induced_2face_triangulations_old` directly | Already debugged, handles edge cases |
| Moving cone | New computation | Existing `cybir.core.util.moving_cone(Q)` | Already ported and tested |
| Cone construction | Manual ray collection | CYTools `Cone(rays=...)` and `Cone(hyperplanes=...)` | Handles redundant rays, normalization |

## Common Pitfalls

### Pitfall 1: Kahler Cone Comparison for GrossFlop
**What goes wrong:** Comparing Kahler cone rays directly fails due to scaling and ordering differences.
**Why it happens:** Two cones can be equal but have different ray representations (different generators, different ordering).
**How to avoid:** Use `Cone.contains()` for bidirectional containment checks. [VERIFIED: CYTools Cone has `contains()` method]
**Warning signs:** GrossFlop fix passes unit tests but fails on the 7 known misclassified polytopes.

### Pitfall 2: in_basis=False for Toric Curve Intersection Numbers
**What goes wrong:** Wrong intersection numbers lead to wrong charge vectors and wrong curve classifications.
**Why it happens:** The toric curve algorithm uses raw polytope point indices as keys into the intersection number tensor, not basis-projected indices.
**How to avoid:** Always pass `in_basis=False` to `cy.intersection_numbers()` in toric curve code.
**Warning signs:** Toric GVs don't match computed GVs for known test cases.

### Pitfall 3: VectorConfiguration vs Point Configuration
**What goes wrong:** Creating a Fan from polytope points instead of GLSM charge matrix columns gives wrong triangulation.
**Why it happens:** regfans VectorConfiguration expects the column vectors of Q (the charge matrix), which define the vector configuration in the secondary fan.
**How to avoid:** Use `VectorConfiguration(Q.T)` where Q is the GLSM charge matrix.
**Warning signs:** `respects_ptconfig()` always returns False even for known FRSTs.

### Pitfall 4: Frozen ExtremalContraction
**What goes wrong:** Cannot add `toric_origin` field after construction.
**Why it happens:** ExtremalContraction is frozen by default (`_frozen = True` in `__init__`).
**How to avoid:** Add `toric_origin` as a constructor parameter with default None.
**Warning signs:** AttributeError when trying to set toric_origin.

### Pitfall 5: Orbit Expansion with Different Reflection Sets
**What goes wrong:** Using wrong reflection set produces wrong cone (EKC vs HEKC vs full).
**Why it happens:** Currently `apply_coxeter_orbit` only uses `_sym_flop_refs`. The HEKC also needs `SU2_NONGENERIC_CS` reflections.
**How to avoid:** The `reflections` parameter in D-04 selects which set to use. Must carefully track which reflections belong to which category.
**Warning signs:** HEKC matches EKC when there are SU2_NONGENERIC_CS walls (should differ).

### Pitfall 6: Cone Union for EKC/HEKC Construction
**What goes wrong:** The EKC/HEKC is a union of (possibly overlapping) cones, not a single convex cone.
**Why it happens:** The extended Kahler cone is not generally convex -- it's a union of convex cones.
**How to avoid:** For the movable/effective/infinity cones (which ARE convex), use `Cone(rays=...)`. For EKC/HEKC, either return a list of phase Kahler cones or compute the convex hull of all rays (which gives a containing convex cone, not the exact EKC).
**Warning signs:** EKC doesn't match expected structure for known examples.

## Code Examples

### GrossFlop Detection

```python
# Source: CONTEXT.md D-01 + codebase analysis
def is_symmetric_flop(int_nums, c2, curve, gv_eff_1, gv_eff_3,
                      coxeter_ref, source_kc=None, flopped_kc=None):
    """Check symmetric flop with optional Kahler cone check."""
    # Condition (a): wall data matches under reflection
    wc_intnums = wall_cross_intnums(int_nums, curve, gv_eff_3)
    wc_c2 = wall_cross_c2(c2, curve, gv_eff_1)
    M = coxeter_ref
    cox_intnums = np.einsum("ia,jb,kc,abc->ijk", M, M, M, int_nums)
    cox_c2 = M @ c2
    
    condition_a = (np.allclose(wc_intnums, cox_intnums)
                   and np.allclose(wc_c2, cox_c2))
    
    if not condition_a:
        return False, False  # (is_symmetric, is_gross_flop)
    
    # Condition (b): Kahler cone maps correctly
    if source_kc is not None and flopped_kc is not None:
        condition_b = _kahler_cones_match(source_kc, flopped_kc, M)
        if not condition_b:
            return False, True  # Gross flop!
    
    return True, False  # True symmetric flop
```

### FRST Detection

```python
# Source: CONTEXT.md D-06 + regfans API verification
def classify_phase_type(kahler_cone, moving_cone, Q):
    """Classify phase as FRST, vex, or non-inherited."""
    from regfans import VectorConfiguration
    
    # Check solid intersection with moving cone
    intersection = kahler_cone.intersection(moving_cone)
    if not intersection.is_solid():
        return "non_inherited", None
    
    # Find interior point and lift to heights
    J = intersection.tip_of_stretched_cone(1)
    # Solve Qx = J for height vector h
    h = np.linalg.lstsq(Q, J, rcond=None)[0]
    
    # Subdivide vector configuration
    vc = VectorConfiguration(Q.T)
    try:
        fan = vc.triangulate(heights=h)
    except Exception:
        return "non_inherited", None
    
    if fan.respects_ptconfig():
        return "frst", fan
    else:
        return "vex", fan
```

### CoxeterGroup Dataclass

```python
# Source: CONTEXT.md D-03
@dataclass(frozen=True)
class CoxeterGroup:
    """Coxeter group data from orbit expansion."""
    factors: tuple  # tuple of (family: str, rank: int, order: int)
    
    @property
    def order(self):
        result = 1
        for _, _, o in self.factors:
            result *= o
        return result
    
    @property
    def rank(self):
        return sum(r for _, r, _ in self.factors)
    
    def __repr__(self):
        parts = []
        for family, rank, _ in self.factors:
            # Unicode subscript digits
            sub = str(rank).translate(str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉"))
            parts.append(f"{family}{sub}")
        return " x ".join(parts)  # using multiplication sign
```

### Induced 2-Face Triangulations

```python
# Source: cornell-dev/lib_axion/cytools_ext/polytopeface_ext.py lines 275-319
# Port of induced_2face_triangulations_old
def induced_2face_triangulations(polytope, triangulations):
    """Compute induced 2-face triangulations from a list of FRSTs."""
    import itertools
    twofaces = [set(f.points(as_indices=True)) for f in polytope.faces(2)]
    triangulations_2faces = [[] for _ in twofaces]
    
    for t in triangulations:
        # Get 4-simplices, drop origin (index 0)
        four_simplices = np.delete(t.simplices().T, 0, 0).T
        # Extract all 3-subsets (potential 2-face simplices)
        three_simplices = {
            tuple(x) for s in four_simplices
            for x in itertools.combinations(s, 3)
        }
        three_simplices = [set(s) for s in three_simplices]
        
        # Assign to 2-faces
        assignments = [
            np.where([len(s.intersection(f)) == 3 for f in twofaces])[0]
            for s in three_simplices
        ]
        # Keep only simplices assigned to exactly one 2-face
        valid = np.where([len(a) == 1 for a in assignments])[0]
        face_assigns = np.array([assignments[i][0] for i in valid])
        valid_simps = np.array([np.sort(list(three_simplices[i])) for i in valid])
        
        induced = [valid_simps[face_assigns == i] for i in range(len(twofaces))]
        for i in range(len(twofaces)):
            triangulations_2faces[i].append(induced[i])
    
    # Deduplicate
    deduped = [
        set(frozenset(tuple(k) for k in j) for j in face_triags)
        for face_triags in triangulations_2faces
    ]
    return [[np.array(list(j)) for j in list(s)] for s in deduped]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| is_symmetric_flop checks only condition (a) | Must also check condition (b): Kahler cone mapping | Phase 6 (this phase) | Fixes 7/243 h11=3 misclassifications |
| apply_coxeter_orbit uses only sym_flop_refs | Flexible: ekc/hekc/all reflection sets | Phase 6 (this phase) | Users can construct EKC, HEKC, or full orbit |
| Coxeter type stored as raw list | CoxeterGroup frozen dataclass | Phase 6 (this phase) | Clean API with properties and repr |
| No toric curve computation | Full toric curve pipeline with FRST detection | Phase 6 (this phase) | Cross-validation of GV-based results |

## Key Technical Details

### Moving Cone Already Implemented
`moving_cone(Q)` in `cybir/core/util.py` (line 45) is already ported from `cornell-dev/projects/Elijah/misc.py:595`. It takes the charge matrix Q and returns a CYTools Cone. [VERIFIED: codebase]

### CYTools Cone API
- `Cone(rays=...)` -- construct from generators [VERIFIED: tested]
- `Cone(hyperplanes=...)` -- construct from inequalities [VERIFIED: tested]
- `cone.rays()` -- get extremal rays [VERIFIED: tested]
- `cone.dual()` -- dual cone [VERIFIED: tested]
- `cone.tip_of_stretched_cone(c)` -- interior point [VERIFIED: tested]
- `cone.intersection(other_cone)` -- cone intersection [VERIFIED: confirmed via `dir(cytools.Cone(...))` in conda env]
- `cone.is_solid()` -- check full-dimensionality [VERIFIED: confirmed via `dir(cytools.Cone(...))` in conda env]
- `cone.contains(other_cone)` -- check if cone contains another [VERIFIED: confirmed via `dir(cytools.Cone(...))` in conda env]
- `cone.is_full_dimensional()` -- alias for is_solid [VERIFIED: confirmed via `dir(cytools.Cone(...))` in conda env]

### regfans API
- `VectorConfiguration(vectors)` -- construct from row vectors [VERIFIED: tested]
- `vc.triangulate(heights=h)` -- subdivide by heights, returns Fan [VERIFIED: tested]
- `fan.respects_ptconfig()` -- check if fan is a point-config subdivision [VERIFIED: help output]

### ExtremalContraction Modification
To add `toric_origin`, must add it as a constructor parameter since the object is frozen. The `_frozen = True` is set in `__init__`, so we need to set `_toric_origin` before the freeze line. [VERIFIED: types.py line 384]

### GROSS_FLOP Enum Member
Add to ContractionType enum and update both notation dicts. Gross flops are generic flops that happen to have matching wall data under reflection but different Kahler cones. They do NOT contribute to orbit expansion. [VERIFIED: CONTEXT.md D-01]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A4 | `is_symmetric_flop` return type can change to tuple | Code Examples | Would need separate function instead |

**All previous assumptions (A1-A3) have been resolved:**
- A1 (CYTools Cone `intersection()`): VERIFIED via `dir(cytools.Cone(...))` in conda env
- A2 (CYTools Cone `is_solid()`): VERIFIED via `dir(cytools.Cone(...))` in conda env
- A3 (CYTools Cone `contains()`): VERIFIED via `dir(cytools.Cone(...))` in conda env

## Open Questions (RESOLVED)

1. **Cone equality check for GrossFlop** (RESOLVED)
   - CYTools Cone has `contains()` method (verified via `dir(cytools.Cone(...))`).
   - Use bidirectional `contains()`: `reflected_cone.contains(flopped_kc) and flopped_kc.contains(reflected_cone)`.
   - No fallback needed -- PPL backend handles all edge cases.

2. **Shared edges across 2-face triangulations** (RESOLVED)
   - Empirical verification will be added as an acceptance criterion in Plan 03 tests.
   - Plan 03 Task 2 test suite includes a test checking that shared edges across triangulations produce consistent curve classes and diagnoses.
   - If inconsistencies are found during testing, the deduplication strategy will be adjusted.

3. **EKC/HEKC cone union return type** (RESOLVED)
   - Decision: `extended_kahler_cone()` returns the convex hull of all phase Kahler cone rays as a single `cytools.Cone` (outer approximation).
   - Users who need the exact non-convex union can iterate `self.phases` and access individual Kahler cones.
   - `hyperextended_kahler_cone()` delegates to `extended_kahler_cone()` -- the distinction is in which orbit expansion was run beforehand ('ekc' vs 'hekc').
   - Documented in Plan 05 cone construction docstrings.

## Sources

### Primary (HIGH confidence)
- cybir codebase inspection: types.py, classify.py, ekc.py, coxeter.py, build_gv.py, util.py, __init__.py
- cornell-dev source: lib/geom/curves/toric.py (compute_toric_curves_old), lib_axion/cytools_ext/polytopeface_ext.py (induced_2face_triangulations_old), projects/Elijah/misc.py (moving_cone)
- regfans API: Fan.respects_ptconfig(), VectorConfiguration.triangulate() -- verified via conda run help()
- CYTools Cone API: verified via conda run interactive test AND `dir()` inspection confirming `contains`, `intersection`, `is_solid` methods
- 06-CONTEXT.md: all 14 decisions (D-01 through D-14)

### Secondary (MEDIUM confidence)
- Memory notes: project_grossflop_and_ekc_physics.md, project_toric_curves_integration.md -- developer insights from Phase 5 validation

## Metadata

**Confidence breakdown:**
- GrossFlop fix: HIGH -- exact issue and fix well-documented in memory notes and CONTEXT.md
- Toric curves port: HIGH -- source code fully read and understood, only porting
- FRST detection: HIGH -- regfans API verified, CYTools Cone API (intersection, is_solid) confirmed
- Cone construction: HIGH -- CYTools Cone API fully verified (contains, intersection, is_solid, rays, dual, hyperplanes)
- CoxeterGroup dataclass: HIGH -- straightforward frozen dataclass

**Research date:** 2026-04-19
**Valid until:** 2026-05-19 (stable domain, no external dependencies changing)
