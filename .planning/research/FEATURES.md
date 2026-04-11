# Feature Landscape

**Domain:** CY3 birational geometry / extended Kahler cone reconstruction from GV invariants
**Researched:** 2026-04-11

## Table Stakes

Features the package must have or it is unusable -- these reproduce the mathematical capabilities of the original ~2700-line script.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **GV-based phase construction (`construct_phases`)** | The core algorithm: iteratively adjoin phases by flopping nop curves until moduli space boundary is reached. Without this, the package has no purpose. | High | Main loop with wall queue, deduplication, phase bookkeeping. Must match original math bit-for-bit. |
| **Wall diagnosis / classification** | Every wall must be classified as asymptotic, CFT, su(2) enhancement, symmetric flop, or generic flop. This is the decision logic that drives phase assembly. | High | Currently a ~100-line dispatcher with sub-cases. Needs structured return, not ad-hoc attribute mutation. |
| **GV series and effective GV computation** | Computing $n^0_{k[\mathcal{C}]}$ for $k=1,2,3,\ldots$ along a curve ray, and the effective GV $\sum k^3 n^0_{k[\mathcal{C}]}$ for wall-crossing. Required for every wall classification. | Med | Currently monkey-patched onto `cytools.calabiyau.Invariants`. |
| **Wall-crossing formula** | Transformation of intersection numbers $\kappa'_{abc} = \kappa_{abc} - n^0_\mathcal{C} \mathcal{C}_a \mathcal{C}_b \mathcal{C}_c$ and second Chern class $c'_a = c_a + 2n^0_\mathcal{C} \mathcal{C}_a$ across flop walls. | Low | Pure linear algebra, already correct. Needs clean function signature. |
| **Potent/nilpotent curve classification** | Classifying Mori cone generators as potent (infinite GV sequence) or nilpotent (finite). Nilpotent-outside-potent (nop) identification for flopping candidates. | Med | Relies on `ensure_nilpotency` which may trigger on-demand GV recomputation. |
| **Coxeter reflection / Weyl group computation** | Computing the Coxeter reflection matrices from su(2) and symmetric-flop walls. Building the Coxeter matrix from the full set of reflections. | Med | `get_coxeter_reflection`, `coxeter_matrix`. Essential for hyperextended cone. |
| **Weyl orbit expansion** | Expanding the fundamental domain of the EKC by applying stable Weyl reflections to all phases. Constructs the full hyperextended cone $\mathcal{K}_\text{hyp}$. | Med | Currently in `construct_phases` with `weyl=True`. Has known code-quality issues (comments like "should really copy over a LOT more data"). |
| **CY phase data model** | Each phase stores: intersection numbers, second Chern class, Mori cone, Kahler cone, walls, tip point. Must support equality comparison and deduplication. | Med | Currently split across `CY`, `CY_GV`, `CY_Toric`. Needs structured data types, not raw numpy arrays hanging off objects. |
| **Wall data model** | Each wall stores: curve, start/end phases, category, GV series, effective GV, Coxeter reflection (if applicable), zero-volume divisor. | Med | Currently `Wall` class with lots of mutable attributes set during diagnosis. Needs clean immutable-after-construction pattern or explicit state machine. |
| **CYTools monkey-patching** | `ensure_nilpotency`, `gv_series`, `gv_eff`, `copy`, `flop_gvs`, `gv_incl_flop`, `cone_incl_flop` on `Invariants`. Desired at Polytope, Triangulation, and CalabiYau levels too. | Med | Currently patches `Invariants` only. Extension to higher levels is a project requirement. |
| **Infinity cone and effective cone extraction** | After phase construction: collecting asymptotic/CFT walls into $\mathcal{M}_\infty$ generators, CFT/su(2) walls into effective cone generators. | Low | Currently done in a post-loop in `construct_phases`. |
| **Standalone lattice/combinatorics utilities** | `find_minimal_N`, `normalize_curve`, `matrix_period`, projection matrix, LCM, etc. Currently imported from `lib.util.lattice` and `misc`. | Low | Must be copied/refactored into cybir. No cornell-dev dependency. |
| **InsufficientGVError and error handling** | Explicit exception when GV series not computed to high enough degree, rather than silent miscategorization. | Low | Already implemented in refactor. Preserve. |

