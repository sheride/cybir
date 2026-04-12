---
phase: 04-coxeter-weyl
plan: 01
subsystem: math
tags: [coxeter, weyl, bfs, reflection, dynkin, group-theory, int64]

# Dependency graph
requires:
  - phase: 02-core-math
    provides: util.py with matrix_period, coxeter_reflection, coxeter_matrix
  - phase: 03-pipeline
    provides: build_gv.py BFS pipeline, CalabiYauLite, PhaseGraph
provides:
  - "coxeter.py with Coxeter group construction, type classification, BFS enumeration"
  - "CalabiYauLite curve_signs and tip persistent fields"
  - "Deprecation re-exports in util.py for backward compatibility"
affects: [04-02, 04-03, orbit-expansion, ekc-methods]

# Tech tracking
tech-stack:
  added: []
  patterns: [streaming-bfs-cayley-graph, int64-matrix-arithmetic, dynkin-diagram-classification]

key-files:
  created: [cybir/core/coxeter.py, tests/test_coxeter.py]
  modified: [cybir/core/util.py, cybir/core/types.py, cybir/core/build_gv.py]

key-decisions:
  - "Positive definiteness tolerance 1e-10 (strict) to catch affine/semi-definite cases"
  - "B_2 fixtures derived from Cartan matrix (plan-suggested matrices had wrong order)"
  - "coxeter_matrix kept as deprecated alias for coxeter_element (P-04)"

patterns-established:
  - "Streaming BFS: enumerate_coxeter_group yields int64 matrices via Cayley graph BFS with memory estimation"
  - "Deprecation re-exports: moved functions stay importable from old location with DeprecationWarning"
  - "Persistent phase data: curve_signs and tip stored on CalabiYauLite during BFS, frozen after"

requirements-completed: [SC-1, SC-2, SC-6]

# Metrics
duration: 6min
completed: 2026-04-12
---

# Phase 4 Plan 1: Coxeter Group Construction Summary

**Coxeter group construction with full Dynkin diagram classification (A_n through I_2(m)), streaming BFS enumeration with int64 arithmetic, and memory-safe seen-set estimation**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-12T18:57:53Z
- **Completed:** 2026-04-12T19:04:30Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 5

## Accomplishments
- Created cybir/core/coxeter.py as single source for all Coxeter group operations (12 functions)
- Full finite-type classification covering A_n, B_n, D_n, E_6/7/8, F_4, G_2, H_3/4, I_2(m)
- Streaming BFS enumeration with int64 arithmetic prevents float drift
- Memory estimation warns before large enumerations (T-04-01 mitigation)
- Added curve_signs and tip as persistent fields on CalabiYauLite (D-15)
- Backward-compatible deprecation re-exports in util.py (P-05)

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests** - `a3367ec` (test)
2. **Task 1 (GREEN): Implementation** - `4982f57` (feat)

## Files Created/Modified
- `cybir/core/coxeter.py` - Coxeter group construction, classification, and BFS enumeration (12 functions)
- `cybir/core/util.py` - Removed 3 functions, added deprecation re-exports
- `cybir/core/types.py` - Added curve_signs and tip fields to CalabiYauLite
- `cybir/core/build_gv.py` - Persists curve_signs and tip on phases during BFS
- `tests/test_coxeter.py` - 50 tests covering full chain from matrix_period to BFS enumeration

## Decisions Made
- **Positive definiteness tolerance:** Changed from -1e-10 to 1e-10 (strict positive) to correctly reject affine/semi-definite Coxeter groups where eigenvalues are ~0
- **B_2 fixture correction:** Plan-suggested B_2 reflections M2=[[1,1],[0,-1]] gave order 3 instead of 4; derived correct M2=[[1,2],[0,-1]] from B_2 Cartan matrix
- **Deprecated alias:** coxeter_matrix kept as deprecated alias for coxeter_element with DeprecationWarning

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed B_2 reflection matrix fixture**
- **Found during:** Task 1 (TDD GREEN)
- **Issue:** Plan-provided B_2 reflection M2=[[1,1],[0,-1]] produced product of order 3, not 4
- **Fix:** Derived correct M2=[[1,2],[0,-1]] from B_2 Cartan matrix [[2,-2],[-1,2]]
- **Files modified:** tests/test_coxeter.py
- **Verification:** matrix_period(M1 @ M2) == 4, enumerate yields 8 elements
- **Committed in:** 4982f57

**2. [Rule 1 - Bug] Fixed is_finite_type tolerance for semi-definite cases**
- **Found during:** Task 1 (TDD GREEN)
- **Issue:** Tolerance > -1e-10 accepted eigenvalue ~0 as positive, incorrectly classifying affine A_2 (triangle) as finite
- **Fix:** Changed tolerance to > 1e-10 (strictly positive)
- **Files modified:** cybir/core/coxeter.py
- **Verification:** Affine A_2 correctly detected as infinite type
- **Committed in:** 4982f57

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs)
**Impact on plan:** Both fixes necessary for mathematical correctness. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- coxeter.py provides all group construction and enumeration needed for orbit expansion (Plan 02)
- CalabiYauLite curve_signs and tip fields ready for use in apply_coxeter_orbit
- All 86 tests pass (50 coxeter + 36 types)

---
*Phase: 04-coxeter-weyl*
*Completed: 2026-04-12*
