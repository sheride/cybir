# Phase 3: Pipeline & Integration - Context

**Gathered:** 2026-04-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire the Phase 1-2 math modules into a BFS-driven EKC construction pipeline, add Weyl orbit expansion, expose a clean post-construction read-only API, monkey-patch CYTools at three levels, and build Sphinx docs with example notebooks. This phase delivers the full user-facing package.

</domain>

<decisions>
## Implementation Decisions

### Data Organization
- **D-01:** `ExtremalContraction` drops `start_phase`/`end_phase` fields. The graph encodes topology — `CYGraph.add_contraction(contraction, phase_a, phase_b)` takes both phases as arguments. `CYGraph` provides `phases_adjacent_to(contraction)` and `contractions_from(phase_label)` for queries.
- **D-02:** Curves are stored in canonical form (first nonzero component positive, via `normalize_curve`). When accessed from a specific phase's perspective (`contractions_from`), curves are oriented inward to that phase's Kahler cone. The sign flip is edge metadata stored on the graph.
- **D-03:** Kahler cone face geometric data (normal vector, facet data) is monkey-patched onto CYTools `Cone` objects rather than duplicated on `ExtremalContraction`. The contraction holds a reference to the cone face.
- **D-04:** Drop `Circuit`, `start_circuit`, `end_circuit` entirely — toric pipeline is v2.
- **D-05:** BFS tracking data (explored set, visit order) is kept on the orchestrator as a build log, persists after construction for debugging.
- **D-06:** Cone generators (`coxeter_refs`, `sym_flop_refs`, `infinity_cone_gens`, `eff_cone_gens`) live on the orchestrator (`CYBirationalClass`), not on the graph.

### Pipeline Orchestrator
- **D-07:** Rename `ExtendedKahlerCone` to `CYBirationalClass`. This is the main result/orchestrator object.
- **D-08:** `CYBirationalClass` holds: `CYGraph` (phases + contractions), reference to CYTools `CalabiYau` (the root), cone generators, Weyl expansion data, read-only query API.
- **D-09:** Step-by-step construction API:
  ```python
  ekc = CYBirationalClass(cy)          # cheap: wraps CY, builds root phase
  ekc.setup_root(max_deg=10)            # moderate: computes GVs
  ekc.construct_phases(verbose=True)    # expensive: BFS
  ekc.expand_weyl()                     # optional: Weyl expansion
  ```
- **D-10:** Convenience classmethod `CYBirationalClass.from_gv(cy, max_deg=10)` runs all steps and returns the populated object. Future `from_toric` classmethod for toric pipeline (v2).
- **D-11:** Construction logic lives in a separate builder module (`build_gv.py`), not in the class itself. `CYBirationalClass` is the result container + query API. `from_gv` delegates to the builder.
- **D-12:** Post-construction read-only API: `ekc.phases`, `ekc.contractions`, `ekc.coxeter_matrix`, `ekc.graph`, etc. No ad-hoc attribute hunting.

### Weyl Expansion
- **D-13:** Weyl expansion is a separate step from BFS construction. `construct_phases` accumulates reflection data (`coxeter_refs`, `sym_flop_refs`); `expand_weyl` uses that data to generate the hyperextended cone. They are independently testable.
- **D-14:** `expand_weyl` can be called lazily — only when someone asks for the hyperextended cone.

### CYTools Monkey-Patching
- **D-15:** Three levels of patching:
  - `CalabiYau.birational_class(**kwargs)` → main entry point, returns `CYBirationalClass.from_gv(self, **kwargs)`
  - `Invariants` → GV-related helpers the builder uses internally (`gv_series`, `gv_eff`, `ensure_nilpotency`)
  - `Polytope.birational_class(**kwargs)` → convenience, does `self.triangulate().get_cy().birational_class(**kwargs)`
  - Skip `Triangulation` level — no value over going through CY directly.
- **D-16:** Patches activated by explicit `cybir.patch_cytools()` call, not on import. No surprises.
- **D-17:** Version guards on all patches — check CYTools version, warn/skip if incompatible.

