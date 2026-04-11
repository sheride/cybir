# Domain Pitfalls

**Domain:** Refactoring research-grade CY birational geometry code into a Python package
**Researched:** 2026-04-11

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: Reorganization Without Rethinking (the "same code in more files" trap)

**What goes wrong:** Two prior Claude refactors moved code around -- reordering classes, extracting dispatchers, renaming methods -- without changing the fundamental data model or access patterns. The result was the same code in a different shape, not qualitatively better code. The user explicitly rejected this outcome twice.

**Why it happens:** AI refactoring tools (and human developers) default to the easiest transformation: move code between files, extract methods, rename things. These are mechanical transformations that feel productive but do not address root causes like awkward data access, ad-hoc attribute attachment, or missing domain abstractions.

**Consequences:** Wasted effort, user loses trust in the tool, and the next refactor starts from an already-muddied codebase. The second refactor (refactor_2.py) introduced `ToricData`, `GVInvariants` wrapper, and type hints -- but still left the `Wall` class as a 700-line god object with mutable state scattered across diagnosis, flopping, and bookkeeping.

**Prevention:**
- Before writing any code, identify the 3-5 concrete usability problems (not code smells) that the refactor must fix. For cybir, these are: (1) after `construct_phases`, accessing results requires knowing internal attribute names like `infinity_cone_gens`, `eff_cone_gens`, `coxeter_refs`; (2) Wall objects accumulate attributes dynamically during `diagnose()` (`zero_vol_divisor`, `coxeter_reflection`, `category_note`, `flip_polytope_note`) with no indication of what exists; (3) CY equality is `np.allclose` on intersection numbers -- fragile and semantically wrong for lattice data; (4) the `start=True` flag pattern on every Wall method is a code smell indicating the Wall/CY relationship is modeled wrong.
- Write usage examples (how a researcher would call the API in a notebook) BEFORE designing the internal structure.
- Each module/class change must trace back to a specific usability improvement.

**Detection:** If a PR diff is mostly `import` changes, file moves, and renames with no new data types or API changes, the refactor is reorganization, not rethinking.

**Phase:** Must be addressed in the very first design phase, before any code is written.

### Pitfall 2: Breaking Mathematical Correctness During Refactoring

**What goes wrong:** The wall-crossing formula, GV classification logic (potent/nilpotent, asymptotic/CFT/su(2)/symmetric-flop/flop), Weyl orbit expansion, Coxeter matrix computation, and intersection number transformations under flopping are mathematically intricate. A refactoring change that looks trivial -- reordering an if/elif chain, changing a sign convention, swapping `start=True` defaults -- can silently produce wrong physics.

**Why it happens:** The code encodes domain knowledge that is not obvious from variable names. For example:
- `normalize_curve` sets a sign convention (first nonzero entry positive) that the entire deduplication system relies on.
- The `gv_eff_1` and `gv_eff_3` quantities are `sum(n * GV(nC))` and `sum(n^3 * GV(nC))` -- swapping them silently breaks the wall-crossing formula for intersection numbers vs. second Chern class.
- The `precompose` matrix on GV invariants handles change-of-basis; losing it means GV lookups return values for the wrong curve class.
- The Coxeter reflection `get_coxeter_reflection(zero_vol_divisor, curve)` argument order matters; the matrix acts by `I - 2 * outer(curve, divisor) / dot(curve, divisor)`.

**Consequences:** The code runs without errors but produces wrong extended Kahler cones. Since there is no ground truth for most geometries, the error may not be caught until a paper is submitted or a downstream computation gives contradictory results.

**Prevention:**
- Build a test suite of known EKC results BEFORE refactoring. Use small h11 (2 or 3) polytopes where the answer can be verified by hand or from published results (arXiv:2212.10573 Table 1, arXiv:2303.00757).
- Test at the level of `construct_phases` output: number of phases, wall categories, infinity/effective cone generators, Coxeter matrices. Not at the level of individual functions (those tests are useful but insufficient).
- Every mathematical function must have a docstring citing the specific equation number in 2212.10573 or 2303.00757 that it implements.
- When moving code, run the integration test after every structural change, not just at the end.

