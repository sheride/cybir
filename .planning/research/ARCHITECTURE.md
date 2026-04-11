# Architecture Patterns

**Domain:** CY birational geometry / extended Kahler cone construction
**Researched:** 2026-04-11

## Recommended Architecture

### Package Layout

```
cybir/
    __init__.py              # Public API: from cybir import ExtendedKahlerCone, Phase, Wall
    core/
        __init__.py
        types.py             # Structured data types (PhaseData, WallData, WallCategory enum, etc.)
        wall_crossing.py     # Pure functions: wall_cross_intnums, wall_cross_c2, flop_cy, sym_flop_cy
        diagnosis.py         # Pure functions: is_asymptotic, is_cft, find_zero_vol_divisor, etc.
        algebra.py           # Pure functions: coxeter_matrix, get_coxeter_reflection, matrix_period, etc.
        util.py              # normalize_curve, find_minimal_N, projection_matrix, is_parallel, etc.
        lattice.py           # Copied/refactored from cornell-dev lib.util.lattice + misc helpers
    phases/
        __init__.py
        phase.py             # Phase class (replaces CY / CY_GV hierarchy)
        wall.py              # Wall class (combines old Wall + Facet)
        ekc.py               # ExtendedKahlerCone orchestrator (construct_phases pipeline)
    patching/
        __init__.py          # Auto-applies patches on import
        invariants.py        # Monkey-patches on cytools.calabiyau.Invariants
        polytope.py          # Monkey-patches on cytools.Polytope (future)
        triangulation.py     # Monkey-patches on cytools.Triangulation (future)
        calabiyau.py         # Monkey-patches on cytools.CalabiYau (future)
documentation/
    source/
        conf.py
        index.rst
        ...
    build/
notebooks/
    examples.ipynb
```

### Design Rationale

**Why `core/` vs `phases/` split:** The `core/` module contains stateless mathematical functions and data types -- the "library" layer. The `phases/` module contains stateful objects that orchestrate the EKC construction algorithm -- the "application" layer. This mirrors dbrane-tools' `core/` vs `analysis/` split but with domain-appropriate names.

**Why `patching/` as a separate module:** Monkey-patching is a cross-cutting concern that touches CYTools internals. Isolating it makes the patches explicit, testable, and optional. Users who want cybir without modifying CYTools globals can skip `import cybir.patching`.

**Why flatten CY/CY_GV/CY_Toric into Phase:** The old hierarchy conflates two orthogonal concerns: (1) the data a phase carries (intersection numbers, c2, Mori cone, Kahler cone, walls) and (2) how that data was obtained (from GV invariants vs toric fan). Since the toric pipeline is out of scope, there's only one construction method. The Phase class holds phase data; construction logic lives in the orchestrator. If the toric pipeline returns later, it produces the same Phase objects via a different code path -- no class hierarchy needed.

**Why not `analysis/`:** The dbrane-tools `analysis/` holds scanning/profiling scripts. cybir has no equivalent yet. The `phases/` module is closer to "application logic" than "analysis." If scanning scripts emerge later (e.g., "scan all h11=4 polytopes for interesting EKC structure"), an `analysis/` module can be added then.

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `core/types.py` | Data containers: `PhaseData`, `WallData`, `WallCategory`, `CurveClass`, `GVSeriesData` | Everything (imported everywhere) |
| `core/wall_crossing.py` | Wall-crossing formulas: transform intersection numbers and c2 across a flop | `phases/wall.py`, `phases/ekc.py` |
| `core/diagnosis.py` | Wall classification: asymptotic, CFT, su(2), symmetric flop, generic flop | `phases/wall.py` |
| `core/algebra.py` | Coxeter/Weyl reflection computation, matrix period, projection matrices | `core/diagnosis.py`, `phases/wall.py` |
| `core/util.py` | Small stateless helpers: normalize_curve, find_minimal_N, vector alignment checks | Everywhere |
| `core/lattice.py` | Lattice utilities from cornell-dev: moving_cone, glsm, tuplify, sympy_number_clean | `phases/phase.py`, `phases/ekc.py` |
| `phases/phase.py` | Phase representation: holds int_nums, c2, Mori/Kahler cones, tip, walls, volume computations | `phases/ekc.py`, `phases/wall.py` |
| `phases/wall.py` | Wall between phases: curve, facet geometry, GV data, diagnosis dispatch, flop execution | `phases/phase.py`, `phases/ekc.py`, `core/diagnosis.py`, `core/wall_crossing.py` |
| `phases/ekc.py` | Orchestrator: BFS over walls, phase registration, sign tracking, Weyl orbit expansion, result collection | `phases/phase.py`, `phases/wall.py`, CYTools objects |
| `patching/invariants.py` | Extends `cytools.calabiyau.Invariants` with: `gv_series`, `gv_eff`, `copy`, `flop_gvs`, `gv_incl_flop`, `cone_incl_flop`, `ensure_nilpotency` | CYTools internals only |
| `patching/polytope.py` | Extends `cytools.Polytope` with convenience methods (e.g., direct EKC construction) | `phases/ekc.py` |

