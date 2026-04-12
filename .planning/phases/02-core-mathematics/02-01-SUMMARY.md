---
phase: 02-core-mathematics
plan: 01
subsystem: core-math
tags: [numpy, einsum, coxeter, reflection, lattice, hsnf, intersection-numbers]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: CalabiYauLite, ExtremalContraction types, projection_matrix utility
provides:
  - projected_int_nums function for projecting intersection number tensors
  - find_minimal_N function for integer multiplicity detection
  - matrix_period function for matrix periodicity computation
  - get_coxeter_reflection function implementing Eq. (4.6) of 2212.10573
  - coxeter_matrix function for Coxeter element computation
  - gv_series and gv_eff_1 fields on ExtremalContraction
affects: [02-02, 02-03, 02-04, 03-pipeline]

# Tech tracking
tech-stack:
  added: [functools, scipy.linalg.null_space (import)]
  patterns: [einsum-based tensor contraction, TDD red-green for math utilities]

key-files:
  created: []
  modified:
    - cybir/core/util.py
    - cybir/core/types.py
    - tests/test_util.py
    - tests/test_types.py

key-decisions:
  - "projected_int_nums uses explicit einsum subscripts per n_projected value rather than sequential contraction to avoid index collision"
  - "squeeze() applied to projected results so h11=2 full projection yields scalar while h11>2 yields (h11-1)^3 tensor"

patterns-established:
  - "Equation-cited docstrings: every math function references arXiv paper, equation number, and LaTeX"
  - "Defensive copy pattern for list fields (gv_series returns list copy)"

requirements-completed: [MATH-05, MATH-06]

# Metrics
duration: 5min
completed: 2026-04-12
---

# Phase 02 Plan 01: Utility Functions & ExtremalContraction Fields Summary

**5 Coxeter/lattice utility functions with equation-cited docstrings, plus gv_series and gv_eff_1 fields on ExtremalContraction**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-12T05:09:47Z
- **Completed:** 2026-04-12T05:15:28Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Implemented projected_int_nums, find_minimal_N, matrix_period, get_coxeter_reflection, coxeter_matrix in util.py with full arXiv equation citations
- Added gv_series and gv_eff_1 optional fields to ExtremalContraction with defensive copy and updated __repr__
- All 73 tests pass (37 in test_util.py, 36 in test_types.py)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add 5 utility functions to util.py** - `4ee913b` (test: TDD RED), `7dea8e9` (feat: TDD GREEN)
2. **Task 2: Add gv_series and gv_eff_1 fields to ExtremalContraction** - `e0efc50` (feat)

_Note: Task 1 followed TDD with separate RED and GREEN commits_

## Files Created/Modified
- `cybir/core/util.py` - Added projected_int_nums, find_minimal_N, matrix_period, get_coxeter_reflection, coxeter_matrix; added functools and scipy.linalg imports
- `cybir/core/types.py` - Added gv_series and gv_eff_1 parameters, properties, and __repr__ update to ExtremalContraction
- `tests/test_util.py` - 20 new tests across 5 test classes for the new utility functions
- `tests/test_types.py` - 7 new tests for gv_series/gv_eff_1 construction, defensive copy, defaults, and repr

## Decisions Made
- Used explicit einsum subscript strings per n_projected value instead of sequential contraction (avoids index name collision in intermediate results)
- squeeze() on projected results means h11=2 full projection yields a scalar but h11>2 yields an (h11-1)^3 tensor -- this matches the original code's behavior where the projected intersection numbers are a reduced tensor

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed projected_int_nums einsum contraction**
- **Found during:** Task 1 (TDD GREEN)
- **Issue:** Sequential einsum contraction had index collision causing incorrect tensor shapes
- **Fix:** Used explicit per-case einsum subscripts (n_projected=3/2/1 each get their own einsum call)
- **Files modified:** cybir/core/util.py
- **Verification:** All projection tests pass with correct output shapes
- **Committed in:** 7dea8e9

**2. [Rule 1 - Bug] Fixed test expectations for projected_int_nums shapes**
- **Found during:** Task 1 (TDD GREEN)
- **Issue:** Tests assumed n_projected=2 leaves (h11-1,) but it actually leaves unprojected original indices giving different shapes after squeeze
- **Fix:** Corrected expected shapes: n_projected=2 with h11=2 gives (2,), n_projected=1 gives (2,2), h11=3 full projection gives (2,2,2)
- **Files modified:** tests/test_util.py
- **Verification:** All tests pass with corrected expectations
- **Committed in:** 7dea8e9

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes were necessary for correct tensor contraction behavior. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Utility functions ready for use by classify.py (Plan 02-02/03)
- get_coxeter_reflection and coxeter_matrix satisfy MATH-05
- gv_series and gv_eff_1 fields on ExtremalContraction ready for GV pipeline (Plan 02-02)

---
*Phase: 02-core-mathematics*
*Completed: 2026-04-12*
