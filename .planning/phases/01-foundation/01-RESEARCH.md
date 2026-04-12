# Phase 1: Foundation - Research

**Researched:** 2026-04-11
**Domain:** Python package scaffolding, scientific data types, test infrastructure
**Confidence:** HIGH

## Summary

Phase 1 creates the cybir package skeleton with its core data types (`CalabiYauLite`, `ExtremalContraction`, `ContractionType`, `InsufficientGVError`), a phase adjacency graph, utility functions ported from cornell-dev, and a pytest test suite. No mathematical algorithms are ported -- only containers, helpers, and verification infrastructure.

The technical domain is well-constrained: pure Python packaging with hatchling, dataclass-like containers for numerical data, and straightforward utility functions. The main complexity is in the design of `CalabiYauLite` to be interface-compatible with dbrane-tools while adding EKC-specific fields, and in correctly porting the 4 cornell-dev utility functions.

**Primary recommendation:** Follow the dbrane-tools pattern (private `_` attributes + `@property` accessors) for `CalabiYauLite`; use frozen dataclasses for `ExtremalContraction`; use networkx (already in env, v3.6.1) for the adjacency graph; use pytest fixtures with JSON-serialized test data generated from the original code on h11=2 polytopes.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** All code lives in `cybir/core/` for this milestone. No `phases/` or `patching/` subdirectories.
- **D-02:** Module split: `types.py` (CalabiYauLite, ExtremalContraction, ContractionType, InsufficientGVError), `flop.py` (wall-crossing, diagnosis, GV math -- Phase 2), `util.py` (normalize_curve, projection_matrix, lattice helpers, cornell-dev replacements), `ekc.py` (ExtendedKahlerCone orchestrator -- Phase 3).
- **D-03:** Monkey-patches live next to the functions they relate to, not in a separate `patching/` module.
- **D-04:** `CalabiYauLite` -- own version in cybir, interface-compatible with dbrane-tools' CalabiYauLite for future unification. Fields: int_nums, c2, kahler_cone, mori_cone, polytope, charges, indices, eff_cone, triangulation, fan (matching dbrane-tools), PLUS gv_invariants (reference to CYTools Invariants object) and label (phase ID for adjacency graph). Mutable by default; EKC orchestrator freezes after construction.
- **D-05:** `ExtremalContraction` (not `Contraction`, not `Wall`) -- represents an extremal birational contraction. Fields: flopping_curve, start_phase, end_phase, contraction_type, gv_invariant, effective_gv, zero_vol_divisor, coxeter_reflection. All fields defined in `__init__` with `None` defaults for type-specific fields.
- **D-06:** `ContractionType` -- enum with 5 values: ASYMPTOTIC, CFT, SU2, SYMMETRIC_FLOP, FLOP. Configurable display notation.
- **D-07:** `InsufficientGVError` -- exception subclass of RuntimeError.
- **D-08:** Phase adjacency graph as first-class object -- phases as nodes, ExtremalContractions as edges.
- **D-09:** `misc.glsm` -> use `charge_matrix_hsnf` from dbrane-tools util.py.
- **D-10:** `misc.moving_cone` -> port the 5-line function directly.
- **D-11:** `misc.sympy_number_clean` -> rewrite as one-liner: `sympy.Rational(x).limit_denominator()`.
- **D-12:** `misc.tuplify` -> rewrite simple recursive numpy-to-tuple converter.
- **D-13:** `lib.util.lattice` -> drop entirely (only used in commented-out line, replaced by hsnf).
- **D-14:** Do NOT copy `lazy_cached` or other dbrane-tools utilities not needed by EKC code. Only bring what cybir actually uses.
- **D-15:** Generate test fixtures by running the original `extended_kahler_cone.py` on h11=2 polytopes and serializing the results.
- **D-16:** Tests cover data type instantiation, immutability enforcement, and cornell-dev replacement functions against known inputs.

### Claude's Discretion
- pyproject.toml details (hatchling config, version, metadata)
- Exact adjacency graph implementation (networkx, custom dict-based, etc.)
- Immutability mechanism (frozen dataclass, `__setattr__` override, etc.)
- Test fixture serialization format (JSON, pickle, npz)

