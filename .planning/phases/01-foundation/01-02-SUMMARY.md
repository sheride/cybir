---
plan: 01-02
phase: 01-foundation
subsystem: core-utils-graph
status: complete
tags: [utilities, phase-graph, cornell-dev-decoupling, networkx, hsnf, tests]
dependency_graph:
  requires: [01-01]
  provides: [charge_matrix_hsnf, moving_cone, sympy_number_clean, tuplify, normalize_curve, projection_matrix, PhaseGraph]
  affects: [phase-02, phase-03]
tech_stack:
  added: [networkx]
  patterns: [snf-kernel-basis, undirected-phase-graph, label-keyed-nodes]
key_files:
  created:
    - cybir/core/util.py
    - cybir/core/graph.py
    - tests/test_util.py
    - tests/test_graph.py
  modified:
    - cybir/core/__init__.py
    - cybir/__init__.py
key_decisions:
  - "PhaseGraph uses phase labels (strings) as node keys, not CalabiYauLite objects directly"
  - "ExtremalContraction start_phase/end_phase store labels for graph edge keys"
  - "tuplify handles 0-d numpy arrays via ndim check (original missed this edge case)"
  - "charge_matrix_hsnf test corrected: input rows are vectors, not columns"
metrics:
  duration_seconds: 259
  completed: "2026-04-12T04:00:00Z"
  tasks_completed: 2
  tasks_total: 2
  tests_passed: 57
  tests_failed: 0
requirements:
  - INTG-02
  - DATA-05
---

# Phase 01 Plan 02: Utility Functions & PhaseGraph Summary

Six cornell-dev replacement utilities (charge_matrix_hsnf, moving_cone, sympy_number_clean, tuplify, normalize_curve, projection_matrix) plus PhaseGraph adjacency graph backed by networkx, with 27 new tests (57 total across all modules).

## Tasks Completed

### Task 1: Implement util.py with cornell-dev replacement functions (TDD)
- Created `cybir/core/util.py` with 6 functions ported from cornell-dev/dbrane-tools
- `charge_matrix_hsnf`: integer kernel basis via Smith Normal Form (from dbrane-tools)
- `moving_cone`: moving cone from charge matrix via cytools.Cone (from misc.py)
- `sympy_number_clean`: float-to-exact-rational via sympy.Rational.limit_denominator
- `tuplify`: numpy array to nested tuple, with 0-d scalar handling
- `normalize_curve`: canonical positive-first-nonzero form with optional sign return
- `projection_matrix`: orthogonal complement via SNF for curve projection
- 17 tests in `tests/test_util.py` covering all functions
- Commit: `3f1bd6d`

### Task 2: Implement PhaseGraph adjacency graph and tests (TDD)
- Created `cybir/core/graph.py` with PhaseGraph class backed by `networkx.Graph`
- Nodes keyed by phase label (string), storing CalabiYauLite in node data
- Edges store ExtremalContraction objects, keyed by start/end labels
- Properties: phases, contractions, num_phases, num_contractions
- Methods: add_phase, add_contraction, neighbors, get_phase
- Updated `cybir/core/__init__.py` to export PhaseGraph and all 6 util functions
- Updated `cybir/__init__.py` to re-export all new symbols
- 10 tests in `tests/test_graph.py` covering empty graph, node ops, edge ops, neighbor chains
- Commit: `46200a4`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed tuplify 0-d scalar handling**
- **Found during:** Task 1 GREEN phase
- **Issue:** `np.array(5).tolist()` returns `5` (not iterable), causing TypeError
- **Fix:** Added `arr.ndim == 0` check returning `arr.item()` before iteration
- **Files modified:** cybir/core/util.py
- **Commit:** 3f1bd6d

**2. [Rule 1 - Bug] Fixed charge_matrix_hsnf test data**
- **Found during:** Task 1 GREEN phase
- **Issue:** Plan's test vectors `[[1,0,1],[0,1,1]]` are 2 vectors in 3D (full rank, no relations), but test expected 1 relation. Corrected to `[[1,0],[0,1],[1,1]]` (3 vectors in 2D).
- **Fix:** Updated test data to match the documented "3 points in 2D" semantics
- **Files modified:** tests/test_util.py
- **Commit:** 3f1bd6d

## Known Stubs

None -- all functions are fully implemented with no placeholder logic.

## Self-Check: PASSED

- All 4 created files exist on disk
- Both task commits (3f1bd6d, 46200a4) found in git log
- 57/57 tests pass (30 types + 17 util + 10 graph)
- All exports importable from `cybir` and `cybir.core`
- No cornell-dev imports in cybir/