**Detection:** Any change to files containing `wall_cross_intnums`, `wall_cross_second_chern_class`, `diagnose`, `is_symmetric`, `get_coxeter_reflection`, or `compute_gv_eff` should trigger a full integration test run.

**Phase:** Testing infrastructure must be built in the first phase, before any refactoring begins.

### Pitfall 3: Premature Abstraction Over the GV vs. Toric Split

**What goes wrong:** The GV-based pipeline (`construct_phases`) and toric pipeline (`construct_phases_toric`) share some structure (both explore phases by flopping across walls) but differ in critical ways: how GV invariants are computed (from the Invariants object vs. from toric intersection theory), how walls are diagnosed (the GV pipeline uses `gv_series` nilpotency; the toric pipeline uses circuit types), and how new CYs are constructed (different `flop_cy` vs `flop_cy_toric` paths). The first refactor tried to unify them via `_register_new_cy`. The second introduced a class hierarchy `CY -> CY_GV / CY_Toric`. Both created leaky abstractions where the unified interface constantly needed `isinstance` checks or `start=True` flags.

**Why it happens:** The two pipelines look similar at a distance (both walk a graph of Kahler cones connected by walls), but the details of what data is available and how diagnosis works are fundamentally different. Forcing them into a shared abstraction creates the "wrong seam" problem -- the abstraction boundary cuts across the natural structure of the mathematics.

**Consequences:** The toric pipeline is explicitly out of scope for this milestone. But if the GV pipeline is designed with a premature eye toward "making it easy to add toric later," the abstractions will be wrong for both. The GV pipeline should be designed for GV-pipeline clarity, and the toric pipeline should be designed independently later.

**Prevention:**
- Design cybir's first milestone around the GV pipeline ONLY. Do not add abstract base classes, protocol interfaces, or hook points for the toric pipeline.
- When a function takes `start=True` to choose between `start_cy` and `end_cy`, that is not an abstraction -- it is a flag. Replace it with explicit methods or clear data flow.
- The toric milestone can introduce shared abstractions once both pipelines exist concretely.

**Detection:** If the design includes any class named `BasePipeline`, `AbstractWall`, or similar, or if any method signature includes parameters that only exist for the toric case, the abstraction is premature.

**Phase:** Architecture/design phase. Revisit when toric milestone begins.

## Moderate Pitfalls

### Pitfall 4: Dynamic Attribute Accumulation on Wall Objects

**What goes wrong:** The current `Wall` class starts with ~12 constructor parameters, then accumulates additional attributes during `diagnose()`: `zero_vol_divisor`, `coxeter_reflection`, `zero_vol_divisor_result`, `category_note`, `flip_polytope_note`, `minface_dim`, `moving_wall`. Some of these are set conditionally (only for certain wall categories). Code that accesses `wall.coxeter_reflection` on a generic flop wall gets `AttributeError`. This is the single most common source of confusion when working with the results of `construct_phases`.

**Prevention:**
- Introduce structured result types for wall diagnosis. A diagnosed wall should carry a `DiagnosisResult` (or similar) dataclass with well-defined fields per category, not ad-hoc attributes.
- All attributes that a Wall might have should be declared in `__init__` (set to `None` if not yet computed). No `setattr` during diagnosis.
- Consider making diagnosis return a new object (immutable result) rather than mutating the wall in place.

**Detection:** `grep` for `self.` assignments outside `__init__` in the Wall class.

**Phase:** Core data model design phase.

### Pitfall 5: Losing the `misc` and `lib.util.lattice` Functionality Mapping

**What goes wrong:** The code imports `misc.moving_cone`, `misc.glsm`, `misc.sympy_number_clean`, `misc.tuplify` and `lib.util.lattice.extended_euclidean` (commented out but referenced). When decoupling from cornell-dev, developers copy these functions without understanding which are used, which are dead code, and which have subtle behavior that downstream code relies on. The `misc.glsm` function in particular computes GLSM charge matrices from fan vectors -- this is nontrivial lattice computation.