### Deferred Ideas (OUT OF SCOPE)
- Tuned complex structure mode (ENH-02)
- Higher-codimension contractions
- Symbolic prepotential / sympy variable storage on CalabiYauLite
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | `CalabiYauLite` class for phase data | dbrane-tools geometry.py interface analyzed; field list locked in D-04; property pattern documented |
| DATA-02 | `ExtremalContraction` class (contraction metadata) | Original Wall class fields mapped to new names in D-05; frozen dataclass recommended |
| DATA-03 | `ContractionType` enum with configurable notation | 5 string categories from original code mapped to enum values; notation dict pattern documented |
| DATA-04 | `InsufficientGVError` exception | Simple RuntimeError subclass per D-07 and CHANGES.md |
| DATA-05 | Phase adjacency graph as first-class object | networkx 3.6.1 available in env; Graph with CalabiYauLite nodes and ExtremalContraction edges |
| DATA-06 | Immutable/frozen phase objects after construction | Freeze mechanism researched -- `__setattr__` override with `_frozen` flag recommended |
| PKG-01 | Proper Python package structure | hatchling + pyproject.toml; `cybir/core/` layout per D-01/D-02 |
| INTG-02 | Decouple from cornell-dev | All 4 functions analyzed: charge_matrix_hsnf (copy), moving_cone (port 5 lines), sympy_number_clean (one-liner), tuplify (rewrite) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Mathematical correctness**: All algorithms must remain bit-for-bit equivalent to the original
- **CYTools compatibility**: Must work with the CYTools version in the `cytools` conda env
- **Package structure**: Follow the dbrane-tools model -- `cybir/core/`, Sphinx docs, notebooks
- **Python environment**: Use `conda run -n cytools` or activate -- do not install packages from scratch
- **When working with fans**: Use Fan/VectorConfiguration objects from the appropriate library, not CYTools Triangulation or ToricVariety objects

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | 2.3.5 | Dense arrays, linear algebra | Already in cytools env [VERIFIED: conda env] |
| scipy | 1.17.0 | Sparse matrices, null_space | Already in cytools env [VERIFIED: conda env] |
| python-flint | 0.8.0 | Exact integer arithmetic | Used for nullspace in moving_cone fallback [VERIFIED: conda env] |
| hsnf | 0.3.16 | Smith Normal Form | Used by charge_matrix_hsnf, projection_matrix [VERIFIED: conda env] |
| sympy | 1.14.0 | Rational arithmetic | Used by sympy_number_clean [VERIFIED: conda env] |
| cytools | (local) | CY3 geometry pipeline | Cone objects, monkey-patch targets. NOT a PyPI dep [VERIFIED: conda env] |
| networkx | 3.6.1 | Phase adjacency graph | Already in cytools env; mature graph library [VERIFIED: conda env] |

### Dev
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.2 | Test framework | All tests [VERIFIED: conda env] |
| pytest-cov | (in env) | Coverage | Track coverage of critical paths [VERIFIED: conda env] |
| hatchling | >=1.21 | Build backend | pyproject.toml build system [ASSUMED: standard version] |

### What NOT to Use
| Instead of | Why Not |
|------------|---------|
| pydantic | Heavyweight; validation overhead unwanted in numerics [from CLAUDE.md] |
| attrs | Unnecessary when stdlib dataclasses + custom `__setattr__` suffice [from CLAUDE.md] |
| pandas | Data is numpy arrays, not tabular [from CLAUDE.md] |

**Installation:**
```bash
conda activate cytools
pip install -e ".[dev]"
```

## Architecture Patterns

### Package Structure
```
ekc/
  cybir/
    __init__.py          # version, top-level imports
    core/
      __init__.py        # re-exports from types, util
      types.py           # CalabiYauLite, ExtremalContraction, ContractionType, InsufficientGVError
      util.py            # normalize_curve, projection_matrix, charge_matrix_hsnf, moving_cone, sympy_number_clean, tuplify
      flop.py            # (Phase 2 - empty placeholder)
      ekc.py             # (Phase 3 - empty placeholder)
    graph.py             # PhaseGraph adjacency graph wrapper (or in core/types.py)
  tests/
    __init__.py
    conftest.py          # shared fixtures, test data loading
    fixtures/            # serialized test data (JSON)
    test_types.py        # CalabiYauLite, ExtremalContraction, ContractionType, InsufficientGVError
    test_util.py         # normalize_curve, projection_matrix, charge_matrix_hsnf, etc.
    test_graph.py        # PhaseGraph adjacency operations
  pyproject.toml
```