## Differentiators

Features that would set cybir apart from the original script. Not strictly required but significantly improve usability, correctness assurance, or research capability.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Structured data types (dataclasses/NamedTuples)** | Replace ad-hoc attribute mutation with typed, documented containers for Phase, Wall, WallDiagnosis, GVData, CoxeterData. Makes the API self-documenting and catches bugs at construction time. | Med | Project requirement. Key pain point of original code. |
| **Clean post-construction data access API** | After `construct_phases()`, users should access `ekc.phases`, `ekc.walls`, `ekc.infinity_cone`, `ekc.effective_cone`, `ekc.coxeter_matrix`, etc. through well-named, read-only properties -- not by reaching into sets of tuples. | Med | Project requirement. Current code has `self.infinity_cone_gens` as `set()` of tuples, awkward to use. |
| **Sphinx documentation with equation references** | Every public method/class documented with references to specific equations/sections in arXiv:2212.10573 and arXiv:2303.00757. Makes the code a companion to the papers. | Med | Project requirement. No other EKC code has this. Huge value for the research community. |
| **Phase graph / adjacency structure** | Expose the graph of phases connected by flop walls as a first-class object. Enables: counting phases, checking connectivity, traversal queries, visualization. | Low | Implicit in current code (walls link phases). Making it explicit is cheap and very useful. |
| **Serialization / caching of EKC results** | Save/load a fully constructed EKC to disk. Phase construction can take minutes to hours for large $h^{1,1}$; users should not have to recompute. | Med | Not in original. Would use JSON or pickle. Significant usability win. |
| **Verbose logging with configurable levels** | Replace scattered `print()` statements with proper `logging` module usage. Allow quiet, normal, verbose, debug modes. | Low | Original uses ad-hoc `if verbose: print(...)`. Easy cleanup. |
| **Validation / consistency checks** | Post-construction verification: e.g., confirm dual-coordinate identity $\mathcal{K}_\text{hyp} = \mathcal{M}_\infty^\vee$, check wall adjacency consistency, verify intersection number integrality after wall-crossing. | Med | Extremely valuable for catching bugs and building trust. Original has some `assert` statements but no systematic validation. |
| **Example notebooks** | Jupyter notebooks reproducing key results from arXiv:2212.10573 (e.g., $h^{1,1} = 2,3,4$ examples). Serve as both documentation and regression tests. | Med | Following dbrane-tools pattern. |
| **Progress reporting for long runs** | Phase construction for $h^{1,1} \geq 4$ can produce dozens to hundreds of phases. Show progress (phases found, walls remaining, current category breakdown). | Low | Simple counter/callback. Big UX improvement for long-running computations. |
| **Immutable phase objects after construction** | Once a phase is fully constructed and its walls diagnosed, freeze it. Prevents accidental mutation during later phases of the algorithm or by user code. | Low | Use `__setattr__` override or frozen dataclass. Prevents a class of subtle bugs. |

## Anti-Features

