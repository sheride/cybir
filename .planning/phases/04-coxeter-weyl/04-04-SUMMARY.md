---
phase: 04-coxeter-weyl
plan: 04
subsystem: coxeter
tags: [coxeter, weyl, curve_signs, chamber-walk, gap-closure]

requires:
  - phase: 04-coxeter-weyl (plans 01-03)
    provides: Coxeter group BFS, orbit expansion, to_fundamental_domain, invariants_for

provides:
  - Order-safe reflection-curve pairing via _sym_flop_pairs (WR-04 fix)
  - Reflected phases with computed curve_signs and tip (SC-4 fix)
  - Safety warning in _invariants_for_impl for Weyl-expanded phases without curve_signs

affects: []

tech-stack:
  added: []
  patterns:
    - "Paired authoritative list (_sym_flop_pairs) with parallel dedup set (_sym_flop_refs)"
    - "Root phase curve_signs keys as canonical curve set for reflected phases"

key-files:
  created: []
  modified:
    - cybir/core/ekc.py
    - cybir/core/build_gv.py
    - cybir/core/coxeter.py
    - tests/test_coxeter.py
    - tests/test_build_gv.py

key-decisions:
  - "Used root phase curve_signs keys as canonical curve set for reflected phases (not fund_phase keys)"
  - "Kept _sym_flop_refs set for O(1) dedup alongside _sym_flop_pairs authoritative list"
  - "Added _root_label to all MockEKC test fixtures for consistency"

patterns-established:
  - "Paired data storage: when two collections must maintain correspondence, use a list of tuples"

requirements-completed: [SC-4]

duration: 6min
completed: 2026-04-12
---

# Phase 04 Plan 04: Gap Closure Summary

**Fixed reflection-curve pairing mismatch (WR-04) and missing curve_signs on reflected phases (SC-4) for correct Weyl-expanded GV reconstruction**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-12T19:43:10Z
- **Completed:** 2026-04-12T19:49:30Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Replaced unordered set+list pair (_sym_flop_refs/_sym_flop_curves) with authoritative _sym_flop_pairs list, fixing to_fundamental_domain pairing mismatch for multi-wall geometries
- Reflected phases from apply_coxeter_orbit now have computed tip and curve_signs, enabling invariants_for() to correctly reorient GVs for Weyl-expanded phases
- Added safety warning in _invariants_for_impl when Weyl-expanded phase has no curve_signs (IN-06)
- 4 new tests covering curve_signs propagation, tip propagation, sign differentiation, and warning emission

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace _sym_flop_refs + _sym_flop_curves with _sym_flop_pairs** - `86ceb9c` (fix)
2. **Task 2: Compute curve_signs for reflected phases in apply_coxeter_orbit** - `ae06755` (fix)

## Files Created/Modified
- `cybir/core/ekc.py` - Replaced _sym_flop_curves with _sym_flop_pairs; updated to_fundamental_domain extraction
- `cybir/core/build_gv.py` - Paired (ref, curve) storage in _accumulate_generators with dedup guard
- `cybir/core/coxeter.py` - curve_signs/tip computation for reflected phases; warning in _invariants_for_impl; reads from _sym_flop_pairs
- `tests/test_coxeter.py` - 4 new tests + _sym_flop_pairs/_root_label on all MockEKCs
- `tests/test_build_gv.py` - Updated MockEKC to use _sym_flop_pairs

## Decisions Made
- Used root phase's curve_signs keys as canonical curve set for reflected phases (ensures all phases have same key set for comparison)
- Kept _sym_flop_refs set alongside _sym_flop_pairs for O(1) membership checks and frozenset property
- Added _root_label to all MockEKC test fixtures for robustness

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added _root_label to existing MockEKC fixtures**
- **Found during:** Task 2 (curve_signs computation)
- **Issue:** Existing MockEKC test fixtures lacked _root_label attribute, causing AttributeError when apply_coxeter_orbit tried to look up root phase for curve_signs keys
- **Fix:** Added `ekc._root_label = "CY_0"` to all 7 MockEKC setups in test_coxeter.py
- **Files modified:** tests/test_coxeter.py
- **Verification:** All 80 coxeter tests pass
- **Committed in:** ae06755 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Auto-fix necessary for test compatibility. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 04 gap closure complete: SC-4 fully satisfied, WR-04 resolved
- All 374 tests pass with 0 failures
- No remaining references to _sym_flop_curves in source or test files
- Ready for phase verification re-run

---
*Phase: 04-coxeter-weyl*
*Completed: 2026-04-12*