### Pattern 1: CalabiYauLite -- Private Attributes + Property Accessors
**What:** Match the dbrane-tools pattern: `_` private attributes set in `__init__`, exposed via `@property`. This is the established pattern in the codebase.
**When to use:** For CalabiYauLite specifically, which needs to be mutable during construction then frozen.
**Example:**
```python
# Source: dbrane-tools/dbrane_tools/core/geometry.py lines 15-55
class CalabiYauLite:
    def __init__(
            self, int_nums, c2=None, kahler_cone=None,
            mori_cone=None, polytope=None, charges=None,
            indices=None, eff_cone=None, triangulation=None,
            fan=None, gv_invariants=None, label=None):
        self._int_nums = int_nums
        self._c2 = c2
        self._kahler_cone = kahler_cone
        self._mori_cone = mori_cone
        self._polytope = polytope
        self._charges = charges
        self._indices = indices
        self._eff_cone = eff_cone
        self._triangulation = triangulation
        self._fan = fan
        # cybir-specific fields
        self._gv_invariants = gv_invariants
        self._label = label
        self._frozen = False

    @property
    def int_nums(self):
        """Triple intersection numbers kappa_{ijk}."""
        return self._int_nums

    # ... similar for all other fields ...

    def freeze(self):
        """Make this object immutable. Called by EKC orchestrator after construction."""
        self._frozen = True

    def __setattr__(self, name, value):
        if getattr(self, '_frozen', False) and name != '_frozen':
            raise AttributeError(
                f"Cannot modify frozen CalabiYauLite (attribute '{name}')")
        super().__setattr__(name, value)
```

### Pattern 2: ExtremalContraction -- Frozen After Init
**What:** Use `__setattr__` freeze pattern, frozen by default since all fields are set at construction.
**Why not frozen dataclass:** Fields include numpy arrays (not hashable), and `None` defaults require mutable-feeling construction. The `__setattr__` approach is more flexible.
**Example:**
```python
class ExtremalContraction:
    def __init__(
            self, flopping_curve, start_phase=None, end_phase=None,
            contraction_type=None, gv_invariant=None, effective_gv=None,
            zero_vol_divisor=None, coxeter_reflection=None):
        self._flopping_curve = flopping_curve
        self._start_phase = start_phase
        self._end_phase = end_phase
        self._contraction_type = contraction_type
        self._gv_invariant = gv_invariant
        self._effective_gv = effective_gv
        self._zero_vol_divisor = zero_vol_divisor
        self._coxeter_reflection = coxeter_reflection
        self._frozen = True  # frozen by default

    @property
    def flopping_curve(self):
        return self._flopping_curve

    # ... similar for all fields ...

    def __setattr__(self, name, value):
        if getattr(self, '_frozen', False) and name != '_frozen':
            raise AttributeError(
                f"Cannot modify frozen ExtremalContraction (attribute '{name}')")
        super().__setattr__(name, value)
```

### Pattern 3: ContractionType Enum with Notation
**What:** Python `enum.Enum` with a class method for display name lookup.
**Example:**
```python
import enum

class ContractionType(enum.Enum):
    ASYMPTOTIC = "asymptotic"
    CFT = "CFT"
    SU2 = "su2"
    SYMMETRIC_FLOP = "symmetric_flop"
    FLOP = "flop"

    # Notation mappings
    _WILSON_NAMES = {
        "ASYMPTOTIC": "Type III",
        "CFT": "Type II",
        "SU2": "Type I",
        "SYMMETRIC_FLOP": "Symmetric Flop",
        "FLOP": "Flop",
    }

    _PAPER_NAMES = {
        "ASYMPTOTIC": "asymptotic",
        "CFT": "CFT",
        "SU2": "su(2) enhancement",
        "SYMMETRIC_FLOP": "symmetric flop",
        "FLOP": "generic flop",
    }

    def display_name(self, notation="paper"):
        """Return human-readable name in given notation."""
        if notation == "wilson":
            return self._WILSON_NAMES.value[self.name]
        return self._PAPER_NAMES.value[self.name]
```

