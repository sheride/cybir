# Phase 3: Pipeline & Integration - Research

**Researched:** 2026-04-12
**Domain:** BFS pipeline orchestration, CYTools monkey-patching, Sphinx documentation
**Confidence:** HIGH

## Summary

Phase 3 wires the Phase 1-2 math modules (classify, flop, gv, util, graph, types) into a complete EKC construction pipeline. The core work is: (1) a BFS loop that iterates over undiagnosed Mori cone walls, classifies each, flops when appropriate, and deduplicates phases by their curve-sign dictionaries; (2) Weyl orbit expansion that applies symmetric-flop reflections to discover phases beyond the fundamental domain; (3) a `CYBirationalClass` orchestrator class with a read-only post-construction API; (4) monkey-patching CYTools `Invariants`, `CalabiYau`, and `Polytope` classes; and (5) Sphinx documentation mirroring the dbrane-tools pattern.

The original `extended_kahler_cone.py` (~2700 lines) contains a working but monolithic implementation of all of this. The key translation challenge is extracting the BFS loop and Weyl expansion into clean builder functions that operate on the already-refactored cybir types (`CalabiYauLite`, `ExtremalContraction`, `CYGraph`), while preserving the exact algorithmic behavior -- particularly the curve-sign deduplication, wall re-encounter logic, and GV series management through flops.

**Primary recommendation:** Implement the BFS builder as a standalone `build_gv.py` module that accepts a `CYBirationalClass` and mutates it in-place, keeping the orchestrator class (`ekc.py`) focused on the result container and query API. The Weyl expansion goes in a separate `weyl.py`. Monkey-patching goes in `patch.py` with an explicit `patch_cytools()` activation function.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** `ExtremalContraction` drops `start_phase`/`end_phase` fields. The graph encodes topology -- `CYGraph.add_contraction(contraction, phase_a, phase_b)` takes both phases as arguments. `CYGraph` provides `phases_adjacent_to(contraction)` and `contractions_from(phase_label)` for queries.
- **D-02:** Curves are stored in canonical form (first nonzero component positive, via `normalize_curve`). When accessed from a specific phase's perspective (`contractions_from`), curves are oriented inward to that phase's Kahler cone. The sign flip is edge metadata stored on the graph.
- **D-03:** Kahler cone face geometric data (normal vector, facet data) is monkey-patched onto CYTools `Cone` objects rather than duplicated on `ExtremalContraction`. The contraction holds a reference to the cone face.
- **D-04:** Drop `Circuit`, `start_circuit`, `end_circuit` entirely -- toric pipeline is v2.
- **D-05:** BFS tracking data (explored set, visit order) is kept on the orchestrator as a build log, persists after construction for debugging.
- **D-06:** Cone generators (`coxeter_refs`, `sym_flop_refs`, `infinity_cone_gens`, `eff_cone_gens`) live on the orchestrator (`CYBirationalClass`), not on the graph.
- **D-07:** Rename `ExtendedKahlerCone` to `CYBirationalClass`. This is the main result/orchestrator object.
- **D-08:** `CYBirationalClass` holds: `CYGraph` (phases + contractions), reference to CYTools `CalabiYau` (the root), cone generators, Weyl expansion data, read-only query API.
- **D-09:** Step-by-step construction API: `__init__` -> `setup_root` -> `construct_phases` -> `expand_weyl`.
- **D-10:** Convenience classmethod `CYBirationalClass.from_gv(cy, max_deg=10)` runs all steps and returns the populated object.
- **D-11:** Construction logic lives in a separate builder module (`build_gv.py`), not in the class itself.
- **D-12:** Post-construction read-only API: `ekc.phases`, `ekc.contractions`, `ekc.coxeter_matrix`, `ekc.graph`, etc.
- **D-13:** Weyl expansion is a separate step from BFS construction.
- **D-14:** `expand_weyl` can be called lazily.
- **D-15:** Three levels of patching: `CalabiYau.birational_class()`, `Invariants` (GV helpers), `Polytope.birational_class()`. Skip `Triangulation` level.
- **D-16:** Patches activated by explicit `cybir.patch_cytools()` call, not on import.
- **D-17:** Version guards on all patches.
- **D-18:** Sphinx setup mirrors dbrane-tools `conf.py` pattern.
- **D-19:** Two example notebooks: h11=2 and h11=3. Pre-executed, not executed during doc build.
- **D-20:** API reference auto-generated from numpy-style docstrings.

### Claude's Discretion
- Exact builder module name and internal structure
- Specific CYTools Invariants methods to patch (based on what the builder actually needs)
- Sphinx conf.py details and notebook content structure
- BFS implementation details (queue type, deduplication strategy)
- `CYGraph` API additions needed for `contractions_from` and curve orientation

