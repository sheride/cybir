---
phase: 06-classification-correctness-toric-curves-cone-construction
plan: 05
subsystem: ekc
tags: [cone-construction, movable-cone, effective-cone, ekc, hekc, diagnose-curve, toric-crosscheck]

# Dependency graph
requires:
  - phase: 06-04
    provides: toric_curves accessor, mori bounds, _toric_curve_data, _phase_types
provides:
  - Five cone construction methods (effective, movable, infinity, EKC, HEKC)
  - diagnose_curve convenience function with toric cross-check
  - All Phase 6 public API exported from cybir.core and cybir
affects: [06-06, documentation, notebooks]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Cone construction delegates to cytools.Cone(rays=...)"
    - "diagnose_curve standalone function pattern for user convenience"
    - "Toric cross-check via gv_dict lookup on ToricCurveData"

key-files:
  created: []
  modified:
    - cybir/core/ekc.py
    - cybir/core/__init__.py
    - cybir/__init__.py
    - tests/test_types.py

key-decisions:
  - "hyperextended_kahler_cone delegates to extended_kahler_cone -- identical when orbit expanded with 'hekc'"
  - "diagnose_curve is a standalone function (not a method) since it needs cy, curve, and optionally ekc"

patterns-established:
  - "Cone construction: check generators non-empty, build numpy ray array, return cytools.Cone"
  - "Toric cross-check: lookup curve_tuple and neg_tuple in gv_dict, classify by membership in flop/weyl/other lists"

requirements-completed: []

# Metrics
duration: 4min
completed: 2026-04-19
---

# Phase 06 Plan 05: Cone Construction & diagnose_curve Summary

**Five cone construction methods (effective, movable, infinity, EKC, HEKC) plus diagnose_curve convenience function with D-12 toric cross-check, all Phase 6 API exported**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-04-20T02:00:37Z
- **Completed:** 2026-04-20T02:05:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added effective_cone, movable_cone, infinity_cone, extended_kahler_cone, hyperextended_kahler_cone methods to CYBirationalClass
- Added diagnose_curve standalone function accepting CYTools Invariants or plain GV list, with toric cross-check when ekc with toric data provided
- Updated cybir/core/__init__.py and cybir/__init__.py to export all Phase 6 public API (CoxeterGroup, ToricCurveData, diagnose_curve, classify_phase_type, compute_toric_curves, induced_2face_triangulations, orient_curves_for_phase)
- Added import verification tests (test_phase6_core_imports, test_phase6_top_level_imports)

## Task Commits

Each task was committed atomically:

1. **Task 1: Cone construction methods on CYBirationalClass** - PENDING (feat)
2. **Task 2: diagnose_curve function with toric cross-check and updated re-exports** - PENDING (feat)

**Plan metadata:** PENDING (docs: complete plan)

_Note: Git commits were blocked by sandbox. All code changes are complete and verified -- commits need to be made by orchestrator._

## Files Created/Modified
- `cybir/core/ekc.py` - Added 5 cone construction methods and diagnose_curve function
- `cybir/core/__init__.py` - Added toric_curves and diagnose_curve imports/exports
- `cybir/__init__.py` - Added CoxeterGroup, ToricCurveData, diagnose_curve top-level exports
- `tests/test_types.py` - Added TestPhase6Imports class with 2 import tests

## Decisions Made
- hyperextended_kahler_cone() delegates to extended_kahler_cone() since they are identical when the orbit has been expanded with reflections='hekc'. The separate method exists for API clarity.
- diagnose_curve is a standalone function (not a CYBirationalClass method) because it needs the CYTools CalabiYau object, a curve, and optionally an ekc -- keeping it standalone avoids awkward parameter passing.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Git commit blocked by sandbox. All code changes, tests, and verifications completed successfully. Commits need to be performed by orchestrator.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All cone construction methods and diagnose_curve are in place
- All Phase 6 public API is exported
- Ready for Plan 06 (final verification/integration)

---
*Phase: 06-classification-correctness-toric-curves-cone-construction*
*Completed: 2026-04-19*

## Self-Check: PENDING

Git commits blocked by sandbox. Code changes verified via:
- `pytest tests/test_types.py`: 52 passed
- All imports verified programmatically
- All 5 cone methods exist on CYBirationalClass
- ruff check: no new errors introduced (4 pre-existing)