**Note on the enum notation dicts:** Storing dicts as enum members requires care. A cleaner approach is to use module-level dicts or a `@staticmethod`. The planner should decide the exact mechanism -- the key requirement is that `ContractionType.FLOP.display_name("wilson")` returns `"Flop"` and `ContractionType.FLOP.display_name("paper")` returns `"generic flop"`. [ASSUMED: exact notation strings may need user confirmation for Wilson convention names]

### Pattern 4: Phase Adjacency Graph
**What:** Thin wrapper around `networkx.Graph` (undirected -- contractions connect two phases symmetrically).
**Example:**
```python
import networkx as nx

class PhaseGraph:
    def __init__(self):
        self._graph = nx.Graph()

    def add_phase(self, phase: CalabiYauLite):
        """Add a phase node."""
        self._graph.add_node(phase.label, phase=phase)

    def add_contraction(self, contraction: ExtremalContraction):
        """Add a contraction edge between two phases."""
        self._graph.add_edge(
            contraction.start_phase.label,
            contraction.end_phase.label,
            contraction=contraction)

    @property
    def phases(self):
        """All phase objects."""
        return [d['phase'] for _, d in self._graph.nodes(data=True)]

    @property
    def contractions(self):
        """All contraction objects."""
        return [d['contraction'] for _, _, d in self._graph.edges(data=True)]

    def neighbors(self, label):
        """Phases adjacent to the given phase."""
        return [self._graph.nodes[n]['phase'] for n in self._graph.neighbors(label)]
```

### Anti-Patterns to Avoid
- **String-based contraction types:** The original code uses strings like `'asymptotic'`, `'CFT'`, `'symmetric flop'`, `'su(2) enhancement'`, `'generic flop (I)'`, `'generic flop (II)'`, `'potent "flop" wall (insufficient degree)'`. This makes comparison fragile. Use the ContractionType enum instead.
- **Mixing mutable and immutable:** CalabiYauLite is mutable during construction (Phase 3 BFS loop builds it up), then frozen. Do not use `@dataclass(frozen=True)` because it prevents construction-time mutation. Use the `_frozen` flag pattern instead.
- **Copying dbrane-tools utilities not needed:** Per D-14, only bring `charge_matrix_hsnf`. Do NOT copy `lazy_cached`, `multivariable_lazy_cached`, `matrix_affine_eval`, or any other dbrane-tools utility.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Graph data structure | Custom dict-of-dicts | `networkx.Graph` | Mature, handles node/edge attributes, already in env |
| SNF-based charge matrix | Manual matrix operations | `charge_matrix_hsnf` from dbrane-tools | Exact copy, tested, uses `hsnf` library correctly |
| Rational number cleanup | Custom float rounding | `sympy.Rational(x).limit_denominator()` | Exact arithmetic, handles edge cases |
| Package build system | setup.py + setup.cfg | hatchling + pyproject.toml | PEP 621 standard, minimal config |

## Common Pitfalls

### Pitfall 1: numpy Arrays in Frozen Dataclasses
**What goes wrong:** `@dataclass(frozen=True)` requires all fields to be hashable. numpy arrays are not hashable.
**Why it happens:** Natural instinct is to use frozen dataclasses for immutable data.
**How to avoid:** Use the `__setattr__` + `_frozen` flag pattern instead. This provides the same immutability guarantee without requiring hashability.
**Warning signs:** `TypeError: unhashable type: 'numpy.ndarray'` at construction time.

### Pitfall 2: charge_matrix_hsnf Returns Transposed Result
**What goes wrong:** The hsnf-based function returns relations as rows of the result matrix (`relations.T`). Confusing rows vs columns leads to wrong charge matrices.
**Why it happens:** Linear algebra conventions differ (row vectors vs column vectors).
**How to avoid:** Copy `charge_matrix_hsnf` exactly from dbrane-tools `util.py` lines 41-61. Test against known h11=2 results.
**Warning signs:** Charge matrix has wrong shape or wrong rank.

### Pitfall 3: CalabiYauLite Properties Returning Mutable References
**What goes wrong:** If `int_nums` property returns `self._int_nums` directly, callers can mutate the internal state even after freezing.
**Why it happens:** numpy arrays are mutable; returning a reference allows external mutation.
**How to avoid:** The original CY class (line 2231) returns `np.copy(self._int_nums)`. Decide whether cybir should do the same. For frozen objects this provides defense-in-depth; for performance-sensitive paths it adds overhead. Recommendation: return copies for dense arrays (int_nums, c2), direct references for Cone objects (immutable by construction in CYTools).
**Warning signs:** Test modifies returned array, original object changes.