### Deferred Ideas (OUT OF SCOPE)
- Toric pipeline (`from_toric` classmethod, `build_toric.py`) -- v2
- `Circuit` class for toric fan data -- v2
- `Triangulation.birational_class()` convenience patch -- low value
- Serialization/caching of EKC results (ENH-01)
- Narrative "how the algorithm works" documentation page
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PIPE-01 | `construct_phases` BFS loop with dictionary-keyed phase deduplication | BFS Architecture section: curve-sign dedup, wall re-encounter, queue management |
| PIPE-02 | Weyl orbit expansion for hyperextended cone | Weyl Expansion section: reflection application, `sym_flop_cy` translation |
| PIPE-03 | Clean read-only post-construction API | CYBirationalClass API section: property design, freeze pattern |
| PIPE-04 | Verbose logging replacing scattered print statements | Logging pattern section: Python `logging` module approach |
| INTG-01 | CYTools Invariants monkey-patching (gv_series, gv_eff, ensure_nilpotency, flop_gvs) | Monkey-Patching section: exact methods needed, Invariants internal API |
| INTG-03 | Monkey-patching at Polytope, CalabiYau levels | Monkey-Patching section: entry points, delegation to `from_gv` |
| INTG-04 | Version guards on monkey-patches | Monkey-Patching section: version detection approach |
| PKG-02 | Sphinx documentation with equation references | Documentation section: conf.py pattern, RST structure |
| PKG-03 | Example notebooks for h11=2,3 | Documentation section: notebook structure, myst-nb integration |
</phase_requirements>

## Standard Stack

### Core (already in pyproject.toml / cytools env)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | 2.3.5 (env) | Array operations throughout pipeline | Already used in all Phase 1-2 modules |
| scipy | 1.17.0 (env) | null_space in classify, ConvexHull | Already used |
| networkx | >=3.0 | CYGraph backing store | Already in pyproject.toml and CYGraph |
| cytools | (local) | Root CY data, Invariants for GV | The package being extended |

### Documentation (already in cytools env)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Sphinx | 9.1.0 (env) | Doc generation | `documentation/` build |
| sphinx-book-theme | (env) | Theme | Same as dbrane-tools |
| sphinx-autodoc-typehints | (env) | Type hints in docs | Auto API docs |
| sphinx-copybutton | (env) | Code block copy button | UX |
| sphinx_design | (env) | Admonitions, cards | Math callouts |
| sphinx-togglebutton | (env) | Collapsible sections | Long derivations |
| myst-nb | (env) | Notebook integration | h11=2 and h11=3 notebooks |

### New Dependencies
None needed. All required packages are already in the cytools conda environment and pyproject.toml. [VERIFIED: pyproject.toml and conda env inspection]

## Architecture Patterns

### New Module Layout
```
cybir/
  core/
    ekc.py          # CYBirationalClass (orchestrator + read-only API)
    build_gv.py     # BFS construction logic (builder pattern)
    weyl.py         # Weyl orbit expansion
    patch.py        # CYTools monkey-patching
    types.py        # (existing) CalabiYauLite, ExtremalContraction, etc.
    graph.py        # (existing) CYGraph -- needs API additions
    classify.py     # (existing)
    flop.py         # (existing)
    gv.py           # (existing)
    util.py         # (existing)
  __init__.py       # Re-export CYBirationalClass, patch_cytools
documentation/
  source/
    conf.py
    index.rst
    cybir.rst        # Top-level module page
    cybir.core.rst   # Core subpackage
    cybir.core.ekc.rst
    cybir.core.build_gv.rst
    ... (one RST per module)
  Makefile
notebooks/
  h11_2_walkthrough.ipynb
  h11_3_walkthrough.ipynb
```

### Pattern 1: Builder Separation (D-11)

The orchestrator class (`CYBirationalClass`) is the result container. The builder module (`build_gv.py`) contains the BFS algorithm and mutates the orchestrator. This separation means:

- `CYBirationalClass.__init__` is cheap (wraps CY, creates empty graph)
- `build_gv.setup_root()` computes GVs and creates the root phase
- `build_gv.construct_phases()` runs the BFS loop
- `weyl.expand_weyl()` runs Weyl orbit expansion

```python
# Source: D-09 from CONTEXT.md, original construct_phases pattern
class CYBirationalClass:
    def __init__(self, cy):
        self._cy = cy
        self._graph = CYGraph()
        self._root = None
        self._coxeter_refs = set()
        self._sym_flop_refs = set()
        self._infinity_cone_gens = set()
        self._eff_cone_gens = set()
        self._build_log = []  # D-05: BFS tracking data
        self._constructed = False
        self._weyl_expanded = False

    def setup_root(self, max_deg=10):
        from .build_gv import setup_root
        setup_root(self, max_deg=max_deg)

    def construct_phases(self, verbose=True, limit=100):
        from .build_gv import construct_phases
        construct_phases(self, verbose=verbose, limit=limit)
        self._constructed = True

    def expand_weyl(self):
        from .weyl import expand_weyl
        expand_weyl(self)
        self._weyl_expanded = True

    @classmethod
    def from_gv(cls, cy, max_deg=10, verbose=True, limit=100):
        ekc = cls(cy)
        ekc.setup_root(max_deg=max_deg)
        ekc.construct_phases(verbose=verbose, limit=limit)
        return ekc

    # Read-only API (D-12)
    @property
    def phases(self):
        return self._graph.phases

    @property
    def contractions(self):
        return self._graph.contractions

    @property
    def coxeter_matrix(self):
        from .util import coxeter_matrix
        refs = list(self._coxeter_refs)
        if not refs:
            return None
        return coxeter_matrix([np.array(r) for r in refs])
```