## Data Flow

### Primary Pipeline: `construct_phases`

```
User provides: cytools.Polytope (or CalabiYau)
                    |
                    v
        ExtendedKahlerCone.__init__()
            - Extracts GLSM charge matrix, basis, vector configuration
            - Computes toric moving cone, effective cone
            - Stores polytope reference
                    |
                    v
        setup_root()
            - Triangulates polytope -> CY
            - Computes GVs via CYTools (monkey-patched Invariants)
            - Creates root Phase with int_nums, c2, Mori cone, walls
            - Initializes wall queue with root's Kahler cone facets
                    |
                    v
        construct_phases() -- BFS loop
            |
            +---> Pick next undiagnosed Wall from queue
            |         |
            |         v
            |     Wall.diagnose()
            |         |
            |         +-- core/diagnosis.py: is_asymptotic? is_cft?
            |         +-- core/diagnosis.py: find_zero_vol_divisor
            |         +-- patching/invariants.py: compute gv_series, gv_eff
            |         +-- core/diagnosis.py: is_symmetric_flop?
            |         |
            |         v
            |     Wall now has category: asymptotic | CFT | su(2) | 
            |         symmetric_flop | generic_flop | insufficient_gv
            |         |
            |     If floppable:
            |         |
            |         v
            |     core/wall_crossing.py: wall_cross_intnums, wall_cross_c2
            |         |
            |         v
            |     New Phase created with flopped data
            |         |
            |         v
            |     Deduplication via curve_signs dictionary
            |         |
            |         v
            |     Register new Phase, add its walls to queue
            |         |
            +----<--- Loop
                    |
                    v (after BFS exhausted)
        Optional: Weyl orbit expansion
            - For each sym_flop reflection, reflect existing phases
            - Register reflected phases and their walls
                    |
                    v
        Post-processing
            - Collect infinity_cone_gens, eff_cone_gens, coxeter_refs
            - Build effective cone
                    |
                    v
        Result: ExtendedKahlerCone with .phases, .walls, .eff_cone, etc.
```

### Data Ownership

- **Phase owns:** `int_nums`, `c2`, `mori` (Cone), `tip`, `walls` (list of Wall refs), `curve_signs`, `is_toric` flag, sympy variables for polynomial display
- **Wall owns:** `curve`, `facet` (Cone), `start_phase`, `end_phase`, `category` (WallCategory enum), `gv_series`, `gv_eff_1`, `gv_eff_3`, `zero_vol_divisor`, `coxeter_reflection`
- **ExtendedKahlerCone owns:** `polytope`, `phases` (list), `walls` (list), `root` (Phase ref), global aggregates (infinity_cone_gens, eff_cone_gens, coxeter_refs, sym_flop_refs, su2_refs, eff_cone)

### Key Data Type Decisions

**WallCategory as an enum, not strings.** The original code uses string literals (`'asymptotic'`, `'CFT'`, `'su(2) enhancement'`, `'symmetric flop'`, `'generic flop (I)'`, `'generic flop (II)'`, `'potent "flop" wall (insufficient degree)'`). These should become:

```python
class WallCategory(Enum):
    ASYMPTOTIC = "asymptotic"
    CFT = "cft"
    SU2_ENHANCEMENT = "su2_enhancement"
    SYMMETRIC_FLOP = "symmetric_flop"
    GENERIC_FLOP = "generic_flop"          # merge (I) and (II)
    INSUFFICIENT_GV = "insufficient_gv"
```

The distinction between "generic flop (I)" (no zero-vol divisor) and "generic flop (II)" (has zero-vol divisor but not symmetric) can be tracked via the presence/absence of `zero_vol_divisor` on the Wall, rather than encoded in the category.