### Pitfall 4: Enum Members Shadowing Dict Values
**What goes wrong:** Putting `_WILSON_NAMES = {...}` as a class attribute inside an `enum.Enum` makes it an enum member itself.
**Why it happens:** Python enums treat all class attributes as members unless prefixed with `_` and using specific patterns.
**How to avoid:** Use `_ignore_` or define notation dicts as module-level constants or use a `@staticmethod` method that returns the dict. Alternatively, store notation as a tuple in the enum value: `ASYMPTOTIC = ("asymptotic", "Type III", "asymptotic")`.
**Warning signs:** `len(ContractionType)` returns more than 5.

### Pitfall 5: Forgetting `__eq__` on CalabiYauLite
**What goes wrong:** The original code (line 2243) uses `np.allclose(self.int_nums, other.int_nums)` for equality. Without explicit `__eq__`, identity comparison (`is`) is used by default, and the adjacency graph cannot deduplicate phases.
**Why it happens:** The default `__eq__` is identity-based.
**How to avoid:** Implement `__eq__` using `np.allclose` on `int_nums` and `c2`, matching the original code. Also implement `__hash__` based on `label` for use as graph node keys.
**Warning signs:** Phase deduplication fails in Phase 3 BFS.

## Code Examples

### cornell-dev Function Ports

#### charge_matrix_hsnf (copy from dbrane-tools)
```python
# Source: dbrane-tools/dbrane_tools/core/util.py lines 41-61
import numpy as np
import hsnf

def charge_matrix_hsnf(vectors):
    """Compute integer relations among vectors via Smith Normal Form."""
    D, U, W = hsnf.smith_normal_form(np.array(vectors).T)
    rank = sum(1 for i in range(min(len(D), len(D[0]))) if D[i, i] != 0)
    relations = W[:, rank:]
    return relations.T
```

#### moving_cone (port from misc.py)
```python
# Source: cornell-dev/projects/Elijah/misc.py lines 595-601
import numpy as np
import cytools

def moving_cone(Q, verbose=False):
    """Compute the moving cone from the charge matrix Q.

    Iterates over columns of Q, takes the cone of remaining columns'
    hyperplanes, and forms the intersection.
    """
    hyps = np.vstack([
        cytools.Cone(rays=np.delete(Q, i, axis=1).T).hyperplanes()
        for i in range(Q.shape[1])
    ])
    return cytools.Cone(hyperplanes=hyps)
```

#### sympy_number_clean (one-liner)
```python
# Source: cornell-dev/projects/Elijah/misc.py line 210-211
import sympy

def sympy_number_clean(x):
    """Convert a float to its exact rational representation."""
    return sympy.Rational(x).limit_denominator()
```

#### tuplify (rewrite)
```python
# Source: cornell-dev/projects/Elijah/misc.py lines 84-90
import numpy as np

def tuplify(arr):
    """Convert a numpy ndarray into a nested tuple structure."""
    if isinstance(arr, np.ndarray):
        return tuple(tuplify(x) for x in arr.tolist())
    if isinstance(arr, list):
        return tuple(tuplify(x) for x in arr)
    return arr
```

### Utility Functions from Original EKC Code (for util.py)

These are helpers used by the data types and Phase 2/3 code. They should live in `util.py`:

```python
# Source: extended_kahler_cone.py lines 95-108
def normalize_curve(curve, return_sign=False):
    """Normalize a curve class so first nonzero element is positive."""
    if next(c for c in curve if c != 0) > 0:
        to_return = tuple(curve.tolist())
        sign = 1
    else:
        to_return = tuple((-curve).tolist())
        sign = -1
    return (to_return, sign) if return_sign else to_return

# Source: extended_kahler_cone.py lines 110-119
def projection_matrix(curve):
    """Return (N-1) x N matrix projecting onto complement of curve."""
    return hsnf.smith_normal_form(np.array([curve]).T)[1][1:]
```