### Documentation & Notebooks
- **D-18:** Sphinx setup mirrors dbrane-tools `conf.py` pattern (sphinx-book-theme, myst-nb, napoleon, mathjax, sphinx-autodoc-typehints, sphinx-copybutton, sphinx_design, sphinx-togglebutton).
- **D-19:** Two example notebooks: h11=2 walkthrough (full pipeline, inspect phases/contractions/Weyl) and h11=3 (more complex example). Pre-executed, regenerated periodically — not executed during doc build.
- **D-20:** API reference auto-generated from numpy-style docstrings. No additional narrative docs for now — arXiv papers cover the math.

### Claude's Discretion
- Exact builder module name and internal structure
- Specific CYTools Invariants methods to patch (based on what the builder actually needs)
- Sphinx conf.py details and notebook content structure
- BFS implementation details (queue type, deduplication strategy)
- `CYGraph` API additions needed for `contractions_from` and curve orientation

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Original Source Code
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/extended_kahler_cone.py` — the ~2700-line original. The BFS loop (`construct_phases`), Weyl expansion, and CYTools integration patterns are all here.

### Prior Refactors
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/claude/CHANGES.md` — prior refactor notes
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/claude/extended_kahler_cone_claude_refactor.py` — first refactor
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/claude/extended_kahler_cone_claude_refactor_2.py` — second refactor

### cybir Phase 1-2 Code (the modules this phase wires together)
- `cybir/core/types.py` — CalabiYauLite, ExtremalContraction, ContractionType, CYGraph
- `cybir/core/classify.py` — classify_contraction and helpers
- `cybir/core/flop.py` — wall_cross_intnums, wall_cross_c2, flop_phase
- `cybir/core/gv.py` — gv_series, gv_eff, is_potent, is_nilpotent
- `cybir/core/util.py` — projection, Coxeter, lattice utilities
- `cybir/core/graph.py` — CYGraph

### dbrane-tools Documentation Pattern
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/dbrane-tools/` — Sphinx conf.py and doc structure to mirror

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CYGraph` (graph.py): Phase adjacency graph — needs `contractions_from`, `phases_adjacent_to`, curve orientation support added
- `CalabiYauLite` (types.py): Phase data container — already has `flop()` convenience method
- `ExtremalContraction` (types.py): Contraction data — needs `start_phase`/`end_phase` fields removed, cone face reference added
- All math functions (classify.py, flop.py, gv.py, util.py): Ready to wire into pipeline
- `tests/fixtures/h11_2/`: 36 polytope snapshots for integration testing

### Established Patterns
- Standalone functions as real implementation, thin convenience methods on types (D-04/D-05 from Phase 2)
- Numpy-style docstrings with arXiv equation citations
- `normalize_curve` for canonical curve forms
- Immutable types after construction (freeze pattern)

### Integration Points
- `cybir/core/` — new modules: `ekc.py` (CYBirationalClass), `build_gv.py` (BFS builder), `weyl.py` (expansion), `patch.py` (monkey-patching)
- `cybir/__init__.py` — re-export CYBirationalClass, patch_cytools
- `documentation/` — Sphinx docs directory
- `notebooks/` — example notebooks

</code_context>

<specifics>
## Specific Ideas

- The step-by-step API (`__init__` → `setup_root` → `construct_phases` → `expand_weyl`) preserves the original code's workflow where users may want to inspect intermediate state
- Curve orientation is edge metadata on the graph, not a property of the contraction itself
- Cone face geometry monkey-patched onto CYTools Cone objects to avoid data duplication

</specifics>

<deferred>
## Deferred Ideas

- Toric pipeline (`from_toric` classmethod, `build_toric.py`) — v2
- `Circuit` class for toric fan data — v2
- `Triangulation.birational_class()` convenience patch — low value
- Serialization/caching of EKC results (ENH-01)
- Narrative "how the algorithm works" documentation page

</deferred>

---

*Phase: 03-pipeline-integration*
*Context gathered: 2026-04-12*
