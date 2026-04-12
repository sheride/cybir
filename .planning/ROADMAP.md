# Roadmap: cybir

## Overview

Transform the ~2700-line `extended_kahler_cone.py` script into a clean, modular Python package (`cybir`) for GV-based extended Kahler cone construction. The approach is foundation-first: establish structured data types, package skeleton, and test infrastructure before porting math or building the pipeline. Prior refactors failed by reorganizing without changing the data model -- this roadmap fixes that by making Phase 1 about types and tests, not code shuffling.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Package structure, data types, test infrastructure, and cornell-dev decoupling
- [ ] **Phase 2: Core Mathematics** - Port all math functions into cybir with structured types and equation citations
- [ ] **Phase 3: Pipeline & Integration** - BFS pipeline, Weyl expansion, CYTools monkey-patching, docs, and notebooks

## Phase Details

### Phase 1: Foundation
**Goal**: The cybir package exists with well-defined data types, a test suite validating those types, and zero dependency on cornell-dev
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, PKG-01, INTG-02
**Success Criteria** (what must be TRUE):
  1. `pip install -e .` succeeds and `import cybir` works in the cytools conda environment
  2. `CalabiYauLite`, `ExtremalContraction`, `ContractionType`, `InsufficientGVError`, and phase adjacency graph classes exist with documented interfaces and can be instantiated with test data
  3. Phase objects are immutable after construction (attempting mutation raises an error)
  4. All utility functions previously imported from cornell-dev `misc` and `lib.util.lattice` exist within cybir and pass tests against known inputs
  5. A test suite runs via pytest covering all data types and decoupled utilities
**Plans:** 2 plans
Plans:
- [x] 01-01-PLAN.md -- Package skeleton, core data types (CalabiYauLite, ExtremalContraction, ContractionType, InsufficientGVError), and type tests
- [x] 01-02-PLAN.md -- Utility functions (cornell-dev ports), PhaseGraph adjacency graph, and tests

### Phase 2: Core Mathematics
**Goal**: All mathematical algorithms from the original script are ported into cybir, operating on the new data types, with verified correctness against the original code
**Depends on**: Phase 1
**Requirements**: MATH-01, MATH-02, MATH-03, MATH-04, MATH-05, MATH-06
**Success Criteria** (what must be TRUE):
  1. Wall-crossing formula produces bit-for-bit identical intersection numbers and second Chern class values as the original code on test cases
  2. ExtremalContraction diagnosis correctly classifies all 5 types (asymptotic, CFT, su(2), symmetric flop, generic flop) on known examples
  3. GV series computation, potent/nilpotent classification, nop identification, and Coxeter reflection all produce identical results to the original on test cases
  4. Every math function docstring cites the relevant equation/section from arXiv:2212.10573 or arXiv:2303.00757
**Plans:** 4 plans
Plans:
- [x] 02-01-PLAN.md -- Utility additions (projected_int_nums, Coxeter functions) and ExtremalContraction field update
- [x] 02-02-PLAN.md -- Wall-crossing formula (flop.py) and GV series computation (gv.py)
- [x] 02-03-PLAN.md -- Contraction classification algorithm (classify.py)
- [x] 02-04-PLAN.md -- Re-exports, convenience methods, snapshot generation, and integration tests

### Phase 3: Pipeline & Integration
**Goal**: Users can run the full EKC construction pipeline on a CYTools CalabiYau object and access results through a clean read-only API, with Sphinx docs and example notebooks
**Depends on**: Phase 2
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04, INTG-01, INTG-03, INTG-04, PKG-02, PKG-03
**Success Criteria** (what must be TRUE):
  1. `construct_phases` BFS loop runs on h11=2 and h11=3 test cases and produces identical phase graphs to the original code
  2. Weyl orbit expansion produces the hyperextended cone matching the original code on test cases
  3. Post-construction API (`ekc.phases`, `ekc.contractions`, `ekc.coxeter_matrix`, etc.) provides read-only access to all results without ad-hoc attribute hunting
  4. CYTools monkey-patching works at Invariants, Polytope, Triangulation, and CalabiYau levels with version guards, and `cy.construct_phases()` triggers the full pipeline
  5. Sphinx documentation builds cleanly with equation references, and example notebooks for h11=2 and h11=3 run end-to-end
**Plans:** 4 plans
Plans:
- [x] 03-01-PLAN.md -- CYGraph API update, ExtremalContraction cleanup, CYBirationalClass orchestrator
- [x] 03-02-PLAN.md -- BFS builder (build_gv.py) and CYTools Invariants monkey-patches (patch.py)
- [x] 03-03-PLAN.md -- Weyl expansion (weyl.py) and package re-exports
- [x] 03-04-PLAN.md -- Sphinx documentation and example notebooks

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 2/2 | Complete | 2026-04-12 |
| 2. Core Mathematics | 4/4 | Complete | 2026-04-12 |
| 3. Pipeline & Integration | 4/4 | Complete | 2026-04-12 |
| 4. Coxeter Group & Weyl Expansion | 0/3 | Planned | - |

### Phase 4: Coxeter Group & Weyl Expansion
**Goal**: Proper Coxeter group construction from symmetric-flop reflections with finite-type detection and memory-safe enumeration, full Weyl orbit expansion acting on all phase data with correct index conventions (g on Mori, (g^-1)^T on Kahler), and generator accumulation from reflected phases
**Depends on**: Phase 3
**Requirements**: SC-1, SC-2, SC-3, SC-4, SC-5, SC-6
**Success Criteria** (what must be TRUE):
  1. `coxeter.py` constructs the Coxeter group from symmetric-flop reflection matrices using streaming BFS with memory estimation
  2. Finite type detection via positive definiteness of the bilinear form; infinite type stops and reports fundamental domain only
  3. Weyl expansion applies every group element to every fundamental-domain phase with correct index conventions (g on Mori/kappa/c2, (g^-1)^T on Kahler)
  4. Reflected phases carry properly oriented GV Invariants objects (reflected flop curve images)
  5. Infinity cone gens and effective cone gens are accumulated from all reflected phases (Kahler rays, zero-vol divisors, terminal wall curves)
  6. Only symmetric-flop Coxeter matrices are used (not su(2)); the birational geometry is the correct object
**Plans:** 3 plans

Plans:
- [x] 04-01-PLAN.md -- Coxeter group construction: order matrix, finite-type classification, streaming BFS enumeration, move functions from util.py
- [ ] 04-02-PLAN.md -- Orbit expansion: apply_coxeter_orbit with correct index conventions, graph orbit, phases=False mode, generator accumulation
- [ ] 04-03-PLAN.md -- invariants_for, to_fundamental_domain, delete weyl.py, update re-exports and tests
