# Phase 2: Core Mathematics - Context

**Gathered:** 2026-04-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Port all mathematical algorithms from `extended_kahler_cone.py` into cybir, operating on the Phase 1 data types (CalabiYauLite, ExtremalContraction, ContractionType), with verified correctness against the original code. This phase delivers the math functions and their tests — not the BFS pipeline or CYTools integration (Phase 3).

</domain>

<decisions>
## Implementation Decisions

### Module Organization
- **D-01:** Split math into multiple modules under `cybir/core/`:
  - `flop.py` — wall-crossing formula (intersection number + c2 transform across a flop)
  - `classify.py` — contraction type classification (asymptotic, CFT, su(2), symmetric flop, generic flop)
  - `gv.py` — GV series computation, effective GV, potent/nilpotent curve classification, nop identification
- **D-02:** Coxeter reflection functions (`get_coxeter_reflection`, `coxeter_matrix`) go in `util.py` alongside existing utilities — only 2 functions, not worth a dedicated module.
- **D-03:** `ekc.py` remains a placeholder — that's the Phase 3 orchestrator (construct_phases BFS, Weyl expansion, post-construction API).

### API Surface
- **D-04:** Standalone functions are the real implementation (e.g., `flop.wall_cross(cy_lite, curve, ...)`). Types stay as data containers.
- **D-05:** Thin convenience methods on CalabiYauLite/ExtremalContraction that delegate to standalone functions (e.g., `contraction.classify()` calls `classify.classify_contraction(contraction)`). Mirrors the original code's pattern of standalone + class method wrappers.
- **D-06:** All math functions must be individually callable — not buried inside class methods.

### Correctness Verification
- **D-07:** Intermediate value snapshots for all 36 h11=2 polytopes. Run the original `extended_kahler_cone.py`, capture values at each stage (intersection numbers after wall-crossing, GV series values, classification decisions per wall, Coxeter reflections) — not just final outputs.
- **D-08:** Tests compare cybir's intermediate results against these snapshots. This pinpoints where any divergence occurs rather than just detecting it.

### Data Organization
- **D-09:** Preserve ALL information from the original code's data structures (every attribute on CY, Wall, Facet, EKC — e.g., `start_cy`/`end_cy` on walls, `coxeter_refs` on EKC, phase keying by intersection number tuples). Nothing should be silently dropped.
- **D-10:** Reorganize into cleaner data structures where it makes sense. The researcher should sweep the original EKC code, catalog all data storage patterns, and propose concrete reorganizations before planning.
- **D-11:** Use "classify" terminology throughout (not "diagnose") — e.g., `classify_contraction`, `classify.py`.

### Equation Citations
- **D-12:** Every math function docstring must cite the relevant equation from arXiv:2212.10573 or arXiv:2303.00757 with: equation number, brief physical context (1-2 sentences), AND the actual equation in LaTeX so it renders in Sphinx docs.

### Claude's Discretion
- Exact function signatures (argument names, return types)
- How to structure test fixtures (JSON, npz, pickle) as long as they capture intermediate values
- Specific reorganization proposals for data structures (subject to D-09: nothing dropped)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Original Source Code
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/extended_kahler_cone.py` — the ~2700-line original; ALL math functions to port live here. Researcher MUST sweep this for data storage patterns (D-10).
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/claude/CHANGES.md` — prior refactor notes

### Prior Refactors
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/claude/extended_kahler_cone_claude_refactor.py` — first refactor
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/claude/extended_kahler_cone_claude_refactor_2.py` — second refactor

### Phase 1 Implementation (cybir types and utilities)
- `cybir/core/types.py` — CalabiYauLite, ExtremalContraction, ContractionType, InsufficientGVError
- `cybir/core/util.py` — existing utilities (normalize_curve, projection_matrix, moving_cone, etc.) — Coxeter functions will be added here
- `cybir/core/graph.py` — PhaseGraph adjacency graph

### Knowledge Base
- `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/literature/2212.10573/paper.md` — EKC reconstruction method (equation citations for docstrings)
- `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/literature/2303.00757/paper.md` — GV computation method (equation citations for docstrings)

### Mathematics
- Wilson, "The Kähler cone on Calabi-Yau threefolds" (1992) — contraction type classification (Type I/II/III)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cybir/core/types.py`: CalabiYauLite (12 properties, freeze mechanism), ExtremalContraction (8 properties, frozen by default), ContractionType (5-member enum with dual notation)
- `cybir/core/util.py`: normalize_curve, projection_matrix, moving_cone, charge_matrix_hsnf, sympy_number_clean, tuplify — these are already ported and tested
- `cybir/core/graph.py`: PhaseGraph with networkx backend — phases as nodes, contractions as edges

### Established Patterns
- Types use `__setattr__` + `_frozen` flag for immutability (not frozen dataclass) to support numpy arrays
- Properties return `np.copy` for defense-in-depth on array fields
- PhaseGraph uses string labels as node keys; ExtremalContraction start/end store labels not objects

### Integration Points
- `flop.py` placeholder exists (1 line) — ready for wall-crossing implementation
- ExtremalContraction already has fields for all classification results (contraction_type, gv_invariant, effective_gv, zero_vol_divisor, coxeter_reflection)
- ContractionType enum already has ASYMPTOTIC, CFT, SU2, SYMMETRIC_FLOP, FLOP values

</code_context>

<specifics>
## Specific Ideas

- The researcher should systematically catalog every attribute on CY, CY_GV, Wall, Facet, and ExtendedKahlerCone in the original code, then propose how each maps to cybir's types (CalabiYauLite, ExtremalContraction, PhaseGraph) or needs a new home
- Intermediate test snapshots should capture enough to independently verify each function — not just inputs/outputs but the internal state that led to a classification decision (e.g., which GV values triggered a CFT vs su(2) classification)

</specifics>

<deferred>
## Deferred Ideas

- Tuned complex structure mode (ENH-02) — deferred from Phase 1, user wants to discuss during later implementation
- Higher-codimension contractions — future generalization
- BFS pipeline, Weyl expansion, CYTools monkey-patching — all Phase 3

</deferred>

---

*Phase: 02-core-mathematics*
*Context gathered: 2026-04-12*