### Pattern 2: BFS with Curve-Sign Deduplication

The original code's core deduplication mechanism uses a "curve_signs" dictionary: for each phase, record the sign of the Kahler cone tip dotted with each known flop curve. Two phases are the same if and only if they have the same curve-sign dictionary. This is faster and more robust than comparing intersection numbers.

```python
# Source: original extended_kahler_cone.py lines 860-975
# Key insight: deduplication uses curve_signs dict, NOT int_nums comparison

def construct_phases(ekc, verbose=True, limit=100):
    """BFS loop: process undiagnosed walls, flop, deduplicate."""
    # walls is a list of (contraction_data, source_phase_label) tuples
    # that haven't been classified yet
    undiagnosed = deque(walls_from_root)

    while undiagnosed:
        if ekc._graph.num_phases >= limit:
            break

        wall_curve, source_label = undiagnosed.popleft()
        source_phase = ekc._graph.get_phase(source_label)

        # Classify the wall
        result = classify_contraction(
            source_phase.int_nums, source_phase.c2,
            wall_curve, gv_series_for_curve)

        ctype = result["contraction_type"]

        # Terminal walls: asymptotic, CFT, su(2)
        if ctype in (ASYMPTOTIC, CFT, SU2):
            # Record contraction, accumulate generators
            ...
            continue

        # Symmetric flops: record but don't explore (D-13, ignore_sym=True)
        if ctype == SYMMETRIC_FLOP:
            # Record for Weyl expansion later
            ...
            continue

        # Generic flop: construct flopped phase, check if new
        flopped_phase = flop_phase(source_phase, wall_curve, gv_series)

        # Normalize curve for canonical comparison
        tuple_curve = normalize_curve(wall_curve)

        # Update curve signs for all existing phases if new curve
        if tuple_curve not in known_curves:
            update_all_curve_signs(ekc, tuple_curve)

        flopped_signs = compute_curve_signs(flopped_phase, known_curves)
        existing_idx = find_matching_phase(ekc, flopped_signs)

        if existing_idx is None:
            # New phase: add to graph, enqueue its walls
            ekc._graph.add_phase(flopped_phase)
            ekc._graph.add_contraction(contraction, source_label, new_label)
            # Enqueue walls of new phase, merging with already-known walls
            for new_wall in flopped_phase_walls:
                if new_wall not in known_walls:
                    undiagnosed.append(new_wall)
                else:
                    # Re-encountered wall: link to existing
                    ...
        else:
            # Existing phase: just add edge
            ekc._graph.add_contraction(contraction, source_label, existing_label)
```

### Pattern 3: CYGraph API Additions (D-01, D-02)

The current `CYGraph.add_contraction(contraction)` reads `contraction.start_phase` and `contraction.end_phase`. Per D-01, this must change to `add_contraction(contraction, phase_a, phase_b)` with the graph storing the topology. Curve orientation (D-02) is stored as edge metadata.

```python
# Required CYGraph additions
def add_contraction(self, contraction, phase_a_label, phase_b_label,
                    curve_sign_a=1, curve_sign_b=-1):
    """Add contraction between two phases with curve orientation metadata."""
    self._graph.add_edge(
        phase_a_label, phase_b_label,
        contraction=contraction,
        curve_sign_a=curve_sign_a,   # +1 = inward to phase_a
        curve_sign_b=curve_sign_b,   # -1 = outward from phase_b's perspective
    )

def contractions_from(self, label):
    """All contractions adjacent to a phase, with curves oriented inward."""
    results = []
    for neighbor in self._graph.neighbors(label):
        edge = self._graph.edges[label, neighbor]
        contraction = edge["contraction"]
        # Determine sign for this phase
        if label < neighbor:  # consistent ordering
            sign = edge["curve_sign_a"]
        else:
            sign = edge["curve_sign_b"]
        results.append((contraction, sign))
    return results

def phases_adjacent_to(self, contraction):
    """Return the two phases connected by this contraction."""
    for u, v, data in self._graph.edges(data=True):
        if data["contraction"] is contraction:
            return (self.get_phase(u), self.get_phase(v))
    return None
```

### Pattern 4: GV Invariants Management Through Flops

The original code's most complex aspect is managing GV invariants across flops. The CYTools `Invariants` object stores a `_charge2invariant` dict keyed by curve charges. When flopping across a curve C, the GV invariants for curves aligned/anti-aligned with C must be negated (the curve reverses direction). The original tracks this via:

1. `Invariants.flop_curves` -- list of curves that have been flopped
2. `Invariants.precompose` -- basis change matrix from current to original topology
3. `Invariants.gv_incl_flop(curve)` -- looks up GV, flipping sign for flopped curves

For cybir, the builder must:
- Keep a reference to the original `Invariants` object (from the root CY)
- Track the accumulated flop chain for each phase
- When querying GVs for a wall in a flopped phase, compose the flop transformations

