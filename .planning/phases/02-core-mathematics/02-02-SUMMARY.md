---
phase: 02-core-mathematics
plan: 02
subsystem: mathematics
tags: [wall-crossing, gopakumar-vafa, flop, intersection-numbers, numpy]

# Dependency graph
requires:
  - phase: 02-core-mathematics/01
    provides: "CalabiYauLite, ExtremalContraction types, util.py helper functions"
provides:
  - "wall_cross_intnums: transforms intersection numbers across flop"
  - "wall_cross_c2: transforms second Chern class across flop"
  - "flop_phase: creates new CalabiYauLite from flopped phase"
  - "compute_gv_series: extracts GV series from Invariants object"
  - "compute_gv_eff: computes effective GV invariants (linear and cubic)"
  - "is_potent / is_nilpotent: curve classification predicates"
affects: [02-core-mathematics/03, 02-core-mathematics/04, 03-pipeline-integration]

# Tech tracking
tech-stack:
  added: []
  patterns: ["einsum for tensor outer products in wall-crossing", "mock-based testing for CYTools Invariants"]

key-files:
  created:
    - cybir/core/gv.py
    - tests/test_flop.py
    - tests/test_gv.py
  modified:
    - cybir/core/flop.py

key-decisions:
  - "Implemented gv.py compute_gv_eff first as stub for flop.py import dependency, then fully implemented in Task 2"

patterns-established:
  - "Raw docstrings (r-prefix) for LaTeX math in all math functions"
  - "Mock CYTools Invariants in tests to avoid CYTools import dependency"

requirements-completed: [MATH-01, MATH-03, MATH-04, MATH-06]

# Metrics
duration: 5min
completed: 2026-04-12
---

# Phase 2 Plan 2: Wall-Crossing and GV Functions Summary

**Wall-crossing formula (flop.py) and GV series computation/classification (gv.py) with equation-cited docstrings and 32 TDD tests**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-12T05:17:26Z
- **Completed:** 2026-04-12T05:22:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- 3 wall-crossing functions in flop.py: `wall_cross_intnums`, `wall_cross_c2`, `flop_phase`
- 4 GV functions in gv.py: `compute_gv_series`, `compute_gv_eff`, `is_potent`, `is_nilpotent`
- All docstrings cite arXiv:2212.10573 / arXiv:2303.00757 with equation numbers and LaTeX
- 32 passing tests (14 flop + 18 gv) covering all behaviors and edge cases

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement flop.py wall-crossing functions** - `2a9331f` (feat)
2. **Task 2: Implement gv.py GV series and curve classification** - `f183dfa` (feat)

_Both tasks followed TDD: tests written first (RED), then implementation (GREEN)._

## Files Created/Modified
- `cybir/core/flop.py` - Wall-crossing formula: `wall_cross_intnums`, `wall_cross_c2`, `flop_phase`
- `cybir/core/gv.py` - GV series: `compute_gv_series`, `compute_gv_eff`, `is_potent`, `is_nilpotent`
- `tests/test_flop.py` - 14 tests for wall-crossing functions
- `tests/test_gv.py` - 18 tests for GV functions (uses mock Invariants object)

## Decisions Made
- Implemented `compute_gv_eff` as a stub in gv.py during Task 1 to resolve the flop.py import dependency, then replaced with full implementation in Task 2
- Used mock `MockGVInvariants` class in test_gv.py instead of importing CYTools, keeping tests fast and isolated

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- flop.py and gv.py are complete and tested, ready for:
  - classify.py (Plan 3) which will use `compute_gv_eff` and `is_potent`/`is_nilpotent`
  - Pipeline integration (Phase 3) which will use `flop_phase` in the BFS loop
- All functions individually callable per D-06

## Self-Check: PASSED

- FOUND: cybir/core/flop.py
- FOUND: cybir/core/gv.py
- FOUND: tests/test_flop.py
- FOUND: tests/test_gv.py
- FOUND: commit 2a9331f (Task 1)
- FOUND: commit f183dfa (Task 2)

---
*Phase: 02-core-mathematics*
*Completed: 2026-04-12*