**Prevention:**
- Before copying anything, build a complete call graph from `extended_kahler_cone.py` into `misc` and `lib.util.lattice`. For each function: (a) is it actually called in the GV pipeline (not just toric)? (b) does CYTools already provide equivalent functionality?
- `misc.moving_cone` computes the moving cone of divisors -- check if CYTools' `Polytope` or `Cone` classes already expose this.
- `misc.glsm` computes GLSM charges -- CYTools' `Polytope.glsm_charge_matrix()` likely does the same thing. Verify equivalence before duplicating.
- `misc.sympy_number_clean` is a display helper; consider replacing with standard formatting.
- `misc.tuplify` is trivial; inline it.

**Detection:** If the new package contains a file named `utils.py` or `helpers.py` with copied functions that are only called once, the decoupling was done mechanically rather than thoughtfully.

**Phase:** Dependency audit phase, early in the project.

### Pitfall 6: Monkey-Patching CYTools Without Versioning Guards

**What goes wrong:** The code monkey-patches `cytools.calabiyau.Invariants` with methods like `gv_series`, `gv_eff`, `copy`, `flop_gvs`, `gv_incl_flop`, `cone_incl_flop`, `ensure_nilpotency`. These patches assume specific internal structure of the `Invariants` class (`_charge2invariant` dict, `grading_vec` attribute). A CYTools version update that changes `Invariants` internals will silently break the monkey-patches.

**Prevention:**
- The second refactor's `GVInvariants` wrapper approach is better than monkey-patching. Use composition (wrapper holds an `Invariants` instance) rather than modification.
- If monkey-patching is retained for CYTools integration at the `Polytope`/`Triangulation`/`CalabiYau` level, add version checks: `assert cytools.__version__ == "X.Y.Z"` or at minimum document the tested version.
- Pin the CYTools version in package dependencies.
- Write integration tests that exercise the monkey-patched methods so version breakage is caught immediately.

**Detection:** Any `setattr(cytools.some_class, 'method_name', ...)` without a corresponding version check or integration test.

**Phase:** Package structure and CYTools integration phase.

### Pitfall 7: Losing Numerical Precision in Lattice Computations

**What goes wrong:** The code mixes exact integer arithmetic (lattice vectors, GLSM charges, intersection numbers) with floating-point operations (`np.linalg.inv`, `np.allclose`, `scipy.linalg.null_space`). The `cob` (change-of-basis) matrix is inverted with `np.rint(np.linalg.inv(cob)).astype(int)` -- this works for small integer matrices but is fragile. CY equality is checked with `np.allclose` on intersection numbers that should be exact integers.

**Prevention:**
- Use exact integer arithmetic (Python ints, `hsnf`, `flint`) for all lattice operations. Reserve `np.float64` for cone interior point computations only.
- Replace `np.allclose` equality with exact integer comparison where the quantities are known to be integers.
- For change-of-basis inversion, use `hsnf` or `flint` for exact integer matrix inversion rather than float inversion followed by rounding.
- Document which quantities are exact integers and which are floating-point approximations.

**Detection:** `np.allclose` used to compare quantities that should be exact integers. `np.linalg.inv` followed by `.astype(int)` on lattice matrices.

**Phase:** Core data model phase (choose representations) and throughout implementation.

### Pitfall 8: The `Facet(Wall)` Inheritance Is a Domain Modeling Error

**What goes wrong:** In the original code, `Facet` inherits from `Wall` but represents a different concept: a facet of a Kahler cone (before diagnosis) vs. a wall between two phases (after diagnosis). The inheritance creates confusion about when a Facet "becomes" a Wall and what data is available at each stage. The second refactor eliminated `Facet` by making it an optional storage on `Wall`, but this made every Wall carry nullable cone/facet data.