```python
# Source: original lines 2655-2692
# The Invariants object is cloned and flop_curves updated at each flop
# cybir should replicate this exactly

def _get_gv_series_for_wall(gv_invariants, curve, flop_chain):
    """Get GV series for a curve in a phase reached by a chain of flops.

    Parameters
    ----------
    gv_invariants : cytools.Invariants
        The root Invariants object (from setup_root).
    curve : ndarray
        The wall curve in the current phase's basis.
    flop_chain : list of ndarray
        Curves that were flopped to reach this phase from the root.
    """
    # Apply flop_gvs to get Invariants in this phase's topology
    gvs = gv_invariants.flop_gvs(flop_chain)
    # Then extract the series
    return gvs.gv_series(curve)
```

### Anti-Patterns to Avoid

- **Computing GVs from scratch for each phase:** The original propagates GVs through flops. Do NOT recompute `cy.compute_gvs()` for each flopped phase -- use `flop_gvs` to transform the existing Invariants.
- **Comparing phases by intersection numbers:** Use the curve-sign dictionary for deduplication. `np.allclose` on intersection numbers is fragile and slow.
- **Storing topology on ExtremalContraction:** Per D-01, the graph owns the topology. ExtremalContraction is a data container only.
- **Mutating frozen CalabiYauLite objects:** Phases are frozen after construction. The builder must set all fields before calling `freeze()`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Phase deduplication | Custom hash function on int_nums | Curve-sign dictionary matching (original algorithm) | Numerically exact, handles floating-point issues |
| GV series through flops | Manual charge2invariant dict manipulation | CYTools `Invariants.flop_gvs()` (monkey-patched) | Already handles sign flips, basis changes, nilpotency checks |
| Mori cone of flopped phase | Manual cone computation | `Invariants.cone_incl_flop()` (monkey-patched) | Handles flop curve sign reversal in cone generators |
| Sphinx doc structure | Manual HTML generation | `sphinx.ext.autodoc` + `autosummary` with RST templates | Standard approach, auto-generates from docstrings |
| Graph adjacency queries | Custom adjacency lists | `networkx.Graph` (already used in CYGraph) | Mature, handles all graph operations |

**Key insight:** The GV invariant management through flops is the most subtle part. The original code's `flop_gvs`/`gv_incl_flop`/`cone_incl_flop` methods on the `Invariants` object encode non-trivial sign-flipping logic. Monkey-patching these onto the CYTools `Invariants` class (INTG-01) is essential -- do not attempt to reimplement this from scratch.

## BFS Algorithm Details

### The Original Algorithm (lines 871-1073)

The BFS loop in the original works as follows:

1. **Initialize:** `setup_root()` creates the root CY from `polytope.triangulate().cy()`, computes GVs, creates walls from Mori cone generators
2. **Loop:** While undiagnosed walls exist and phase count < limit:
   a. Pop next undiagnosed wall
   b. Call `wall.diagnose()` which classifies it (asymptotic/CFT/su2/sym_flop/flop)
   c. If terminal (asymptotic, CFT, su2): record and continue
   d. If symmetric flop and `ignore_sym=True`: record reflection, continue
   e. If generic flop:
      - Normalize curve via `normalize_curve`
      - If new curve, update `curve_signs` for all existing CYs
      - Construct flopped CY via `wall.flop_cy()`
      - Compute flopped CY's `curve_signs`
      - Check if curve_signs match any existing CY
      - If new: add CY, merge walls (re-encounter logic)
      - If existing: link edge only
3. **Post-loop:** Accumulate `infinity_cone_gens`, `eff_cone_gens`, `coxeter_refs`, `sym_flop_refs`, and build `eff_cone`

### Curve-Sign Deduplication Details

```python
# Source: original lines 860-870, 931-943
# Each CY has a dict: {normalized_curve_tuple: +1 or -1}
# The sign = np.sign(cy.tip @ curve) where tip = interior point of Kahler cone

# When a new flop curve is discovered, ALL existing CYs get updated:
def update_curve_signs(ekc, tuple_curve):
    for cy in ekc.cys:
        cy.curve_signs[tuple_curve] = np.sign(cy.tip @ tuple_curve)

# Deduplication: find existing CY with same curve_signs
index = safe_index([cy.curve_signs for cy in ekc.cys], flopped_cy.curve_signs)
```

The "tip" is an interior point of the Kahler (dual Mori) cone, computed via `cone.tip_of_stretched_cone()`. For cybir, each `CalabiYauLite` needs either a `tip` attribute or the Kahler cone from which the tip can be computed.

### Wall Re-Encounter Logic

When a flopped phase has walls that match already-known walls, the original links them rather than creating duplicates:

```python
# Source: original lines 954-965
for n, wall in enumerate(flopped_cy.walls):
    wall_index = safe_index(self.walls, wall)
    if wall_index is None:
        self.walls.append(wall)
    else:
        flopped_cy.walls[n] = self.walls[wall_index]
        if self.walls[wall_index].end_cy is None:
            self.walls[wall_index].end_cy = flopped_cy
```

In cybir, "wall equality" should be based on the Facet (cone face) equality -- two walls from different phases that share the same cone face are the same wall.

### Root Phase Setup