### Test Fixture Generation (one-time script)
```python
# Run in cytools env with cornell-dev on path
# Generates fixture data for h11=2 polytopes
import json
import numpy as np

# ... load polytope, run original EKC code ...
# Serialize: int_nums, c2, mori_cone rays, contraction types,
#            flopping curves, Coxeter matrices, adjacency structure

fixture = {
    "int_nums": int_nums.tolist(),
    "c2": c2.tolist(),
    "mori_rays": mori_cone.extremal_rays().tolist(),
    "charge_matrix": Q.tolist(),
    # ... etc
}

with open("tests/fixtures/h11_2_poly_0.json", "w") as f:
    json.dump(fixture, f, indent=2)
```

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Wilson notation names are "Type I/II/III" for SU2/CFT/ASYMPTOTIC | Pattern 3: ContractionType | Display strings would be wrong; low risk since easily corrected |
| A2 | hatchling >=1.21 is current enough | Standard Stack | Build would fail; easily fixable by adjusting version pin |
| A3 | Adjacency graph should be undirected (contractions are symmetric) | Pattern 4 | If contractions are directed (they have start/end phases), may need DiGraph; the start/end distinction is stored on the edge attribute regardless |

## Open Questions

1. **Should the adjacency graph be directed or undirected?**
   - What we know: ExtremalContraction has `start_phase` and `end_phase`, implying directionality. But physically, contractions connect phases symmetrically (you can flop in either direction).
   - What's unclear: Whether the BFS algorithm in Phase 3 needs directed edges.
   - Recommendation: Use `networkx.Graph` (undirected) with the contraction stored as edge data. The start/end distinction is on the ExtremalContraction object itself, not the graph edge. This matches the physical symmetry while preserving directionality metadata.

2. **Should CalabiYauLite properties return copies of numpy arrays?**
   - What we know: The original CY class returns `np.copy(self._int_nums)`. This is defensive but adds overhead.
   - What's unclear: Whether performance matters at this stage.
   - Recommendation: Return copies for now (matches original behavior). Can optimize later if profiling shows it matters.

3. **Test fixture generation: should it be automated or one-shot?**
   - What we know: D-15 says generate from original code on h11=2 polytopes.
   - What's unclear: Whether to include the generation script in the repo or just commit the fixtures.
   - Recommendation: Include the generation script in `tests/fixtures/generate.py` but commit the generated JSON files too, so tests can run without cornell-dev installed.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | Yes | 3.12.12 | -- |
| numpy | Core arrays | Yes | 2.3.5 | -- |
| scipy | Sparse arrays, null_space | Yes | 1.17.0 | -- |
| python-flint | Exact arithmetic | Yes | 0.8.0 | -- |
| hsnf | Smith Normal Form | Yes | 0.3.16 | -- |
| sympy | Rational cleanup | Yes | 1.14.0 | -- |
| cytools | Cone objects | Yes | (local) | -- |
| networkx | Phase graph | Yes | 3.6.1 | -- |
| pytest | Testing | Yes | 9.0.2 | -- |
| hatchling | Build | Not verified | -- | `pip install hatchling` at build time |

**Missing dependencies with no fallback:** None -- all core dependencies are present in the cytools conda env.

**Missing dependencies with fallback:**
- hatchling: Will be installed automatically by pip when building from pyproject.toml. No manual install needed.

## Sources

### Primary (HIGH confidence)
- dbrane-tools `core/geometry.py` -- CalabiYauLite reference implementation (read directly)
- dbrane-tools `core/util.py` -- charge_matrix_hsnf source (read directly)
- cornell-dev `misc.py` -- glsm, moving_cone, sympy_number_clean, tuplify (read directly)
- cornell-dev `extended_kahler_cone.py` -- Wall, CY, CY_GV class definitions and utility functions (read directly)
- cornell-dev `lib/util/lattice.py` -- confirmed only used in commented-out line (read directly)
- cornell-dev `claude/CHANGES.md` -- prior refactor patterns (read directly)
- cytools conda env -- all package versions verified via `conda run -n cytools python -c "import X; print(X.__version__)"` 

### Secondary (MEDIUM confidence)
- CLAUDE.md stack recommendations -- hatchling, ruff, pytest versions

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all versions verified against conda env
- Architecture: HIGH -- patterns directly observed in dbrane-tools and original code
- Pitfalls: HIGH -- derived from reading actual code and understanding numpy/enum behavior

**Research date:** 2026-04-11
**Valid until:** 2026-05-11 (stable domain, no fast-moving dependencies)