**Prevention:**
- Separate the concepts clearly: a Kahler cone facet (geometric boundary of one phase's cone) and a wall (relationship between two adjacent phases). A facet may be promoted to a wall during exploration, but they are not an inheritance relationship.
- Consider: facets are inputs to the exploration algorithm; walls are outputs. The algorithm discovers that certain facets correspond to walls between phases.

**Detection:** If `Wall.__init__` has more than 5-6 parameters, or if many parameters are `None` by default and set later, the class is trying to represent multiple lifecycle stages.

**Phase:** Core data model design.

## Minor Pitfalls

### Pitfall 9: The `start=True` Flag Pattern

**What goes wrong:** Nearly every method on `Wall` takes `start=True` to select between `start_cy` and `end_cy`. This is error-prone (easy to forget or pass the wrong value) and makes the code harder to read. It also encodes a directed-ness into walls that is sometimes physical (flop direction) and sometimes arbitrary (which side was explored first).

**Prevention:** Model walls as undirected relationships between two phases. Give each wall a clear "from" and "to" based on the exploration order, and make the direction explicit in method names (`wall.flopped_int_nums()` rather than `wall.wall_cross_intnums(start=True)`).

**Phase:** API design phase.

### Pitfall 10: Sphinx Documentation That Documents Structure, Not Mathematics

**What goes wrong:** Docstrings describe parameter types and return values but not the mathematical content. A researcher reading `wall_cross_intnums(int_nums, curve, gv_eff_3)` needs to know that this implements Equation (2.7) of arXiv:2212.10573: kappa'_ijk = kappa_ijk + N_3 * C_i * C_j * C_k. Without this, the code is opaque to anyone who did not write it.

**Prevention:**
- Every function that implements a formula from the papers must cite the paper and equation number in its docstring.
- Use LaTeX in Sphinx docstrings (with `sphinx.ext.mathjax`) to render the formulas.
- Group the Sphinx docs by mathematical topic (wall-crossing formulas, GV classification, Weyl group), not by Python module.

**Phase:** Documentation phase, but equation references should be added during implementation.

### Pitfall 11: Test Fixtures Requiring Full CYTools Computation

**What goes wrong:** Integration tests that start from `Polytope.triangulate().cy().compute_gvs(...)` take minutes per test case because GV computation is expensive. This makes the test suite too slow to run during development, so developers stop running tests.

**Prevention:**
- Serialize the output of `compute_gvs` for 2-3 small test polytopes (h11=2, h11=3) and load from fixtures in tests.
- Test mathematical functions (wall-crossing, classification, Coxeter reflection) with synthetic inputs that do not require CYTools at all.
- Reserve full-pipeline integration tests (starting from polytope) for CI only, not local development.

**Detection:** If `import cytools` appears in more than 2-3 test files, the tests are too tightly coupled to CYTools.

**Phase:** Test infrastructure phase (should be first or second phase).

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Data model design | Premature abstraction for toric pipeline (#3) | Design for GV pipeline only; defer toric abstractions |
| Data model design | Dynamic attribute accumulation (#4) | Require all attributes in `__init__`; use result dataclasses for diagnosis |
| Data model design | Wall/Facet confusion (#8) | Separate facet (input) from wall (output) concepts |
| Dependency decoupling | Blind copying of `misc`/`lib.util.lattice` (#5) | Map call graph first; check CYTools equivalents |
| Core implementation | Mathematical correctness (#2) | Build integration tests BEFORE refactoring |
| Core implementation | Numerical precision (#7) | Use exact integer arithmetic for lattice data |
| CYTools integration | Monkey-patch breakage (#6) | Use wrapper pattern; add version guards |
| API design | `start=True` flag proliferation (#9) | Model walls as undirected; explicit direction in method names |
| Documentation | Structure-only docs (#10) | Require equation citations in every math function docstring |
| Testing | Slow test suite (#11) | Serialize fixtures; test math functions independently of CYTools |

## Sources

- Prior refactor analysis: `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/claude/CHANGES.md`
- Original source: `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/extended_kahler_cone.py` (2697 lines)
- First refactor: `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/claude/extended_kahler_cone_claude_refactor.py` (2837 lines)
- Second refactor: `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/claude/extended_kahler_cone_claude_refactor_2.py` (2519 lines)
- CYTools pitfalls: `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/software/CYTools/pitfalls.md`
- arXiv:2212.10573 (Gendler, Heidenreich, McAllister, Moritz, Rudelius) -- primary algorithm reference
- arXiv:2303.00757 (Demirtas, Kim, McAllister, Moritz, Rios-Tascon) -- toric methods reference