The original's `setup_root` does:
1. `polytope.triangulate().cy()` to get a CalabiYau
2. `cy.mori_cone_cap(in_basis=True).find_grading_vector()` for GV grading
3. `cy.compute_gvs(grading_vec=grading, max_deg=max_deg)` for Invariants
4. Sets up `gvs.flop_curves = []` and `gvs.precompose = np.eye(h11)`
5. Creates a `CY_GV` wrapping the CY data

For cybir, `setup_root` should:
1. Extract `int_nums = cy.intersection_numbers(in_basis=True, format='dense')`
2. Extract `c2 = cy.second_chern_class(in_basis=True)`
3. Get Kahler cone: `cy.kahler_cone()` or `cy.mori_cone().dual()`
4. Get Mori cone generators for walls
5. Compute GVs and store the `Invariants` object
6. Create root `CalabiYauLite` with all this data

## Weyl Expansion Details

The Weyl expansion (original lines 977-1035) works as follows:

1. Mark all existing phases as `fund=True` (fundamental domain)
2. For each phase in the fundamental domain, for each symmetric-flop reflection M:
   a. Apply `sym_flop_cy(int_nums, c2, kahler_cone, M)` to create reflected phase
   b. The reflected phase has `int_nums' = M^T @ int_nums @ M @ M @ M` (einsum) and `c2' = M @ c2`
   c. The Kahler cone rays are transformed: `new_rays = old_rays @ M`
   d. Check if reflected phase is new (by Mori cone comparison)
   e. If new: add phase, process its walls, inherit wall categories from parent
3. Reflected walls inherit their category from the original wall that maps to them under M

```python
# Source: original lines 268-276
def sym_flop_cy(int_nums, c2, kc, cox_ref):
    new_kc = cytools.Cone(rays=kc.rays() @ np.round(cox_ref).astype(int))
    return CY_GV(
        int_nums=np.einsum('abc,xa,yb,zc', int_nums, cox_ref, cox_ref, cox_ref),
        c2=np.einsum('a,xa', c2, cox_ref),
        mori=new_kc.dual())
```

For cybir's `weyl.py`:
- `expand_weyl(ekc)` iterates over fundamental-domain phases and sym_flop reflections
- Creates new `CalabiYauLite` objects with transformed data
- Adds them to the graph with appropriate contraction edges
- Inherits wall classifications from parent phases

**Known quality issue (from STATE.md):** The Weyl expansion in the original has known quality issues. The planner should ensure careful review and testing.

## Monkey-Patching Details (INTG-01, INTG-03, INTG-04)

### Methods to Patch onto CYTools Invariants

Based on reading the original code (lines 2530-2692), the builder needs these methods on `Invariants`:

| Method | Purpose | Original Line |
|--------|---------|---------------|
| `copy()` | Deep-copy Invariants object (needed for flop propagation) | 2635-2647 |
| `flop_gvs(curves)` | Clone Invariants with flop-curve tracking updated | 2655-2670 |
| `gv_incl_flop(curve, check_deg)` | Look up GV accounting for flop sign flips and basis change | 2672-2684 |
| `gv_series(curve)` | Extract GV series [GV(C), GV(2C), ...] using `gv_incl_flop` | 2594-2612 |
| `ensure_nilpotency(curve)` | Recompute GVs to higher degree until series terminates | 2530-2590 |
| `cone_incl_flop()` | Mori cone with flop-curve signs corrected | 2686-2692 |

The CYTools `Invariants.__init__` accepts: `invariant_type`, `charge2invariant` (dict or coo), `grading_vec`, `cutoff`, `calabiyau`, `basis`. [VERIFIED: CYTools source inspection]

The existing `Invariants` has methods: `charges`, `cone`, `coo`, `cutoff`, `dok`, `grading_vec`, `gv`, `gvs`, `gw`, `gws`, `invariant`, `size`. [VERIFIED: CYTools env inspection]

Key implementation detail: the monkey-patched methods add attributes (`flop_curves`, `precompose`) to `Invariants` instances that don't exist in the original class. The `copy()` method must deep-copy these custom attributes.

### Entry-Point Patches

```python
# CalabiYau.birational_class() -- D-15
def _cy_birational_class(self, **kwargs):
    from cybir.core.ekc import CYBirationalClass
    return CYBirationalClass.from_gv(self, **kwargs)

# Polytope.birational_class() -- D-15
def _poly_birational_class(self, **kwargs):
    return self.triangulate().get_cy().birational_class(**kwargs)
```

### Version Guards (INTG-04)

CYTools doesn't expose `__version__`. Use structural checks instead:

```python
import warnings

def patch_cytools():
    """Patch CYTools classes with cybir methods."""
    try:
        from cytools.calabiyau import CalabiYau, Invariants
        from cytools.polytope import Polytope
    except ImportError:
        warnings.warn("CYTools not available; skipping monkey-patches")
        return

    # Verify Invariants has expected API
    if not hasattr(Invariants, 'gv'):
        warnings.warn("CYTools Invariants missing 'gv' method; skipping patches")
        return

    # Check Invariants.__init__ signature compatibility
    import inspect
    sig = inspect.signature(Invariants.__init__)
    required_params = {'invariant_type', 'charge2invariant'}
    if not required_params.issubset(sig.parameters.keys()):
        warnings.warn("CYTools Invariants.__init__ signature incompatible")
        return

    # Apply patches
    Invariants.copy = _invariants_copy
    Invariants.flop_gvs = _invariants_flop_gvs
    Invariants.gv_incl_flop = _invariants_gv_incl_flop
    Invariants.gv_series_cybir = _invariants_gv_series  # avoid name collision
    Invariants.ensure_nilpotency = _invariants_ensure_nilpotency
    Invariants.cone_incl_flop = _invariants_cone_incl_flop

    CalabiYau.birational_class = _cy_birational_class
    Polytope.birational_class = _poly_birational_class
```

Note: The original patches `gv_series` directly onto `Invariants`, but CYTools may already have methods with similar names (`gvs`). Use `gv_series_cybir` or check for conflicts. [ASSUMED]

### ExtremalContraction Changes (D-01)

The current `ExtremalContraction` has `start_phase` and `end_phase` fields. Per D-01, these must be removed. The constructor changes to:

```python
class ExtremalContraction:
    def __init__(self, flopping_curve, contraction_type=None,
                 gv_invariant=None, effective_gv=None,
                 zero_vol_divisor=None, coxeter_reflection=None,
                 gv_series=None, gv_eff_1=None,
                 cone_face=None):  # D-03: reference to cone face
        # Remove start_phase, end_phase
        # Add cone_face reference
```

This is a breaking change for existing tests that use `start_phase`/`end_phase` -- the Phase 2 integration tests in `test_integration.py` don't use these (they test standalone functions), but `test_graph.py` may need updating.

## Logging Pattern (PIPE-04)

Replace `print` statements with Python `logging`:

```python
import logging

logger = logging.getLogger("cybir")

# In build_gv.py:
def construct_phases(ekc, verbose=True, limit=100):
    if verbose:
        logging.basicConfig(level=logging.INFO)

    while undiagnosed:
        logger.info("Phases so far: %d", ekc._graph.num_phases)
        ...
        if ctype == ContractionType.ASYMPTOTIC:
            logger.info("Found end: %s, asymptotic", curve)
        elif ctype == ContractionType.FLOP:
            logger.info("New flop: %s", curve)
```

The `verbose` parameter controls whether logging is enabled, maintaining backward compatibility with the original's print-statement interface.

## Documentation Pattern

### Sphinx Configuration

Mirror the dbrane-tools `conf.py` exactly [VERIFIED: `/Users/elijahsheridan/Research/string/cytools_code/dbrane-tools/documentation/source/conf.py`]:

```python
# documentation/source/conf.py
import os, sys
sys.path.insert(0, os.path.abspath('../../'))

project = "cybir"
copyright = "2026, Elijah Sheridan"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx_autodoc_typehints",
    "sphinx_togglebutton",
    "sphinx_design",
    "myst_nb",
]

source_suffix = [".rst", ".ipynb", ".md"]
autodoc_default_flags = ["members"]
autosummary_generate = True
napoleon_use_rtype = False
napoleon_custom_sections = [('Returns', 'params_style')]

html_theme = "sphinx_book_theme"
nb_execution_mode = "off"
myst_enable_extensions = ["dollarmath"]
myst_dmath_double_inline = True
add_module_names = False
toc_object_entries_show_parents = "hide"
```

### RST Structure

One RST per module, following dbrane-tools pattern:
```rst
cybir.core.ekc
==============

.. automodule:: cybir.core.ekc
   :members:
   :undoc-members:
   :show-inheritance:
```

### Notebook Structure (D-19)

Notebooks are pre-executed and committed. The build uses `nb_execution_mode = "off"`. Structure:

**h11=2 walkthrough:**
1. Import cybir and CYTools, load an h11=2 polytope
2. Construct `CYBirationalClass.from_gv(cy)`
3. Inspect `ekc.phases`, `ekc.contractions`
4. Show contraction types and GV data
5. Display the phase graph structure
6. Show Coxeter matrix and reflections

**h11=3 walkthrough:**
1. Same flow with a more complex example
2. Multiple flop phases, Weyl expansion
3. Show the hyperextended cone

## Common Pitfalls

### Pitfall 1: GV Series Through Flop Chains

**What goes wrong:** GV invariants for curves in a flopped phase are incorrect because the flop-curve sign flip wasn't applied.
**Why it happens:** When you flop across curve C, the GV invariants for C (and its multiples) must be looked up with the sign flipped. The `flop_gvs`/`gv_incl_flop` mechanism handles this, but only if the flop chain is correctly tracked.
**How to avoid:** Always propagate the `Invariants` object through `flop_gvs([curve])` at each flop. Never look up GVs directly with `gv(curve)` -- use `gv_incl_flop(curve)`.
**Warning signs:** GV series that should be nilpotent appearing potent; wrong contraction types in flopped phases.

### Pitfall 2: Curve-Sign Dictionary Must Be Updated Globally