Features to explicitly NOT build in this milestone.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Toric EKC construction (`construct_phases_toric`)** | Explicitly out of scope per PROJECT.md. Needs qualitative rethinking, not just refactoring. The toric pipeline has fundamentally different data flow (fans, circuits, GLSM charges). | Defer to future milestone. Keep the GV-based pipeline clean and complete first. |
| **Toric GV computation methods** | Tightly coupled to the toric pipeline. Including them would pull in fan/circuit infrastructure that muddies the core GV-based API. | Defer. Will be merged after toric pipeline rethink. |
| **Genus > 0 GV invariants** | Out of scope per PROJECT.md. The algorithm in arXiv:2212.10573 uses only genus-zero GV invariants. Higher genus would require different methods (modular forms, etc.). | Do not design for extensibility here. If needed later, it would be a separate module. |
| **Non-toric-hypersurface CY3s** | Out of scope. The GV computation via mirror symmetry (arXiv:2303.00757) requires toric hypersurface structure. | Do not abstract the input interface to accommodate hypothetical future CY sources. |
| **GUI / interactive visualization** | Scope creep. Visualization is useful but should not be in the core package. | Provide data access that makes visualization easy in notebooks (e.g., phase graph as networkx-compatible adjacency). |
| **Database of precomputed EKC results** | Scope creep. A database is a separate project. | Support serialization so results can be saved/loaded, but do not build a database layer. |
| **Automatic GV degree optimization** | The original has commented-out logic for automatically determining how many GV invariants to compute. This is a research question, not a software feature. | Expose `InsufficientGVError` clearly so users can handle recomputation in their own workflow. |
| **Circuit class and toric diagnosis** | `Circuit`, `diagnose_toric`, `diagnose_no_GV`, toric GV helpers -- all belong to the toric pipeline. | Exclude from this milestone. The `Wall.diagnose` GV-based path is the only one in scope. |
| **`CY_Toric` class** | Only needed for toric pipeline. The GV-based pipeline uses `CY_GV` (or a unified `Phase` data type). | Exclude. |

## Feature Dependencies

```
GV series computation → Potent/nilpotent classification → Nop curve identification
                                                            ↓
Wall-crossing formula ← Wall diagnosis ← Nop curve identification
     ↓                       ↓
CY phase construction    Coxeter reflection computation
     ↓                       ↓
Phase deduplication      Weyl orbit expansion
     ↓                       ↓
construct_phases loop    Hyperextended cone construction
     ↓
Post-construction data extraction (infinity cone, effective cone, Coxeter matrix)
     ↓
Clean data access API / serialization / validation
```

Key ordering constraints:
- **Data types must be designed first**: Phase, Wall, WallDiagnosis types define the interfaces everything else uses.
- **Wall diagnosis before phase loop**: The classification logic is the heart of the algorithm; it must be correct and well-tested before being wired into the main loop.
- **Monkey-patching early**: GV series computation is called by wall diagnosis, so the `Invariants` extensions must be in place first.
- **Post-construction API last**: Depends on everything above being stable.

## MVP Recommendation

Prioritize:
1. **Structured data types** (Phase, Wall, WallDiagnosis) -- these define the API contract for everything else
2. **GV series / effective GV / ensure_nilpotency** as clean functions or methods (not monkey-patch-first; design the interface, then provide the monkey-patch as a convenience layer)
3. **Wall diagnosis pipeline** with all five categories (asymptotic, CFT, su(2), symmetric flop, generic flop)
4. **Wall-crossing formula** as pure functions
5. **Phase construction loop** (`construct_phases`) with proper bookkeeping
6. **Weyl orbit expansion** for hyperextended cone
7. **Post-construction read-only API** (phases, walls, cones, Coxeter matrix)
8. **CYTools monkey-patching** at Polytope/Triangulation/CalabiYau levels
9. **Sphinx documentation** with arXiv equation references

Defer to post-MVP:
- Serialization/caching: valuable but not blocking research use
- Phase graph as explicit object: easy to add later
- Validation suite: important but can be iterative
- Example notebooks: create after API stabilizes

## Sources

- Original source: `cornell-dev/projects/vex/elijah/extended_kahler_cone.py` (2697 lines)
- Claude refactor notes: `cornell-dev/projects/vex/elijah/claude/CHANGES.md`
- arXiv:2212.10573 (Gendler et al.) -- EKC reconstruction algorithm
- arXiv:2303.00757 (Demirtas et al.) -- GV computation method
- dbrane-tools package structure (local): `cytools_code/dbrane-tools/`
- [CYTools GitHub](https://github.com/LiamMcAllisterGroup/cytools)
- [CYTools paper](https://arxiv.org/abs/2211.03823)
