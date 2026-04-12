---
phase: 04-coxeter-weyl
plan: 03
subsystem: math
tags: [coxeter, weyl, chamber-walk, gv-reconstruction, module-cleanup]

# Dependency graph
requires:
  - phase: 04-coxeter-weyl
    provides: coxeter.py with enumerate_coxeter_group, reflect_phase_data, apply_coxeter_orbit
  - phase: 03-pipeline
    provides: build_gv.py BFS pipeline, CYGraph, CalabiYauLite with curve_signs/tip
provides:
  - "to_fundamental_domain: chamber walk algorithm for Mori space points"
  - "_invariants_for_impl: on-demand GV reconstruction via curve_signs comparison"
  - "CYBirationalClass.invariants_for and to_fundamental_domain methods"
  - "weyl.py deleted, coxeter.py is single module for all Coxeter/orbit functionality"
  - "Package re-exports updated: coxeter functions directly from cybir and cybir.core"
affects: [ekc-api, documentation, monkey-patching]

# Tech tracking
tech-stack:
  added: []
  patterns: [chamber-walk-reflection, on-demand-gv-reconstruction, curve-signs-comparison]

key-files:
  created: []
  modified: [cybir/core/coxeter.py, cybir/core/ekc.py, cybir/core/build_gv.py, cybir/__init__.py, cybir/core/__init__.py, tests/test_coxeter.py]

key-decisions:
  - "_sym_flop_curves stored during BFS accumulation for chamber walk access (Approach A from plan)"
  - "to_fundamental_domain returns (point, group_element) with g @ point == original for traceability"
  - "invariants_for on root phase short-circuits to return root_invariants directly"

patterns-established:
  - "Chamber walk: repeatedly reflect through walls with negative pairing until in fundamental domain"
  - "On-demand GV: compare curve_signs dicts, flop differing curves via root_invariants.flop_gvs"
  - "Module consolidation: single coxeter.py replaces weyl.py + util.py Coxeter functions"

requirements-completed: [SC-3, SC-4, SC-5, SC-6]

# Metrics
duration: 6min
completed: 2026-04-12
---

# Phase 4 Plan 3: API Completion & Module Cleanup Summary

**Chamber walk to_fundamental_domain, on-demand invariants_for GV reconstruction, weyl.py deletion with clean coxeter.py module consolidation and updated package re-exports**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-12T19:14:52Z
- **Completed:** 2026-04-12T19:21:11Z
- **Tasks:** 2 (Task 1: TDD RED+GREEN, Task 2: cleanup)
- **Files modified:** 8

## Accomplishments
- Implemented to_fundamental_domain chamber walk with max_iter safety bound (T-04-07)
- Implemented _invariants_for_impl for on-demand GV reconstruction via curve_signs comparison (D-17)
- Added CYBirationalClass.invariants_for and to_fundamental_domain public API methods
- Deleted weyl.py entirely; coxeter.py is now the single source for all Coxeter/orbit functionality
- Updated cybir/__init__.py and cybir/core/__init__.py to export coxeter functions directly
- Added _sym_flop_curves storage during BFS for chamber walk curve access

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests** - `beb7580` (test)
2. **Task 1 (GREEN): Implementation** - `e2f72fd` (feat)
3. **Task 2: Delete weyl.py, update re-exports** - `d08b801` (feat)

## Files Created/Modified
- `cybir/core/coxeter.py` - Added to_fundamental_domain and _invariants_for_impl functions
- `cybir/core/ekc.py` - Added invariants_for, to_fundamental_domain methods and _sym_flop_curves storage
- `cybir/core/build_gv.py` - Populates _sym_flop_curves during _accumulate_generators
- `cybir/__init__.py` - Imports coxeter functions from coxeter.py, added new __all__ entries
- `cybir/core/__init__.py` - Same changes as cybir/__init__.py
- `tests/test_coxeter.py` - 8 new tests, migrated weyl comparison test to self-contained check
- `tests/test_build_gv.py` - Added _sym_flop_curves to MockEKC
- `cybir/core/weyl.py` - DELETED
- `tests/test_weyl.py` - DELETED

## Decisions Made
- **Approach A for curve storage:** Store _sym_flop_curves during BFS accumulation (not extracted from graph at query time) for reliable chamber walk access
- **Group element convention:** to_fundamental_domain returns g such that g @ mapped_point == original_point, enabling both the fundamental-domain point and the transform that produced it
- **Root phase short-circuit:** invariants_for returns root_invariants directly when phase_label == root_label, avoiding unnecessary curve_signs comparison

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added _sym_flop_curves to MockEKC in test_build_gv.py**
- **Found during:** Task 1 (GREEN)
- **Issue:** MockEKC in test_build_gv.py missing _sym_flop_curves attribute after adding storage to _accumulate_generators
- **Fix:** Added `self._sym_flop_curves = []` to MockEKC.__init__
- **Files modified:** tests/test_build_gv.py
- **Verification:** Full test suite passes (370 tests)
- **Committed in:** e2f72fd

---

**Total deviations:** 1 auto-fixed (1 Rule 3 blocking)
**Impact on plan:** Test mock update necessary for new attribute. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 4 (Coxeter Group & Weyl Expansion) is complete
- Full Coxeter pipeline operational: construction, classification, BFS enumeration, orbit expansion, chamber walk, on-demand GV reconstruction
- 370 tests passing, clean module structure with single coxeter.py
- Ready for next milestone phase (documentation, monkey-patching, or integration testing)

## Self-Check: PASSED

All files verified present/deleted, all commit hashes found in git log.

---
*Phase: 04-coxeter-weyl*
*Completed: 2026-04-12*