**What goes wrong:** A new phase is incorrectly identified as matching an existing phase (or vice versa) because some phases don't have curve-sign entries for newly discovered curves.
**Why it happens:** When a new flop curve is discovered, ALL existing phases must be updated with their sign for this curve. Forgetting this means comparison dictionaries have different key sets.
**How to avoid:** Maintain a global set of known curves. When a new curve is added, iterate over ALL phases and compute their signs. This is the `update_curve_signs` pattern from the original.
**Warning signs:** Assertion failures on `index == index2` (the original's sanity check that curve-sign dedup agrees with Mori cone comparison).

### Pitfall 3: Wall Re-Encounter Edge Cases

**What goes wrong:** The same wall (cone face) is processed twice, leading to duplicate contractions in the graph.
**Why it happens:** When a flopped phase has a wall that was already encountered from the other side, the original code links them. If this linking is missed, the wall gets classified twice and potentially creates inconsistent graph edges.
**How to avoid:** Track walls by their cone face identity (Facet equality in the original). When enqueuing walls of a new phase, check against known walls first.
**Warning signs:** Duplicate edges in `CYGraph`, phases with more contractions than Mori cone generators.

### Pitfall 4: Kahler Cone Tip Computation

**What goes wrong:** `tip_of_stretched_cone` returns `None` for some cone configurations.
**Why it happens:** The CYTools method can fail when the cone has certain degenerate structures. The original code has a retry loop that adjusts the stretching parameter.
**How to avoid:** Replicate the original's retry pattern (lines 2212-2218): start with `c=1`, divide by 10 until a valid tip is found, then scale back.
**Warning signs:** `None` tips causing `np.sign(None @ curve)` errors.

### Pitfall 5: Frozen Object Mutation During Construction

**What goes wrong:** Attempting to set attributes on a frozen `CalabiYauLite` during the BFS loop.
**Why it happens:** The builder creates phases and may need to add data (like the Kahler cone tip) after initial construction.
**How to avoid:** Only call `freeze()` after the entire BFS (and optionally Weyl expansion) is complete. The original code never freezes objects during construction.
**Warning signs:** `AttributeError: Cannot modify frozen CalabiYauLite`.

## Code Examples

### Complete BFS Wall Processing (one iteration)

```python
# Source: original lines 896-975, translated to cybir types
def _process_wall(ekc, wall_curve, source_label, gv_invariants, flop_chain,
                  known_curves, curve_signs_map):
    """Process one undiagnosed wall in the BFS loop."""
    source = ekc._graph.get_phase(source_label)

    # Get GV series for this wall's curve
    gvs_local = gv_invariants.flop_gvs(flop_chain)
    series = gvs_local.gv_series(wall_curve)

    # Classify
    result = classify_contraction(
        source.int_nums, source.c2, wall_curve, series)

    ctype = result["contraction_type"]

    # Build contraction object
    contraction = ExtremalContraction(
        flopping_curve=np.array(normalize_curve(wall_curve)),
        contraction_type=ctype,
        gv_invariant=result["gv_invariant"],
        effective_gv=result["effective_gv"],
        zero_vol_divisor=result["zero_vol_divisor"],
        coxeter_reflection=result["coxeter_reflection"],
        gv_series=result["gv_series"],
        gv_eff_1=result["gv_eff_1"],
    )

    # Accumulate generators on orchestrator (D-06)
    if ctype in (ContractionType.ASYMPTOTIC, ContractionType.CFT):
        ekc._infinity_cone_gens.add(normalize_curve(wall_curve))
    if ctype == ContractionType.CFT and result["zero_vol_divisor"] is not None:
        ekc._eff_cone_gens.add(tuplify(result["zero_vol_divisor"]))
    if ctype == ContractionType.SU2:
        ekc._eff_cone_gens.add(tuplify(result["zero_vol_divisor"]))
        ekc._coxeter_refs.add(tuplify(result["coxeter_reflection"]))
    if ctype == ContractionType.SYMMETRIC_FLOP:
        ekc._coxeter_refs.add(tuplify(result["coxeter_reflection"]))
        ekc._sym_flop_refs.add(tuplify(result["coxeter_reflection"]))

    return contraction, ctype, series
```

### Weyl Orbit Reflection

```python
# Source: original lines 990-1005, sym_flop_cy lines 268-276
def _reflect_phase(phase, reflection_matrix):
    """Create a new phase by applying a Coxeter reflection."""
    M = np.array(reflection_matrix)
    new_int_nums = np.einsum('abc,xa,yb,zc', phase.int_nums, M, M, M)
    new_c2 = M @ phase.c2

    # Transform Kahler cone rays
    import cytools
    old_kc_rays = phase.kahler_cone.rays()
    new_kc = cytools.Cone(rays=old_kc_rays @ np.round(M).astype(int))
    new_mori = new_kc.dual()

    return CalabiYauLite(
        int_nums=new_int_nums,
        c2=new_c2,
        kahler_cone=new_kc,
        mori_cone=new_mori,
    )
```

## State of the Art

| Old Approach (original) | New Approach (cybir) | Impact |
|------------------------|---------------------|--------|
| Monolithic `ExtendedKahlerCone` class | Separated `CYBirationalClass` + `build_gv` + `weyl` | Testable, maintainable |
| String-based categories | `ContractionType` enum | Type-safe |
| `start_phase`/`end_phase` on Wall | Graph topology with edge metadata | Clean separation |
| Print statements | `logging` module | Configurable verbosity |
| Implicit monkey-patching on import | Explicit `patch_cytools()` call | No surprises |
| `CY_GV` wrapping CYTools CalabiYau | `CalabiYauLite` standalone container | No runtime CYTools dependency for phase data |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | CYTools `Invariants` doesn't already have a `gv_series` method (only has `gvs`) | Monkey-Patching | Name collision; use `gv_series_cybir` as fallback |
| A2 | `Cone.tip_of_stretched_cone()` is available in the current CYTools version | BFS Algorithm | Need alternative interior point computation |
| A3 | `CalabiYau.mori_cone_cap(in_basis=True).find_grading_vector()` is the correct call chain for GV setup | BFS Algorithm | Root setup fails; check exact API |

## Open Questions

1. **Mori cone construction for flopped phases**
   - What we know: The original uses `Invariants.cone_incl_flop()` to get the Mori cone of a flopped phase. This requires the monkey-patched `cone_incl_flop` method.
   - What's unclear: Whether the Mori cone is needed immediately during BFS (for computing walls) or can be deferred.
   - Recommendation: Compute Mori cone at flop time since walls are derived from Mori cone generators.

2. **Kahler cone tip storage on CalabiYauLite**
   - What we know: The BFS needs the "tip" (interior point) of each phase's Kahler cone for curve-sign computation. The original stores this on the CY object.
   - What's unclear: Whether to add a `tip` attribute to `CalabiYauLite` or compute it on the fly.
   - Recommendation: Add a `_tip` attribute set during construction, before freeze. It's cheap to compute but needed frequently during BFS.

3. **Test data for BFS integration tests**
   - What we know: The existing h11_2 fixtures contain per-wall data (classification, GV series, wall-crossed quantities). They do NOT contain the full BFS result (phase graph, phase count, contraction connectivity).
   - What's unclear: Whether to extend `generate_snapshots.py` to capture the full BFS graph, or write BFS tests differently.
   - Recommendation: Extend `generate_snapshots.py` to capture: number of phases, phase labels, contraction edges, and phase connectivity. This enables end-to-end BFS verification.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (cytools env) | Runtime | Yes | 3.12.12 | -- |
| CYTools | INTG-01, INTG-03 | Yes | (local) | -- |
| Sphinx | PKG-02 | Yes | 9.1.0 | -- |
| sphinx-book-theme | PKG-02 | Yes | (env) | -- |
| myst-nb | PKG-03 | Yes | (env) | -- |
| pytest | Testing | Yes | 9.0.2 | -- |
| networkx | CYGraph | Yes | (env) | -- |

**Missing dependencies with no fallback:** None.

## Project Constraints (from CLAUDE.md)

- **Mathematical correctness**: All algorithms must remain bit-for-bit equivalent to the original
- **CYTools compatibility**: Must work with the CYTools version in the `cytools` conda env
- **Package structure**: Follow the dbrane-tools model -- `cybir/core/`, Sphinx docs in `documentation/`, notebooks for examples
- **Python 3.12**: Do not target 3.13+
- **conda (cytools env)**: Install cybir into the existing cytools env via `pip install -e .`
- **Use numpy-style docstrings** with arXiv equation citations (MATH-06 pattern from Phase 2)
- **Ruff** for linting and formatting
- **No pydantic, attrs, pandas, SageMath, jupyter-book** (see CLAUDE.md What NOT to Use)

## Sources

### Primary (HIGH confidence)
- Original `extended_kahler_cone.py` -- BFS algorithm (lines 871-1073), Weyl expansion (977-1035), monkey-patching (2530-2692), `sym_flop_cy` (268-276), `CY_GV` class (2291-2360)
- Existing cybir code -- `types.py`, `graph.py`, `classify.py`, `flop.py`, `gv.py`, `util.py`, `__init__.py`
- CYTools `Invariants` class -- inspected via Python introspection (methods, `__init__` signature, `gv` source)
- dbrane-tools `conf.py` -- Sphinx configuration pattern
- `tests/generate_snapshots.py` -- existing fixture generation
- `tests/fixtures/h11_2/` -- 36 polytope test fixtures

### Secondary (MEDIUM confidence)
- CYTools `CalabiYau` methods list -- inspected via `dir()` in conda env
- CONTEXT.md decisions D-01 through D-20

### Tertiary (LOW confidence)
- A1, A2, A3 in Assumptions Log

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all packages already in env, no new dependencies
- Architecture: HIGH -- directly translating from working original code with clear CONTEXT.md decisions
- BFS algorithm: HIGH -- read the exact original implementation, line by line
- Weyl expansion: MEDIUM -- original has known quality issues (noted in STATE.md), careful review needed
- Monkey-patching: HIGH -- read the exact methods to patch, verified CYTools API
- Documentation: HIGH -- exact dbrane-tools conf.py available as reference
- Pitfalls: HIGH -- identified from original code patterns and prior phase experience

**Research date:** 2026-04-12
**Valid until:** 2026-05-12 (stable domain, no external API changes expected)