**Phase replaces CY/CY_GV/CY_Toric.** A single Phase dataclass-like object holds the geometric data. Construction-method-specific fields (e.g., `gvs` for GV-based, `fan` for toric) become optional attributes or are not stored at all (the Invariants object is used transiently during wall diagnosis, not stored permanently on the phase).

**Structured GV data.** Currently, GV series are bare lists and gv_eff values are bare ints scattered across Wall attributes. These should be grouped:

```python
@dataclass
class GVWallData:
    series: list[int]       # GV(C), GV(2C), GV(3C), ...
    eff_1: int              # sum_n n * GV(nC)
    eff_3: int              # sum_n n^3 * GV(nC)
    nilpotent: bool         # whether series terminates
```

## Patterns to Follow

### Pattern 1: Stateless Core Functions

**What:** All mathematical operations in `core/` are pure functions taking numpy arrays and returning numpy arrays. No class state, no side effects.

**When:** Wall-crossing formulas, diagnosis checks, algebraic computations.

**Why:** The original code already does this for the free functions (lines 43-480) but the Wall class re-wraps them as methods that extract arguments from `self`. Keep the pure functions; let Wall be a thin dispatch layer.

**Example:**
```python
# core/wall_crossing.py
def wall_cross_intnums(
    int_nums: np.ndarray,
    curve: np.ndarray,
    gv_eff_3: int
) -> np.ndarray:
    """Transform intersection numbers across a flop wall."""
    ...

# phases/wall.py
class Wall:
    def flopped_intnums(self) -> np.ndarray:
        return wall_cross_intnums(
            self.start_phase.int_nums,
            self.curve,
            self.gv_data.eff_3
        )
```

### Pattern 2: Registry / Deduplication in Orchestrator

**What:** The ExtendedKahlerCone maintains a registry of phases indexed by `curve_signs` dictionaries. New phases are checked against this registry before being added.

**When:** Every time a flop produces a candidate new phase.

**Why:** The original code does this with `safe_index` linear scans. A dictionary keyed by frozen curve_signs tuples is cleaner and O(1).

```python
# phases/ekc.py
class ExtendedKahlerCone:
    def _register_phase(self, phase: Phase) -> tuple[Phase, bool]:
        """Register phase, return (canonical_phase, is_new)."""
        key = phase.curve_signs_key()
        if key in self._phase_registry:
            return self._phase_registry[key], False
        self._phase_registry[key] = phase
        self.phases.append(phase)
        return phase, True
```

### Pattern 3: Explicit Monkey-Patch Registration

**What:** Each monkey-patch function is defined in `patching/invariants.py` as a normal function, then explicitly assigned to the CYTools class. A module-level list tracks all patches for introspection/testing.

**When:** GV series operations on `cytools.calabiyau.Invariants`.

**Example:**
```python
# patching/invariants.py
_PATCHES = []

def _register_patch(cls, name, func):
    setattr(cls, name, func)
    _PATCHES.append((cls.__name__, name))

def gv_series(self, curve, do_ensure_nilpotency=False, **kwargs):
    ...

_register_patch(cytools.calabiyau.Invariants, 'gv_series', gv_series)
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Deep Class Hierarchy for Data Variants

**What:** `CY` -> `CY_GV` -> (future `CY_Toric`) hierarchy where subclasses mainly differ in constructor logic.

**Why bad:** Proliferates classes for what is fundamentally the same data. Forces `isinstance` checks in Wall.flop_cy. Makes it hard to create phases from mixed sources.

**Instead:** Single Phase class. Different construction paths (GV-based, toric-based) are factory functions or methods on the orchestrator that produce Phase objects.

### Anti-Pattern 2: Mutable State Scattered Across Objects

**What:** The original code mutates Wall objects (setting `.category`, `.end`, `.gv_series`, `.zero_vol_divisor`, `.coxeter_reflection`) across many methods. Phase objects get `.toric`, `.fund`, `.orbit_computed`, `.curve_signs` added dynamically.

**Why bad:** Hard to know what state a Wall or Phase has at any point. No IDE completion. Bugs from accessing attributes before they're set.

**Instead:** Initialize all fields in `__init__` (use `None` for "not yet computed"). Use the structured types (WallCategory enum, GVWallData dataclass) so the type system documents what's available.

### Anti-Pattern 3: String-Based Category Dispatch

**What:** `wall.category == 'su(2) enhancement'` scattered throughout the code.

**Why bad:** Typo-prone. No autocomplete. The string `'potent "flop" wall (insufficient degree)'` is unwieldy.

**Instead:** `WallCategory` enum. Pattern matching or explicit `if wall.category is WallCategory.SU2_ENHANCEMENT` checks.

### Anti-Pattern 4: Monkey-Patching at Module Scope Without Guards

**What:** `cytools.calabiyau.Invariants.gv_series = gv_series` at module top level -- executes on first import, no way to undo.

**Why bad:** Makes testing difficult. Two versions of cybir loaded simultaneously would clobber each other.

**Instead:** Isolate in `patching/` module. Apply on explicit `import cybir.patching` (or auto-apply via `cybir/__init__.py` with a flag). Store originals for potential restoration in tests.

## Dependency Graph (Build Order)

```
Layer 0 (no internal deps):
    core/util.py
    core/types.py
    core/lattice.py

