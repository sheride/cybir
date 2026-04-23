# cybir

## What This Is

A Python package for studying the birational geometry of Calabi-Yau threefold hypersurfaces in toric varieties. The initial scope is reconstructing the extended Kahler cone (EKC) of a CY3 from its genus-zero Gopakumar-Vafa invariants, following the methods of arXiv:2212.10573 (Gendler, Heidenreich, McAllister, Moritz, Rudelius) and arXiv:2303.00757 (Demirtas, Kim, McAllister, Moritz, Rios-Tascon). Built to integrate cleanly with CYTools.

## Core Value

A clean, well-documented, modular implementation of GV-based EKC construction that is easy to use, extend, and understand — structured as a proper Python package with Sphinx documentation and CYTools monkey-patching.

## Requirements

### Validated

- [x] Structured data types for phases, walls, curves (not ad-hoc attributes) — Validated in Phase 1: Foundation
- [x] Proper Python package structure (like dbrane-tools: `cybir/core/`, `cybir/analysis/`, `__init__.py`) — Validated in Phase 1: Foundation
- [x] Decouple from cornell-dev: copy/refactor anything currently imported from `lib.util.lattice` and `misc` — Validated in Phase 1: Foundation
- [x] Sphinx documentation with arXiv references to equations/sections in 2212.10573 and 2303.00757 — Validated in Phase 8: Deploy cybir Sphinx docs to GitHub Pages (CI build + deploy workflow, autodoc_mock_imports narrow list, public site at https://sheride.github.io/cybir)

### Active

- [ ] Refactor the GV-based `construct_phases` pipeline into clean, modular code
- [ ] Proper Python package structure (like dbrane-tools: `cybir/core/`, `cybir/analysis/`, `__init__.py`)
- [ ] Cleaner, more consistent naming and intuitive public API for accessing EKC data after construction
- [ ] Structured data types for phases, walls, curves (not ad-hoc attributes)
- [ ] CYTools monkey-patching at Polytope, Triangulation, and CalabiYau levels
- [ ] Decouple from cornell-dev: copy/refactor anything currently imported from `lib.util.lattice` and `misc`
- [ ] Preserve mathematical correctness of all algorithms (wall-crossing, GV classification, Weyl reflections, etc.)
- [ ] Look for efficiency improvements and better OO organization throughout

### Out of Scope

- Toric EKC construction (`construct_phases_toric` pipeline) — needs qualitative rethinking, deferred to future milestone
- Toric GV computation methods — will be merged later, after the core refactor
- Genus > 0 GV invariants
- Non-toric-hypersurface CY3s

## Context

The code originates as a ~2700-line single-file script (`extended_kahler_cone.py`) in the cornell-dev repo. It has been through two prior Claude refactors that reorganized the code (class hierarchy, error handling, module sections, consolidated toric GV helpers) but didn't produce a qualitatively different or more usable result. The key issues were: naming inconsistencies, awkward data access patterns after phase construction, lack of structured data types, and no proper package/documentation structure.

The earlier refactors (documented in `CHANGES.md` in the claude/ directory) did useful work on:
- `InsufficientGVError` exception instead of silent categorization
- `_register_new_cy` shared bookkeeping helper
- Class hierarchy cleanup (CY base → CY_GV → CY_Toric)
- Consolidated toric GV helpers
- Wall diagnosis dispatcher pattern
- Invariants monkey-patch cleanup

These ideas may be worth preserving or building on.

External dependencies (numpy, scipy, flint, hsnf, sympy, cytools) are fine. Dependencies on cornell-dev (`lib.util.lattice`, `misc`) must be eliminated by copying/refactoring the needed functionality into cybir.

## Constraints

- **Mathematical correctness**: All algorithms must remain bit-for-bit equivalent to the original — wall-crossing formula, potent/nilpotent classification, asymptotic/CFT/su(2)/symmetric-flop/flop diagnosis, Weyl orbit expansion, Coxeter matrix computation, etc.
- **CYTools compatibility**: Must work with the CYTools version in the `cytools` conda environment on this machine
- **Package structure**: Follow the dbrane-tools model — `cybir/core/`, Sphinx docs in `documentation/`, notebooks for examples

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Package name: `cybir` | Short for CY birational geometry; broader scope than just EKC | — Pending |
| Exclude toric pipeline from this milestone | Needs qualitative rethinking, not just refactoring | — Pending |
| Decouple from cornell-dev | Want a standalone package, not dependent on internal repo | — Pending |
| Follow dbrane-tools structure | Proven pattern for this group's packages (Sphinx + core/analysis split) | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-23 after Phase 8 completion*
