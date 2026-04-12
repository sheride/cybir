# Phase 1: Foundation - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Package skeleton, data type design, test infrastructure, and cornell-dev decoupling for cybir. This phase delivers the types, utilities, and tests that Phases 2 and 3 build on. No math algorithms are ported here — just the containers, helpers, and verification infrastructure.

</domain>

<decisions>
## Implementation Decisions

### Package Layout
- **D-01:** All code lives in `cybir/core/` for this milestone. No `phases/` or `patching/` subdirectories.
- **D-02:** Module split: `types.py` (CalabiYauLite, ExtremalContraction, ContractionType, InsufficientGVError), `flop.py` (wall-crossing, diagnosis, GV math — Phase 2), `util.py` (normalize_curve, projection_matrix, lattice helpers, cornell-dev replacements), `ekc.py` (ExtendedKahlerCone orchestrator — Phase 3).
- **D-03:** Monkey-patches live next to the functions they relate to, not in a separate `patching/` module.

### Data Type Design
- **D-04:** `CalabiYauLite` — own version in cybir, interface-compatible with dbrane-tools' CalabiYauLite for future unification. Fields: int_nums, c2, kahler_cone, mori_cone, polytope, charges, indices, eff_cone, triangulation, fan (matching dbrane-tools), PLUS gv_invariants (reference to CYTools Invariants object) and label (phase ID for adjacency graph). Mutable by default; EKC orchestrator freezes after construction.
- **D-05:** `ExtremalContraction` (not `Contraction`, not `Wall`) — represents an extremal birational contraction (codim-1 in Kahler cone / ray of Mori cone). Fields: flopping_curve, start_phase, end_phase, contraction_type, gv_invariant, effective_gv, zero_vol_divisor, coxeter_reflection. All fields defined in `__init__` with `None` defaults for type-specific fields. Leaves `Contraction` available as a future base class for higher-codim faces.
- **D-06:** `ContractionType` — enum with 5 values: ASYMPTOTIC, CFT, SU2, SYMMETRIC_FLOP, FLOP. Configurable display notation so users can see Wilson (Type I/II/III) or 2212.10573 names. Details of notation mapping deferred to implementation.
- **D-07:** `InsufficientGVError` — exception subclass of RuntimeError, raised when GV series hasn't been computed to high enough degree.
- **D-08:** Phase adjacency graph as first-class object — phases as nodes, ExtremalContractions as edges.

### Cornell-dev Audit
- **D-09:** `misc.glsm` → use `charge_matrix_hsnf` from dbrane-tools util.py (SNF-based, gives proper Z-basis for kernel; flint nullspace can give generators that span over R but not Z).
- **D-10:** `misc.moving_cone` → port the 5-line function directly (iterates over columns of Q, takes cone of remaining columns' hyperplanes, forms intersection).
- **D-11:** `misc.sympy_number_clean` → rewrite as one-liner: `sympy.Rational(x).limit_denominator()`.
- **D-12:** `misc.tuplify` → rewrite simple recursive numpy-to-tuple converter.
- **D-13:** `lib.util.lattice` → drop entirely (only used in commented-out line, replaced by hsnf).
- **D-14:** Do NOT copy `lazy_cached` or other dbrane-tools utilities not needed by EKC code. Only bring what cybir actually uses.

### Test Strategy
- **D-15:** Generate test fixtures by running the original `extended_kahler_cone.py` on h11=2 polytopes and serializing the results (intersection numbers, phases found, contraction types, Coxeter matrices, adjacency structure).
- **D-16:** At this phase, tests cover data type instantiation, immutability enforcement, and cornell-dev replacement functions against known inputs. Integration tests against full EKC results come in Phase 3.

### Claude's Discretion
- pyproject.toml details (hatchling config, version, metadata)
- Exact adjacency graph implementation (networkx, custom dict-based, etc.)
- Immutability mechanism (frozen dataclass, `__setattr__` override, etc.)
- Test fixture serialization format (JSON, pickle, npz)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Original Source Code
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/extended_kahler_cone.py` — the ~2700-line original to be refactored
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/claude/CHANGES.md` — documents what prior refactors attempted (useful patterns to preserve or avoid)

### Prior Refactors
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/claude/extended_kahler_cone_claude_refactor.py` — first refactor
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/claude/extended_kahler_cone_claude_refactor_2.py` — second refactor

### Package Model
- `/Users/elijahsheridan/Research/string/cytools_code/dbrane-tools/dbrane_tools/core/geometry.py` — CalabiYauLite reference implementation (interface to match)
- `/Users/elijahsheridan/Research/string/cytools_code/dbrane-tools/dbrane_tools/core/util.py` — `charge_matrix_hsnf` to copy, general util patterns

### Cornell-dev Dependencies
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/Elijah/misc.py` — source of glsm, moving_cone, sympy_number_clean, tuplify

### Knowledge Base
- `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/software/CYTools/overview.md` — CYTools architecture and API
- `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/literature/2212.10573/paper.md` — EKC reconstruction method
- `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/literature/2303.00757/paper.md` — GV computation method

### Mathematics
- Wilson, "The Kähler cone on Calabi-Yau threefolds" (1992) — contraction type classification (Type I/II/III)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- dbrane-tools `charge_matrix_hsnf`: SNF-based GLSM charge matrix computation — copy into cybir util.py
- dbrane-tools `CalabiYauLite`: interface template for cybir's version — match the property API
- Original code utility functions (lines 43-200): normalize_curve, find_minimal_N, projection_matrix, projected_int_nums, is_asymptotic_facet, is_cft_facet, etc. — these move to util.py

### Established Patterns
- dbrane-tools uses properties with `_` private attributes (no dataclasses)
- CYTools monkey-patches are defined as standalone functions then assigned to classes (e.g., `cytools.triangulation.Triangulation.cyl = triang_to_cy`)
- Original code classes: Circuit (line 482), ExtendedKahlerCone (742), Wall (1360), Facet (2123), CY (2180), CY_GV (2291), CY_Toric (2361)

### Integration Points
- CYTools `cytools.calabiyau.CalabiYau` — monkey-patch target for EKC construction
- CYTools `cytools.cone.Cone` — used for Kahler/Mori cones, referenced by ExtremalContraction
- CYTools `Invariants` class (on CalabiYau) — monkey-patch target for GV operations (Phase 2/3)

</code_context>

<specifics>
## Specific Ideas

- CalabiYauLite should be designed so it can eventually be promoted to a centralized location (e.g., CYTools) shared by both cybir and dbrane-tools
- ExtremalContraction leaves room for a broader `Contraction` class later when higher-codim faces are needed
- The flint-based charge_matrix is specifically avoided because it can produce generators spanning the kernel over R but not Z — the hsnf version gives a proper Z-basis

</specifics>

<deferred>
## Deferred Ideas

- Tuned complex structure mode (ENH-02) — user wants to discuss algorithm details during implementation of a later phase
- Higher-codimension contractions — future generalization of ExtremalContraction
- Symbolic prepotential / sympy variable storage on CalabiYauLite — can be monkey-patched on later if needed

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-04-11*