Layer 1 (depends on Layer 0):
    core/algebra.py        [uses util]
    core/diagnosis.py      [uses util, algebra, types]
    core/wall_crossing.py  [uses util, types]

Layer 2 (depends on Layers 0-1):
    phases/phase.py        [uses types, lattice, util]
    phases/wall.py         [uses types, diagnosis, wall_crossing, algebra, phase]

Layer 3 (depends on Layers 0-2):
    phases/ekc.py          [uses phase, wall, types, lattice, util]

Layer 4 (cross-cutting, depends on Layers 0-1):
    patching/invariants.py [uses util; modifies cytools globals]
    patching/polytope.py   [uses phases/ekc; modifies cytools globals]
    patching/calabiyau.py  [modifies cytools globals]

Layer 5 (package interface):
    cybir/__init__.py      [re-exports from phases/, optionally applies patching/]
```

**Suggested build order for implementation phases:**

1. **Layer 0 first:** `core/types.py` (data types), `core/util.py` (pure helpers), `core/lattice.py` (cornell-dev decoupling). These have no internal dependencies and are needed by everything.

2. **Layer 1 next:** `core/wall_crossing.py`, `core/diagnosis.py`, `core/algebra.py`. These are the pure mathematical functions, extracted and cleaned up from the original free functions.

3. **Layer 2:** `phases/phase.py` and `phases/wall.py`. These are the stateful objects that use the core functions.

4. **Layer 3:** `phases/ekc.py`. The orchestrator that ties everything together. This is where `construct_phases` lives.

5. **Layer 4:** `patching/invariants.py`. The CYTools monkey-patches. These are needed for the orchestrator to actually run, but they're architecturally separate.

6. **Layer 5:** Package `__init__.py`, Sphinx docs, notebooks.

## Scalability Considerations

| Concern | h11 = 2-3 (typical) | h11 = 5-10 | h11 > 10 |
|---------|---------------------|------------|----------|
| Number of phases | 2-20 | 10-100+ | Potentially thousands |
| Wall diagnosis cost | Cheap (small GV tables) | Moderate (larger GV computations, ensure_nilpotency loops) | Expensive (GV computation dominates) |
| Memory for phases | Negligible | ~MB range (many int_nums tensors of size h11^3) | Could be significant; consider lazy computation |
| Phase deduplication | Linear scan OK | Dictionary lookup preferred | Dictionary essential |
| Weyl orbit expansion | Few reflections | Could multiply phase count significantly | Must cap or iterate carefully |

**Recommendation:** For the initial refactor, the dictionary-based phase registry is sufficient. If h11 > 10 becomes a target, consider lazy Phase objects that compute int_nums / c2 / Mori on demand rather than eagerly in the constructor.

## Sources

- Original source: `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/extended_kahler_cone.py` (~2700 lines)
- dbrane-tools package structure: `/Users/elijahsheridan/Research/string/cytools_code/dbrane-tools/`
- CYTools architecture: `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/software/CYTools/overview.md`
- CYTools pipeline: Polytope -> Triangulation -> ToricVariety -> CalabiYau (documented at cy.tools)
- arXiv:2212.10573 (Gendler et al.) and arXiv:2303.00757 (Demirtas et al.) -- algorithmic references for wall-crossing and EKC reconstruction
