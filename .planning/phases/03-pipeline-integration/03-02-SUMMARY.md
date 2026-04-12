---
phase: 03-pipeline-integration
plan: 02
subsystem: core
tags: [bfs-builder, monkey-patch, gv-propagation, invariants, flop-chain]

# Dependency graph
requires:
  - phase: 03-pipeline-integration
    plan: 01
    provides: CYGraph API, CYBirationalClass orchestrator
  - phase: 02-core-math
    provides: classify_contraction, flop_phase, gv_eff, normalize_curve
provides:
  - BFS construction via setup_root and construct_phases
  - CYTools Invariants monkey-patches (copy, flop_gvs, gv_incl_flop, gv_series_cybir, ensure_nilpotency, cone_incl_flop)
  - Entry-point patches (CalabiYau.birational_class, Polytope.birational_class)
  - Curve-sign deduplication and flop chain GV propagation
affects: [03-03, 03-04]

# Tech tracking
tech-stack:
  added: []
  patterns: [bfs-deduplication, flop-chain-gv-propagation, monkey-patching-with-version-guards]

key-files:
  created: [cybir/core/patch.py, cybir/core/build_gv.py, tests/test_build_gv.py]
  modified: []

key-decisions:
  - "Used toric_kahler_cone() and mori_cone_cap(in_basis=True) as CYTools API (not kahler_cone/mori_cone which don't exist)"
  - "Named flop-aware GV series method gv_series_cybir to avoid collision with CYTools Invariants.gv_series"
  - "Idempotent patch_cytools() with module-level _patched flag"
  - "Terminal walls (asymptotic, CFT, su2) and symmetric flops stored as self-loop edges in graph"

patterns-established:
  - "Flop chain propagation: root Invariants.flop_gvs(chain) creates topology-correct GV lookup for any phase"
  - "Curve-sign deduplication: {phase_label: {curve_tuple: sign}} dicts for O(1) phase matching"
  - "Tip retry pattern: tip_of_stretched_cone(c) with c/=10 loop, then scale back"

requirements-completed: [PIPE-01, PIPE-04, INTG-01]

# Metrics
duration: 6min
completed: 2026-04-12
---

# Phase 03 Plan 02: BFS Builder and Invariants Patches Summary

**BFS pipeline builder with curve-sign deduplication and CYTools Invariants monkey-patches for flop chain GV propagation**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-12T07:59:26Z
- **Completed:** 2026-04-12T08:05:38Z
- **Tasks:** 2
- **Files created:** 3

## Accomplishments

- Created `cybir/core/patch.py` with 6 Invariants methods (copy, flop_gvs, gv_incl_flop, gv_series_cybir, ensure_nilpotency, cone_incl_flop) faithfully translated from original lines 2530-2692
- Created `cybir/core/build_gv.py` with setup_root (geometry extraction, GV computation, root phase creation) and construct_phases (BFS loop with curve-sign dedup, flop chain propagation, generator accumulation)
- 17 unit tests for BFS helper functions (find_matching_phase, update_all_curve_signs, accumulate_generators, compute_tip)
- Version guards on patch_cytools() check for Invariants.gv method and __init__ signature compatibility
- Entry-point patches for CalabiYau.birational_class and Polytope.birational_class

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Invariants monkey-patches (patch.py)** - `762a5e1` (feat)
2. **Task 2: Create BFS builder (build_gv.py) with tests** - `43711c4` (feat)

## Files Created/Modified

- `cybir/core/patch.py` - CYTools Invariants monkey-patches with version guards and entry-point patches
- `cybir/core/build_gv.py` - BFS builder with setup_root, construct_phases, and helper functions
- `tests/test_build_gv.py` - 17 unit tests for BFS helper functions

## Decisions Made

- Used `toric_kahler_cone()` and `mori_cone_cap(in_basis=True)` as the CYTools cone API (the version in the cytools env does not have `kahler_cone()` or `mori_cone()` methods on CalabiYau)
- Named the flop-aware GV series method `gv_series_cybir` to avoid collision with the original CYTools `gv_series` method
- Made `patch_cytools()` idempotent with a module-level `_patched` flag
- Terminal walls and symmetric flops stored as self-loop edges in the graph (contraction connects phase to itself)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] CYTools API mismatch for cone methods**
- **Found during:** Task 2
- **Issue:** Plan specified `cy.kahler_cone()` and `cy.mori_cone()` but the CYTools version in the env uses `cy.toric_kahler_cone()` and `cy.mori_cone_cap(in_basis=True)` with `find_grading_vector()` for grading
- **Fix:** Used the actual CYTools API: `toric_kahler_cone()`, `mori_cone_cap(in_basis=True)`, `find_grading_vector()`
- **Files modified:** `cybir/core/build_gv.py`
- **Commit:** `43711c4`

## Issues Encountered

None beyond the API mismatch noted above.

## User Setup Required

None.

## Next Phase Readiness

- BFS builder ready for end-to-end integration testing (03-04)
- Invariants patches ready for Weyl expansion module (03-03) to use
- construct_phases populates graph, cone generators, and build log for CYBirationalClass read-only API

---
*Phase: 03-pipeline-integration*
*Completed: 2026-04-12*
